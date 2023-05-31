safe_fs = True # bool for the activation of the write and remove ops

def safe_to_modify(filename):
    return not (filename[:7] == '_blinx_' or filename == 'boot.py')

import _blinx_blinx as blinx

#------------------------------------------------------------------------------

# turn on peripherals

blinx.periph_power(1)
blinx.i2c_init()

#------------------------------------------------------------------------------

# import all

import _blinx_config as _config
import _blinx_wifi as _wifi
import _blinx_version as _version

import ubinascii, os, sys, time
from struct import pack
from binascii import crc32

import uasyncio

import network
import ntptime
import gc

import _blinx_output_sensor as output_sensor_file
import _blinx_shtc3 as shtc3
import _blinx_analog as analog
import _blinx_ds1820 as ds1820

import _blinx_ssd1306 as ssd1306
import _blinx_font8x12 as font

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
# information the delta, for the data
general_size = 180
size_data_sensors = [
    general_size+1, # 1  seconds
    general_size+1, # 10 seconds
    general_size+1, # 1  minutes
    general_size+1, # 10 minutes
    general_size+1, # 1  hours
    general_size+1  # 1  day
]
offset_data = [
    0,
    0,
    1,
    2,
    3,
    4
]
offset_to_seconds = [
    1,
    10,
    60,
    600,
    3600,
    3600*24
]
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# time

def get_time():
    return time.time()


#------------------------------------------------------------------------------
# screen output
wlan = None

def screen_init():
    global screen
    screen = ssd1306.SSD1306_I2C(128, 32, blinx.i2c)

def screen_write(line, text, start_x, fg=1):
    screen.fill_rect(start_x, line*8, 128, 8, 1-fg)
    screen.text(text, start_x, line*8, fg)

time.sleep_ms(10)

screen_init()


def write(text, w, h, start_x, start_y):
    start_x *= font.width
    start_y *= font.height
    for i in range(len(text)):
        bitmap = font.bitmap[ord(text[i])]
        posx = (i+1) * font.width
        if posx * w > 128: break
        for yy in range(font.height):
            y = yy * h
            if y >= 32: break
            hh = h
            if yy == font.height-1: hh -= 1
            b = ~bitmap[yy]
            for xx in range(font.width):
                x = (posx - xx - 1) * w
                col = b & 1
                screen.rect(start_x+x, start_y+y, start_x+w, start_y+hh, col)
                b >>= 1
    screen.show()

def screen_erase():
    screen.fill(0)

screen_cycle_count = 0
screen_instructions_count = 0

def write_config_id(data = []):
    global screen_cycle_count, screen_instructions_count

    screen_erase()

    def show_name():
        name = 'name:' + _config.id
        name += ' '*(16-len(name))
        screen_write(0, name[:16], 0, 0)

    def show_wifi():
        if wlan:
            wifi = wlan.config('essid')
        else:
            wifi = _wifi.ssid
        wifi = 'wifi:' + wifi
        wifi += ' '*(16-len(wifi))
        screen_write(0, wifi[:16], 0, 0)

    if not wlan:
        if screen_cycle_count <= 1:
            show_name()
            if screen_instructions_count < 4:
                screen_instructions_count += 1
        elif screen_cycle_count <= 3:
            show_wifi()
        else:
            screen_write(0, 'PLEASE WAIT... ', 0, 0)
        if screen_instructions_count >= 4:
            screen_write(1, '> scan the QR  <', 0, 0)
            screen_write(2, '> code to view <', 0, 0)
            screen_write(3, '> instructions <', 0, 0)
    else:

        if screen_cycle_count <= 1:
            show_name()
        else:
            show_wifi()

        y = 1
        for index in data:
            z = 0
            for el in index:
                screen_write(y, el, z)
                z += 64
            y += 1

    screen_cycle_count = (screen_cycle_count+1) % 6

    screen.show()

write_config_id()

#------------------------------------------------------------------------------
# start networking

network.hostname(_config.id)  # assign the mDNS name <device_id>.local

wlan_connected = uasyncio.ThreadSafeFlag()  # flag indicating wlan connection

def wlan_start_connect():
    print('wlan_start_connect')
    global wlan
    wlan_connected.clear()
    wlan = None
    wl = network.WLAN(network.STA_IF)
    wl.active(True)
    wl.connect(_wifi.ssid, _wifi.pwd)
    uasyncio.create_task(wlan_connect_loop(wl))

async def wlan_connect_loop(wl):
    global wlan
    elapsed = 0
    while True:
        await uasyncio.sleep_ms(250)
        blinx.led_pin.value(elapsed & 1)
        if wl.isconnected(): break
        elapsed += 1
        print(elapsed)
    print('connected to WLAN after',elapsed*0.25,'secs')
    blinx.led_pin.value(0) # led on
    print(wl.ifconfig())
    wlan = wl
    wlan_connected.set()

def wlan_disconnect():
    global wlan
#    wlan.active(False)
    wlan.disconnect()
    wlan = None
    wlan_connected.clear()
    blinx.led_pin.value(1) # led off

#------------------------------------------------------------------------------

# web server
class AsyncWriter:
    def __init__(self, wstream, size = 1400):
        self.wstream = wstream
        self.sizeBuf = size
        self.buf = bytearray(self.sizeBuf)
        self.size = 0
    async def write(self, data):
        L = len(data)
        l = L
        y = 0
        while True:
            diff = self.sizeBuf - (self.size + l)
            if diff <= 0:
                for i in range(l+diff):
                    self.buf[self.size] = data[y + i]
                    self.size += 1

                self.wstream.write(self.buf)
                await self.wstream.drain()
                self.size = 0
                self.buf = bytearray(1400)
                
                l = -diff
                y = L+diff
            else:
                for i in range(l):
                    self.buf[self.size] = data[y + i]
                    self.size += 1
                break
    async def drain(self):
        self.wstream.write(self.buf)
        await self.wstream.drain()
        self.size = 0
        self.buf = bytearray(1400)

class AsyncReader:

    def __init__(self, rstream):
        self.rstream = rstream
        self.buf = bytearray(10)
        self.lo = 0
        self.hi = 0
        self.remaining_bytes = 999999

    async def read_byte(self):
        if self.remaining_bytes <= 0:
            return -1  # EOF
        else:
            if self.lo < self.hi:
                byte = self.buf[self.lo]
                self.lo += 1
            else:
                n = await self.rstream.readinto(self.buf)
                if n > 0:
                    byte = self.buf[0]
                    self.lo = 1
                    self.hi = n
                else:
                    self.remaining_bytes = 0
                    return -1  # EOF
            self.remaining_bytes -= 1
            return byte

    async def expect(self, seq):
        for i in range(len(seq)):
            byte = await self.read_byte()
            if byte != seq[i]:
                return False
        return True

    async def read_group(self, ender):
        result = b''
        while len(result) < 100:
            byte = await self.read_byte()
            if byte <= 0x20: break
            result += chr(byte)
        if byte == ender:
            return result
        else:
            return b''

    async def read_header_attribute(self, attribute):
        attribute_value = -1
        state = 2  # CR-LF seen
        byte = await self.read_byte()
        while True:
            if byte < 0:
                break  # EOF
            elif byte == 10:
                state = ((state>>1)+1)*2
                if state == 4:
                    break  # empty line
            elif byte == 13 and (state & 1) == 0:
                state += 1
            elif state == 2:  # at start of line
                state = 0
                i = 0
                while i < len(attribute):
                    if byte >= 65 and byte <= 90: byte += 32  # lower case
                    if byte != attribute[i]:
                        break
                    byte = await self.read_byte()
                    i += 1
                if i < len(attribute):
                    continue
                if byte == 32:  # optional space
                    byte = await self.read_byte()
                if byte >= 48 and byte <= 57:  # 0-9
                    attribute_value = 0
                    while byte >= 48 and byte <= 57:
                        attribute_value = attribute_value*10 + byte - 48
                        byte = await self.read_byte()
                    if not (byte == -1 or byte == 10 or byte == 13):
                        attribute_value = -1
                continue
            else:
                state = 0
            byte = await self.read_byte()
        return attribute_value

    async def read_to_eof(self):
        content = b''
        while True:
            byte = await self.read_byte()
            if byte < 0: break
            content += chr(byte)
        return content

async def web_server():

    async def handle_client_connection(rstream, wstream):
        # register for know what type of requests we receive
        async def register(doc, q, content, encapsulation, wstream):
            
            # to init all the list for the data/sensor
            def init_data_sensor(error = False):
                global nsensors_input, nsensors_input_use, bytes_per_measurement, size_bytearray, measurements, input_index_sensors, input_functions_sensors, \
                input_functions_sensors_csv, input_size_sensors_csv, type_char_sensors, import_file_sensors, input_short_name_sensors, \
                affichage_sensors_list, hi, lo, all_csv, default_input_index_sensors, input_pin_sensors, input_type_sensors, input_true_name, input_more_sensors
                hi = [0] * len(size_data_sensors)
                lo = [0] * len(size_data_sensors)
                done_one = [0] * len(size_data_sensors)
                nsensors_input = 4
                nsensors_input_use = 0
                bytes_per_measurement = nsensors_input * 2

                size_bytearray = []
                for i in size_data_sensors:
                    size_bytearray.append(i * bytes_per_measurement)

                measurements = [] # bytearray(size_data_sensors * bytes_per_measurement)
                for i in size_bytearray:
                    measurements.append(bytearray(i))
                input_index_sensors = []
                input_pin_sensors = []
                input_type_sensors = []
                input_short_name_sensors = []
                input_functions_sensors = []
                input_functions_sensors_csv = []
                input_size_sensors_csv = [0]
                type_char_sensors = []
                import_file_sensors = []
                affichage_sensors_list = []
                input_true_name = []
                input_more_sensors = []
                all_csv = b''
                default_input_index_sensors = []
                output_sensor_file.value_output = [[],[],[],[]]
                write_config_id()  # show device id on screen
                screen.show()
                if error:
                    wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

            global nsensors_input, nsensors_input_use, bytes_per_measurement, size_bytearray, measurements, input_index_sensors, input_functions_sensors, \
            input_functions_sensors_csv, input_size_sensors_csv, type_char_sensors, import_file_sensors, input_short_name_sensors, \
            affichage_sensors_list, hi, lo, all_csv, default_input_index_sensors, input_pin_sensors, input_type_sensors, input_true_name, input_more_sensors
            
            l = len(doc)
            #print('register', q, l, doc)
            codeBoot = True
            if q < l:
                if doc[q:q+7] == b'seqnum=':
                    print('seqnum')
                    q += 7
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l
                
                if doc[q:q+6] == b'write=' and not safe_fs: # write a file
                    print('write')
                    codeBoot = False
                    q += 6
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1

                    content = ''
                    format = 'w'
                    if doc[q:q+8] == b'content=': # the content to write
                        print('content')
                        q += 8
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        content = ubinascii.a2b_base64(doc[start:q])
                        if q < l:
                            q += 1
                    if doc[q:q+7] == b'format=': # the format to opent the file : `w`, `a`, `w+`, `a+`, `x` ...
                        print('format')
                        q += 7
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        format = str(doc[start:q], 'utf-8')
                        if q < l:
                            q += 1
                    try :
                        if safe_to_modify(name): # verify if we can remove it
                            wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                        else:
                            f = open(name, format)
                            f.write(content)
                            f.close()
                            #del f, name, format, content

                            await encapsulation.start(b'text/plain', 0)  # total length in bytes
                            await encapsulation.add(b'')
                            await encapsulation.end()
                    except Exception as e:
                        print('write : error', e)
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                elif doc[q:q+5] == b'read=': # read a file
                    print('read')
                    codeBoot = False
                    q += 5
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                    pos = 0
                    if doc[q:q+4] == b'pos=': # where we are in the reading of the file
                        print('pos')
                        q += 6
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        pos = int(doc[start:q])
                        if q < l:
                            q += 1
                    
                    try :
                        if safe_to_modify(name): # verify if we can remove it
                            wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                        else:
                            f = open(name, 'rb+')
                            for _ in range(pos):
                                f.read(4000)

                            size = os.stat(name)[6] - 4000*pos
                        
                            if size < 0: size = 0
                            if size > 4000 : size = 4000
                            
                            await encapsulation.start(b'text/plain', size)  # total length in bytes
                            for _ in range(100):
                                await encapsulation.add(f.read(40))
                            f.close()
                            #del f, name, size
                            await encapsulation.end()
                    except Exception as e:
                        print('read : error', e)
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                elif doc[q:q+7] == b'remove=' and not safe_fs: # remove a file
                    print('remove')
                    codeBoot = False
                    q += 7
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                    
                    try:
                        if safe_to_modify(name): # verify if we can remove it
                            wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                        else:
                            os.remove(name)
                            #del name

                            await encapsulation.start(b'text/plain', 0)  # total length in bytes
                            await encapsulation.add(b'')
                            await encapsulation.end()
                    except Exception as e:
                        print('remove : error', e)
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                elif doc[q:q+3] == b'ls=': # get the list of the files
                    print('ls')
                    codeBoot = False
                    q += 6
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    dir = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                    size = 0
                    
                    try:
                        t = os.listdir(dir)
                        for i in t:
                            size += len(bytes(i, 'utf-8')) + 1

                        await encapsulation.start(b'text/plain', size)  # total length in bytes
                        for i in t:
                            await encapsulation.add(bytes(i + '\n', 'utf-8'))
                        #del dir, t
                        await encapsulation.end()
                    except Exception as e:
                        print('file list : error', e)
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                elif doc[q:q+8] == b'version=': # get the version of blinx
                    print('version')
                    codeBoot = False
                    q += 8
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l

                    v = _version.version # TODO
                    
                    await encapsulation.start(b'text/plain', len(v))  # total length in bytes
                    await encapsulation.add(v)
                    await encapsulation.end()
                elif doc[q:q+13] == b'sensors_stop=': # stop the data collection
                    blinx.periph_power(0)
                    print('sensors_stop')
                    codeBoot = False
                    q += 13
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l

                    ds1820.reset_ds1820()
                    blinx.periph_power(1)
                    init_data_sensor(False)
                    await encapsulation.start(b'text/plain', 0)  # total length in bytes
                    await encapsulation.add(b'')
                    await encapsulation.end()
                elif doc[q:q+7] == b'config=': # config the sensor
                    blinx.periph_power(0)
                    print('config')
                    codeBoot = False
                    q += 13
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name_sensors = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                    
                    ds1820.reset_ds1820()
                    blinx.periph_power(1)
                    info_sensors = name_sensors.split(',')
                    nsensors_input_use = len(info_sensors)
                    if nsensors_input_use == 0 :
                        init_data_sensor(True)
                    else :
                        nsensors_input = 4
                        hi = [0] * len(size_data_sensors)
                        lo = [0] * len(size_data_sensors)
                        done_one = [0] * len(size_data_sensors)

                        affichage_sensors_list = []

                        input_index_sensors = []
                        input_type_sensors = []
                        input_functions_sensors = []
                        input_functions_sensors_csv = []
                        input_size_sensors_csv = []
                        type_char_sensors = []
                        input_true_name = []
                        input_more_sensors = []

                        input_short_name_sensors = []
                        input_pin_sensors = []
                        import_file_sensors_temp = []
                        true_name = []
                        
                        for i in info_sensors:
                            t = i.split('=')
                            input_index_sensors.append(t[0])
                            t = t[1].split('/')
                            tt = t[0]
                            
                            if len(tt) > 2:
                                init_data_sensor(True)
                                break
                            if len(t) < 4:
                                init_data_sensor(True)
                                break
                            
                            input_short_name_sensors.append(tt)
                            input_pin_sensors.append(t[1])
                            import_file_sensors_temp.append(t[2])
                            true_name.append(t[3])
                            
                            if input_pin_sensors[-1] == 'i2c':
                                nsensors_input += 1
                        else: 
                            for i in import_file_sensors:
                                if i in sys.modules:
                                    del sys.modules[i]
                                if not (i in import_file_sensors_temp) and (safe_to_modify(i)) and i in os.listdir():
                                    os.remove(i)
                                    
                            import_file_sensors = import_file_sensors_temp[:]
                            for i in range(len(import_file_sensors)):
                                # get the file, and the information of the sensor from the file
                                temp_name = import_file_sensors[i]
                                if temp_name[-4:] == '.mpy':
                                    temp_name = temp_name[:-4]
                                elif temp_name[-3:] == '.py':
                                    temp_name = temp_name[:-3]

                                try:
                                    a = __import__(temp_name)
                                    info = a.info[true_name[i]]
                                    input_true_name.append(true_name[i])
                                    input_functions_sensors.append(info['function'])
                                    input_functions_sensors_csv.append(info['function_csv'])
                                    input_size_sensors_csv.append(info['size_csv'])
                                    type_char_sensors.append(info['char'])
                                    input_type_sensors.append(info['type'])
                                    input_more_sensors.append(info['more'])
                                except Exception as e:
                                    print('config sensor : error', e)
                                    init_data_sensor(True)
                                    break
                            else:
                                bytes_per_measurement = nsensors_input * 2

                                size_bytearray = []
                                for i in size_data_sensors:
                                    size_bytearray.append(i * bytes_per_measurement)

                                measurements = [] # bytearray(size_data_sensors * bytes_per_measurement)
                                for i in size_bytearray:
                                    measurements.append(bytearray(i))

                                all_csv = b''
                                for i in range(len(input_index_sensors)):
                                    all_csv += b',' + bytes(input_index_sensors[i], 'utf-8') + ':' + bytes(type_char_sensors[i], 'utf-8')
                                all_csv += b'\n'

                                default_input_index_sensors = list(range(nsensors_input_use))
                                input_size_sensors_csv.append(sum(input_size_sensors_csv))
                                await encapsulation.start(b'text/plain', 0)  # total length in bytes
                                await encapsulation.add(b'')
                                await encapsulation.end()
                elif doc[q:q+8] == b'content=' or doc[q:q+7] == b'output=': # change a output sensor
                    # if it is `content` then we have a text in base64, if it is `output` we have a text in utf8
                    print('output-content')
                    codeBoot = False
                    output_or_content = False
                    if doc[q:q+8] == b'content=':
                        q += 8
                        output_or_content = True
                    else:
                        q += 7
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    
                    if output_or_content:
                        output_sensors = str(ubinascii.a2b_base64(doc[start:q]), 'utf-8')
                    else:
                        output_sensors = str(doc[start:q], 'utf-8')
                        
                    if q < l:
                        q += 1
                    
                    try:
                        t = output_sensors.split(',')
                        for i in t:
                            tt = i.split('=')
                            name = tt[0]
                            if len(tt) > 1:
                                args = tt[1].split('/')
                            else :
                                args = []
                            if not (name.lower() in output_sensor_file.dict_sensors_output):
                                wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                                break
                            else :
                                output_sensor_file.dict_sensors_output[name](args)
                        else:
                            #await measurements_as_csv(encapsulation, '', 9999999, '1s')
                            await encapsulation.start(b'text/plain', 0)  # total length in bytes
                            await encapsulation.add(b'')
                            await encapsulation.end()
                    except Exception as e:
                        print('output : error', e)
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

            if codeBoot : # if it is nothing above, we go to codeboot.org
                print('codeBoot')
                await main_page(encapsulation)
        def registerGetSensor(doc, q): # get the information, when we want to get the data : we want the csv
            l = len(doc)
            n = 999999
            times_sensors = '1s'
            if q < l:
                if doc[q:q+7] == b'seqnum=':
                    q += 7
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l
                if doc[q:q+6] == b'delta=': # delta we want
                    q += 6
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    times_sensors = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                if doc[q:q+2] == b'n=': # the number of data we want
                    q += 2
                    n = 0
                    while q < l:
                        byte = doc[q]
                        if byte >= 48 and byte <= 57:
                            n = n*10 + (byte - 48)
                            q += 1
                        else:
                            break
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l
            return n, times_sensors

        print('handle_client_connection')

        ar = AsyncReader(rstream)

        if not await ar.expect(b'GET '):
            wstream.write(b'HTTP/1.1 405 Method Not Allowed\r\n')
        else:
            doc = await ar.read_group(0x20)  # group must be followed by a space
            if not (doc and await ar.expect(b'HTTP/1.1\r\n')):
                wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
            else:

                # important to avoid 'connection reset' errors
                content_length = await ar.read_header_attribute(b'content-length:')
                ar.remaining_bytes = content_length
                content = await ar.read_to_eof()

                q = doc.find(b'?')  # find first '?' if any
                if q < 0:
                    q = len(doc)

                pathUrl = str(doc[:q], 'utf-8')
                print('doc =', pathUrl)

                q += 1
                if q < len(doc) and doc[q] == 0x3f: # two '?' in a row?
                    encapsulation = PNGEncapsulation(wstream)
                    q += 1
                else:
                    encapsulation = NoEncapsulation(wstream)


                #print(pathUrl, len(pathUrl))
                if pathUrl == '/favicon.ico':
                    print('favicon')
                    wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                elif pathUrl != '/' :
                    print('sensor')
                    pathUrl = pathUrl[1:]
                    if pathUrl[-4:] == '.csv':
                        pathUrl = pathUrl[:-4]
                        n, times_sensors = registerGetSensor(doc, q)
                        await measurements_as_csv(encapsulation, pathUrl, n, times_sensors)
                    else:
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                else:
                    print('other')
                    await register(doc, q, content, encapsulation, wstream)

        await wstream.drain()
        await wstream.wait_closed()

#        print(gc.mem_free())

    
    wlan_start_connect()
    await wlan_connected.wait()
    
    if wlan:
#        sync_ntptime()
        #gc.collect()
        uasyncio.create_task(settime_from_unixtime_servers())
        uasyncio.create_task(uasyncio.start_server(handle_client_connection, '0.0.0.0', 80))

unixtime_servers = (
    ('blinx.codeboot.org', 80, b'/cgi-bin/unixtime.cmd'),
    ('worldtimeapi.org', 80, b'/api/timezone/Etc/UTC.txt'),
    )

async def settime_from_unixtime_servers():
    i = 0
    while True:
        unixtime_server = unixtime_servers[i]
        i = (i+1) % len(unixtime_servers)
        host = unixtime_server[0]
        port = unixtime_server[1]
        path = unixtime_server[2]
        print('trying to connect to ' + host)
#        rstream, wstream = await uasyncio.create_task(uasyncio.open_connection('worldtimeapi.org', 80))
        rstream = None
        try:
            rstream, wstream = await uasyncio.create_task(uasyncio.open_connection(host, port))
        except Exception as e:
            print('e =', repr(e))
        if rstream is None:
            print('could not connect to ' + host)
            await uasyncio.sleep_ms(1000)
        else:
            print('connected to ' + host)
            ar = AsyncReader(rstream)
            wstream.write(b'GET ')
            wstream.write(path)
            wstream.write(b' HTTP/1.1\r\n\r\n')
            await wstream.drain()
            content_length = await ar.read_header_attribute(b'content-length:')
            ar.remaining_bytes = content_length
            unixtime = await ar.read_header_attribute(b'unixtime:')
            wstream.close()
            if unixtime > 0:
                print('unixtime =', unixtime)
                settime(unixtime)
                return
            await uasyncio.sleep_ms(4000)

def settime(t):

    import machine, utime

    tm = utime.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

def sync_ntptime():
    ntp_servers = ('pool.ntp.org', '142.112.54.28', '216.6.2.70', '206.108.0.131', '206.108.0.132')
    i = 0
    n = 10
    while n > 0:
        ntptime.ntphost = ntp_servers[i]
        print('trying', ntptime.ntphost)
        try:
            ntptime.settime()  # get time from NTP server
            print('time synced!')
            return
        except Exception as e:
            print('exception', e)
            i = (i+1) % len(ntp_servers)
            n -= 1
    print('failed to sync time using ntp server')

async def main_page(encapsulation):
    # TODO: add query to URL so that codeboot knows my name and address
    content = '<meta http-equiv="Refresh" content="0; url=&quot;https://blinx.codeboot.org&quot;"/>'
    await encapsulation.start(b'text/html', len(content))
    await encapsulation.add(content)
    await encapsulation.end()

class NoEncapsulation:

    def __init__(self, wstream):
        self.wstream = wstream #AsyncWriter(wstream)
        #self.size = 0

    async def start(self, type, nbytes):
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: ')
        #self.size += 31
        self.wstream.write(type)
        #self.size += len(type)
        self.wstream.write(b'\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        #self.size += 50
        self.wstream.write(bytes(str(nbytes), 'utf-8'))
        #self.size += len(t)
        #del t
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')
        #self.size += 24
        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    async def add(self, data):
        self.wstream.write(data)
        #self.size += len(data)
        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    async def end(self):
        await self.wstream.drain()
        #self.size = 0
        #await self.wstream.drain()
        pass

# convert sequence of bytes to PNG image


png_overhead = 69  # bytes added by PNG encapsulation

class PNGEncapsulation:

    def __init__(self, wstream):
        self.wstream = wstream # AsyncWriter(wstream)
        self.crc = 0
        self.a = 0
        self.b = 0
        self.padding = 0
        #self.size = 0

    async def start(self, type, nbytes):
        self.padding = 2 - nbytes % 3  # bytes ignored at end
        nbytes_div3 = (nbytes + 3) // 3
        nbytes = nbytes_div3 * 3
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: image/x-png\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        #self.size += 92
        self.wstream.write(bytes(str(nbytes + png_overhead), 'utf-8'))
        #self.size += len(t)
        #del t
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')
        #self.size += 24

        self.wstream.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A') # PNG signature
        #self.size += 8

        self.chunk_start(b'IHDR', 13)  # IHDR chunk
        self.chunk_add(pack('>II', nbytes_div3, 1))
        self.chunk_add(b'\x08\x02\x00\x00\x00')  # \x02 = Truecolour
        self.chunk_end()

        self.chunk_start(b'IDAT', nbytes + 12)  # IDAT chunk
        self.chunk_add(b'\x78\x01\x01')
        n = nbytes+1
        self.chunk_add(pack('<HH', n, n ^ 0xFFFF))
        self.adler_start()
        self.adler_add(b'\x00')
        self.adler_add(bytes([self.padding]))

        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    async def add(self, data):
        self.adler_add(data)

    async def end(self):
        self.adler_add(b'\xFF'*self.padding)  # add padding at end
        self.adler_end()
        self.chunk_end()

        self.chunk_start(b'IEND', 0)  # IEND chunk
        self.chunk_end()

        self.size = 0
        await self.wstream.drain()

    def chunk_start(self, type, length):
        self.wstream.write(pack('>I', length))
        #self.size += 4
        self.wstream.write(type)
        #self.size += len(type)
        self.crc = crc32(type)
        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    def chunk_add(self, data):
        self.crc = crc32(data, self.crc)
        self.wstream.write(data)
        #self.size += len(data)
        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    def chunk_end(self):
        self.wstream.write(pack('>I', self.crc))
        #self.size += 4
        #if self.size > 500:
        #    self.size = 0
        #    await self.wstream.drain()

    def adler_start(self):
        self.a = 1
        self.b = 0

    def adler_add(self, data):
        self.chunk_add(data)
        a = self.a
        b = self.b
        for i in range(len(data)):
            a = (a+data[i]) % 65521
            b = (b+a) % 65521
        self.a = a
        self.b = b

    def adler_end(self):
        self.chunk_add(pack('>I', (self.b << 16) + self.a))

#------------------------------------------------------------------------------

# sensor reader

import_file_sensors = ['shtc3.mpy', 'analog.mpy', 'ds1820.mpy']

# when we ask to modify a ouput sensor, we modify the type for the port
def modify_port_input(port, name, save_output_sensors_csv, get_save_output_sensors):
    global input_index_sensors, input_short_name_sensors, input_functions_sensors, input_functions_sensors_csv, \
        input_size_sensors_csv, nsensors_input_use, input_pin_sensors, input_type_sensors, all_csv
    # do we know this sensors
    if port in input_pin_sensors :
        indexSensors = input_pin_sensors.index(port)
        # is it a input sensors, if yes we modify the type
        if input_type_sensors[indexSensors] == 'in':
            input_index_sensors[indexSensors] = 'port-' + name
            input_short_name_sensors[indexSensors] = 'p' + str(port+1)
            input_functions_sensors_csv[indexSensors] = save_output_sensors_csv
            input_size_sensors_csv[indexSensors] = 4
            input_size_sensors_csv.pop()
            input_size_sensors_csv.append(sum(input_size_sensors_csv))
            input_pin_sensors[indexSensors] = port
            input_type_sensors[indexSensors] = 'out'
            type_char_sensors[indexSensors] = ''
            #import_file_sensors[indexSensors] = ''
        
            all_csv = b''
            for i in range(len(input_index_sensors)):
                all_csv += b',' + bytes(input_index_sensors[i], 'utf-8') + ':' + bytes(type_char_sensors[i], 'utf-8')
            all_csv += b'\n'
        
            if port == 0:
                input_functions_sensors[indexSensors] = get_save_output_sensors(0)
            elif port == 1:
                input_functions_sensors[indexSensors] = get_save_output_sensors(1)
            elif port == 2:
                input_functions_sensors[indexSensors] = get_save_output_sensors(2)
            elif port == 3:
                input_functions_sensors[indexSensors] = get_save_output_sensors(3)

            for i in range(len(size_bytearray)):
                for y in range(size_data_sensors[i]):
                    t = y * bytes_per_measurement + 2 * indexSensors
                    measurements[i][t] = 0 & 0xff
                    measurements[i][t+1] = 0 >> 8
    else:
        # we don't know the sensor, then now we know it
        input_index_sensors.append('port-' + name)
        input_short_name_sensors.append('p' + str(port+1))
        input_functions_sensors_csv.append(save_output_sensors_csv)
        input_size_sensors_csv[-1] = 4
        input_size_sensors_csv.append(sum(input_size_sensors_csv))
        nsensors_input_use += 1
        input_pin_sensors.append(port)
        input_type_sensors.append('out')
        type_char_sensors.append('')
        import_file_sensors.append('')
        
        all_csv = b''
        for i in input_index_sensors:
            all_csv += b',' + bytes(i, 'utf-8')
        all_csv += b'\n'
        
        if port == 0:
            input_functions_sensors.append(get_save_output_sensors(0))
        elif port == 1:
            input_functions_sensors.append(get_save_output_sensors(1))
        elif port == 2:
            input_functions_sensors.append(get_save_output_sensors(2))
        elif port == 3:
            input_functions_sensors.append(get_save_output_sensors(3))

output_sensor_file.modify_port_input = modify_port_input

# list of info for the sensor
input_index_sensors = [
    'temp',
    'humid'
]

input_short_name_sensors = [
    't',
    'h'
]

input_functions_sensors = [
    shtc3.info['shtc3-temp']['function'],
    shtc3.info['shtc3-humid']['function']
]

input_functions_sensors_csv = [
    shtc3.info['shtc3-temp']['function_csv'],
    shtc3.info['shtc3-humid']['function_csv']
]

input_size_sensors_csv = [
    shtc3.info['shtc3-temp']['size_csv'],
    shtc3.info['shtc3-humid']['size_csv']
]

input_more_sensors = [
    shtc3.info['shtc3-temp']['more'],
    shtc3.info['shtc3-humid']['more']
]

type_char_sensors = [
    shtc3.info['shtc3-temp']['char'],
    shtc3.info['shtc3-humid']['char']
]

input_true_name = [
    'shtc3-temp',
    'shtc3-humid'
]

nsamples = 4
nsensors_input = 6
nsensors_input_use = 2

input_pin_sensors = [
    'i2c',
    'i2c',
    0,
    1,
    2,
    3
]
input_type_sensors = [
    shtc3.info['shtc3-temp']['type'],
    shtc3.info['shtc3-humid']['type'],
    'in',
    'in',
    'in',
    'in'
]

# get the information for the sensor file
def get_sensor_analog_ds1820(n,m):
    global input_index_sensors, input_short_name_sensors, input_functions_sensors, \
        input_functions_sensors_csv, input_size_sensors_csv, nsensors_input_use, \
        input_true_name, input_more_sensors, type_char_sensors
    index = n*2 + m - 3
    name = str(n) + ('a' if m == 1 else 'b')
    nsensors_input_use += 1
    if ds1820.info['ds1820_'+str(n)+str(m)]['use']:
        input_index_sensors.append('temp' + str(index + 1))
        input_short_name_sensors.append('t' + str(index + 1))
        input_true_name.append('ds1820_'+str(n)+str(m))
        input_functions_sensors.append(ds1820.info['ds1820_'+str(n)+str(m)]['function'])
        input_functions_sensors_csv.append(ds1820.info['ds1820_'+str(n)+str(m)]['function_csv'])
        input_size_sensors_csv.append(ds1820.info['ds1820_'+str(n)+str(m)]['size_csv'])
        type_char_sensors.append(ds1820.info['ds1820_'+str(n)+str(m)]['char'])
        input_more_sensors.append(ds1820.info['ds1820_'+str(n)+str(m)]['more'])
    else:
        input_index_sensors.append('volt' + str(index + 1))
        input_short_name_sensors.append('v' + str(index + 1))
        input_true_name.append('analog_'+str(n)+str(m))
        input_functions_sensors.append(analog.info['analog_'+str(n)+str(m)]['function'])
        input_functions_sensors_csv.append(analog.info['analog_'+str(n)+str(m)]['function_csv'])
        input_size_sensors_csv.append(analog.info['analog_'+str(n)+str(m)]['size_csv'])
        type_char_sensors.append(analog.info['analog_'+str(n)+str(m)]['char'])
        input_more_sensors.append(analog.info['analog_'+str(n)+str(m)]['more'])

for i in range(1,3):
    for y in range(1,3):
        get_sensor_analog_ds1820(i,y)

measurement_time = get_time()
lo = [0] * len(size_data_sensors)
hi = [0] * len(size_data_sensors)
done_one = [0] * len(size_data_sensors)

bytes_per_measurement = nsensors_input * 2

size_bytearray = []
for i in size_data_sensors:
    size_bytearray.append(i * bytes_per_measurement)

measurements = [] # bytearray(size * bytes_per_measurement)
for i in size_bytearray:
    measurements.append(bytearray(i))

input_size_sensors_csv.append(sum(input_size_sensors_csv))

affichage_sensors_list = [0, 1, 2, 3, 4, 5]


async def sensor_reader():
    global lo, hi, measurement_time, done_one
    while True:
        ms = 1000 - (time.ticks_ms() % 1000)
#        print('sleep_ms',ms)
        await uasyncio.sleep_ms(ms)
        if nsensors_input_use == 0:
            continue
        
        if done_one[0] > 0:
            if done_one[0] >= done_one[1]/done_one[0]:
                done_one[0] = -1
            else:
                done_one[0] += 1
        elif done_one[0] == 0:
            done_one[0] += 1

        timeInterval = int(time.ticks_ms() / 1000)
        
        # can we do an other delta time ?
        toDo_interval = None
        for i in range(1,len(offset_data)):
            if (timeInterval - offset_data[i]) % offset_to_seconds[i] == 0:
                toDo_interval = i
                break

        # do we use ds1820 sensor ?
        list_ds1820 = ['ds1820_'+str(i)+str(y) for y in range(1,3) for i in range(1,3)]
        use_ds1820 = False
        for i in range(len(input_true_name)):
            if input_true_name[i] in list_ds1820:
                use_ds1820 = True
                input_more_sensors[i][0].convert_temp()
        start_ds1820 = time.ticks_ms()
        
        output_sensor_file.remove_output_value()


        measurement_time = get_time()
        data = [0] * nsensors_input_use
        
        for i in range(nsamples): # ?
            for y in range(nsensors_input_use):
                #print(nsensors_input_use, y, input_functions_sensors)
                if input_true_name[y] not in list_ds1820:
                    data[y] += input_functions_sensors[y]()
        
        for i in range(nsensors_input_use):
            data[i] = data[i] // nsamples
        
        for i in range(nsensors_input_use):
            measurements[0][j + 2*i] = data[i] & 0xff; measurements[0][j + 2*i + 1] = data[i] >> 8

        # if we use ds1820 sensor, is there enough time passed so that we can read the value
        if use_ds1820:
            diff = time.ticks_ms() - start_ds1820
            if diff > 0: await uasyncio.sleep_ms(diff)
            for y in range(nsensors_input_use):
                if input_true_name[y] in list_ds1820:
                    v = input_functions_sensors[y]()
                    measurements[0][j + 2*y] = v & 0xff; measurements[0][j + 2*y + 1] = v >> 8

        hi[0] += 1
        if hi[0] == size_data_sensors[0]: hi[0] = 0
        j = hi[0] * bytes_per_measurement

        if lo[0] == hi[0]:
            lo[0] += 1
            if lo[0] == size_data_sensors[0]: lo[0] = 0

        if toDo_interval != None : # we can do an other delta time ?
            moyenneData(toDo_interval)

        # can we show data on the screen ?
        if not output_sensor_file.screen_modify:
            tempL = len(affichage_sensors_list)
            if tempL != 0:
                data = []
                for i in range(min(6,tempL)):
                    t = affichage_sensors_list[i]
                    name = input_short_name_sensors[t]
                    tt = input_functions_sensors_csv[t](measurements[0][j + 2*t] + (measurements[0][j + 2*t + 1] << 8), 0) + ':' + name + ' ' * (2 - len(name))
                    tt = ' ' * (8 - len(tt)) + tt
                    if i%2 == 0:
                        data.append([])
                    data[-1].append(tt)
                write_config_id(data)

        #screen_write(3, 'T=%5.1f  H=%5.1f' % (temp_from_raw(t)/100, humid_from_raw(h)/100))
        #screen.show()

        #gc.collect()

# to do the median of the value for the next delta time
def moyenneData(toDo_interval):
    global lo, hi, measurements, done_one
    diff = offset_to_seconds[toDo_interval] / offset_to_seconds[toDo_interval-1]
    textError = ''
    if done_one[toDo_interval-1] != 0:
        if done_one[toDo_interval] != -1:
            if done_one[toDo_interval] >= done_one[toDo_interval]/done_one[toDo_interval-1]:
                done_one[toDo_interval] = -1
            else:
                done_one[toDo_interval] += 1

        hi[toDo_interval] += 1
        l = size_data_sensors[toDo_interval]
        if hi[toDo_interval] == l: hi[toDo_interval] = 0
        j = hi[toDo_interval] * bytes_per_measurement
        last_j = hi[toDo_interval-1]

        somme = [0] * nsensors_input_use
        minI = last_j-diff
        numI = 0
        if last_j < diff:
            if done_one[toDo_interval-1] == -1:
                textError += '\na-' + str(minI) + '-'  + str(l+minI) + '-'  + str(l) + '\n'
                for i in range(l+minI,l):
                    textError += 'b-' + str(i) + '-'  + str(nsensors_input_use) + '\n'
                    for y in range(nsensors_input_use):
                        textError += 'c-' + str(y) + '\n'
                        indexData = int(i*bytes_per_measurement + 2*y)
                        if y == 0:
                            #if (measurements[toDo_interval-1][indexData] == '\x00' and measurements[toDo_interval-1][indexData + 1] == '\x00'):
                            #    break
                            #else:
                                numI += 1
                        somme[y] += measurements[toDo_interval-1][indexData] + (measurements[toDo_interval-1][indexData + 1] << 8) # int.from_bytes(measurements[toDo_interval-1][i + 2*y : i + 2*y + 2], 'little')
            minI = 0

        #print(minI, last_j, hi, lo)
        textError += '\nd-' + str(minI) + '-'  + str(last_j) + '\n'
        for i in range(minI,last_j):
            textError += 'e-' + str(i) + '-' + str(nsensors_input_use) + '\n'
            for y in range(nsensors_input_use):
                textError += 'f-' + str(y) + '\n'
                indexData = int(i*bytes_per_measurement + 2*y)
                #print('b',i,i*bytes_per_measurement,indexData, len(measurements[toDo_interval-1]))
                if y == 0:
                    #if (measurements[toDo_interval-1][indexData] == '\x00' and measurements[toDo_interval-1][indexData + 1] == '\x00'):
                    #    break
                    #else:
                        numI += 1
                somme[y] += measurements[toDo_interval-1][indexData] + (measurements[toDo_interval-1][indexData + 1] << 8) # int.from_bytes(measurements[toDo_interval-1][i + 2*y : i + 2*y + 2], 'little')

        #print(numI)
        if numI == 0:
            print(numI, last_j,minI, diff, toDo_interval, hi[toDo_interval-1], textError)

        for y in range(nsensors_input_use):
            t = int(somme[y] / numI)
            measurements[toDo_interval][j + 2*y] = t & 0xff; measurements[toDo_interval][j + 2*y + 1] = t >> 8

        if lo[toDo_interval] == hi[toDo_interval]:
            lo[toDo_interval] += 1
            if lo[toDo_interval] == size_data_sensors[toDo_interval]: lo[toDo_interval] = 0


csv_header = b'T:unix_timestamp'

all_csv = b''
for i in range(len(input_index_sensors)):
    all_csv += b',' + bytes(input_index_sensors[i], 'utf-8') + ':' + bytes(type_char_sensors[i], 'utf-8')
all_csv += b'\n'

default_input_index_sensors = list(range(nsensors_input_use))

async def measurements_as_csv(encapsulation, name, n, times_sensors):
    def get_time_sensors(modulo):
        t = measurement_time
        while t%modulo != 0:
            t -= 1
        return t
    global affichage_sensors_list
    
    # which delta time we want ?
    if times_sensors == '1s':
        times_sensors = 0
    elif times_sensors == '10s':
        times_sensors = 1
    elif times_sensors == '1m':
        times_sensors = 2
    elif times_sensors == '10m':
        times_sensors = 3
    elif times_sensors == '1h':
        times_sensors = 4
    elif times_sensors == '1d':
        times_sensors = 5
    else :
        times_sensors = 0
    
    input_index_sensors_look = []
    size_lign_csv = 1 + 10 # for the '\n' and the time
    csv_header_modify = csv_header
    if name == '' or name == 'foo':
        input_index_sensors_look = default_input_index_sensors
        csv_header_modify += all_csv 
        size_lign_csv += input_size_sensors_csv[-1] + nsensors_input_use
    else :
        t = name.split(',')
        for i in t :
            csv_header_modify += b',' + bytes(i, 'utf-8')
            if i in input_index_sensors:
                temp = input_index_sensors.index(i)
                input_index_sensors_look.append(temp)
                csv_header_modify += ':' + bytes(type_char_sensors[temp], 'utf-8')
                size_lign_csv += input_size_sensors_csv[temp] + 1
            else :
                input_index_sensors_look.append(-1)
                size_lign_csv += 1
        csv_header_modify += b'\n'
    
    
    affichage_sensors_list = []
    for i in input_index_sensors_look:
        if i != -1:
            affichage_sensors_list.append(i)


    avail = hi[times_sensors] - lo[times_sensors]
    if avail < 0: avail += size_data_sensors[times_sensors]
    #print(avail,hi,lo,n, times_sensors)
    n = min(n, avail)  # number of measurements

    print('measurements_as_csv', n, input_index_sensors_look)

    await encapsulation.start(b'text/plain', len(csv_header_modify) + n * size_lign_csv)  # total length in bytes

    await encapsulation.add(csv_header_modify)

    i = n
    modulo = offset_to_seconds[times_sensors]
    measurement_time_temp = get_time_sensors(modulo)
    #a = bytearray()
    #for i in range(25):
    #    a += measurements[0][i*bytes_per_measurement:i*bytes_per_measurement+2]
    #print(a)
    while i > 0:
        #print(i)
        i -= 1
        j = hi[times_sensors] - i
        if j < 0: j += size_data_sensors[times_sensors]
        j *= bytes_per_measurement
        text = '%10d' % (measurement_time_temp - i * modulo)
        for y in input_index_sensors_look:
            text += ','
            if y != -1:
                text += input_functions_sensors_csv[y](measurements[times_sensors][j + 2*y] + (measurements[times_sensors][j + 2*y + 1] << 8), times_sensors)
        text += '\n'
        #gc.collect()
        row = bytes(text, 'utf-8')
        #print(row)
        await encapsulation.add(row)

    await encapsulation.end()

    #if not output_sensor_file.screen_modify:
    #    write_config_id()


#------------------------------------------------------------------------------

def main():
    uasyncio.create_task(sensor_reader())
    uasyncio.create_task(web_server())
    uasyncio.get_event_loop().run_forever()

main()
