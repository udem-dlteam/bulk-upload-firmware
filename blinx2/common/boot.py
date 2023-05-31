# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import os

# the test file exists ?
files = os.listdir()
if '_blinx_test.py' in files or '_blinx_test.mpy' in files:
    import _blinx_test
else:
    from _blinx_blinx import button, LEFT, RIGHT

    if not (button(LEFT) or button(RIGHT)):
        import _blinx_program
