import _ttgo as dev
import _config
import machine
import os

fg = '#fff'
bg = '#000'

def pad(text, width):  # pad text with spaces at end
    return text + ' ' * (width - len(text))

def center(x, y, text, fg, bg):
    dev.draw_text(x-len(text)*dev.font_width//2, y-dev.font_height//2, text, fg, bg)

timer = 0

def loop0():
    global timer
    dev.clear_screen('#0f0')  # green screen
    timer += 1
    if dev.button(0) and dev.button(1):
        # when both buttons pressed, boot normally
        machine.reset()
    else:
        dev.after(0.1, loop1)

def loop1():
    center(dev.screen_width//2, dev.screen_height//2, _config.id, fg, bg)
    try:
        center(dev.screen_width//2, dev.screen_height//2+64, pad(_config.ssid, 8), fg, bg)
        center(dev.screen_width//2, dev.screen_height//2+80, pad(_config.pwd, 8), fg, bg)
    except AttributeError:
        pass
    dev.after(0.9, loop0)

loop0()
