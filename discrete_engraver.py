#!/usr/bin/python
#
#       Copyright (C) 2015 Jeremy Van Grinsven
#       Copyright (C) 2013 Stephen M. Cameron
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
import plot_dxf

imagename = "image.jpg";
if (len(sys.argv) >= 2):
  imagename = sys.argv[1];

dxfname = imagename[0:imagename.rfind (".")]+".dxf"

dxf = plot_dxf.PlotDxf()

im = Image.open(imagename).convert("L")

pix = im.load()
image_width = float(im.size[0]);
image_height = float(im.size[1]);
screen_width = 800
screen_height = int(screen_width * image_height / image_width);
print image_width, image_height, screen_width, screen_height

# origin on screen
osx = 0
osy = 0

# distance each line is offset, screen units
line_spacing = 8
# distance along each line for intensity changes, screen units
line_res = 3
# number of total levels of line intensity, screen units
line_levels = 7
line_level_spacing = 1

if screen_width > screen_height:
   radius = math.sqrt(2.0) * (1.1 * screen_width)

# screen x to image x
def sxtoix(sx):
  return (image_width * sx) / screen_width;

def sytoiy(sy):
  return (image_height * sy) / screen_height;

def sampleimg(sx, sy):
   ix = sxtoix(sx)
   iy = sytoiy(sy)
   if ix < 0:
      return 257
   if iy < 0:
      return 257
   if ix >= image_width:
      return 257
   if iy >= image_height:
      return 257
   return pix[ix, iy]

def do_a_line(thresholds, x):
   for i in xrange(int(screen_height / float(line_res))):
      s = sampleimg(x, i * line_res + line_res / 2.0)

      l = 0;
      for t in thresholds:
         if s <= t:
            l += 1
      # keep it odd
      if l > 0 and l % 2 == 0:
         l -= 1

      for o in xrange(l):
         x_o = (o - l / 2.0) * line_level_spacing 
         x1 = x + x_o
         y1 = i * line_res
         x2 = x + x_o
         y2 = (i + 1) * line_res
         dxf.line(x1, -y1, x2, -y2)

x_count = int(screen_width / float(line_spacing))
thresholds = [i * 256 / line_levels for i in xrange(line_levels)]

print 'x_count = %d' % x_count
print 'thresholds = %s' % thresholds

for i in xrange(x_count):
   print('line %d' % i)
   do_a_line(thresholds, i * line_spacing)

dxf.footer(dxfname)

