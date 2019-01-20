from renderer.renderer import RendererSink
from rgbmatrix import RGBMatrix, RGBMatrixOptions


class MatrixSink(RendererSink):
    def __init__(self, size):
        RendererSink.__init__(self, size)

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
        pass

    def size(self):
        return self._size