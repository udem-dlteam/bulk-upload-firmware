import onewire, ds18x20, machine, time
import _blinx_blinx as blinx

ds1820_rom = [None, None, None, None]
ds1820_sensor = [None, None, None, None]
ds1820_onewire = [None, None, None, None]
ds1820_probable = [None, None, None, None]

# get measurement function
def get_ds1820_function(index):
    return lambda : int(ds1820_sensor[index].read_temp(ds1820_rom[index])*100)

# transform value to a lisible value for human
def byte_to_int_ds1820(n, times_sensors):
    return '%5.1f' % (n / 100)

def other(*args,**kargs):
    return 0

# test if a ds1820 sensor is connected
def get_sensor_analog_ds1820(n,m):
    global ds1820_sensor, ds1820_rom, ds1820_onewire
    index = m*2 + n - 3
    t1 = blinx.port_pin_num(n,m)

    if ds1820_probable[index]:
        t = blinx.input_pin(t1)
        ds1820_onewire[index] = onewire.OneWire(t)
        ds1820_sensor[index] = ds18x20.DS18X20(ds1820_onewire[index])
        tt = ds1820_sensor[index].scan()
        # t = blinx.input_pin(t1)
        #print(index, tt, ds1820_probable[index])
        if tt == []:
            ds1820_onewire[index].reset()
            ds1820_sensor[index] = None
            blinx.input_pin(t1)
            return other, [None], False
        else:
            ds1820_rom[index] = tt[0]
            return get_ds1820_function(index), [ds1820_sensor[index], ds1820_rom[index]], True
    else:
        return other, [None], False

info = {}

# first scan for the ds sensor
def scan_ds1820():
    global ds1820_probable
    a = machine.Pin(2, machine.Pin.IN)
    b = machine.ADC(a, atten=machine.ADC.ATTN_11DB)
    pull = [machine.Pin.PULL_UP, None]
    limits = [[2000,2340], [500,1520]]
    for i in range(2,6):
        autodetect = True
        for j in range(len(limits)):
            a = machine.Pin(i, machine.Pin.IN, pull[j])
            b = machine.ADC(a, atten=machine.ADC.ATTN_11DB)
            v = 0
            for k in range(64):
                v += b.read()
            v = v // 64
            if v < limits[j][0] or v > limits[j][1]:
                autodetect = False
        autodetect = True
        ds1820_probable[i-2] = autodetect
#    print(ds1820_probable)

# get info on the sensor
def get_info():
    global info
    for i in range(1,3):
        for y in range(1,3):
            name = 'ds1820_'+str(i)+str(y)
            t = get_sensor_analog_ds1820(i,y)
            info[name] = {}
            info[name]['function'] = t[0]
            info[name]['function_csv'] = byte_to_int_ds1820
            info[name]['size_csv'] = 5
            info[name]['type'] = 'in'
            info[name]['char'] = ''
            info[name]['more'] = t[1]
            info[name]['use'] = t[2]

# reset all the measurements
def reset_ds1820():
    global ds1820_sensor, ds1820_rom, ds1820_onewire
    for index in range(4):
        if ds1820_onewire[index] != None:
            ds1820_onewire[index].reset()
            ds1820_onewire[index] = None
            ds1820_sensor[index] = None
            ds1820_rom[index] = None
    scan_ds1820()
    get_info()

reset_ds1820()
