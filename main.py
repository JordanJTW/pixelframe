from PIL import Image
from plugin.cast_album_art import CastPlugin
from renderer.renderer import Alignment, Renderer
from time import localtime, strftime

import argparse
import math
import requests
import sys
import threading


class PixelFrame(threading.Thread):
    def __init__(self, renderer_sink):
        threading.Thread.__init__(self)
        self.daemon = True

        self._condvar = threading.Condition()
        self._shutdown = False

        self._renderer = Renderer(renderer_sink)
        self._background = None
        self._plugins = []

        self.start()

    def shutdown(self):
        with self._condvar:
            self._shutdown = True
            self._condvar.notify()

        self.join()

    def add_plugin(self, plugin):
        self._plugins.append(plugin)
        plugin.setup_plugin(self)

    def run(self):
        while True:
            with self._condvar:
                if self._shutdown:
                    return

                self._condvar.wait()

    def set_background(self, image):
        self._background = image
        self.update()

    def set_background_url(self, url):
        image = Image.open(requests.get(url, stream=True).raw)
        self.set_background(image)

    def update(self):
        if self._background:
            self._renderer.draw_image(self._background, 0.5)
        self._renderer.draw_string(
                strftime('%-I:%M', localtime()),
                anchor=Alignment.ANCHOR_BOTTOM | Alignment.ANCHOR_RIGHT)
        self._renderer.render()


url = ('https://www2.padi.com/blog/wp-content/uploads/2015/06/'
       'manatee-crystal-river-florida-e1458927615956.jpg')


def parse_args():
    parser = argparse.ArgumentParser(description='PixelFrame application')
    parser.add_argument('-s', '--sink', default='matrix', choices=['matrix', 'image', 'gui', 'dummy'],
                    help='The type of render sink to use.')
    parser.add_argument('-n', '--number', default=32, type=int,
                    help='The number of pixels (squared) making up the display.')
    return parser.parse_args()


def main():
    args = parse_args()

    dimensions = (args.number, args.number)

    if args.sink == 'matrix':
        from renderer.matrix_sink import MatrixSink
        sink = MatrixSink(dimensions)
    elif args.sink == 'image':
        from renderer.image_sink import ImageSink
        sink = ImageSink(dimensions)
    elif args.sink == 'gui':
        from renderer.tk_sink import TkSink
        sink = TkSink(dimensions)
    elif args.sink == 'dummy':
        from renderer.renderer import RendererSink
        sink = RendererSink(dimensions)

    instance = PixelFrame(sink)
    instance.set_background_url(url)
    instance.add_plugin(CastPlugin(instance))
    
    sink.start()
    instance.shutdown()


if __name__ == '__main__':
    main()
