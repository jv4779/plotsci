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
import random
import math
import time
import argparse
import plot_dxf
from collections import namedtuple
Point = namedtuple('Point', 'x y')

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--dxf', help='dxf file to output', default='cuber.dxf')
parser.add_argument('--size', help='square size', default=10)
parser.add_argument('--offset', help='square center distance', default=12)
parser.add_argument('--rows', help='number of rows', default=24)
parser.add_argument('--cols', help='number of cols', default=34)
parser.add_argument('--move', help='movement energy', default=0.25)
parser.add_argument('--rotate', help='rotational energy', default=0.1)

args = parser.parse_args()
print args.dxf

offset = float(args.offset)
size = float(args.size)
rows = int(args.rows)
cols = int(args.cols)
move_energy = float(args.move)
rot_energy = float(args.rotate)

Move = namedtuple('Move', 'x y a')

dxf = plot_dxf.PlotDxf()

def random_move(x, y):
  rotation = random.random() * math.pi * 2 - math.pi
  direction = random.random() * math.pi * 2
  mag = random.random()
  return Move(math.sin(direction) * mag, math.cos(direction) * mag, rotation)

cubes = [[random_move(x,y) for y in xrange(rows)] for x in xrange(cols)]

def calc_move(x, y):
  global cubes
  if x == 0 or y == 0 or x == cols - 1 or y == rows - 1:
    return cubes[x][y]
  if x < cols / 2.0:
    x1 = x - 1
  else:
    x1 = x + 1
  if y < rows / 2.0:
    y1 = y - 1
  else:
    y1 = y + 1
  m0 = cubes[x][y]
  m1 = cubes[x][y1]
  m2 = cubes[x1][y]
  m3 = cubes[x1][y1]
  m = Move((m0.x + m1.x + m2.x + m3.x) / 4.0,
           (m0.y + m1.y + m2.y + m3.y) / 4.0,
           (m0.a + m1.a + m2.a + m3.a) / 4.0)
  cubes[x][y] = m
  return m

def draw_cube(dxf, shell, x, y):
  print('layer %d,%d' % (x,y))
  m = calc_move(x, y)
  x_center = offset * x + offset / 2.0 + size * m.x * shell * move_energy
  y_center = offset * y + offset / 2.0 + size * m.y * shell * move_energy
  a = m.a * shell * rot_energy
  r = math.sqrt(size * size / 2.0)
  angles = [i * math.pi / 2.0 + math.pi / 4.0 for i in xrange(4)]
  p = [Point(x_center + r * math.sin(a + rot), y_center + r * math.cos(a + rot)) for rot in angles]
  for i in xrange(4):
    p1 = p[i]
    p2 = p[(i + 1) % 4]
    dxf.line(p1.x, p1.y, p2.x, p2.y)

for shell in xrange(rows/2):
  print 'shell %d' % shell
  for x in xrange(shell, cols-shell):
    y_top = shell
    draw_cube(dxf, shell, x, y_top)
    y_bottom = rows-shell-1
    if y_top != y_bottom:
      draw_cube(dxf, shell, x, y_bottom)
  for y in xrange(shell+1, rows-shell-1):
    x_left = shell
    draw_cube(dxf, shell, x_left, y)
    x_right = cols-shell-1
    if x_left != x_right:
      draw_cube(dxf, shell, x_right, y)

dxf.footer(args.dxf)

