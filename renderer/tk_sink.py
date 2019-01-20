
try:
  from tkinter import *
except:
  from Tkinter import *

from renderer.renderer import RendererSink
from time import sleep

import sys

CELL_DIM = 7
CELL_PADDING = 1
WINDOW_PADDING = 5


class TkSink(RendererSink):
  def __init__(self, size):
    RendererSink.__init__(self, size)

    self._buffer = [(0, 0, 0) for i in range(size[0] * size[1])]

    width =  (size[0] * CELL_DIM) + ((size[0] - 1) * CELL_PADDING) + (WINDOW_PADDING * 2)
    height =  (size[1] * CELL_DIM) + ((size[1] - 1) * CELL_PADDING) + (WINDOW_PADDING * 2)

    root = Tk()
    root.geometry("{}x{}+0+0".format(width, height))
    self._root = root

    canvas = Canvas(root)
    canvas.pack(fill='both', expand='yes')
    canvas.configure(background='black')
    self._canvas = canvas

  def start(self):
    try:
      self._root.mainloop()
    except KeyboardInterrupt:
      sys.exit(0)

  def putpixel(self, position, color=(255, 255, 255)):
    x, y = position
    index = y * self._size[0] + x
    self._buffer[index] = color

  def render(self):
    self._root.after(0, self._render)

  def _render(self):
    for index in range(len(self._buffer)):
      position = (index % self._size[0], int(index / self._size[1]))

      x = position[0] * (CELL_DIM + CELL_PADDING) + WINDOW_PADDING
      y = position[1] * (CELL_DIM + CELL_PADDING) + WINDOW_PADDING

      color = '#%02x%02x%02x' % self._buffer[index]
      self._canvas.create_rectangle(x, y, x + CELL_DIM, y + CELL_DIM, fill=color)
