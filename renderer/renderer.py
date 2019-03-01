from asset.font import FONT
from enum import IntEnum
from PIL import Image
from time import sleep

import colorsys
import math
import sys


def center_crop(image):
    width, height = image.size
    square = min(width, height)
    left = (width - square) / 2
    top = (height - square) / 2
    right = (width + square) / 2
    bottom = (height + square) / 2
    return image.crop((left, top, right, bottom))


def modify_brightness(color, brightness):
    r, g, b = color
    hsv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return tuple(int(value * 0xFF) for value in colorsys.hsv_to_rgb(
            hsv[0], hsv[1], hsv[2] * brightness))


class RendererSink:
    def __init__(self, size):
        self._size = size

    def start(self):
        while True:
            try:
                print('Press Ctrl+C to quit.')
                sleep(1000)
            except KeyboardInterrupt:
                sys.exit(0)

    def putpixel(self, position, color):
        pass

    def render(self):
        pass

    def size(self):
        return self._size


class Anchor(IntEnum):
    LEFT = 1 << 0
    RIGHT = 1 << 1
    TOP = 1 << 2
    BOTTOM = 1 << 3
    CENTER_X = 1 << 4
    CENTER_Y = 1 << 5
    CENTER = CENTER_X | CENTER_Y


class Renderer:
    def __init__(self, sink, scale=1):
        print('Renderer init(%dx%d) scale: %d' % (*sink.size(), scale))
        print('Renderer sink: %s' % (sink.__class__.__name__))

        self._scale = scale
        self._window_width, self._window_height = sink.size()
        self._buffer = [
            (0, 0, 0) for i in range(self._window_width * self._window_height)]
        self._sink = sink

    def draw_bitmap(self, bitmap, x, y):
        data = bitmap['data']
        width = bitmap['width']
        height = int(len(data) / width)

        def hex_to_rgb(value):
            value = hex(value).lstrip('0x')
            lv = len(value)
            return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

        for dx in range(width):
            for dy in range(height):
                value = data[dy * width + dx]

                if not value:
                    continue
          
                color = hex_to_rgb(bitmap['pallete'][value - 1])
                self.putpixel((x + self._scale * dx, y + self._scale * dy), color, self._scale)

    def draw_image(self, image, brightness):
        image = center_crop(image).convert("RGB")
        image = image.resize((self._window_width, self._window_height))

        for y in range(self._window_height):
            for x in range(self._window_width):
                color = image.getpixel((x, y))
                # Images should always have a scale of 1.0:
                self.putpixel((x, y), color, brightness, scale=1)

    def draw_char(self, char, x, y, color, scale=None):
        font_width, font_height = FONT['font_dimens']
        scale = scale if scale else self._scale

        width = FONT[char].get('width', font_width)
        width_offset = (font_width - width)

        for dy in range(font_height):
            for dx in range(font_width):
                position = (x + ((dx - width_offset) * scale), y + (dy * scale))

                if FONT[char]['data'][dy * font_width + dx]:
                    self.putpixel(position, color, scale)

        return x + (width * scale)

    def draw_string(self, string,
                    anchor=Anchor.LEFT, color=None,
                    padding=1, spacing=1, icon=None, scale=None):
        font_width, font_height = FONT['font_dimens']
        bitmap, alignment = icon if icon else (None, None)

        scale = scale if scale else self._scale
        scaled_spacing = spacing * scale
        scaled_padding = padding * scale

        def calc_length():
            length = 0
            for char in string:
                length += FONT[char].get('width', font_width) + spacing
            return (length - spacing) * scale

        def calc_x():
            if anchor & Anchor.LEFT:
                return scaled_padding
            if anchor & Anchor.RIGHT:
                x = self._window_width - calc_length() - scaled_padding
                return x if not bitmap else x - bitmap['width'] * scale - scaled_spacing

            return math.ceil((self._window_width - calc_length()) / 2)

        def calc_y():
            if anchor & Anchor.TOP:
                return scaled_padding
            if anchor & Anchor.BOTTOM:
                return self._window_height - font_height * scale - scaled_padding

            return math.ceil((self._window_height - font_height * scale) / 2)

        x = calc_x()
        y = calc_y()

        if color is None:
            total_pixels = font_height * calc_length()
            sum_color = (0, 0, 0)
            for dx in range(calc_length()):
                for dy in range(font_height):
                    cell_color = self._buffer[
                            (dy + y) * self._window_width + (dx + x)]
                    sum_color = tuple(
                            sum(x) for x in zip(sum_color, cell_color))

            color = tuple(int(x/total_pixels) for x in sum_color)
            color = tuple(255 if x < 128 else 0 for x in color)

        if icon and alignment is Anchor.LEFT:
            self.draw_bitmap(bitmap, x, y)
            x = x + bitmap['width'] + spacing

        for char in string:
            x = self.draw_char(char, x, y, color, scale) + scaled_spacing

        if icon and alignment is Anchor.RIGHT:
            self.draw_bitmap(bitmap, x, y)

    def putpixel(self, position, color, brightness=1.0, scale=None):
        x, y = position
        if (x < 0 or x >= self._window_width) or (
                y < 0 or y >= self._window_height):
            raise Exception('({}, {}) is out of bounds.'.format(x, y))

        color = color if brightness == 1.0 else modify_brightness(color, brightness)
        scale = scale if scale else self._scale

        for sx in range(scale):
            for sy in range(scale):
                index = (y + sy) * self._window_width + (x + sx)
                self._buffer[index] = color

    def render(self):
        for index in range(len(self._buffer)):
            position = (
                index %
                self._window_width, int(
                    index / self._window_width))
            self._sink.putpixel(position, self._buffer[index])

        self._sink.render()
