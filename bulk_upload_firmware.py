# bulk_upload_firmware.py

# This module is used to automatically install firmware when devices are
# connected to the computer's USB ports.

import sys, os, re, time
import esptool

# Detect newly connected serial ports of interest

serial_port_pattern = {
    'darwin': r'tty\.wchusbserial.*|tty\.usbserial.*|tty\.usbmodem.*',
    'linux': r'ttyUSB.*',
}

# Detect devices with know names

device_id_patterns = {
    'BLINX': ['BLX([0-9]*0)'],
    'TTGO': ['()'],  # catch all
}

# Id generation either by extracting the device id from serial port name or
# generating a fresh one.

id_counter = 0

def generate_id():  # generates '111', '112', '113', '114', '121', ...
    global id_counter
    i = id_counter
    id_counter += 1
    return str(i//16+1) + str(i//4%4+1) + str(i%4+1)

def device_id_from_port(port):
    for name in device_id_patterns:
        for pattern in device_id_patterns[name]:
            m = re.match('^.*('+pattern+')$', port)
            if m:
                g = m.groups()
                if len(g) == 2:
                    return name + (g[1] or generate_id())
    return None

# Detect newly connected serial ports of interest

def search_for_serial_ports():
    dir = '/dev'
    pattern = serial_port_pattern.get(sys.platform)
    ports = set()
    for name in os.listdir(dir):
        if re.fullmatch(pattern, name):
            ports.add(dir + '/' + name)
    return ports

def observe_serial_ports_for_changes(notify):
    connected = set()
    while True:
        ports = search_for_serial_ports()
        for port in connected - ports:
            notify(port, False)
        for port in ports - connected:
            notify(port, True)
        connected = ports
        time.sleep(0.1)

# Detect newly connected devices and upload appropriate firmware

def get_device(port):
    try:
        return esptool.cmds.detect_chip(port=port)
    except:
        return None

def get_chip(dev):
    try:
        return dev.get_chip_description().split(' ')[0]
    except:
        return None

def get_mac(dev):
    try:
        return ':'.join(map(lambda x: "%02x" % x, dev.read_mac()))
    except:
        return None

def detect_device_and_upload_firmware(port, device_id, firmware):
    dev = get_device(port)
    if dev:
        chip = get_chip(dev)
        if chip:
            mac = get_mac(dev)
            if mac:
                upload(port, device_id, dev, firmware, chip, mac)

def upload(port, device_id, dev, firmware, chip, mac):
    firmware_dir = 'firmware/' + firmware + '/' + chip
    common_dir = 'firmware/' + firmware + '/common'
    firmware_files = list(os.listdir(firmware_dir))
    bin_files = list(filter(lambda name: name.endswith('.bin'), firmware_files))
    if len(bin_files) == 0:
        print('*** ERROR: no .bin files in ' + firmware_dir)
    elif len(bin_files) >= 2:
        print('*** ERROR: 2 or more .bin files in ' + firmware_dir)
    else:
        bin_file = firmware_dir + '/' + bin_files[0]

        print('###############################################################################')
        print('################### ' + device_id)
        print('################### ' + mac)
        print('################### ' + chip)
        print('################### ' + bin_file)
        print('###############################################################################')

        baud = '460800'

        esptool_run(['--port', port, '--baud', baud, 'erase_flash'])
        esptool_run(['--port', port, '--baud', baud, 'write_flash', '-z', '0x0', bin_file])

        dev._port.close()  # release serial port so ampy can use it

        delay = '0.3'
        baud = '115200'

        def generate_config():
            filename = device_id + '.config'
            f = open(filename, 'w')
            f.write('device_id = ' + repr(device_id) + '\n')
            f.close()
            return filename

        def upload_dir(dir):

            def rmdir(remote_path):
                print('ampy rmdir', remote_path)
                ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'rmdir', remote_path])

            def mkdir(remote_path):
                print('ampy mkdir', remote_path)
                ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'mkdir', remote_path])

            def put(local_path, remote_path):
                print('ampy put', local_path, remote_path)
                ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'put', local_path, remote_path])

            if dir != '': dir = dir + '/'
            files = list(os.listdir(common_dir + '/' + dir))
            for file in files:
                local_path = common_dir + '/' + dir + file
                remote_path = dir + file
                if os.path.isdir(local_path):
                    rmdir(remote_path)
                    mkdir(remote_path)
                    upload_dir(remote_path)
                elif file.endswith('.py'):
                    config = file == 'config.py'
                    print(local_path, config)
                    if config: local_path = generate_config()
                    put(local_path, remote_path)
                    if config: local_path = generate_config()

        upload_dir('')

        #ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'ls'])
        #ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'reset'])
        print('------------ DONE with ' + port)

def esptool_run(args):
    command = 'esptool ' + ' '.join(args)
    print(command)
    esptool.main(args)

import subprocess

def ampy_run(args):
    command = 'ampy ' + ' '.join(args)
    print(command)
    os.system(command)

# Start uploading firmware automatically when devices are connected

def main(firmware):

    def serial_port_notification(port, connection):
        device_id = device_id_from_port(port)
        if connection:
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> connected: ' + port)
            detect_device_and_upload_firmware(port, device_id, firmware)
        else:
            print('                               disconnected: ' + port)

    observe_serial_ports_for_changes(serial_port_notification)

if __name__ == '__main__':
    firmware = 'micropython'
    if len(sys.argv) > 1:
        firmware = sys.argv[1]
    main(firmware)
