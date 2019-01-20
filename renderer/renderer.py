from asset.font import FONT
from enum import Flag, auto
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


class Alignment(Flag):
    ANCHOR_LEFT = auto()
    ANCHOR_RIGHT = auto()
    ANCHOR_TOP = auto()
    ANCHOR_BOTTOM = auto()
    ANCHOR_CENTER_X = auto()
    ANCHOR_CENTER_Y = auto()


class Renderer:
    def __init__(self, sink):
        print('Renderer init(%dx%d)' % sink.size())
        print('Renderer sink: %s' % (sink.__class__.__name__))

        self._window_width, self._window_height = sink.size()
        self._buffer = [
            (0, 0, 0) for i in range(self._window_width * self._window_height)]
        self._sink = sink

    def draw_image(self, image, brightness):
        image = center_crop(image).convert("RGB")
        image = image.resize((self._window_width, self._window_height))

        for y in range(self._window_height):
            for x in range(self._window_width):
                color = image.getpixel((x, y))
                self.putpixel((x, y), color, brightness)

    def draw_char(self, char, x, y, color):
        font_width, font_height = FONT['font_dimens']

        width = FONT[char].get('width', font_width)
        width_offset = (font_width - width)

        for dy in range(font_height):
            for dx in range(font_width):
                position = (x + dx - width_offset, y + dy)

                if FONT[char]['data'][dy * font_width + dx]:
                    self.putpixel(position, color)

        return x + width

    def draw_string(self, string,
                    anchor=Alignment.ANCHOR_LEFT, color=None,
                    padding=1, spacing=1):
        font_width, font_height = FONT['font_dimens']

        def calc_length():
            length = 0
            for char in string:
                length += FONT[char].get('width', font_width) + spacing
            return length

        def calc_x():
            if anchor & Alignment.ANCHOR_LEFT:
                return padding
            if anchor & Alignment.ANCHOR_RIGHT:
                return self._window_width - calc_length() - padding + spacing

            return math.ceil((self._window_width - calc_length()) / 2)

        def calc_y():
            if anchor & Alignment.ANCHOR_TOP:
                return padding
            if anchor & Alignment.ANCHOR_BOTTOM:
                return self._window_height - font_height - padding

            return math.ceil((self._window_height - font_height) / 2)

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

        for char in string:
            x = self.draw_char(char, x, y, color) + spacing

    def putpixel(self, position, color, brightness=1.0):
        x, y = position
        if (x < 0 or x >= self._window_width) or (
                y < 0 or y >= self._window_height):
            raise Exception('({}, {}) is out of bounds.'.format(x, y))

        index = y * self._window_width + x
        color = color if brightness == 1.0 else modify_brightness(color, brightness)
        self._buffer[index] = color

    def render(self):
        for index in range(len(self._buffer)):
            position = (
                index %
                self._window_width, int(
                    index / self._window_width))
            self._sink.putpixel(position, self._buffer[index])

        self._sink.render()
