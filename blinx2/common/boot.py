# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import os

from _blinx_blinx import button, LEFT, RIGHT

if not (button(LEFT) or button(RIGHT)):
    import _blinx_program
else:
    import _blinx_portal
