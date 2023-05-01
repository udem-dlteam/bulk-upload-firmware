import blinx
import ubinascii, os

#------------------------------------------------------------------------------

# time

import time

def get_time():
    return time.time()

#------------------------------------------------------------------------------

# turn on peripherals

blinx.periph_power(1)

#------------------------------------------------------------------------------

# screen output

import ssd1306

def screen_init():
    global screen
    screen = ssd1306.SSD1306_I2C(128, 32, blinx.i2c)

def screen_write(line, text):
    screen.fill_rect(0, line*8, 128, 8, 0)
    screen.text(text, 0, line*8, 1)

time.sleep_ms(10)

blinx.i2c_init()

screen_init()

import font8x12 as font

def write(text, w, h):
    screen.fill(0)
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
                screen.rect(x, y, w, hh, col)
                b >>= 1
    screen.show()

import _config

write(_config.id, 2, 2)  # show device id on screen

#------------------------------------------------------------------------------

# start networking

import uasyncio

import network
import ntptime
import gc

network.hostname(_config.id)  # assign the mDNS name <device_id>.local

wlan_connected = uasyncio.ThreadSafeFlag()  # flag indicating wlan connection

wlan = None

def wlan_start_connect():
    print('wlan_start_connect')
    global wlan
    wlan_connected.clear()
    wlan = None
    wl = network.WLAN(network.STA_IF)
    wl.active(True)
    wl.connect(_config.ssid, _config.pwd)
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
    print("connected to WLAN after",elapsed*0.25,"secs")
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
        async def register(doc, q, content, encapsulation, wstream):
            l = len(doc)
            print("register", q, l, doc)
            codeBoot = True
            if q < l:
                if doc[q:q+7] == b'seqnum=':
                    print("seqnum")
                    q += 7
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = l
                if doc[q:q+6] == b'write=':
                    print("write")
                    codeBoot = False
                    q += 6
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1

                    content = ""
                    format = "w"
                    if doc[q:q+8] == b'content=':
                        print("content")
                        q += 8
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        content = ubinascii.a2b_base64(doc[start:q])
                        if q < l:
                            q += 1
                    if doc[q:q+7] == b'format=':
                        print("format")
                        q += 7
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        format = str(doc[start:q], 'utf-8')
                        if q < l:
                            q += 1
                    try :
                        f = open(name, format)
                        f.write(content)
                        f.close()
                        #del f, name, format, content
                    except :
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                    await encapsulation.start(b'text/plain', 0)  # total length in bytes
                    await encapsulation.add(b"")
                    await encapsulation.end()
                elif doc[q:q+5] == b'read=':
                    print("read")
                    codeBoot = False
                    q += 5
                    start = q
                    q = doc.find(b'&', q)
                    if q < 0:
                        q = l
                    name = str(doc[start:q], 'utf-8')
                    if q < l:
                        q += 1
                    rendu = 0
                    if doc[q:q+6] == b'rendu=':
                        print("rendu")
                        q += 6
                        start = q
                        q = doc.find(b'&', q)
                        if q < 0:
                            q = l
                        rendu = int(doc[start:q])
                        if q < l:
                            q += 1
                    
                    try :
                        f = open(name, 'rb+')
                        for _ in range(rendu):
                            f.read(4000)

                        size = os.stat(name)[6] - 4000*rendu
                    
                        if size < 0: size = 0
                        if size > 4000 : size = 4000

                    except :
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                    await encapsulation.start(b'text/plain', size)  # total length in bytes
                    for _ in range(100):
                        await encapsulation.add(f.read(40))
                    f.close()
                    #del f, name, size
                    await encapsulation.end()
                elif doc[q:q+7] == b'remove=':
                    print("remove")
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
                        os.remove(name)
                        #del name
                    except :
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                    await encapsulation.start(b'text/plain', 0)  # total length in bytes
                    await encapsulation.add(b"")
                    await encapsulation.end()
                elif doc[q:q+6] == b'liste=':
                    print("liste")
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
                            size += len(bytes(i, "utf-8")) + 1
                    except :
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')

                    await encapsulation.start(b'text/plain', size)  # total length in bytes
                    for i in t:
                        await encapsulation.add(bytes(i + '\n', "utf-8"))
                    #del dir, t
                    await encapsulation.end()
                elif doc[q:q+2] == b'sensors_stop=':
                    print("sensors_stop")
                    pass
                elif doc[q:q+2] == b'configSensor=':
                    print("configSensor")
                    pass

            if codeBoot :
                print("codeBoot")
                await main_page(encapsulation)
        def registerGetSensor(doc, q):
            n = 999999
            if q < len(doc):
                if doc[q:q+7] == b'seqnum=':
                    q += 7
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = len(doc)
                if doc[q:q+2] == b'n=':
                    q += 2
                    n = 0
                    while q < len(doc):
                        byte = doc[q]
                        if byte >= 48 and byte <= 57:
                            n = n*10 + (byte - 48)
                            q += 1
                        else:
                            break
                    q = doc.find(b'&', q) + 1
                    if q == 0:
                        q = len(doc)
            return n

        print('handle_client_connection')

        ar = AsyncReader(rstream)

        if not await ar.expect(b'GET '):
            wstream.write(b'HTTP/1.1 405 Method Not Allowed\r\n')
        else:
            doc = await ar.read_group(0x20)  # group must be followed by a space
            if not (doc and await ar.expect(b'HTTP/1.1\r\n')):
                wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
            else:

                # important to avoid "connection reset" errors
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


                print(pathUrl, len(pathUrl))
                if pathUrl == "/favicon.ico":
                    print('favicon')
                    wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                elif pathUrl != '/' :
                    print("sensor")
                    pathUrl = pathUrl[1:]
                    if pathUrl[-4:] == '.csv':
                        pathUrl = pathUrl[:-4]
                        n = registerGetSensor(doc, q)
                        await measurements_as_csv(encapsulation, pathUrl, n)
                    else:
                        wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
                else:
                    print("other")
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
        self.wstream = wstream
        self.size = 0

    async def start(self, type, nbytes):
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: ')
        self.size += 31
        self.wstream.write(type)
        self.size += len(type)
        self.wstream.write(b'\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        self.size += 50
        t = bytes(str(nbytes), 'utf-8')
        self.wstream.write(t)
        self.size += len(t)
        #del t
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')
        self.size += 24
        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

    async def add(self, data):
        self.wstream.write(data)
        self.size += len(data)
        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

    async def end(self):
        self.size = 0
        await self.wstream.drain()
        pass

# convert sequence of bytes to PNG image

from struct import pack
from binascii import crc32

png_overhead = 69  # bytes added by PNG encapsulation

class PNGEncapsulation:

    def __init__(self, wstream):
        self.wstream = wstream
        self.crc = 0
        self.a = 0
        self.b = 0
        self.padding = 0
        self.size = 0

    async def start(self, type, nbytes):
        self.padding = 2 - nbytes % 3  # bytes ignored at end
        nbytes_div3 = (nbytes + 3) // 3
        nbytes = nbytes_div3 * 3
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: image/x-png\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        self.size += 92
        t = bytes(str(nbytes + png_overhead), 'utf-8')
        self.wstream.write(t)
        self.size += len(t)
        #del t
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')
        self.size += 24

        self.wstream.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A') # PNG signature
        self.size += 8

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

        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

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
        self.size += 4
        self.wstream.write(type)
        self.size += len(type)
        self.crc = crc32(type)
        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

    def chunk_add(self, data):
        self.crc = crc32(data, self.crc)
        self.wstream.write(data)
        self.size += len(data)
        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

    def chunk_end(self):
        self.wstream.write(pack('>I', self.crc))
        self.size += 4
        if self.size > 1400:
            self.size = 0
            await self.wstream.drain()

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

from shtc3 import SHTC3, temp_from_raw, humid_from_raw
from machine import ADC

shtc3_sensor = SHTC3()
adc1a = ADC(blinx.input_pin(blinx.port_pin_num(1,1)), atten=ADC.ATTN_11DB)
adc1b = ADC(blinx.input_pin(blinx.port_pin_num(1,2)), atten=ADC.ATTN_11DB)
adc2a = ADC(blinx.input_pin(blinx.port_pin_num(2,1)), atten=ADC.ATTN_11DB)
adc2b = ADC(blinx.input_pin(blinx.port_pin_num(2,2)), atten=ADC.ATTN_11DB)

def analog(adc):
    return (adc.read_u16() + adc.read_u16() + adc.read_u16() + adc.read_u16() + 2) >> 2

size = 300+1
measurement_time = get_time()
lo = 1
hi = 0

nsamples = 4
nsensors = 6

bytes_per_measurement = nsensors * 2
measurements = bytearray(size * bytes_per_measurement)

async def sensor_reader():
    global lo, hi, measurement_time
    while True:
        ms = 1000 - (time.ticks_ms() % 1000)
#        print('sleep_ms',ms)
        await uasyncio.sleep_ms(ms)
        measurement_time = get_time()
        t = 0
        h = 0
        an1a = 0
        an1b = 0
        an2a = 0
        an2b = 0
        for i in range(nsamples):
            m = shtc3_sensor.measurements
            t += m[0]
            h += m[1]
            an1a += analog(adc1a)
            an1b += analog(adc1b)
            an2a += analog(adc2a)
            an2b += analog(adc2b)
        t = t // nsamples
        h = h // nsamples
        an1a = an1a // nsamples
        an1b = an1b // nsamples
        an2a = an2a // nsamples
        an2b = an2b // nsamples

        hi += 1
        if hi == size: hi = 0
        j = hi * bytes_per_measurement
        measurements[j+ 0] = t    & 0xff; measurements[j+ 1] = t >> 8
        measurements[j+ 2] = h    & 0xff; measurements[j+ 3] = h >> 8
        measurements[j+ 4] = an1a & 0xff; measurements[j+ 5] = an1a >> 8
        measurements[j+ 6] = an1b & 0xff; measurements[j+ 7] = an1b >> 8
        measurements[j+ 8] = an2a & 0xff; measurements[j+ 9] = an2a >> 8
        measurements[j+10] = an2b & 0xff; measurements[j+11] = an2b >> 8
        if lo == hi:
            lo += 1
            if lo == size: lo = 0

        screen_write(3, "T=%5.1f  H=%5.1f" % (temp_from_raw(t)/100, humid_from_raw(h)/100))
        screen.show()

        #gc.collect()

csv_header = b'T:unix_timestamp,temp,humid,analog1a,analog1b,analog2a,analog2b\n'

async def measurements_as_csv(encapsulation, name, n):

    avail = hi - lo
    if avail < 0: avail += size
    n = min(n, avail)  # number of measurements

    print('measurements_as_csv', n)

    await encapsulation.start(b'text/plain', len(csv_header) + n * 43)  # total length in bytes

    await encapsulation.add(csv_header)

    i = n
    while i > 0:
        i -= 1
        j = hi - i
        if j < 0: j += size
        j *= bytes_per_measurement
        t    = measurements[j+ 0] + (measurements[j+ 1] << 8)
        t    = temp_from_raw(t)
        h    = measurements[j+ 2] + (measurements[j+ 3] << 8)
        h    = humid_from_raw(h)
        an1a = measurements[j+ 4] + (measurements[j+ 5] << 8)
        an1b = measurements[j+ 6] + (measurements[j+ 7] << 8)
        an2a = measurements[j+ 8] + (measurements[j+ 9] << 8)
        an2b = measurements[j+10] + (measurements[j+11] << 8)
        #gc.collect()
        row = bytes("%10d,%5.1f,%5.1f,%4.2f,%4.2f,%4.2f,%4.2f\n" % (measurement_time-i, t/100, h/100, volt_from_raw(an1a), volt_from_raw(an1b), volt_from_raw(an2a), volt_from_raw(an2b)), 'utf-8')
#        print(row)
        await encapsulation.add(row)

    await encapsulation.end()

def volt_from_raw(n):
    return (n+397)/23030

#------------------------------------------------------------------------------

def main():
    uasyncio.create_task(sensor_reader())
    uasyncio.create_task(web_server())
    uasyncio.get_event_loop().run_forever()

main()
