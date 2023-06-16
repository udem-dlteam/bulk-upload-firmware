# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import os

from _blinx_blinx import button, LEFT, RIGHT

if button(LEFT) or button(RIGHT):
    import _blinx_portal
else:
    boot = '_blinx_boot.py'
    try:
        f = open(boot, 'r')
        code = f.read()
        f.close()
        os.remove(boot)
        exec(code)
    except Exception:
        pass
    import _blinx_program
