# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from machine import Pin

right_but = Pin(6, Pin.IN, Pin.PULL_UP)
left_but  = Pin(7, Pin.IN, Pin.PULL_UP)

if not right_but.value():
    import program
