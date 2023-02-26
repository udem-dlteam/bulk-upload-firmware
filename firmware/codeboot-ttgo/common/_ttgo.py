import esp32
from machine import Pin, SPI, deepsleep, soft_reset
import st7789
import vga2_bold_16x16
from time import *
import heapq
import sys
import os

screen_width  = 135
screen_height = 240

def config(rotation=0, buffer_size=0, options=0):
  return st7789.ST7789(
    SPI(2, baudrate=20000000, sck=Pin(18), mosi=Pin(19), miso=None),
    screen_width,
    screen_height,
    reset=Pin(23, Pin.OUT),
    cs=Pin(5, Pin.OUT),
    dc=Pin(16, Pin.OUT),
    backlight=Pin(4, Pin.OUT),
    rotation=rotation,
    options=options,
    buffer_size=buffer_size)

screen = config()
screen.init()

def parseRGB444(color):
  rgb = int(color[1:4], 16) if color[0] == '#' else 0
  return ((rgb<<4)&61440)+((rgb<<3)&1920)+((rgb<<1)&30)

def clear_screen(color):
  fill_rect(0, 0, screen_width, screen_height, color)

def fill_rect(x, y, width, height, color):
  screen.fill_rect(x, y, width, height, parseRGB444(color))

def set_pixel(x, y, color):
  screen.pixel(x, y, parseRGB444(color))

font_width  = 16
font_height = 16

def draw_text(x, y, text, fg, bg):
  screen.text(vga2_bold_16x16, bytes(map(ord, text)), x, y, parseRGB444(fg), parseRGB444(bg))

def draw_image(x, y, image):
  load_image(image)
  img = img_cache[0]
  screen.blit_buffer(img[3], x, y, img[1], img[2])

img_cache = []

def load_image(image):
  for i in range(len(img_cache)):
    c = img_cache[i]
    if c[0] == image:
      img_cache.insert(0, img_cache.pop(i))
      return
  img_cache.insert(0, convert_image(image))
  if len(img_cache) > 3: img_cache.pop()

def convert_image(image):
  rows = image.split('\n')
  if rows[0] == '': rows.pop(0)
  if rows[-1] == '': rows.pop()
  h = len(rows)
  w = 0
  for y in range(h):
    w = max(w, len(rows[y])>>2)
  i = 0
  b = bytearray(2*w*h)
  for y in range(h):
    row = rows[y]
    for x in range(w):
      rgb = parseRGB444(row[x<<2:(x+1)<<2])
      b[i] = rgb>>8; b[i+1] = rgb&255; i += 2
  return [image, w, h, b]

timeout_queue = []
idle_time_ms = 1000

class timed_task:

  def __init__(self, timeout, callback):
    self.timeout = timeout
    self.callback = callback

  def __lt__(self, other):
    return self.timeout < other.timeout

  def __eq__(self, other):
    return self.timeout == other.timeout

def scheduler():
  while True:
    if len(timeout_queue) > 0:
      next = timeout_queue[0]
      delay = ticks_diff(next.timeout, ticks_ms())
      if delay <= 0:
        task = heapq.heappop(timeout_queue)
        task.callback()
      else:
        sleep_ms(min(delay, idle_time_ms))
    else:
      sleep_ms(idle_time_ms)

def after(delay, callback):
  heapq.heappush(timeout_queue,
                 timed_task(ticks_add(ticks_ms(), int(delay*1000)), callback))

buttons = [Pin(0, Pin.IN), Pin(35, Pin.IN)]

last_call_to_button = 0
idle_counter = 0

def button(index):
  global last_call_to_button, idle_counter
  pressed = buttons[index].value() == 0
  if pressed:
    idle_counter = 0
  last_call_to_button = idle_counter
  return pressed

def stop():
  global idle_counter
  screen.off()
  screen.sleep_mode(True)
  esp32.wake_on_ext0(buttons[1], esp32.WAKEUP_ALL_LOW)
  idle_counter = 0
  after(1, deepsleep)

def idle():
  global idle_counter
  idle_counter += 1
  if idle_counter > last_call_to_button + 30:
    os.remove('run.py')  # remove entry point so we get REPL at next reboot
    soft_reset()
  elif idle_counter > 60:  # deep sleep after 1 minute of inactivity
    stop()
  else:
    after(1, idle)  # repeat every second

idle()  # start monitoring idleness

import _thread
_thread.start_new_thread(scheduler, ())
