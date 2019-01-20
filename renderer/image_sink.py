from PIL import Image
from renderer.renderer import RendererSink

class ImageSink(RendererSink):
    def __init__(self, size):
        RendererSink.__init__(self, size)

        self._image = Image.new("RGB", size)
        self._size = size

    def putpixel(self, position, color):
        self._image.putpixel(position, color)

    def render(self):
        self._image.show()

    def size(self):
        return self._size
