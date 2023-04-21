import blinx

#------------------------------------------------------------------------------

# turn on peripherals

blinx.periph_power(True)

#------------------------------------------------------------------------------

# time

import time

def get_time():
    return time.time()

#------------------------------------------------------------------------------

# screen output

import ssd1306

def screen_init():
    global screen
    screen = ssd1306.SSD1306_I2C(128, 32, blinx.i2c)

def screen_write(line, text):
    screen.fill_rect(0, line*8, 128, 8, 0)
    screen.text(text, 0, line*8, 1)

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
        print(elapsed)
        blinx.led_pin.value(elapsed & 1)
        if wl.isconnected(): break
        await uasyncio.sleep_ms(250)
        elapsed += 1
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

class RequestReader:

    def __init__(self, rstream):
        self.rstream = rstream
        self.buf = bytearray(10)
        self.lo = 0
        self.hi = 0

    async def read_byte(self):
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
                return -1  # EOF
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
            result += bytes([byte])
        if byte == ender:
            return result
        else:
            return b''

    async def read_to_end(self):
        state = 0
        while state < 4:
            byte = await self.read_byte()
            if byte == (10 if state & 1 else 13):
                state += 1
            elif byte >= 0:
                state = 0
            else:
                break  # EOF

async def web_server():

    async def handle_client_connection(rstream, wstream):

        print('handle_client_connection')

        rr = RequestReader(rstream)

        if not await rr.expect(b'GET '):
            wstream.write(b'HTTP/1.1 405 Method Not Allowed\r\n')
        else:
            doc = await rr.read_group(0x20)  # group must be followed by a space
            if not (doc and await rr.expect(b'HTTP/1.1\r\n')):
                wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
            else:

                await rr.read_to_end()  # important to avoid "connection reset" errors

                q = doc.find(b'?')  # find first '?' if any
                if q < 0:
                    q = len(doc)

                print('doc =', str(doc[:q], 'utf-8'))

                q += 1
                if q < len(doc) and doc[q] == 0x3f: # two '?' in a row?
                    encapsulation = PNGEncapsulation(wstream)
                    q += 1
                else:
                    encapsulation = NoEncapsulation(wstream)

                if q < len(doc):
                    print('query =', str(doc[q:], 'utf-8'))

                await measurements_as_csv(encapsulation)

        await wstream.drain()
        await wstream.wait_closed()

#        print(gc.mem_free())

    wlan_start_connect()
    await wlan_connected.wait()
    if wlan:
        await uasyncio.sleep_ms(5000)
        ntptime.settime()  # get time from NTP server
        gc.collect()
        uasyncio.create_task(uasyncio.start_server(handle_client_connection, '0.0.0.0', 80))

class NoEncapsulation:

    def __init__(self, wstream):
        self.wstream = wstream

    async def start(self, nbytes):
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        self.wstream.write(bytes(str(nbytes), 'utf-8'))
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')
        await self.wstream.drain()

    async def add(self, data):
        self.wstream.write(data)
        await self.wstream.drain()

    async def end(self):
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

    async def start(self, nbytes):
        self.padding = 2 - nbytes % 3  # bytes ignored at end
        nbytes_div3 = (nbytes + 3) // 3
        nbytes = nbytes_div3 * 3
        self.wstream.write(b'HTTP/1.1 200 OK\r\nContent-Type: image/x-png\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: ')
        self.wstream.write(bytes(str(nbytes + png_overhead), 'utf-8'))
        self.wstream.write(b'\r\nConnection: Closed\r\n\r\n')

        self.wstream.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A') # PNG signature

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

        await self.wstream.drain()

    async def add(self, data):
        self.adler_add(data)

    async def end(self):
        self.adler_add(b'\xFF'*self.padding)  # add padding at end
        self.adler_end()
        self.chunk_end()

        self.chunk_start(b'IEND', 0)  # IEND chunk
        self.chunk_end()

    def chunk_start(self, type, length):
        self.wstream.write(pack('>I', length))
        self.wstream.write(type)
        self.crc = crc32(type)

    def chunk_add(self, data):
        self.crc = crc32(data, self.crc)
        self.wstream.write(data)

    def chunk_end(self):
        self.wstream.write(pack('>I', self.crc))

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
adc11 = ADC(blinx.input_pin(blinx.conn_pin_num(1,1)), atten=ADC.ATTN_11DB)
adc12 = ADC(blinx.input_pin(blinx.conn_pin_num(1,2)), atten=ADC.ATTN_11DB)
adc31 = ADC(blinx.input_pin(blinx.conn_pin_num(3,1)), atten=ADC.ATTN_11DB)
adc32 = ADC(blinx.input_pin(blinx.conn_pin_num(3,2)), atten=ADC.ATTN_11DB)

def analog(adc):
    return (adc.read_u16() + adc.read_u16() + adc.read_u16() + adc.read_u16() + 2) >> 2

size = 300+1
measurement_time = get_time()
lo = 0
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
        an11 = 0
        an12 = 0
        an31 = 0
        an32 = 0
        for i in range(nsamples):
            m = shtc3_sensor.measurements
            t += m[0]
            h += m[1]
            an11 += analog(adc11)
            an12 += analog(adc12)
            an31 += analog(adc31)
            an32 += analog(adc32)
        t = t // nsamples
        h = h // nsamples
        an11 = an11 // nsamples
        an12 = an12 // nsamples
        an31 = an31 // nsamples
        an32 = an32 // nsamples

        hi += 1
        if hi == size: hi = 0
        j = hi * bytes_per_measurement
        measurements[j+ 0] = t    & 0xff; measurements[j+ 1] = t >> 8
        measurements[j+ 2] = h    & 0xff; measurements[j+ 3] = h >> 8
        measurements[j+ 4] = an11 & 0xff; measurements[j+ 5] = an11 >> 8
        measurements[j+ 6] = an12 & 0xff; measurements[j+ 7] = an12 >> 8
        measurements[j+ 8] = an31 & 0xff; measurements[j+ 9] = an31 >> 8
        measurements[j+10] = an32 & 0xff; measurements[j+11] = an32 >> 8
        if lo == hi:
            lo += 1
            if lo == size: lo = 0

        screen_write(3, "T=%5.1f  H=%5.1f" % (temp_from_raw(t)/100, humid_from_raw(h)/100))
        screen.show()

        gc.collect()

csv_header = b'T:unix_timestamp,temp,humid,analog11,analog12,analog31,analog32\n'

async def measurements_as_csv(encapsulation):

    n = hi - lo  # number of measurements
    if hi < lo: n += size

    await encapsulation.start(len(csv_header) + n * 42)  # total length in bytes

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
        an11 = measurements[j+ 4] + (measurements[j+ 5] << 8)
        an12 = measurements[j+ 6] + (measurements[j+ 7] << 8)
        an31 = measurements[j+ 8] + (measurements[j+ 9] << 8)
        an32 = measurements[j+10] + (measurements[j+11] << 8)
        gc.collect()
        await encapsulation.add(bytes("%9d,%5.1f,%5.1f,%4.2f,%4.2f,%4.2f,%4.2f\n" % (measurement_time-i, t/100, h/100, an11/65535*3.3, an12/65535*3.3, an31/65535*3.3, an32/65535*3.3), 'utf-8'))

    await encapsulation.end()

#------------------------------------------------------------------------------

def main():
    uasyncio.create_task(sensor_reader())
    uasyncio.create_task(web_server())
    uasyncio.get_event_loop().run_forever()

main()
