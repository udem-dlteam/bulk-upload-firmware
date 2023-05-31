import _blinx_blinx as blinx
from machine import ADC, PWM, Pin
import uasyncio, time

screen_modify = False

# to write text on the screen
def output_screen(args):
    global screen_modify
    if len(args) > 0:
        screen_modify = True
        screen_erase()
        text = args[0].split('\\n')
        if len(text) == 1:
            if text[0] == '':
                screen_modify = False
                screen.show()
                return
            if text[0] == ' ':
                screen.show()
                return
        for i in range(min(4,len(text))):
            screen_write(i, text[i], 0)
        screen.show()

# function for the pin 8 : led/buzzer
def output_led_buzzer(args):
    global can_be_removed
    if len(args) == 0:
        pwm = 0
        freq = 5000
        timeout = 10
    elif len(args) == 1:
        pwm = args[0] # int(args[0])
        freq = 5000
        timeout = 10
    elif len(args) == 2:
        pwm = args[0] # int(args[0])
        freq = int(args[1])
        timeout = 10
    else:
        pwm = args[0] # int(args[0])
        freq = int(args[1])
        timeout = int(args[2])

    pin = blinx.led_pin
    if timeout < 1:
        timeout = 10
    pwm = pwm.lower()
    
    if pwm in ['on']:
        pin.value(0)
        can_be_removed[4] = [timeout, lambda : remove_dig(pin, 1)]
        #uasyncio.create_task(remove_dig(timeout, pin, 1))
    elif pwm in ['off']:
        pin.value(1)
        can_be_removed[4] = [-1,None]
    else:
        pwm = int(pwm)
        if freq < 5 or freq > 40000000:
            freq = 5000
        if pwm < 0 or pwm > 1023:
            pwm = 1023

        t = PWM(pin)
        t.duty(pwm)
        t.freq(freq)
        can_be_removed[4] = [timeout, lambda : remove_pwm(pin, 1023)]
        #uasyncio.create_task(remove_pwm(timeout, pin, 1023))

def get_output_port(n, m):
    return lambda args : output_port_general(n, m, args)

# function for all the other pin : for the port p1a, p1b, p2a, p2b
def output_port_general(n,m, args):
    global value_output, can_be_removed
    port = n*2+m-3
    name = str(n) + ('a' if m == 1 else 'b')
    #print(args, n, m)
    
    if len(args) == 0:
        pwm = 0
        freq = 5000
        timeout = 10
    elif len(args) == 1:
        pwm = args[0] # int(args[0])
        freq = 5000
        timeout = 10
    elif len(args) == 2:
        pwm = args[0] # int(args[0])
        freq = int(args[1])
        timeout = 10
    else:
        pwm = args[0] # int(args[0])
        freq = int(args[1])
        timeout = int(args[2])

    t = blinx.port_pin_num(n,m)
    pin = Pin(t, Pin.OUT)
    if timeout < 1:
        timeout = 10
    pwm = pwm.lower()
    timeInterval = int(time.ticks_ms() / 1000)
    
    if pwm in ['on']:
        pin.value(1)
        #uasyncio.create_task(remove_dig(timeout, pin))
        can_be_removed[port] = [timeout, lambda : remove_dig(pin)]
        value_output[port] = [1025, timeInterval+timeout]
    elif pwm in ['off']:
        pin.value(0)
        can_be_removed[port] = [-1,None]
        value_output[port] = [0, timeInterval]
    else:
        pwm = int(pwm)
        if freq < 5 or freq > 40000000:
            freq = 5000
        if pwm < 0 or pwm > 1023:
            pwm = 0

        t = PWM(pin)
        t.duty(pwm)
        t.freq(freq)
        
        #uasyncio.create_task(remove_pwm(timeout, pin))
        can_be_removed[port] = [timeout, lambda : remove_pwm(pin)]
        #print(pwm)
        value_output[port] = [pwm+1, timeInterval+timeout]
    
    modify_port_input(port, name, save_output_sensors_csv, get_save_output_sensors)

# remove the output after the timeout
def remove_pwm(port, pwm = 0, freq = 5000):
    t = PWM(port)
    t.duty(pwm)
    t.freq(freq)
def remove_dig(port, value = 0):
    port.value(value)


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
    global can_be_removed
    for i in range(len(can_be_removed)):
        if can_be_removed[i][0] > 0:
            can_be_removed[i][0] -= 1

        if can_be_removed[i][0] == 0:
            can_be_removed[i][0] = -1
            can_be_removed[i][1]()

# information
dict_sensors_output = {
    'screen' : output_screen,
    'led' : output_led_buzzer,
    'buzzer' : output_led_buzzer,
    'p1a' : get_output_port(1,1),
    'p1b' : get_output_port(1,2),
    'p2a' : get_output_port(2,1),
    'p2b' : get_output_port(2,2)
}

can_be_removed = [[-1,None],[-1,None],[-1,None],[-1,None],[-1,None]]
modify_port_input = None
