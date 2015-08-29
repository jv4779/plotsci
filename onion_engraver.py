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
import argparse

parser = argparse.ArgumentParser(description='Create a halftone using nested parallel lines.')
parser.add_argument('--img', help='image file to process', default='image.jpg')
parser.add_argument('--method', help='method to use', default='wave')
parser.add_argument('--spec', help='spec to use', default='extra_fine')
parser.add_argument('--loops', help='merge the sides of the loops', default=False, action='store_true')
args = parser.parse_args()

imagename = args.img

dxfname = imagename[0:imagename.rfind (".")]+".dxf"

dxf = plot_dxf.PlotDxf()

im = Image.open(imagename).convert("L")

pix = im.load()
image_width = float(im.size[0]);
image_height = float(im.size[1]);
screen_width = 800
screen_height = int(screen_width * image_height / image_width);

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

# return end1 moved towards end2 by offset amount
def offset_line_end1(x1, y1, x2, y2, offset):
    dx = x1 - x2
    dy = y1 - y2
    length = math.sqrt(dx * dx + dy * dy)
    dx /= length
    dy /= length
    return (x1 - dx * offset, y1 - dy * offset)

def level_line(pen, step, x1, o1, y1, x2, o2, y2, points1=None):
   # normal vector nx.ny
   nx = y2 - y1
   ny = x2 - x1
   length = math.sqrt(nx * nx + ny * ny)
   nx /= length
   ny /= length

   back_off = step / 2.0
   center_start = (o1 == 0 and o2 != 0) or (o1 != 0 and o2 == 0)
   center_line = (o1 == 0 or o2 == 0)

   # draw right side
   xo1 = x1 + o1 * nx
   yo1 = y1 - o1 * ny
   xo2 = x2 + o2 * nx
   yo2 = y2 - o2 * ny

   if points1:
      xo1 = points1[0][0]
      yo1 = points1[0][1]

   if args.loops or not center_start or o2 == 0:
      dxf.line(xo1, -yo1, xo2, -yo2, pen=pen)
   else:
       # if we are skipping loops then clip the line a little
      (x_offset, y_offset) = offset_line_end1(xo1, yo1, xo2, yo2, back_off)
      dxf.line(x_offset, -y_offset, xo2, -yo2, pen=pen)
   result = [[xo2, yo2]]

   # draw left side if it is different than right
   if o1 > 0 or o2 > 0:
      xo1 = x1 - o1 * nx
      yo1 = y1 + o1 * ny
      xo2 = x2 - o2 * nx
      yo2 = y2 + o2 * ny

      if points1:
         xo1 = points1[1][0]
         yo1 = points1[1][1]

      if args.loops or not center_line or o1 == 0:
         dxf.line(xo1, -yo1, xo2, -yo2, pen=pen)
      else:
         # if we are skipping loops then clip the line a little
         (x_offset, y_offset) = offset_line_end1(xo2, yo2, xo1, yo1, back_off)
         dxf.line(xo1, -yo1, x_offset, -y_offset, pen=pen)

   # either different left side or same as right
   result.append([xo2, yo2])
   return result

# thresholds needs to be sorted lowest to highest
# pens and thresholds need to tbe same length
def do_a_line(w, level_step, pens, thresholds):
   try:
      last_pass_o = {}
      last_pass_points = {}

      (x0, y0) = w.next()
      while 1:
         (x1, y1) = w.next()
         (x2, y2) = w.next()

         s = sampleimg(x1, y1)

         l = 0;
         for t in thresholds:
            if s <= t:
               l += 1

         # right side x offset, lowest level is outmost
         this_pass_o = {}
         this_pass_points = {}

         even_offset = 0
         if l % 2 == 0:
            even_offset = level_step / 2.0
         l = (l + 1) / 2
         for j in xrange(l):
            this_pass_o[j] = (l - j - 1) * level_step + even_offset

         for this_l, this_o in this_pass_o.items():
            pen = pens[this_l]
            if this_l in last_pass_o:
               # continue this level from last
               last_o = last_pass_o[this_l]
               this_points = level_line(pen, level_step, x0, last_o, y0, x1, this_o, y1, points1=last_pass_points[this_l])
            elif this_l == 0:
               # layer 0 continues from 0, y0
               last_o = 0
               this_points = level_line(pen, level_step, x0, last_o, y0, x1, this_o, y1)
            else:
               this_points = None
            # all layers go from y1 to y2
            this_points = level_line(pen, level_step, x1, this_o, y1, x2, this_o, y2, points1=this_points)
            this_pass_points[this_l] = this_points

         if l == 0 and 0 in last_pass_o:
            # we end so close an open 0
            pen = pens[l]
            last_o = last_pass_o[0]
            this_o = 0
            level_line(pen, level_step, x0, last_o, y0, x1, this_o, y1, points1=last_pass_points[0])

         last_pass_o = this_pass_o
         last_pass_points = this_pass_points

         (x0, y0) = (x2, y2)

   except StopIteration:
      pass

class wave_path:
   def __init__(self, x_center, y_center, offset=0, step=1, angle=0, length=1, period=1, amplitude=1):
      self.i = -length / 2.0
      self.length = length
      self.step = step
      self.period = float(period)
      self.amplitude = amplitude
      self.dx = math.sin(angle)
      self.dy = math.cos(angle)
      self.x = x_center - self.dy * offset
      self.y = y_center + self.dx * offset

   def __iter__(self):
      return self

   def next(self):
      if self.i >= self.length / 2.0:
         raise StopIteration()

      o = math.sin(self.i / self.period) * self.amplitude
      x = self.x + self.dx * self.i - o * self.dy
      y = self.y + self.dy * self.i + o * self.dx
      self.i += self.step
      #print "i=%d, x,y=%d,%d" % (self.i, x, y)
      return (x, y)

#dxf.circle(0,-0,3,pen=6)
#dxf.circle(screen_width,-screen_height,3,pen=7)

def draw_waves(spec, period=50, amplitude=20):
  print 'spec = %s' % spec

  line_length = math.sqrt(screen_width * screen_width + screen_height * screen_height)
  x_count = int(line_length / float(spec['line_spacing']))

  print 'x_count = %d' % x_count

  for wave in spec['waves']:
     print('wave %s' % str(wave))
     for i in xrange(x_count):
        w = wave_path(screen_width / 2.0, screen_height / 2.0,
                      offset = (i + 0.5 - x_count / 2.0) * spec['line_spacing'],
                      angle = wave[0],
                      step=spec['line_res'] / 2.0, length=line_length,
                      period=period, amplitude=amplitude)
        do_a_line(w, spec['level_spacing'], wave[1], [255 - i for i in wave[2]])

if args.method == 'wave':
  wave_specs = {
    'extra_fine': {
      # all waves that should be in this overlay
      'waves': [
          # [angle, pens, thresholds]
          (math.pi / 4.0, [1],       [ +80]),
          (0,             [1],       [ +140, +160]),
          (math.pi / 2.0, [1, 1], [ +100, +120, +180]),
      ],
      # distance each line is offset, screen units
      'line_spacing': 2.75,
      # distance along each line for intensity changes, screen units
      'line_res': 1,
      # distance between the onion layers, screen units
      'level_spacing': 0.8,
    },
  
    'fine': {
      # all waves that should be in this overlay
      'waves': [
          # [angle, pens, thresholds]
          (math.pi / 4.0, [1],       [ +80]),
          (0,             [1, 1, 1], [ 140,  140,  140, +140, +160]),
          (math.pi / 2.0, [1, 1, 1], [ 100, +100, +120,  180,  180, +180]),
      ],
      # distance each line is offset, screen units
      'line_spacing': 5,
      # distance along each line for intensity changes, screen units
      'line_res': 1.5,
      # distance between the onion layers, screen units
      'level_spacing': 0.8,
    },

    'marker': {
      # all waves that should be in this overlay
      'waves': [
          # [angle, pens, thresholds]
          (math.pi / 4.0, [1],    [+80]),
          (0,             [2],    [+140, +160]),
          (math.pi / 2.0, [3, 4], [+100, +120, +180]),
      ],
      # distance each line is offset, screen units
      'line_spacing': 5,
      # distance along each line for intensity changes, screen units
      'line_res': 2,
      # distance between the onion layers, screen units
      'level_spacing': 1.5,
    },
  }

  draw_waves(wave_specs[args.spec])

dxf.footer(dxfname)

