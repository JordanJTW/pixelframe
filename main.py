from PIL import Image
from time import localtime, sleep, strftime

import math
import requests

from font import FONT

def center_crop(image):
    width, height = image.size
    square = min(width, height)
    left = (width - square) / 2
    top = (height - square) / 2
    right = (width + square) / 2
    bottom = (height + square) / 2
    return image.crop((left, top, right, bottom))


ANCHOR_LEFT = 1 << 0
ANCHOR_RIGHT = 1 << 1
ANCHOR_TOP = 1 << 2
ANCHOR_BOTTOM = 1 << 3
ANCHOR_CENTER_X = 1 << 4
ANCHOR_CENTER_Y = 1 << 5


class RendererSink:
    def putpixel(self, position, color):
        pass

    def render(self):
        pass

    def size(self):
        pass


class ImageRendererSink(RendererSink):
    def __init__(self, size):
        self._image = Image.new("RGB", size)
        self._size = size

    def putpixel(self, position, color):
        self._image.putpixel(position, color)

    def render(self):
        self._image.show()

    def size(self):
        return self._size


class MatrixRendererSink(RendererSink):
    def __init__(self, size):
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

        options = RGBMatrixOptions()
        options.rows = 32
        options.chain_length = 1
        options.parallel = 1
        # If you have an Adafruit HAT: 'adafruit-hat'
        options.hardware_mapping = 'adafruit-hat'

        self._matrix = RGBMatrix(options=options)
        self._size = size

    def putpixel(self, position, color):
        x, y = position
        self._matrix.SetPixel(x, y, *color)

    def render(self):
        while True:
            pass

    def size(self):
        return self._size


class Renderer:
    def __init__(self, sink):
        self._window_width, self._window_height = sink.size()
        self._buffer = [
            (0, 0, 0) for i in range(self._window_width * self._window_height)]
        self._sink = sink

    def draw_image(self, image):
        image = center_crop(image)
        image = image.resize((self._window_width, self._window_height))

        for y in range(self._window_height):
            for x in range(self._window_width):
                color = image.getpixel((x, y))
                self.putpixel((x, y), color)

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
                    anchor=ANCHOR_LEFT, color=(255, 255, 255),
                    padding=1, spacing=1):
        font_width, font_height = FONT['font_dimens']

        def calc_length():
            length = 0
            for char in string:
                length += FONT[char].get('width', font_width) + spacing
            return length

        def calc_x():
            if anchor & ANCHOR_LEFT:
                return padding
            if anchor & ANCHOR_RIGHT:
                return self._window_width - calc_length() - padding + spacing

            return math.ceil((self._window_width - calc_length()) / 2)

        def calc_y():
            if anchor & ANCHOR_TOP:
                return padding
            if anchor & ANCHOR_BOTTOM:
                return self._window_height - font_height - padding

            return math.ceil((self._window_height - font_height) / 2)

        x = calc_x()
        y = calc_y()

        for char in string:
            x = self.draw_char(char, x, y, color) + spacing

    def putpixel(self, position, color):
        x, y = position
        if (x < 0 or x >= self._window_width) or (
                y < 0 or y >= self._window_height):
            raise Exception('({}, {}) is out of bounds.'.format(x, y))

        index = y * self._window_width + x
        self._buffer[index] = color

    def render(self):
        for index in range(len(self._buffer)):
            position = (
                index %
                self._window_width, int(
                    index / self._window_width))
            self._sink.putpixel(position, self._buffer[index])

        self._sink.render()


url = ("https://www.greatbarrierreefs.com.au/wp-content/uploads/"
       "YEAH-EAT-IT-1024x678.jpg")


def main():
    img = Image.open(requests.get(url, stream=True).raw)

    sink = ImageRendererSink((32, 32))
    renderer = Renderer(sink)

    while True:
        renderer.draw_image(img)
        renderer.draw_string(strftime('%I:%M', localtime()),
                             color=(255, 0, 0),
                             anchor=ANCHOR_BOTTOM | ANCHOR_RIGHT)

    # renderer.draw_string('1:', anchor=ANCHOR_LEFT | ANCHOR_TOP)
    # renderer.draw_string('2:', anchor=ANCHOR_LEFT)
    # renderer.draw_string('3:', anchor=ANCHOR_LEFT | ANCHOR_BOTTOM)
    # renderer.draw_string(':4', anchor=ANCHOR_BOTTOM)
    # renderer.draw_string(':5', anchor=ANCHOR_RIGHT | ANCHOR_BOTTOM)
    # renderer.draw_string(':6', anchor=ANCHOR_RIGHT)
    # renderer.draw_string('7:', anchor=ANCHOR_RIGHT | ANCHOR_TOP)
    # renderer.draw_string('8:', anchor=ANCHOR_TOP)
    # renderer.draw_string('9:', anchor=ANCHOR_CENTER_X | ANCHOR_CENTER_Y)

        renderer.render()
        sleep(60)


if __name__ == '__main__':
    main()
