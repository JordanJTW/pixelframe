import colorsys
import pychromecast
import requests
import sys
import time

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pychromecast.controllers.media import MediaController
from rgbmatrix import RGBMatrix, RGBMatrixOptions


ROWS = 32
COLS = 32


def clamp(value, low=0, high=1.0):
  return max(low, min(high, value))


# def half_gradient(percent, high, low, inverse=False):
#   percent = (1.0 - percent if inverse else percent)
#   return clamp((high - low) * percent + low)


def full_gradient(percent, high, low):
  return clamp(((high - low) * 2) * abs(0.5 - percent) + low)


def blend(foreground, background, alpha=0.5):
  background = tuple(value * (1.0 - alpha) for value in background)
  foreground = tuple(value * alpha for value in foreground)
  blend = tuple(sum(values) for values in zip(foreground, background))
  return tuple(int(clamp(value, high=255)) for value in blend)


def modify_brightness(color, brightness):
  r = (color >> 16) & 0xFF
  g = (color >> 8) & 0xFF
  b = color & 0xFF
  hsv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
  return (int(value * 0xFF) for value in colorsys.hsv_to_rgb(
      hsv[0], hsv[1], hsv[2] * brightness))


def center_crop(img):
   width, height = img.size
   square = min(width, height)
   left = (width - square) / 2
   top = (height - square) / 2
   right = (width + square) / 2
   bottom = (height + square) / 2
   print('Resize to l:', left, 't:', top, 'r:', right, 'b:', bottom)
   return img.crop((left, top, right, bottom))


def draw_image(matrix, image):
  for row in range(ROWS):
    for col in range(COLS):
      pixel = image.getpixel((col, row))
      # Diag: (r/ROWS) * 0.5 + (c/COLS) * 0.5
      # Diag (inverse): abs((r/ROWS) * 0.5 - (c/COLS) * 0.5)
      # alpha = full_gradient(row / ROWS, low=0.3, high=0.75)
      alpha = 0
      color = int('%02x%02x%02x' % blend((0, 0, 0), pixel, alpha), 16)
      (r, g, b) = modify_brightness(color, brightness=1)
      matrix.SetPixel(col, row, r, g, b)


def draw_url(matrix, image_url):
  print("Loading:", image_url)
  source = BytesIO(requests.get(image_url).content)
  image = center_crop(Image.open(source)).resize((ROWS, COLS))
  draw_image(matrix, image.convert('RGB'))


class CastMediaListener(object):
  def __init__(self, matrix):
    self._image_url = None
    self._matrix = matrix

  def new_media_status(self, status):
    image_size = None
    image_url = None

    print(status)

    for image in status.images:
      print('Checking:', image_url, 'size:', image.width)
      size = image.height * image.width

      if (not image_size or size < image_size) and image.url:
        image_size = size
        image_url = image.url

    if image_url and self._image_url != image_url:
      print('Update to:', image_url)
      self._image_url = image_url
      draw_url(self._matrix, image_url)

    print(status)


def main():
  # Configuration for the matrix
  options = RGBMatrixOptions()
  options.rows = 32
  options.chain_length = 1
  options.parallel = 1
  options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'

  matrix = RGBMatrix(options=options)

  draw_url(matrix, sys.argv[1])

  # draw_url(matrix, 'https://kids.nationalgeographic.com/content/dam/kids/photos/animals/Invertebrates/H-P/octopus-ocean-floor.ngsversion.1412640166412.jpg')

  # draw_url(matrix, 'http://www.greatbarrierreefs.com.au/wp-content/uploads/YEAH-EAT-IT.jpg')

  media = MediaController()
  listener = CastMediaListener(matrix)
  media.register_status_listener(listener)

  for cast in pychromecast.get_chromecasts():
    cast.register_handler(media)
  
  try:
    print("Press CTRL-C to stop.")
    while True:
        time.sleep(100)
  except KeyboardInterrupt:
    sys.exit(0)


if __name__ == '__main__':
  main()
