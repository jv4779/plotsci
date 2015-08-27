#!/usr/bin/python
#
#       Copyright (C) 2015 Jeremy Van Grinsven
#
#       This file is part of plotsci.
#
#       plotsci is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       plotsci is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with crosshatcher; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import sdxf

BLACK = 1
RED = 2
GREEN = 3
BLUE = 4
CYAN = 5
YELLOW = 6
MAGENTA = 7
PEN_8 = 8

_pen_to_color = {
  BLACK:   7,
  RED:     1,
  GREEN:   3,
  BLUE:    5,
  CYAN:    4,
  YELLOW:  2,
  MAGENTA: 6,
  PEN_8:   8,
}

class PlotDxf():

  def __init__(self):
    # create a layer for each pen and give it a matching color
    layers = [sdxf.Layer(name=str(pen), color=_pen_to_color[pen]) for pen in xrange(1,9)]
    self.dxf = sdxf.Drawing(layers=layers)

  def line(self, x1, y1, x2, y2, pen=1, **kwargs):
    # pen maps to a specific layer
    self.dxf.append(sdxf.Line(
        points=[(x1, y1), (x2, y2)], layer=pen, **kwargs
    ))

  def circle(self, x, y, r, pen=1, **kwargs):
    # pen maps to a specific layer
    self.dxf.append(sdxf.Circle(
        center=(x, y), radius=r, layer=pen, **kwargs
    ))

  def footer(self, filename):
    self.dxf.saveas(filename)

