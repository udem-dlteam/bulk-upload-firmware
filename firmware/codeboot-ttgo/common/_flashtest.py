import _ttgo as dev
import _config
from machine import reset
import os

fg = '#000'
bg = '#0f0'

def center(x, y, text, fg, bg):
    dev.draw_text(x-len(text)*dev.font_width//2, y-dev.font_height//2, text, fg, bg)

timer = 0

def loop0():
    global timer
    dev.clear_screen(bg)
    timer += 1
    if timer < 600 and not (dev.button(0) and dev.button(1)):  # after 10 minutes, clean up and boot normally
        dev.after(0.25, loop1)
    else:
        os.remove('_flashtest.py')
        reset()

def loop1():
    center(dev.screen_width//2, dev.screen_height//2, _config.id, fg, bg)
    center(dev.screen_width//2, dev.screen_height//2+64, _config.ssid, fg, bg)
    center(dev.screen_width//2, dev.screen_height//2+80, _config.pwd, fg, bg)
    dev.after(0.75, loop0)

loop0()
