import _ttgo as dev
import _config
from machine import reset
import os

fg = '#fff'
bg = '#000'

def center(x, y, text, fg, bg):
    dev.draw_text(x-len(text)*dev.font_width//2, y-dev.font_height//2, text, fg, bg)

timer = 0

def loop0():
    global timer
    dev.clear_screen('#0f0')  # green screen
    timer += 1
    if timer > 110 or (dev.button(0) and dev.button(1)):
        # after ~ 2 minutes or both buttons pressed, clean up and boot normally
        os.remove('_flashtest.py')
        reset()
    else:
        dev.after(0.25, loop1)

def loop1():
    center(dev.screen_width//2, dev.screen_height//2, _config.id, fg, bg)
    try:
        center(dev.screen_width//2, dev.screen_height//2+64, _config.ssid, fg, bg)
        center(dev.screen_width//2, dev.screen_height//2+80, _config.pwd, fg, bg)
    except AttributeError:
        pass
    dev.after(0.75, loop0)

loop0()
