import _blinx_blinx as blinx
import _blinx_ssd1306 as ssd1306
import time

def screen_init():
    global screen
    screen = ssd1306.SSD1306_I2C(128, 32, blinx.i2c)

def screen_write(line, text, start_x, fg=1):
    screen.fill_rect(start_x, line*8, 128, 8, 1-fg)
    screen.text(text, start_x, line*8, fg)

def screen_erase():
    screen.fill(0)

def screen_show():
    screen.show()

#def scaled_write(text, w, h, start_x, start_y):
#    import _blinx_font8x12 as font
#    start_x *= font.width
#    start_y *= font.height
#    for i in range(len(text)):
#        bitmap = font.bitmap[ord(text[i])]
#        posx = (i+1) * font.width
#        if posx * w > 128: break
#        for yy in range(font.height):
#            y = yy * h
#            if y >= 32: break
#            hh = h
#            if yy == font.height-1: hh -= 1
#            b = ~bitmap[yy]
#            for xx in range(font.width):
#                x = (posx - xx - 1) * w
#                col = b & 1
#                screen.rect(start_x+x, start_y+y, start_x+w, start_y+hh, col)
#                b >>= 1
#    screen_show()
