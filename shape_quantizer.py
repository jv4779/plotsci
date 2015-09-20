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

import time
import os, sys
import Image
import random
import math
import time
import argparse
import plot_dxf
from collections import namedtuple

parser = argparse.ArgumentParser(description='Convert a quantized palette image into shapes')
parser.add_argument('--dxf', help='dxf file to output', default='shapes.dxf')
parser.add_argument('--img', help='image file to process', default='image.png')
parser.add_argument('--size', help='square size', default='1')
args = parser.parse_args()

size = float(args.size)

im = Image.open(args.img)
image_width = int(im.size[0]);
image_height = int(im.size[1]);

if not im.palette:
  print 'Error: input image must have a palette'
  sys.exit (1)

pens = {}
palette_data = im.palette.getdata()[1]
count = 0
for r,g,b in zip(palette_data[::3], palette_data[1::3], palette_data[2::3]):
  c=(ord(r), ord(g), ord(b))
  if c == (255,255,255):
    p = None
  else:
    p = count+1
  pens[count] = p
  count += 1

def draw_shape(dxf, pix, x, y):
  p = pens[pix[x, y]]
  if p:
    dxf.line(size*x, -size*y, size*x+size, -(size*y+size), pen=p)
    dxf.line(size*x+size, -size*y, size*x, -(size*y+size), pen=p)

pix = im.load()

dxf = plot_dxf.PlotDxf()

for y in xrange(image_height):
  for x in xrange(image_width):
    draw_shape(dxf, pix, x, y)

dxf.footer(args.dxf)

