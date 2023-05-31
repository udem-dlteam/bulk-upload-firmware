import _blinx_blinx as blinx
from machine import ADC, PWM, Pin

# get measurement function
def get_ds1820_function(index):
    return lambda : analog(adc_value[index])

# average 4 successive readings for better accuracy
def analog(adc):
    return (adc.read_u16() + adc.read_u16() + adc.read_u16() + adc.read_u16() + 2) >> 2

adc_value = [None, None, None, None]

# transform raw ADC reading to volts
def volt_from_raw(n, times_sensors):
    return '%4.2f' % ((n+397)/23030)

def other(*args,**kargs):
    return

# get information
def get_sensor_analog_ds1820(n,m):
    global adc_value
    index = n*2 + m - 3
    t = blinx.port_pin_num(n,m)
    t = blinx.input_pin(t)
    adc_value[index] = ADC(t, atten=ADC.ATTN_11DB)
    return get_ds1820_function(index)

info = {}

for i in range(1,3):
    for y in range(1,3):
        name = 'analog_'+str(i)+str(y)
        t = get_sensor_analog_ds1820(i,y)
        info[name] = {}
        info[name]['function'] = t
        info[name]['function_csv'] = volt_from_raw
        info[name]['size_csv'] = 4
        info[name]['type'] = 'in'
        info[name]['char'] = '0..3'
        info[name]['more'] = []
