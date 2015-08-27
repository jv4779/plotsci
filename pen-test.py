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
import plot_dxf
import argparse
from collections import namedtuple
Point = namedtuple('Point', 'x y')

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--dxf', help='dxf file to output', default='pen-test.dxf')

args = parser.parse_args()

plot = plot_dxf.PlotDxf()

for l in xrange(8):
  for c in xrange(8):
    a = math.pi * (l * 8 + c) / 32.0
    plot.line(math.sin(a), math.cos(a), 0, 0, pen=l+1)

plot.footer(args.dxf)

