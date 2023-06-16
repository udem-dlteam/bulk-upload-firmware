# Pin assignment

# motor : http://mpy-tut.zoic.org/tut/motors.html

scl_pin_num = 18  # I2C SCL pin
sda_pin_num = 19  # I2C SDA pin

#port_pin_nums = [4, 2, 5, 3, sda_pin_num, scl_pin_num]  # 2 signals for each port
port_pin_nums = [4, 5, 2, 3, sda_pin_num, scl_pin_num]  # 2 signals for each port

def signal_index(port, pin):  # port = 1..3, pin = 1..2
    return port*2 - pin

def port_pin_num(port, pin):
    return port_pin_nums[signal_index(port, pin)]

LEFT = 0  # left and right buttons
RIGHT = 1
button_pin_nums = [6, 7]

led_pin_num = 8  # led and buzzer share the same pin
buzzer_pin_num = 8

periph_power_pin_num = 10  # peripheral power


from machine import Pin, SoftI2C, WDT

def input_pin(i):
    return Pin(i, Pin.IN, None)

def output_pin(i, pull=Pin.PULL_DOWN):
    return Pin(i, Pin.OUT, pull)

button_pins = [input_pin(button_pin_nums[0]), input_pin(button_pin_nums[1])]

def button(i):
    return button_pins[i].value() == 0

led_pin = output_pin(led_pin_num, Pin.PULL_UP)

def led(on):
    led_pin.value(not on)

led(False)

periph_power_pin = output_pin(periph_power_pin_num)

def periph_power(on):
    periph_power_pin.value(on)

periph_power(0)

scl_pin = output_pin(scl_pin_num, Pin.PULL_UP)
sda_pin = output_pin(sda_pin_num, Pin.PULL_UP)

scl_pin.value(0)
sda_pin.value(0)

def i2c_init():
    global i2c
    i2c = SoftI2C(scl_pin, sda_pin)

def restart():
    WDT(timeout=1000)  # restart in 1 second
    while True:
        pass
