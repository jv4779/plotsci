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

import Image
import ImageOps
import random
import sys
import time
import colorsys
import argparse

parser = argparse.ArgumentParser(description='Quantize an image to a palette')
parser.add_argument('--img', help='image file to process', default='image.png')
parser.add_argument('--palette', help='palette to use', default='bw')
parser.add_argument('--gamma', help='number of rows', default='1')
args = parser.parse_args()

inputFilename = args.img
color_type = args.palette
gamma_adjust=float(args.gamma)

# Try to open the image using PIL, abort if not found
print 'Loading image... %s' % inputFilename,
try:
  img = Image.open(inputFilename)
except IOError:
  print 'Error: input file does not exist. Aborting.'
  sys.exit (1)

img = img.convert('RGB')

if gamma_adjust != 1:
  gamma=[0,0,0,0]
  for i in range(4):
    gamma[i]=1.0/gamma_adjust

  gammatable=[]
  for band in range(len(img.getbands())):
    g=gamma[band]
    for i in range(256) :
      c=pow((float(i)/255.0),g)*255
      gammatable.append(c)

  print('apply gamma %f...' % gamma_adjust),
  img=img.point(gammatable)

# cmyk iso 12646-2 uncoated white (type 4) process colors
#  CIELAB    sRGB
# cyan   58,-25,-43  0,174,239
# magenta 54,58,-2  236,0,140
# yellow 86,-4,75  255,242,0
# red   52,55,30  
# green  52,-46,16
# blue  36,12,-32  
# black 31,1,1    35,31,32
def tuples(s):
    while True:
        try:
            t1 = s[0]
            t2 = s[1]
            t3 = s[2]
            s    = s[3:]
        except IndexError:
            return
        yield t1,t2,t3

color_list = []

if color_type == 'hues' :
  shades = 3
  hues = [
    0, #red
    120, #green
    240, #blue
    180, #cyan
    300, #magenta
    60 #yellow
  ]

  # colors, white shades
  for hue in hues:
    for i in range(1,shades+1):
      rgb = colorsys.hsv_to_rgb(hue/360.0, float(i)/shades, 1.0)
      color_list.extend( (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)) )

  # colors, black shades
  for hue in hues:
    for i in range(1,shades):
      rgb = colorsys.hsv_to_rgb(hue/360.0, 1.0, float(i)/shades)
      color_list.extend( (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)) )

  # white, grey, black
  for i in range(0,shades+1):
    rgb = colorsys.hsv_to_rgb(0, 0, float(i)/shades)
    color_list.extend( (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)) )

elif color_type == '7color' :
  shades = 1
  colors = [
          0,0,0,         #black
          255,0,0,       #red
          0,255,0,       #green
          0,0,255,       #blue
          0,255,255,     #cyan
          255,0,255,     #magenta
          255,255,0      #yellow
  ]

  for r,g,b in tuples(colors):
    print( 'r=%d g=%d b=%d' % (r,g,b) )
    for i in range(1,shades+1):
      color_list.extend(
        (int(r*i/shades), int(g*i/shades),int(b*i/shades)) )

  color_list.extend( (255,255,255) )


  #color_list.extend( (0,127,255) )
  #color_list.extend( (0,255,127) )
  #color_list.extend( (127,0,255) )
  #color_list.extend( (127,255,0) )
  #color_list.extend( (255,0,127) )
  #color_list.extend( (255,127,0) )

elif color_type == 'bw' :
  color_list.extend( (255,255,255) )

elif color_type == 'point88' :
  colors = [
    0,0,0,       #black
    184,38,83,   #red
    55,150,82,   #green
    58,84,148,   #blue
    96,189,240,  #cyan
    190,64,138,  #magenta
    234,203,117  #yellow
  ]

  for r,g,b in tuples(colors):
    color_list.extend((r,g,b))

  color_list.extend( (255,255,255) )

color_list.extend( [0]*(256*3-len(color_list)) )

print(color_list)

both_palette = Image.new('P',(1,1))
both_palette.putpalette( color_list );
img.quantize(palette=both_palette).save('%s-%s.png' % (inputFilename[0:inputFilename.rfind ('.')],color_type),'PNG')

