import _blinx_blinx as blinx
from machine import ADC, PWM, Pin
import uasyncio, time
import _blinx_screen as screen

screen_modify = False

# to write text on the screen
def output_screen(args):
    global screen_modify
    if len(args) > 0:
        screen_modify = len(args[0]) > 0
        if screen_modify:
            lines = args[0].split('\n')
            screen.screen_erase()
            for i in range(min(4,len(lines))):
                screen.screen_write(i, lines[i][:16], 0)
            screen.screen_show()

# function for the pin 8 : led/buzzer
def output_led_buzzer(args):
    duty = '0'
    freq = 4000
    timeout = 10
    if len(args) >= 1:
        duty = args[0]
        if len(args) >= 2:
            freq = int(args[1])
            if len(args) >= 3:
                timeout = int(args[2])

    pin = blinx.led_pin
    if timeout < 1:
        timeout = 10
    duty = duty.lower()
    
    if duty == 'on':
        pin.value(0)
        can_be_removed[4] = [timeout, lambda : remove_dig(pin, 1)]
        #uasyncio.create_task(remove_dig(timeout, pin, 1))
    elif duty == 'off':
        pin.value(1)
        can_be_removed[4] = [-1,None]
    else:
        duty = int(duty)
        freq = min(max(freq, 5), 40000000)
        if duty < 0 or duty > 1023:
            duty = 1023

        pwm = PWM(pin, duty=duty, freq=freq)
        can_be_removed[4] = [timeout, lambda : remove_pwm(pwm, pin, 1)]
        #uasyncio.create_task(remove_pwm(timeout, pin, 1023))

def get_output_port(n, m):
    return lambda args : output_port_general(n, m, args)

# function for all the other pin : for the port p1a, p1b, p2a, p2b
def output_port_general(n,m, args):
    global value_output, can_be_removed
    port = n*2+m-3
    name = str(n) + ('a' if m == 1 else 'b')
    #print(args, n, m)
    
    duty = '0'
    freq = 4000
    timeout = 10
    if len(args) >= 1:
        duty = args[0]
        if len(args) >= 2:
            freq = int(args[1])
            if len(args) >= 3:
                timeout = int(args[2])

    t = blinx.port_pin_num(n,m)
    pin = Pin(t, Pin.OUT)
    if timeout < 1:
        timeout = 10
    duty = duty.lower()
    timeInterval = int(time.ticks_ms() / 1000)
    
    if duty == 'on':
        pin.value(1)
        #uasyncio.create_task(remove_dig(timeout, pin))
        can_be_removed[port] = [timeout, lambda : remove_dig(pin)]
        value_output[port] = [1025, timeInterval+timeout]
    elif duty == 'off':
        pin.value(0)
        can_be_removed[port] = [-1,None]
        value_output[port] = [0, timeInterval]
    else:
        duty = int(duty)
        freq = min(max(freq, 1), 40000000)
        if duty < 0 or duty > 1023:
            duty = 0

        pwm = PWM(pin, duty=duty, freq=freq)
        #uasyncio.create_task(remove_pwm(timeout, pin))
        can_be_removed[port] = [timeout, lambda : remove_pwm(pwm, pin)]
        #print(pwm)
        value_output[port] = [duty+1, timeInterval+timeout]
    
    modify_port_input(port, name, save_output_sensors_csv, get_save_output_sensors)

# remove the output after the timeout
def remove_pwm(pwm, pin, value = 0):
    pwm.deinit()
    remove_dig(pin, value)

def remove_dig(pin, value = 0):
    pin.value(value)


# get the value for the csv
value_output = [[],[],[],[]]
def get_save_output_sensors(index):
    return lambda : save_output_sensors(index)

def save_output_sensors(port):
    global value_output
    null_value = 0
    timeInterval = int(time.ticks_ms() / 1000)
    if value_output[port] == []:
        return null_value
    elif timeInterval > value_output[port][1]:
        value_output[port] = []
        return null_value
    else :
        return value_output[port][0]

def save_output_sensors_csv(value, times_sensors):
    if times_sensors != 0:
        if value < 512:
            return ' off'
        return ' on '

    if value == 0 :
        value = ' off'
    elif value == 1025 :
        value = ' on '
    else :
        value = '{:04d}'.format(value-1)
    return value


def remove_output_value():
    for i in range(len(can_be_removed)):
        if can_be_removed[i][0] > 0:
            can_be_removed[i][0] -= 1
        elif can_be_removed[i][0] == 0:
            can_be_removed[i][0] = -1
            can_be_removed[i][1]()

# information
dict_sensors_output = {
    'screen' : output_screen,
    'led' : output_led_buzzer,
    'buzzer' : output_led_buzzer,
    'port1' : get_output_port(1,1),
    'port2' : get_output_port(2,1),
    'port3' : get_output_port(1,2),
    'port4' : get_output_port(2,2)
}

can_be_removed = [[-1,None],[-1,None],[-1,None],[-1,None],[-1,None]]
modify_port_input = None
