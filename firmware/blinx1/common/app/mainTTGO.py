#------------------------------------------------------------------------------

# TTGO implementation of codeBoot setPixel

from machine import Pin, SPI
import st7789

def screen_config(rotation=0, buffer_size=0, options=0):
    return st7789.ST7789(
        SPI(2, baudrate=20000000, sck=Pin(18), mosi=Pin(19), miso=None),
        135,
        240,
        reset=Pin(23, Pin.OUT),
        cs=Pin(5, Pin.OUT),
        dc=Pin(16, Pin.OUT),
        backlight=Pin(4, Pin.OUT),
        rotation=rotation,
        options=options,
        buffer_size=buffer_size)

screen = screen_config()

def setScreenMode(w, h):
    screen.init()

def setPixel(x, y, color):  # color is a tuple (r,g,b) with values 0..15
    screen.pixel(x, y, color)
#    screen.pixel(x, y, ((color[0]*4)<<11) + ((color[1]*2)<<6) + color[2]*4)

#------------------------------------------------------------------------------

# TTGO implementation of codeBoot getMouse

class Buttons():

    def __init__(self):
        self.pin_left = Pin(0, Pin.IN)
        self.pin_right = Pin(35, Pin.IN)
        self.left = False
        self.right = False
        self.button = False
        self.shift = False
        self.ctrl = False
        self.get()

    def get(self):
        self.left = self.pin_left.value() == 0
        self.right = self.pin_right.value() == 0
        self.button = self.left or self.right
        self.shift = self.right
        self.ctrl = self.left
        return self

buttons = Buttons()

def getMouse():
    return buttons.get()

#------------------------------------------------------------------------------

# TTGO implementation of codeBoot alert and sleep and random

import time
import vga1_8x8 as font

def alert(msg):
    screen.text(font, msg, 0, 230)

def sleep(duration):
    if duration > 0:
        time.sleep_ms(round(duration * 1000))

from random import random

import math

#------------------------------------------------------------------------------

# preprocess colormap

# Ensemble d'images de taille 16x16 pixels.  Chaque element du
# tableau images correspond a une image d'une tuile du jeu demineur.
# Une image est representee par un tableau des rangees de pixels.
# Chaque rangee est un tableau contenant l'index de la couleur dans
# le tableau colormap.

images = [
 [ # 0 = tuile vide
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 1 = tuile "1"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0]
 ,[8,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0]
 ,[8,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 2 = tuile "2"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0]
 ,[8,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0]
 ,[8,0,0,2,2,2,0,0,0,0,2,2,2,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,2,2,2,0,0,0]
 ,[8,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0]
 ,[8,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0]
 ,[8,0,0,0,2,2,2,2,2,0,0,0,0,0,0,0]
 ,[8,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0]
 ,[8,0,0,2,2,2,2,2,2,2,2,2,2,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 3 = tuile "3"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0]
 ,[8,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0]
 ,[8,0,0,0,0,0,3,3,3,3,3,3,0,0,0,0]
 ,[8,0,0,0,0,0,3,3,3,3,3,3,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,3,3,3,0,0,0]
 ,[8,0,0,3,3,3,3,3,3,3,3,3,3,0,0,0]
 ,[8,0,0,3,3,3,3,3,3,3,3,3,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 4 = tuile "4"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,4,4,4,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,0,4,4,4,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,4,4,4,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,4,4,4,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,4,4,4,4,4,4,4,4,4,4,0,0,0]
 ,[8,0,0,4,4,4,4,4,4,4,4,4,4,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,4,4,4,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 5 = tuile "5"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,5,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,5,0,0,0]
 ,[8,0,0,5,5,5,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,5,5,5,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,0,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,5,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,5,5,5,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,5,5,5,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,5,0,0,0]
 ,[8,0,0,5,5,5,5,5,5,5,5,5,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 6 = tuile "6"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,6,6,6,6,6,6,6,6,0,0,0,0]
 ,[8,0,0,6,6,6,6,6,6,6,6,6,0,0,0,0]
 ,[8,0,0,6,6,6,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,6,6,6,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,6,6,6,6,6,6,6,6,6,0,0,0,0]
 ,[8,0,0,6,6,6,6,6,6,6,6,6,6,0,0,0]
 ,[8,0,0,6,6,6,0,0,0,0,6,6,6,0,0,0]
 ,[8,0,0,6,6,6,0,0,0,0,6,6,6,0,0,0]
 ,[8,0,0,6,6,6,6,6,6,6,6,6,6,0,0,0]
 ,[8,0,0,0,6,6,6,6,6,6,6,6,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 7 = tuile "7"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,7,7,7,7,7,7,7,7,7,7,0,0,0]
 ,[8,0,0,7,7,7,7,7,7,7,7,7,7,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,7,7,7,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,7,7,7,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,7,7,7,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,7,7,7,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,7,7,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,7,7,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,7,7,7,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,7,7,7,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 8 = tuile "8"
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,8,8,8,8,8,8,8,8,0,0,0,0]
 ,[8,0,0,8,8,8,8,8,8,8,8,8,8,0,0,0]
 ,[8,0,0,8,8,8,0,0,0,0,8,8,8,0,0,0]
 ,[8,0,0,8,8,8,0,0,0,0,8,8,8,0,0,0]
 ,[8,0,0,0,8,8,8,8,8,8,8,8,0,0,0,0]
 ,[8,0,0,0,8,8,8,8,8,8,8,8,0,0,0,0]
 ,[8,0,0,8,8,8,0,0,0,0,8,8,8,0,0,0]
 ,[8,0,0,8,8,8,0,0,0,0,8,8,8,0,0,0]
 ,[8,0,0,8,8,8,8,8,8,8,8,8,8,0,0,0]
 ,[8,0,0,0,8,8,8,8,8,8,8,8,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 9 = mine
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,0,0,7,0,7,7,7,7,7,0,7,0,0,0]
 ,[8,0,0,0,0,7,7,7,7,7,7,7,0,0,0,0]
 ,[8,0,0,0,7,7,9,9,7,7,7,7,7,0,0,0]
 ,[8,0,0,0,7,7,9,9,7,7,7,7,7,0,0,0]
 ,[8,0,7,7,7,7,7,7,7,7,7,7,7,7,7,0]
 ,[8,0,0,0,7,7,7,7,7,7,7,7,7,0,0,0]
 ,[8,0,0,0,7,7,7,7,7,7,7,7,7,0,0,0]
 ,[8,0,0,0,0,7,7,7,7,7,7,7,0,0,0,0]
 ,[8,0,0,0,7,0,7,7,7,7,7,0,7,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 10 = mine sur fond rouge
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
 ,[8,3,3,3,3,3,3,3,7,3,3,3,3,3,3,3]
 ,[8,3,3,3,3,3,3,3,7,3,3,3,3,3,3,3]
 ,[8,3,3,3,7,3,7,7,7,7,7,3,7,3,3,3]
 ,[8,3,3,3,3,7,7,7,7,7,7,7,3,3,3,3]
 ,[8,3,3,3,7,7,9,9,7,7,7,7,7,3,3,3]
 ,[8,3,3,3,7,7,9,9,7,7,7,7,7,3,3,3]
 ,[8,3,7,7,7,7,7,7,7,7,7,7,7,7,7,3]
 ,[8,3,3,3,7,7,7,7,7,7,7,7,7,3,3,3]
 ,[8,3,3,3,7,7,7,7,7,7,7,7,7,3,3,3]
 ,[8,3,3,3,3,7,7,7,7,7,7,7,3,3,3,3]
 ,[8,3,3,3,7,3,7,7,7,7,7,3,7,3,3,3]
 ,[8,3,3,3,3,3,3,3,7,3,3,3,3,3,3,3]
 ,[8,3,3,3,3,3,3,3,7,3,3,3,3,3,3,3]
 ,[8,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
 ]
,[ # 11 = mine avec X rouge
  [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,3,3,0,0,0,0,7,0,0,0,0,3,3,0]
 ,[8,0,0,3,3,0,7,7,7,7,7,0,3,3,0,0]
 ,[8,0,0,0,3,3,7,7,7,7,7,3,3,0,0,0]
 ,[8,0,0,0,7,3,3,9,7,7,3,3,7,0,0,0]
 ,[8,0,0,0,7,7,3,3,7,3,3,7,7,0,0,0]
 ,[8,0,7,7,7,7,7,3,3,3,7,7,7,7,7,0]
 ,[8,0,0,0,7,7,3,3,7,3,3,7,7,0,0,0]
 ,[8,0,0,0,7,3,3,7,7,7,3,3,7,0,0,0]
 ,[8,0,0,0,3,3,7,7,7,7,7,3,3,0,0,0]
 ,[8,0,0,3,3,0,7,7,7,7,7,7,3,3,0,0]
 ,[8,0,3,3,0,0,0,0,7,0,0,0,0,3,3,0]
 ,[8,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0]
 ,[8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
 ]
,[ # 12 = tuile non-devoilee
  [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,0]
 ,[9,9,9,9,9,9,9,9,9,9,9,9,9,9,0,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,0,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[0,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ]
,[ # 13 = tuile non-devoilee avec drapeau
  [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,0]
 ,[9,9,9,9,9,9,9,9,9,9,9,9,9,9,0,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,3,3,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,3,3,3,3,0,0,0,0,0,8,8]
 ,[9,9,0,0,3,3,3,3,3,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,3,3,3,3,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,3,3,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,7,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,7,0,0,0,0,0,8,8]
 ,[9,9,0,0,0,0,7,7,7,7,0,0,0,0,8,8]
 ,[9,9,0,0,7,7,7,7,7,7,7,7,0,0,8,8]
 ,[9,9,0,0,7,7,7,7,7,7,7,7,0,0,8,8]
 ,[9,9,0,0,0,0,0,0,0,0,0,0,0,0,8,8]
 ,[9,0,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ,[0,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
 ]
,[ # 14 = curseur
  [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
 ,[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, None, None, None, None, None, None, None, None, None, None, None, None, 3, 3]
 ,[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
 ,[3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
 ]
]

# Ensemble de couleurs utilisees dans la definition des images
# ci-dessus.  A tout endroit ou le nombre c apparait dans une image,
# la couleur RGB du pixel est colormap[c].

colormap = [
 (12, 12, 12) # 0 = gris pale
,( 0,  0, 15) # 1 = bleu
,( 0,  8,  0) # 2 = vert fonce
,(15,  0,  0) # 3 = rouge
,( 0,  0,  8) # 4 = bleu fonce
,( 8,  0,  0) # 5 = rouge fonce
,( 0,  8,  8) # 6 = cyan
,( 0,  0,  0) # 7 = noir
,( 8,  8,  8) # 8 = gris fonce
,(15, 15, 15) # 9 = blanc
]

for i in range(len(colormap)):
    color = colormap[i]
    colormap[i] = (((color[0]*4)<<11) + ((color[1]*2)<<6) + color[2]*4)

#------------------------------------------------------------------------------


# jeu de démineur

LARGEUR = 8
HAUTEUR = 12 # laisser place pour le texte affiche par alert
MINES = 15

size = len(images[0])
mine = 9
mineFondRouge = 10
nonDevoile = 12
imageCurseur = 14

# Etat
grille = None
premierClic = True
curseur = [0, 0]

# Affichage

def afficherImage(x, y, colormap, image):
    for j in range(len(image)):
        for i in range(len(image[0])):
            couleur = image[j][i]
            if couleur is not None:
                setPixel(x+i, y+j, colormap[couleur])

def afficherTuile(x, y, tuile):
    afficherImage(x*size, y*size, colormap, images[tuile])
    
def afficherJeuInitial(largeur, hauteur):
    setScreenMode(largeur*size, hauteur*size)
    for rangee in grille:
        for case in rangee:
            mettreAJourCase(case, False)
            
def afficherTuile(x, y, tuile):
    afficherImage(x*size, y*size, colormap, images[tuile])
    
def afficherVictoire():
    alert("Bravo!")
    sleep(5)
    
def afficherDefaite():
    alert("Boom!")
    sleep(5)
    
def mettreAJourCase(case, devoilement):
    case
    x = case.x
    y = case.y
    
    if case.decouvert:
        if case.mine:
            afficherTuile(x, y, mineFondRouge)
        else:
            afficherTuile(x, y, case.proximite)
    elif case.mine and devoilement:
        afficherTuile(x, y, mine)
    else:
        afficherTuile(x, y, nonDevoile)
    
    if curseur == [x, y]:
        afficherTuile(x, y, imageCurseur)
    
    
# Helper

def randint(n):
    return math.floor(n*random())

def flatten(grille):
    resultat = []
    for l in grille:
        resultat.extend(l)
    return resultat

def melanger(tab):
    for i in range(len(tab)-1, 0, -1):
        j = randint(i)
        t = tab[i]
        tab[i] = tab[j]
        tab[j] = t
    return tab

# Jeu

class struct():
    def __init__(self, x, y, mine, drapeau, decouvert, proximite):
        self.x = x
        self.y = y
        self.mine = mine
        self.drapeau = drapeau
        self.decouvert = decouvert
        self.proximite = proximite

def creerCase(x, y):
    return struct(x, y, False, False, False, 0)

def voisins(x, y):
    tab = []
    
    xs = range(-1 if x > 0 else 0, 2 if x < LARGEUR - 1 else 1)
    ys = range(-1 if y > 0 else 0, 2 if y < HAUTEUR - 1 else 1)
    
    for i in xs:
        for j in ys:
            if i != 0 or j != 0:
                tab.append(grille[x + i][y + j])
    return tab    

def placerMines(nbMines, x, y):
    cases = flatten(grille)
    melanger(cases)
    
    for case in cases[:MINES]:
        if (x, y) == (case.x, case.y):
            case = cases[MINES]
            
        case.mine = True
        for voisin in voisins(case.x, case.y):
            voisin.proximite += 1

def decouvrir(case):
    stack = [case]
    while len(stack) > 0:
        case = stack.pop()
        if not case.decouvert:
            case.decouvert = True
            mettreAJourCase(case, False)
            if case.proximite == 0:
                for v in voisins(case.x, case.y):
                    stack.append(v)

def genererGrille(largeur, hauteur):
    global grille
    
    grille = []
    
    for _ in range(largeur):
        grille.append([None] * hauteur)
        
    for x in range(largeur):
        for y in range(hauteur):
            grille[x][y] = creerCase(x, y)
            
def verifierVictoire():
    for rangee in grille:
        for case in rangee:
            if not case.decouvert and not case.mine:
                return False
    return True

def attendreEvenement():
    left = False
    right = False
    while True:
        sleep(0.01)
        mouse = getMouse()
        if (left or right) and not (mouse.left or mouse.right):
            break
        left = left or mouse.left
        right = right or mouse.right
    if left and right:
        return "clic"
    elif left:
        return "clicGauche"
    else:
        return "clicDroit"
        
def caseSousCurseur():
    x = curseur[0]
    y = curseur[1]
    return grille[x][y]
        
def deplacementCurseurX():
    prec = caseSousCurseur()
    curseur[0] = (curseur[0] + 1) % LARGEUR
    nouv = caseSousCurseur()
    mettreAJourCase(prec, False)
    mettreAJourCase(nouv, False)

def deplacementCurseurY():
    prec = caseSousCurseur()
    curseur[1] = (curseur[1] + 1) % HAUTEUR
    nouv = caseSousCurseur()
    mettreAJourCase(prec, False)
    mettreAJourCase(nouv, False)

def clic():
    global premierClic
    
    if premierClic:
        premierClic = False
        placerMines(MINES, *curseur)
        
    case = caseSousCurseur()
    
    decouvrir(case)
    
    if case.mine:
        for rangee in grille:
            for case in rangee:
                if case.mine:
                    mettreAJourCase(case, True)
        return False
    return True
            
def demineur():
    global premierClic
    while True:
        premierClic = True
        genererGrille(LARGEUR, HAUTEUR)
        afficherJeuInitial(LARGEUR, HAUTEUR)
        
        while True:
            alive = True
            event = attendreEvenement()
            
            if event == "clicGauche":
                deplacementCurseurY()
            elif event == "clicDroit":
                deplacementCurseurX()
            elif event == "clic":
                alive = clic()
                
            if not alive:
                afficherDefaite()
                break
            elif verifierVictoire():
                afficherVictoire()
                break
    
demineur()
