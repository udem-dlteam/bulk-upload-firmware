default_ssid = 'BLINXNET'
default_pwd  = 'blinxnet'

import time
import _blinx_ident as ident
import _blinx_screen as screen

#------------------------------------------------------------------------------

# turn on peripherals and initialize i2c

import _blinx_blinx as blinx

blinx.periph_power(1)
blinx.i2c_init()

# initialize display and show instructions

time.sleep_ms(10)

screen.screen_init()

reboot_count = 0

def show_instructions():

    seconds = reboot_count // 100

    if seconds * 100 == reboot_count:
        remaining = 3 - seconds
        if remaining == 0:
            return True
        screen.screen_erase()
        screen.screen_write(0, 'HOLD ' + str(remaining) + ' SECONDS  ', 0, 0)
        screen.screen_write(1, 'MORE TO CHANGE  ', 0, 0)
        screen.screen_write(2, 'CONFIGURATION   ', 0, 0)
        screen.screen_write(3, '                ', 0, 0)
        screen.screen_show()

    return False

show_instructions()

###############################################################################
###############################################################################

import network

sta_if = network.WLAN(network.STA_IF)

sta_if.active(True)

def scan_wifi_networks():
    seen = {}
    wifi_networks = []
    for x in sorted(sta_if.scan(), key=lambda x: -x[3]): # sort using RSSI
        (ssid, bssid, channel, RSSI, security, hidden) = x
        if ssid not in seen and len(ssid) > 0 and not any(c < 32 for c in ssid):
            seen[ssid] = x
            wifi_networks.append(x)
    return wifi_networks

def signal_stength(RSSI):
    w = 5
    if RSSI >= -50:
        n = 0
    elif RSSI >= -60:
        n = 1
    elif RSSI >= -67:
        n = 2
    elif RSSI >= -74:
        n = 3
    elif RSSI >= -81:
        n = 4
    else:
        n = 5
    n = min(w, max(0, (-46 - RSSI) // 7))
    return '&#x25ae;' * (w-n) + '&#x25af;' * n

def wifi_selection_html(wifi_networks):
    html = ''
    selected = ' selected'
    for x in wifi_networks:
        (ssid, bssid, channel, RSSI, security, hidden) = x
        name = str(ssid, 'utf-8').replace('&', '&amp;')
        html += '<option value="' + name + '"'
        if name == default_ssid:
            html += selected
            selected = ''
        html += '>'
        html += signal_stength(RSSI) + '&nbsp;&nbsp;'
        html += name
        html += '</option>'
        html += '\n'
    html = '<select>\n<option value="" disabled hidden' + selected +\
           '>-- Select wifi to connect to --</option><option value="" disabled hidden>[number of full bars = signal strength]</option>\n' + html + '<option value="">Scan for nearby wifi networks again</option>\n</select>\n'
    return html

###############################################################################
###############################################################################

"""
Minimal captive portal, using uasyncio v3 (MicroPython 1.13+) with a fallback for earlier versions of uasyncio/MicroPython.

* License: MIT
* Repository: https://github.com/metachris/micropython-captiveportal
* Author: Chris Hager <chris@linuxuser.at> / https://twitter.com/metachris

Built upon:
- https://github.com/p-doyle/Micropython-DNSServer-Captive-Portal

References:
- http://docs.micropython.org/en/latest/library/uasyncio.html
- https://github.com/peterhinch/micropython-async/blob/master/v3/README.md
- https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md
- https://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5
"""
import gc
import sys
import network
import socket
import uasyncio as asyncio

# Helper to detect uasyncio v3
IS_UASYNCIO_V3 = hasattr(asyncio, "__version__") and asyncio.__version__ >= (3,)


# Access point settings
SERVER_SSID = ident.id  # max 32 characters
SERVER_IP = '10.0.0.1'
SERVER_SUBNET = '255.255.255.0'


def wifi_start_access_point():
    """ setup the access point """
    wifi = network.WLAN(network.AP_IF)
    wifi.active(True)
    wifi.ifconfig((SERVER_IP, SERVER_SUBNET, SERVER_IP, SERVER_IP))
    wifi.config(essid=SERVER_SSID, authmode=network.AUTH_OPEN)
    print('Network config:', wifi.ifconfig())


def _handle_exception(loop, context):
    """ uasyncio v3 only: global exception handler """
    print('Global exception handler')
    sys.print_exception(context["exception"])
    sys.exit()


class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]
        print("DNSQuery domain:" + self.domain)

    def response(self, ip):
        print("DNSQuery response: {} ==> {}".format(self.domain, ip))
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.')))  # 4bytes of IP
        # print(packet)
        return packet


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

class ConfigurationPortal:
    async def start(self):
        # Get the event loop
        loop = asyncio.get_event_loop()

        # Add global exception handler
        if IS_UASYNCIO_V3:
            loop.set_exception_handler(_handle_exception)

        # Start the wifi AP
        wifi_start_access_point()

        # Create the server and add task to event loop
        server = asyncio.start_server(self.handle_http_connection, "0.0.0.0", 80)
        loop.create_task(server)

        # Start the DNS server task
        loop.create_task(self.run_dns_server())

        # Start looping forever
        print('Looping forever...')
        loop.run_forever()

    async def handle_http_connection(self, rstream, wstream):
        gc.collect()

        ar = AsyncReader(rstream)

        first = await ar.read_byte()

        is_get  = first == 71 and await ar.expect(b'ET ')   # GET
        is_post = first == 80 and await ar.expect(b'OST ')  # POST

        if not (is_get or is_post):
            wstream.write(b'HTTP/1.1 405 Method Not Allowed\r\n')
        else:
            doc = await ar.read_group(0x20)  # group must be followed by a space
            protocol = await ar.read_group(0x0a)
            print(repr(doc))
            print(repr(protocol))
            if not doc:
                wstream.write(b'HTTP/1.1 400 Bad Request\r\n')
            else:

                # important to avoid 'connection reset' errors
                content_length = await ar.read_header_attribute(b'content-length:')
                ar.remaining_bytes = content_length
                content = await ar.read_to_eof()
                print('doc =', doc, is_get, is_post)
                print('content =', content)
                print('peername =', wstream.get_extra_info('peername'))

                if doc == b'/config':
                    response = 'HTTP/1.1 200 OK\r\n\r\nCONFIG!\r\n'
                    print('CONFIG!')
                else:
                    response = 'HTTP/1.1 200 OK\r\n\r\n' + portal_html()
                await wstream.awrite(response)

        await asyncio.sleep_ms(500)  # allow time for transmission

        # Close the socket
        await wstream.aclose()
        # print("client socket closed")

    async def run_dns_server(self):
        """ function to handle incoming dns requests """
        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)
        udps.bind(('0.0.0.0', 53))

        while True:
            try:
                # gc.collect()
                if IS_UASYNCIO_V3:
                    yield asyncio.core._io_queue.queue_read(udps)
                else:
                    yield asyncio.IORead(udps)
                data, addr = udps.recvfrom(4096)
                print("Incoming DNS request...")

                DNS = DNSQuery(data)
                udps.sendto(DNS.response(SERVER_IP), addr)

                print("Replying: {:s} -> {:s}".format(DNS.domain, SERVER_IP))

            except Exception as e:
                print("DNS server error:", e)
                await asyncio.sleep_ms(3000)

        udps.close()

def portal_html():
    return """
<!doctype html>
<html lang="en">
<head>
  <title>""" + ident.id + """ configuration</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta charset="utf8">
  <style>

    html {
      font-family: sans-serif;
      font-size: calc(15px + 0.390625vw);
    }

    body {
      --cb-header-height: 100px;
      --cb-header-color: #016bb6;
      margin: 0;
      padding-top: calc(0.8 * var(--cb-header-height));
      font-size: 125%;
    }

    code {
      font-size: 80%;
    }

    header {
      height: var(--cb-header-height);
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      background-color: var(--cb-header-color);
      color: white;
      text-align: center;
      font-size: 28px;
      transition: box-shadow 0.3s;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    header.shadow {
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    }

    .content {
      padding: 20px;
      margin-bottom: var(--cb-header-height);
    }

p,
input,
select,
option,
button {
    margin: 1vh;
    padding: 1vh;
}

input,
select,
option,
button {
    -webkit-appearance: none;
    border-radius: 1vh;
    border-color: transparent;
}

input,
select,
option {
    background-color: #bce0e9;
}

  </style>
  <script>

    function loaded() {

        window.addEventListener('scroll', function() {
            var header = document.querySelector('header');
            var scrollPosition = window.scrollY || window.pageYOffset;
            var pageHeight = document.documentElement.scrollHeight - window.innerHeight;
            if (scrollPosition > 0) {
                header.classList.add('shadow');
            } else {
                header.classList.remove('shadow');
            }
        });

    }

    document.addEventListener('DOMContentLoaded', loaded);

  </script>
</head>
<body>
  <header>
    <b>""" + ident.id + """ configuration</b>
  </header>
  <div class="content">
    <center>Wifi network """ + ident.id + """ will connect to:</center>
    <form action="/config" action="#" method="POST" target="_blank">
      <center>""" + wifi_selection_html(scan_wifi_networks()) + """</center>
      <br>
      <center>Password:</center>
      <center><input type="text" name="pwd"></center>
      <br><br>
      <center><input type="submit" value="Apply"></center>
    </form>
  </div>
</body>
</html>
"""

###############################################################################
###############################################################################

def pad_text(text, width=16):
    text = text[:width]
    return text + ' '*(width-len(text))

def start_configuration_portal():

    screen.screen_erase()
    screen.screen_write(0, '  CONFIGURING   ', 0, 1)
    screen.screen_write(1, 'connect phone or', 0, 0)
    screen.screen_write(2, 'computer to the ', 0, 0)
    screen.screen_write(3, pad_text('wifi:' + ident.id), 0, 0)
    screen.screen_show()

    # Main code entrypoint
    try:
        # Instantiate app and run
        app = ConfigurationPortal()

        if IS_UASYNCIO_V3:
            asyncio.run(app.start())
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(myapp.start())

    except KeyboardInterrupt:
        print('Bye')

    finally:
        if IS_UASYNCIO_V3:
            asyncio.new_event_loop()  # Clear retained state

###############################################################################
###############################################################################

while blinx.button(blinx.LEFT) or blinx.button(blinx.RIGHT):

    if show_instructions():
        start_configuration_portal()
        break

    reboot_count += 1

    time.sleep_ms(10)

else:

    screen.screen_erase()
    screen.screen_show()

    try:
        import main
    except Exception:
        pass

###############################################################################
###############################################################################
