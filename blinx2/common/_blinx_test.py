import _blinx_blinx as blinx
import _blinx_ssd1306 as ssd1306
import _blinx_config as _config
import _blinx_wifi as _wifi
import uasyncio, os, network, sys, time, machine

error = False

def log_error(text):
    global error
    error = True
    f = open('_blinx_error.txt','a')
    f.write(text+'\n')
    f.close()

try :
    blinx.periph_power(1)
except Exception as e:
    log_error('change periph power : ' + repr(e))
    exit()

i2c_error = False
try :
    blinx.i2c_init()
except Exception as e:
    log_error('i2c init : ' + repr(e))
    i2c_error = True
    #exit()


# -------------------------------------------------------------------------------
# test the file system
# -------------------------------------------------------------------------------
list_error = False
try :
    l = os.listdir()
except Exception as e:
    log_error('verify list file : ' + repr(e))
    list_error = True
    #exit()

if False and not list_error:
    for i in ['_blinx_config.py', '_blinx_wifi.py', '_blinx_blinx.mpy', 'boot.py', '_blinx_font8x12.mpy', '_blinx_program.mpy', '_blinx_shtc3.mpy', '_blinx_ssd1306.mpy', '_blinx_analog.mpy', '_blinx_ds1820.mpy', '_blinx_output_sensor.mpy']:
        if i not in l:
            log_error(i + ' not in fs')
            #exit()

# -------------------------------------------------------------------------------
# test the screen
# -------------------------------------------------------------------------------
screen_error = True
screen = None
if not i2c_error:
    screen_error = False
    try :
        screen = ssd1306.SSD1306_I2C(128, 32, blinx.i2c)
    except Exception as e:
        log_error('init screen : ' + repr(e))
        screen_error = True
        #exit()

    if not screen_error:
        try :
            screen.fill_rect(0, 0, 128, 32, 0)
            screen.show()
            time.sleep(1)
            screen.fill_rect(0, 0, 128, 32, 1)
            screen.show()
            time.sleep(1)
            screen.fill_rect(0, 0, 128, 32, 0)
            screen.show()
            time.sleep(0.5)
        except Exception as e:
            log_error('screen : ' + repr(e))
            screen_error = True
            #exit()

        try :
            for i in range(4):
                screen.text('1234567890123456',0,i*8,1)
                screen.show()
                time.sleep(0.1)
#            screen.fill_rect(0, 0, 128, 32, 0)
#            screen.show()
        except Exception as e:
            log_error('screen : ' + repr(e))
            screen_error = True
            #exit()


# -------------------------------------------------------------------------------
# test the led
# -------------------------------------------------------------------------------
try:
    p = machine.Pin(8, machine.Pin.OUT)
    for i in range(10):
        p.value(0)
        time.sleep(0.1)
        p.value(1)
        time.sleep(0.1)
except Exception as e:
    log_error('led test : ' + repr(e))

# -------------------------------------------------------------------------------
# test the buzzer
# -------------------------------------------------------------------------------
try:
    p = machine.Pin(8, machine.Pin.OUT)
    a = machine.PWM(p)
    for i in [512]:
        a.duty(i)
        for y in [1000,2000,3000,4000,1000,2000,3000,4000,1000,2000,3000,4000]:
            a.freq(y)
            time.sleep(0.2)
    a.duty(1023)
except Exception as e:
    log_error('led buzzer : ' + repr(e))

# -------------------------------------------------------------------------------
# test the sht3c sensor : temp + humid
# -------------------------------------------------------------------------------
shtc3_error = False
try:
    import _blinx_shtc3 as shtc3
except Exception as e:
    log_error('import _blinx_shtc3 : ' + repr(e))
    shtc3_error = True

if not shtc3_error:
    temp = None
    humid = None
    read_sht3c_error = False
    try:
        t1 = shtc3.info['shtc3-temp']['function']()
        t2 = shtc3.info['shtc3-humid']['function']()
    except Exception as e:
        log_error('read shtc3 : ' + repr(e))
        read_sht3c_error = True
    
    if not read_sht3c_error:
        try:
            temp = shtc3.info['shtc3-temp']['function_csv'](t1,0)
            humid = shtc3.info['shtc3-humid']['function_csv'](t2,0)
        except Exception as e:
            log_error('change value shtc3 : ' + repr(e))
        
        if 10 > float(temp) or float(temp) > 30:
            log_error('temp not good value' + temp)

        if not screen_error :
            screen.text('t:'+temp,0,i*8,1)
            screen.text('h:'+humid,0,i*8,1)
            screen.show()
            time.sleep(1)

# -------------------------------------------------------------------------------
# test the network, with the connection on a ntp server. Code the `program.py`
# -------------------------------------------------------------------------------
unixtime_servers = (
    ('blinx.codeboot.org', 80, b'/cgi-bin/unixtime.cmd'),
    ('worldtimeapi.org', 80, b'/api/timezone/Etc/UTC.txt'),
    )

async def test_connection():
    await wlan_start_connect()
    if wlan:
#        sync_ntptime()
        #gc.collect()
        await settime_from_unixtime_servers()
        return 


async def settime_from_unixtime_servers():
    i = 0
    while True:
        unixtime_server = unixtime_servers[i]
        i = (i+1) % len(unixtime_servers)
        host = unixtime_server[0]
        port = unixtime_server[1]
        path = unixtime_server[2]
        print('trying to connect to ' + host)
        rstream = None
        try:
            rstream, wstream = await uasyncio.create_task(uasyncio.open_connection(host, port))
        except Exception as e:
            log_error('e = ' + str(i) + ' : ' + repr(e))
        if rstream is None:
            log_error('could not connect to ' + host)
            print('could not connect to ' + host)
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

                if not error:
                    try:
                        os.remove('_blinx_test.py')
                    except Exception as e:
                        pass
                    try:
                        os.remove('_blinx_test.mpy')
                    except Exception as e:
                        pass
                    import machine
                    machine.reset()

                return

            await uasyncio.sleep_ms(4000)


def settime(t):
    import machine, utime
    tm = utime.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


wlan_connected = uasyncio.ThreadSafeFlag()  # flag indicating wlan connection

wlan = None

async def wlan_start_connect():
    print('wlan_start_connect')
    global wlan
    wlan_connected.clear()
    wlan = None
    wl = network.WLAN(network.STA_IF)
    wl.active(True)
    wl.connect(_wifi.ssid, _wifi.pwd)
    await wlan_connect_loop(wl)
    return

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
    return


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


uasyncio.create_task(test_connection())
uasyncio.get_event_loop().run_forever()
