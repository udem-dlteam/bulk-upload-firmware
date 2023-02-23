try:
  import utime as time
except:
  import time

# from https://github.com/schumixmd/TTGO-ST7789-MicroPython

# librairy from micropython :
try:
  import uos as os
except:
  import os
try:
  import uasyncio as asyncio
except:
  import asyncio

import sys, json, io
import network, binascii
from machine import Pin, I2C, SoftI2C, ADC, PWM, UART, SPI

# librairy form the ota updater
# from ota_updater import OTAUpdater
# librairy for the web server/rpc wifi
# import webServer
# librairy for bluetooth
import ble_uart_peripheral

##### librairy for the screen
####import st7789

####BL_Pin = 4     #backlight pin
####SCLK_Pin = 18  #clock pin
####MOSI_Pin = 19  #mosi pin
####MISO_Pin = 2   #miso pin
####RESET_Pin = 23 #reset pin
####DC_Pin = 16    #data/command pin
####CS_Pin = 5     #chip select pin

##### connection to spi and create the display
####BLK = Pin(BL_Pin, Pin.OUT)
####spi = SPI(2, baudrate=20000000, sck=Pin(18), mosi=Pin(19), miso=None)
####display = st7789.ST7789(spi,
####        135,
####        240,
####        reset=Pin(23, Pin.OUT),
####        cs=Pin(5, Pin.OUT),
####        dc=Pin(16, Pin.OUT),
####        backlight=Pin(4, Pin.OUT),
####        rotation=0,
####        options=0,
####        buffer_size= 0)
####BLK.value(1)

# the loop async
loop = None

# function register
__register = {}

# the connection wifi
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)
wlan_ap = network.WLAN(network.AP_IF)
wlan_ap.active(False)

# the ota updater
# otaUpdater = OTAUpdater('https://github.com/MaelC001/micropython', github_src_dir = 'src', main_dir = 'main', secrets_file = '__config.json')

# connection with the UART
#baud_rate = 76800
#uart = UART(0, baudrate=baud_rate, tx=10, rx=9)  # UART(0, baud_rate)
#uart.init(baudrate = baud_rate)#, rxbuf = 200)

if 'app' not in os.listdir():
    os.mkdir('app')
sys.path.append('/app')

# class for capture the stdout when `exec`
class DUP(io.IOBase):
  def __init__(self):
    self.s = bytearray()
  def write(self, data):
    self.s += data
    return len(data)
  def readinto(self, data):
    return 0
  def read_all(self):
    return str(self.s)

# the register for the user function
def register(name, sub_function = False):
  def wrapper(fn):
    def inner_wrapper(*args, id, **kwargs):
      output = ""
      # execute the function and capture the error
      try:
        # the output of the function
        output = fn(*args, **kwargs)
        # if the function use a user function, then we have to check the other function as well
        if sub_function and type(output) == dict:
          if 'error' in output:
            return {'error' : output['error'], 'id': id}
          elif 'result' in output:
            return {'result' : output['result'], 'id': id}
        return {'result' : output, 'id': id}
      except Exception as e:
        # the error of the function
        return {'error' : {"code": -32000, "message": str(e)}, 'id': id}

    __register[name] = inner_wrapper
    return inner_wrapper
  return wrapper

def sender(text):
  """send message to serial port in json"""
  if isinstance(text, dict) or isinstance(text, list):
    #sys.stdout.write(json.dumps(text))
    sys.stdout.write(json.dumps(text))
    sys.stdout.write('\n')
    return
  sys.stdout.write(text)
  sys.stdout.write('\n')

def senderDonneeSensor(donne):
  """send message to serial port in json"""
  if isinstance(donne, dict) or isinstance(donne, list):
    sys.stdout.write(json.dumps(donne))
    return
  sys.stdout.write(donne)

async def receiver():
  """
    receive information by the serial port in json
    and execute the function with the given argument
  """
  sreader = asyncio.StreamReader(sys.stdin)
  while True:
    # wait for the input
    data = await sreader.readline()
    # read the input
    decode_input(data, send = True, debug = True)

def decode_input(input, send = True, how_send = sender, printMessage = False, debug = False):
  """we will read the input and try to decode it, then we will try to execute it.

  Args:
      input (bytes): the input of the user
      send (bool, optional): do we send the info on the serial port?. Defaults to True.
      debug (bool, optional): do we send info by print?. Defaults to False.
  """
  print(input)
  try:
    # try to transform bytes to str
    line = input.decode('utf-8').rstrip()
    if debug:
      #print(0, line)
      pass
    # try to parse the json
    j = json.loads(line)
    if debug:
      #print(1, j)
      pass
  except Exception as e:
    # if an error appear, we send the error message and we stop the function
    #error = str(e)
    j = {
      'error' : {"code": -32700, "message": "Parse error"},
      'id' : None,
    }
    if debug:
      #print(2, j, str(e), line)
      pass
    elif printMessage:
      #print(j)
      pass
    if send:
      how_send(j)
    return

  read_input(j, send, how_send, printMessage, debug)

def read_input(j, send = True, how_send = sender, printMessage = False, debug = False):
  """we will read the input and try to decode it, then we will try to execute it.

  Args:
      input (bytes): the input of the user
      send (bool, optional): do we send the info on the serial port?. Defaults to True.
      debug (bool, optional): do we send info by print?. Defaults to False.
  """
  # try to read the parameter of the json
  # then the parameter of the method
  # to execute the method with the parameter
  try:
    id = j['id']
    cmd = j['method']
    args = j['params']

    # is the id correct ? and the command ?
    test_id_1 = isinstance(id, str)
    test_id_2 = isinstance(id, int)
    test_id_3 = id is None
    test_cmd = isinstance(cmd, str)
    if not(test_id_1 or test_id_2 or test_id_3) or not(test_cmd):
      j = {
        'error' : {"code": -32600, "message": "Invalid Request"},
        'id' : None,
      }
      if debug:
        #print(3, j, test_id_1, test_id_2, test_id_3, test_cmd)
        pass
      elif printMessage:
        #print(j)
        pass
      if send:
        how_send(j)
      return

    # method exist ?
    if cmd in __register:
      # type of the parameter
      if isinstance(args, list):
        reply = __register[cmd](*args, id = id)
        if debug:
          #print(4, reply)
          pass
        elif printMessage:
          #print(reply)
          pass
        if send:
          # if we don't want to get the data form the sensor then we send the reply normally
          # else we will send the data piece by piece in the function, so we have nothing to send
          # except if the request come from the rpc wifi, then we have to send it all the reply at once
          how_send(reply)
      elif isinstance(args, dict):
        reply = __register[cmd](id = id, **args)
        if debug:
          #print(5, reply)
          pass
        elif printMessage:
          #print(reply)
          pass
        if send:
          # if we don't want to get the data form the sensor then we send the reply normally
          # else we will send the data piece by piece in the function, so we have nothing to send
          # except if the request come from the rpc wifi, then we have to send it all the reply at once
          how_send(reply)
      else :
        # if the args is not a list or a dict we have a error
        j = {
          'error' : {"code": -32602, "message": "Invalid params"},
          'id' : id,
        }
        if debug:
          #print(6, j, type(args))
          pass
        elif printMessage:
          #print(j)
          pass
        if send:
          how_send(j)
    else :
      # if the command don't exist we have a error :
      j = {
        'error' : {"code": -32601, "message": "Method not found"},
        'id' : id,
      }
      if debug:
        #print(7, j, cmd, __register.keys)
        pass
      elif printMessage:
        #print(j)
        pass
      if send:
        how_send(j)
  except Exception as e:
    # if an error appear, we send the error message
    #error = str(e)
    #if id:
    #  error_id = id
    #else:
    j = {
      'error' : {"code": -32600, "message": "Invalid Request"},
      'id' : None,
    }
    if debug:
      #print(8, j, str(e))
      pass
    elif printMessage:
      #print(j)
      pass
    if send:
      how_send(j)


@register('write', False)
def write_file(name, text, format = 'w', do_verification = True):
  """
  write in a file
  arg :
    - name : str
    - text : str
    - format : str (optional)
  """
  if do_verification:
    verification(name, str)
    verification(text, str)
    verification(format, str, ['w', 'w+', 'a', 'a+'])
  f = open(name, format)
  f.write(text)
  f.close()
  return ''

@register('read', False)
def read_file(name):
  """
  read a file
  arg :
    - name : str
  """
  verification(name, str, os.listdir(), True)
  f = open(name, 'r')
  r = f.read()
  f.close()
  return r

@register('create', False)
def create_file(name):
  """
  create a file
  arg :
    - name : str
  """
  verification(name, str, os.listdir(), False)
  f = open(name, 'x')
  f.close()
  return ''

@register('remove', False)
def remove_file(name):
  """
  remove a file
  arg :
    - name : str
  """
  verification(name, str, os.listdir(), True)
  os.remove(name)
  return ''

@register('liste', False)
def list_file():
  """
  do the list of the file
  arg : none
  """
  return os.listdir()

@register('wifi', False)
def wifi():
  """
    we return all the wifi information
  """
  return {
    'wlan_sta' : {
      'active' : wlan_sta.active(), 
      'isconnected' : wlan_sta.isconnected(), 
#      'scan' : wlan_sta.scan() if wlan_sta.active() else [], # all the wifi the microcontroller scan
      'config' : {
        "ifcongif" : wlan_sta.ifconfig(), # the ip, netmask ...
        "mac" : wlan_sta.config('mac'), # the mac address
        "ssid" : wlan_sta.config('essid'), # the ssid of the wifi connected
        "dhcp_hostname" : wlan_sta.config('dhcp_hostname'), # the hostname of the microcontroller (for the mdns)
      }, 
    }, 
    'wlan_ap' : {
      'active' : wlan_ap.active(), 
      'isconnected' : wlan_ap.isconnected(), 
      'config' : {
        "ifcongif" : wlan_ap.ifconfig(), 
        "mac" : wlan_ap.config('mac'), 
        "ssid" : wlan_ap.config('essid'), 
        "channel" : wlan_ap.config('channel'), 
        "hidden" : wlan_ap.config('hidden'), 
        "authmode" : wlan_ap.config('authmode'), 
      }, 
    }, 
  }

@register('wifi_active', False)
def wifi_active(active = True):
  """active the wifi

  Args:
      active (bool, optional): actived the wifi or desactived. Defaults to True.
  """
  wlan_sta.active(active)
  if not active:
    wlan_sta.disconnect()
  return ''

@register('wifi_connect', False)
def wifi_connect(ssid = '', password = ''):
  """connect the microcontroller to wifi

  Args:
      ssid (str, optional): the ssid to connect. Defaults to ''.
      password (str, optional): the password of the ssid. Defaults to ''.
  """
  # try to connect to wifi
  wlan_sta.connect(ssid, password)

  # get the status, to know if a error appear
  status = wlan_sta.status()
  if status == network.STAT_NO_AP_FOUND:
    return "no AP found"
  elif status == network.STAT_WRONG_PASSWORD:
    return "wrong password"
  elif status == network.STAT_CONNECT_FAIL:
    return "connection fail"

  time.sleep(0.1)
  return wlan_sta.isconnected()

@register('wifi_server', False)
def wifi_server(ssid = '', password = '', auth = 3, active = True):
  """create a wifi server

  Args:
      ssid (str, optional): the name of the wifi server. Defaults to ''.
      password (str, optional): the password of the wifi server. Defaults to ''.
      auth (int, optional): the mode of authentication of the wifi server. Defaults to 3.
      active (bool, optional): actived the wifi server?. Defaults to True.
  """
  wlan_ap.active(False)
  if active:
    wlan_ap.config(essid = ssid, password = password, authmode = auth)
    wlan_ap.active(True)
  return ''

@register('display', False)
def display_sensors(func_name, array_value): #*array_value):
  """
    give a command to a display sensor

  Args:
      sensor_name (str): the name of the display sensor
      func_name (str): the function we want to use for the command
  """
  if isinstance(args, list):
    display.register[func_name](*array_value)
  elif isinstance(args, dict):
    display.register[func_name](**array_value)
  else :
      raise ValueError('not the good type of value')
  return ''

@register('removeCode', False)
def remove_code(): #*array_value):
    for i in os.listdir('app'):
        os.remove('app/'+i)
    return 'Done'


@register('updateCode', False)
def change_code(string, name): #*array_value):
    f = open('app/'+name, 'w')
    f.write(string)
    f.close()
    return 'Done'

@register('runCode', False)
def runCode(): #*array_value):
    import mainCode

def verification(value, type_value, possible = [], in_possible = True):
  """
  verify the value the user give us is correct
  """
  if not isinstance(value, type_value):
    message = f"the type of {value} isn't {type_value}"
    raise TypeError(message)
  if possible != [] and not ( (value not in possible) ^ in_possible ):
    message = f"{value} don't have a correct value"
    raise TypeError(message)

def launch(site = False, blue=False):
    if 'config.py' not in os.listdir():
    	return
####    p1 = Pin(0, Pin.IN)
####    p2 = Pin(35, Pin.IN)
####    p1V = p1.value()
####    p2V = p2.value()
####    if p1V == 0 and p2V == 0:
####        launchCode()
####    elif p1V == 0:
####        launchCode()
####    elif p2V == 0:
####        launchCode()
####    else:
####        launchBlinx(site, blue)
    launchBlinx(site, blue)

def launchBlinx(site = False, blue=False):
  import config
  if site:
      pass
  #  webServer.websocket_helper.decode_input = decode_input
  #  webServer.start()
  if blue:
    ble_uart_peripheral.decode_input = decode_input
    ble_uart_peripheral.createBle(name = config.bleName)
  #os.dupterm(uart, 0)
  #os.dupterm(None, 0)
  loop = asyncio.get_event_loop()
  loop.create_task(receiver())
  loop.run_forever()

def launchCode():
    import mainTTGO


"""
for the debugging, we will simulate the serial port
"""
# data = b'{"method":"liste","params":[],"id":0}'
# read_input(data, send = False, debug = True)







# https://github.com/rdehuyss/micropython-ota-updater
#@register('updateFirmware', False)
#def ota_update():
#  """
#    update the firmware of the microcontroller
#  """
#  otaUpdater.install_update_if_available()


