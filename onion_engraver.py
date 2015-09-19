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
parser.add_argument('--method', help='method to use', default='waves')
parser.add_argument('--spec', help='spec to use', default=None)
parser.add_argument('--loops', help='merge the sides of the loops', default=False, action='store_true')
parser.add_argument('--rotate', help='degrees to rotate pattern', default=0)
parser.add_argument('--pen', help='default pen number', default=1)
args = parser.parse_args()

imagename = args.img
default_pen = int(args.pen)

dxfname = imagename[0:imagename.rfind (".")]+".dxf"

dxf = plot_dxf.PlotDxf()

im = Image.open(imagename)
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

# return
#  -1 for out of bounds
#  0 for lightest
#  255 for darkest
def sampleimg(pix, sx, sy):
   ix = sxtoix(sx)
   iy = sytoiy(sy)
   if ix < 0:
      return -1
   if iy < 0:
      return -1
   if ix >= image_width:
      return -1
   if iy >= image_height:
      return -1
   return 255 - pix[ix, iy]

# return end1 moved towards end2 by offset amount
def offset_line_end1(x1, y1, x2, y2, offset):
    dx = x1 - x2
    dy = y1 - y2
    length = math.sqrt(dx * dx + dy * dy)
    dx /= length
    dy /= length
    return (x1 - dx * offset, y1 - dy * offset)

def level_line(pen1, pen2, step, x1, o1, y1, x2, o2, y2, points1=None):
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
   prev_line1 = None
   xo1 = x1 + o1 * nx
   yo1 = y1 - o1 * ny
   xo2 = x2 + o2 * nx
   yo2 = y2 - o2 * ny

   if points1:
      prev_line1 = points1[0][2]
      xo1 = points1[0][0]
      yo1 = points1[0][1]

   if pen1 is not None:
      if args.loops or not center_start or o2 == 0:
         # try and extend an existing line
         if prev_line1:
            prev_line1.points.append((xo2, -yo2))
         else:
            prev_line1 = dxf.polyline(xo1, -yo1, xo2, -yo2, pen=pen1)
      else:
         # if we are skipping loops then clip the line a little, starting a
         # a new line
         (x_offset, y_offset) = offset_line_end1(xo1, yo1, xo2, yo2, back_off)
         prev_line1 = dxf.polyline(x_offset, -y_offset, xo2, -yo2, pen=pen1)
   else:
     prev_line1 = None
   result = [[xo2, yo2, prev_line1]]

   # draw left side if it is different than right
   if o1 > 0 or o2 > 0:
      prev_line2 = None
      xo1 = x1 - o1 * nx
      yo1 = y1 + o1 * ny
      xo2 = x2 - o2 * nx
      yo2 = y2 + o2 * ny

      if points1:
         prev_line2 = points1[1][2]
         xo1 = points1[1][0]
         yo1 = points1[1][1]

      if pen2 is not None:
         if args.loops or not center_line or o1 == 0:
            # try and extend an existing line
            if prev_line2:
               prev_line2.points.append((xo2, -yo2))
            else:
               prev_line2 = dxf.polyline(xo1, -yo1, xo2, -yo2, pen=pen2)
         else:
            # if we are skipping loops then clip the line a little
            (x_offset, y_offset) = offset_line_end1(xo2, yo2, xo1, yo1, back_off)
            if prev_line2:
               # we are breaking this line, so extend it and no prev
               prev_line2.points.append((x_offset, -y_offset))
            else:
               dxf.polyline(xo1, -yo1, x_offset, -y_offset, pen=pen2)
            # since this is broken there is no prev
            prev_line2 = None
   else:
      # a single line in the middle, same xo2, xo2, and prev_line
      prev_line2 = prev_line1


   # either different left side or same as right
   result.append([xo2, yo2, prev_line2])
   return result

# thresholds needs to be sorted lowest to highest
# pens and thresholds need to tbe same length
def do_a_path(w, pix, level_step, pens, thresholds):
   assert len(pens) == len(thresholds), 'lens and thresholds must have the same element count'
   try:
      last_pass_o = {}
      last_pass_points = {}

      (x0, y0) = w.next()
      while 1:
         (x1, y1) = w.next()
         (x2, y2) = w.next()

         s = sampleimg(pix, x1, y1)

         l = 0;
         for t in thresholds:
            if s >= t:
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
            pen1 = pens[this_l * 2]
            pen2 = None
            if this_o > 0:
               pen2 = pens[this_l * 2 + 1]
            if this_l in last_pass_o:
               # continue this level from last
               last_o = last_pass_o[this_l]
               if not pen2 and last_o > 0:
                  pen2 = pens[this_l * 2 + 1]
               this_points = level_line(pen1, pen2, level_step, x0, last_o, y0, x1, this_o, y1, points1=last_pass_points[this_l])
            elif this_l == 0:
               # layer 0 continues from 0, y0
               last_o = 0
               this_points = level_line(pen1, pen2, level_step, x0, last_o, y0, x1, this_o, y1)
            else:
               this_points = None
            # all layers go from y1 to y2
            this_points = level_line(pen1, pen2, level_step, x1, this_o, y1, x2, this_o, y2, points1=this_points)

            this_pass_points[this_l] = this_points

         if l == 0 and 0 in last_pass_o:
            # we end so close an open 0
            this_o = 0
            pen1 = pens[0]
            last_o = last_pass_o[0]
            pen2 = None
            if last_o > 0:
               pen2 = pens[1]
            level_line(pen1, pen2, level_step, x0, last_o, y0, x1, this_o, y1, points1=last_pass_points[0])

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

      o = 0
      if self.period:
         o = math.sin(self.i / self.period) * self.amplitude
      x = self.x + self.dx * self.i - o * self.dy
      y = self.y + self.dy * self.i + o * self.dx
      self.i += self.step
      #print "i=%d, x,y=%d,%d" % (self.i, x, y)
      return (x, y)

def draw_waves(pix, spec):
  print 'spec = %s' % spec
  a = float(args.rotate) / 180.0 * math.pi
  period = spec.get('period', 50)
  amplitude = spec.get('amplitude', 20)

  line_length = math.sqrt(screen_width * screen_width + screen_height * screen_height)
  x_count = int(line_length / float(spec['line_spacing']))

  print 'x_count = %d' % x_count

  for wave in spec['waves']:
     print('wave %s' % str(wave))
     try:
        channel = wave[3]
     except IndexError:
        channel = 0
     for i in xrange(x_count):
        w = wave_path(screen_width / 2.0, screen_height / 2.0,
                      offset = (i + 0.5 - x_count / 2.0) * spec['line_spacing'],
                      angle = wave[0] + a,
                      step=spec['line_res'] / 2.0, length=line_length,
                      period=period, amplitude=amplitude)
        do_a_path(w, pix[channel], spec['level_spacing'], wave[1], wave[2])

def polar_x_y(a,r):
  return (r * math.sin(a), r * math.cos(a))

class circle_involute_path:
  def __init__(self, x_center, y_center, r=1, step=1, end_r=10):
    self.t0 = 0.0
    self.a = float(r) / (math.sqrt(1 + 4 * math.pi * math.pi) - 1)
    self.step = float(step)
    self.end_r2 = end_r * end_r
    self.x_center = x_center
    self.y_center = y_center

  def __iter__(self):
    return self

  def next(self):
    t1 = math.sqrt(2.0 * self.step / self.a + self.t0 * self.t0)
    x = self.a * (math.cos(t1) + t1 * math.sin(t1))
    y = self.a * (math.sin(t1) - t1 * math.cos(t1))
    if x * x + y * y > self.end_r2:
       raise StopIteration()
    self.t0 = t1
    return (x + self.x_center, y + self.y_center)

def draw_circle_involute(pix, spec):
  end_r = (math.sqrt(screen_width * screen_width + screen_height * screen_height) /
           2.0 * spec.get('extra_end_r', 1.0))

  for path in spec['paths']:
    print('path %s' % str(path))
    p = circle_involute_path(screen_width / 2.0 + path[0][0],
                             screen_height / 2.0 + path[0][1],
                             r=spec['line_spacing'],
                             step=spec['line_res'], end_r=end_r)
    do_a_path(p, pix[0], spec['level_spacing'], path[1], path[2])

methods = {
    'waves': {
        'draw': draw_waves,
        'default_spec': 'extra_fine',
        'specs': {
            'extra_fine': {
                # all waves that should be in this overlay
                'waves': [
                    # [angle, pens, thresholds]
                    (math.pi / 4.0, [default_pen],     [ +80]),
                    (0,             [default_pen] * 2, [ +140, +160]),
                    (math.pi / 2.0, [default_pen] * 3, [ +100, +120, +180]),
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
                    (math.pi / 4.0, [default_pen],     [ +80]),
                    (0,             [default_pen] * 5, [ 140,  140,  140, +140, +160]),
                    (math.pi / 2.0, [default_pen] * 6, [ 100, +100, +120,  180,  180, +180]),
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
                    (math.pi / 4.0, [default_pen],     [+80]),
                    (0,             [default_pen] * 2, [+140, +160]),
                    (math.pi / 2.0, [default_pen] * 3, [+100, +120, +180]),
                ],
                # distance each line is offset, screen units
                'line_spacing': 4,
                # distance along each line for intensity changes, screen units
                'line_res': 2,
                # distance between the onion layers, screen units
                'level_spacing': 1.2,
            },
            'moire': {
                'line_spacing': 2.0,
                'level_spacing': 0.3,
                'line_res': 1.0,
                'period': 0,
                'amplitude': 0,
                'waves': [
                    # [angle, pens, thresholds]
                    (-0.05, [default_pen], [0]),
                    (0.05,  [default_pen] + [None] * 6, [0, +80, +100, +120, +140, +160, +180]),
                ],
             },
            'cmyk': {
                'bands': 4,
                'waves': sum([
                    # [angle, pens, thresholds]
                    [(math.pi / 4.0 + a, [l+1],     [ +80], l),
                     (0 + a,             [l+1] * 2, [ +140, +160], l),
                     (math.pi / 2.0 + a, [l+1] * 3, [ +100, +120, +180], l),] for l,a in (
                         # C = 15 deg, M = 75 deg, Y = 0 deg, K = 45 deg
                         (0,math.pi/12.0) ,)],
                         #, (1,5.0*math.pi/12.0), (2,0), (3,math.pi/4.0))],
                    []),
                # distance each line is offset, screen units
                'line_spacing': 2.75,
                # distance along each line for intensity changes, screen units
                'line_res': 1,
                # distance between the onion layers, screen units
                'level_spacing': 0.8,
            },
        },
    },
    'circle_involute': {
        'draw': draw_circle_involute,
        'default_spec': '1+6',
        'specs': {
            '1+6': {
                'line_spacing': 5.0,
                'level_spacing': 0.8,
                'line_res': 1.0,
                'paths': [
                    # [offset, pens, thresholds]
                    ((0, 0), [1] * 6, [+80, +100, +120, +140, +160, +180]),
                ],
            },
            '1+6+all': {
                'line_spacing': 5.0,
                'level_spacing': 0.8,
                'line_res': 1.0,
                'paths': [
                    # [offset, pens, thresholds]
                    ((0, 0), [1] * 7, [0, +80, +100, +120, +140, +160, +180]),
                ],
            },
            '6+1': {
                'line_spacing': 3.0,
                'level_spacing': 0.8,
                'line_res': 1.0,
                'extra_end_r': 2.0,
                'paths': [
                    # [offset, pens, thresholds]
                    ((0, 0),                           [1], [+80]),
                    (polar_x_y(0*math.pi/2.5, 40*3.0), [1], [+100]),
                    (polar_x_y(1*math.pi/2.5, 40*3.0), [1], [+120]),
                    (polar_x_y(2*math.pi/2.5, 40*3.0), [1], [+140]),
                    (polar_x_y(3*math.pi/2.5, 40*3.0), [1], [+160]),
                    (polar_x_y(4*math.pi/2.5, 40*3.0), [1], [+180]),
                ],
            },
            '6+1+all': {
                'line_spacing': 3.0,
                'level_spacing': 0.8,
                'line_res': 1.0,
                'extra_end_r': 2.0,
                'paths': [
                    # [offset, pens, thresholds]
                    ((0, 0),                           [1, 1], [0, +80]),
                    (polar_x_y(0*math.pi/2.5, 40*3.0), [1, 1], [0, +100]),
                    (polar_x_y(1*math.pi/2.5, 40*3.0), [1, 1], [0, +120]),
                    (polar_x_y(2*math.pi/2.5, 40*3.0), [1, 1], [0, +140]),
                    (polar_x_y(3*math.pi/2.5, 40*3.0), [1, 1], [0, +160]),
                    (polar_x_y(4*math.pi/2.5, 40*3.0), [1, 1], [0, +180]),
                ],
            },
        },
    },
}

if args.method not in methods:
  print('method "%s" is not known' % args.method)
  sys.exit(1)

method = methods[args.method]

spec_name = args.spec
if not spec_name:
  spec_name = method.get('default_spec', 'default')

if spec_name not in method['specs']:
  print('spec "%s" is not known in method "%s"' % (args.spec, args.method))
  sys.exit(1)

spec = method['specs'][spec_name]

#dxf.circle(0,-0,3,pen=6)
#dxf.circle(screen_width,-screen_height,3,pen=7)
bands = spec.get('bands', 1)
if bands == 1:
  im = im.convert("L")
im.load()
#print 'doing bands %s' % (im.getbands())
print 'im mode = %s' % im.mode
print im.getextrema()
pix = [x.load() for x in im.split()]

method['draw'](pix, spec)

dxf.footer(dxfname)

