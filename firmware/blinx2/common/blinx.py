# Pin assignment

scl_pin_num = 18  # I2C SCL pin
sda_pin_num = 19  # I2C SDA pin

conn_pin_nums = [2, 3, sda_pin_num, scl_pin_num, 4, 5]  # 2 signals for each connector

def signal_index(conn, pin):  # conn = 1..3, pin = 1..2
    return conn*2 - pin

def conn_pin_num(conn, pin):
    return conn_pin_nums[signal_index(conn, pin)]

LEFT = 0  # left and right buttons
RIGHT = 1
button_pin_nums = [6, 7]

led_pin_num = 8  # led and buzzer share the same pin
buzzer_pin_num = 8

periph_power_pin_num = 10  # peripheral power


from machine import Pin, SoftI2C

def input_pin(i):
    return Pin(i, Pin.IN, Pin.PULL_UP)

def output_pin(i):
    return Pin(i, Pin.OUT, Pin.PULL_UP)

button_pins = [input_pin(button_pin_nums[0]), input_pin(button_pin_nums[1])]

def button(i):
    return button_pins[i].value() == 0

led_pin = output_pin(led_pin_num)

def led(on):
    led.value(not on)

periph_power_pin = output_pin(periph_power_pin_num)

def periph_power(on):
    periph_power_pin.value(on)

i2c = SoftI2C(output_pin(scl_pin_num), output_pin(sda_pin_num))
