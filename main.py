from PIL import Image

from plugin.cast_album_art import CastPlugin
from plugin.weather import WeatherPlugin
from renderer.renderer import Anchor, Renderer

import argparse
import math
import requests
import sys
import threading
import time


class Tween:
    def __init__(self, start_value, end_value, duration):
        self._start_time = time.time()
        self._start_value = start_value
        self._end_value = end_value
        self._duration = duration
        self._current_value = start_value  

    def update(self):
        delta_value = self._end_value - self._start_value
        delta_time = (time.time() - self._start_time)
        percentage = delta_time / self._duration

        self._current_value = (delta_value * percentage) + self._start_value
        
        if self._current_value > self._end_value:
            self._current_value = self._end_value

        return self._current_value

    def current_value(self):
        return self._current_value

    def is_end(self):
        return (self._current_value == self._end_value)


class PixelFrame(threading.Thread):
    def __init__(self, renderer_sink, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = True

        self._condvar = threading.Condition()
        self._shutdown = False

        self._renderer = Renderer(renderer_sink, **kwargs)
        self._background = None
        self._plugins = []

        self._background_tween = Tween(start_value=0.0, end_value=0.5, duration=2.0)

        self._current_time = time.strftime('%-I:%M', time.localtime())
        self._begun = False
        self.start()

    def shutdown(self):
        with self._condvar:
            self._shutdown = True
            self._condvar.notify()

        self.join()

    def add_plugin(self, plugin):
        self._plugins.append(plugin)
        plugin.setup_plugin(self, self._renderer)

    def run(self):
        while True:
            with self._condvar:
                if self._shutdown:
                    return

                new_time = time.strftime('%-I:%M', time.localtime())
                if self._current_time != new_time:
                    self._current_time = new_time
                    self.update()

                if not self._background_tween.is_end() and self._begun:
                    self._background_tween.update()
                    self.update()

                if self._background_tween.is_end():
                    self._condvar.wait(timeout=0.5)

    def set_background(self, image):
        self._background = image
        self._background_tween = Tween(start_value=0.0, end_value=0.5, duration=2.0)
        self.update()
        self._begun = True

    def set_background_url(self, url):
        image = Image.open(requests.get(url, stream=True).raw)
        self.set_background(image)

    def update(self):
        if self._background:
            self._renderer.draw_image(self._background, self._background_tween.current_value())

        self._renderer.draw_string(
                time.strftime('%-I:%M', time.localtime()),
                anchor=Anchor.TOP | Anchor.LEFT)

        for plugin in self._plugins:
            plugin.update()

        self._renderer.render()


url = ('https://www2.padi.com/blog/wp-content/uploads/2015/06/'
       'manatee-crystal-river-florida-e1458927615956.jpg')


def parse_args():
    parser = argparse.ArgumentParser(description='PixelFrame application')
    parser.add_argument('-s', '--sink', default='matrix', choices=['matrix', 'image', 'gui', 'dummy'],
                    help='The type of render sink to use.')
    parser.add_argument('-n', '--number', default=32, type=int,
                    help='The number of pixels (squared) making up the display.')
    parser.add_argument('-q', '--scale', default=1, type=int,
                    help='The number of pixels (squared) representing a single virtual pixel.')
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

    instance = PixelFrame(sink, scale=args.scale)
    instance.set_background_url(url)
    instance.add_plugin(CastPlugin())
    instance.add_plugin(WeatherPlugin())
    
    sink.start()
    instance.shutdown()


if __name__ == '__main__':
    main()
