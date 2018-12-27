from PIL import Image

import colorgram
import colorsys
import math
import requests


FONT = {
  'font_dimens': (3, 5),

  '0': {
    'data': [
      1, 1, 1,
      1, 0, 1,
      1, 0, 1,
      1, 0, 1,
      1, 1, 1,
    ],
  },
  '1': {
    'data': [
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
      0, 0, 1,
    ],
    'width': 1,
  },
  '2': {
    'data': [
      1, 1, 1,
      0, 0, 1,
      1, 1, 1,
      1, 0, 0,
      1, 1, 1,
    ],
  },
  '3': {
    'data': [
      1, 1, 1,
      0, 0, 1,
      0, 1, 1,
      0, 0, 1,
      1, 1, 1,
    ],
  },
  '4': {
    'data': [
      1, 0, 1,
      1, 0, 1,
      1, 1, 1,
      0, 0, 1,
      0, 0, 1,
    ],
  },
  '5': {
    'data': [
      1, 1, 1,
      1, 0, 0,
      1, 1, 1,
      0, 0, 1,
      1, 1, 1,
    ],
  },
  '6': {
    'data': [
      1, 1, 1,
      1, 0, 0,
      1, 1, 1,
      1, 0, 1,
      1, 1, 1,
    ],
  },
  '7': {
    'data': [
      1, 1, 1,
      0, 0, 1,
      0, 1, 0,
      1, 0, 0,
      1, 0, 0,
    ],
  },
  '8': {
    'data': [
      1, 1, 1,
      1, 0, 1,
      1, 1, 1,
      1, 0, 1,
      1, 1, 1,
    ],
  },
  '9': {
    'data': [
      1, 1, 1,
      1, 0, 1,
      1, 1, 1,
      0, 0, 1,
      0, 0, 1,
    ],
  },
  ':': {
    'data': [
      0, 0, 0,
      0, 0, 1,
      0, 0, 0,
      0, 0, 1,
      0, 0, 0,
    ],
    'width': 1,
  },
}


def center_crop(img):
  width, height = img.size
  square = min(width, height)
  left = (width - square) / 2
  top = (height - square) / 2
  right = (width + square) / 2
  bottom = (height + square) / 2
  return img.crop((left, top, right, bottom))


# def draw_colors(colors):
#   img = Image.new("RGB", (1, len(colors)))

#   for index in range(len(colors)):
#     rgb = colors[index]
#     img.putpixel((0, index), rgb)

#   img.show()


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
    options = RGBMatrixOptions()
    options.rows = size[0]
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'

    self._matrix = RGBMatrix(options=options)
    self._size = size

  def putpixel(self, position, color):
    self._matrix.SetPixel(*position, *color)

  def render(self):
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


  def draw_char(self, char, x, y):
    font_width, font_height = FONT['font_dimens']

    width = FONT[char].get('width', font_width)
    width_offset = (font_width - width)

    for dy in range(font_height):
      for dx in range(font_width):
        position = (x + dx - width_offset, y + dy)

        if FONT[char]['data'][dy * font_width + dx]:
          self.putpixel(position, (255, 255, 255))

    return x + width


  def draw_string(self, string, anchor = ANCHOR_LEFT, padding = 1, spacing = 1):
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
      x = self.draw_char(char, x, y) + spacing


  def putpixel(self, position, color):
    x, y = position
    if (x < 0 or x >= self._window_width) or (y < 0 or y >= self._window_height):
      raise Exception('({}, {}) is out of bounds.'.format(x, y))

    index = y * self._window_width + x
    self._buffer[index] = color


  def render(self):
    for index in range(len(self._buffer)):
      position = (index % self._window_width, int(index / self._window_width))
      self._sink.putpixel(position, self._buffer[index])

    self._sink.render()


def main():
  url = "https://www.greatbarrierreefs.com.au/wp-content/uploads/YEAH-EAT-IT-1024x678.jpg"
  img = Image.open(requests.get(url, stream=True).raw)
  # center_crop(img).show()

  # NUM_COLORS = 25
  # colors = colorgram.extract(requests.get(url, stream=True).raw, NUM_COLORS)

  # rgb = [color.rgb for color in colors];

  # draw_colors(rgb)

  # s = sorted((colorsys.rgb_to_hsv(*color) for color in rgb), key=lambda c: c[0])
  # draw_colors([tuple(int(v) for v in colorsys.hsv_to_rgb(*r)) for r in s])

  # center_crop(img).resize((32, 32)).show()

  # x = 0
  # for val in range(8):
  #   x = draw_char(img, val, x + 1, 1)

  # draw_char(img, ':', 1, 6)

  # x = 0
  # for char in '12:34':
    # x = draw_char(img, char, x + 1, 15)

  sink = ImageRendererSink((32, 32))
  renderer = Renderer(sink)

  renderer.draw_image(img)

  renderer.draw_string('1:', anchor=ANCHOR_LEFT | ANCHOR_TOP)
  renderer.draw_string('2:', anchor=ANCHOR_LEFT)
  renderer.draw_string('3:', anchor=ANCHOR_LEFT | ANCHOR_BOTTOM)
  renderer.draw_string(':4', anchor=ANCHOR_BOTTOM)
  renderer.draw_string(':5', anchor=ANCHOR_RIGHT | ANCHOR_BOTTOM)
  renderer.draw_string(':6', anchor=ANCHOR_RIGHT)
  renderer.draw_string('7:', anchor=ANCHOR_RIGHT | ANCHOR_TOP)
  renderer.draw_string('8:', anchor=ANCHOR_TOP)
  renderer.draw_string('9:', anchor=ANCHOR_CENTER_X | ANCHOR_CENTER_Y)

  renderer.render()

if __name__ == '__main__':
  main()

