# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from blinx import button, LEFT, RIGHT

if not (button(LEFT) and button(RIGHT)):
    import program
