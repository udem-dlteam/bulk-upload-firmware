#!/usr/bin/env python3

# bulk_upload_firmware.py

# This module is used to automatically install firmware when devices are
# connected to the computer's USB ports.

import sys, os, re, time, argparse
import esptool

# Detect newly connected serial ports of interest

serial_port_pattern = {
    'darwin': r'tty\.wchusbserial.*|tty\.usbserial.*|tty\.usbmodem.*',
    'linux': r'ttyUSB.*|ttyACM.*',
}

# Detect devices with know names

device_id_patterns = [
    { 'name': 'BLINX', 'patterns': ['BLX([0-9]*0)'] },
    { 'name': '',      'patterns': ['()'] },  # catch all
]

# Id generation either by extracting the device id from serial port name or
# generating a fresh one.

id_counter = 0

def generate_id(template, start):
    global id_counter
    m = re.match('^([^#]*)(##*)([^#]*)$', template)
    if m:
        g = m.groups()
        if len(g) == 3:
            i = id_counter
            id_counter += 1
            return g[0] + str(i+start).zfill(len(g[1])) + g[2]
    return template

def device_id_from_port(port, template, start):
    for i in range(len(device_id_patterns)):
        name = device_id_patterns[i]['name']
        for pattern in device_id_patterns[i]['patterns']:
            m = re.match('^.*('+pattern+')$', port)
            if m:
                g = m.groups()
                if len(g) == 2:
                    if name == '':
                        return generate_id(template, start)
                    else:
                        return name + g[1]
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

def detect_device_and_upload_firmware(port, dir, firmware, device_id, template, start, config):
    dev = get_device(port)
    if dev:
        chip = get_chip(dev)
        if chip:
            mac = get_mac(dev)
            if mac:
                upload(port, dir, firmware, device_id, template, start, config, dev, chip, mac)

def upload(port, dir, firmware, device_id, template, start, config, dev, chip, mac):

    firmware_dir = dir + '/' + firmware + '/' + chip

    if not os.path.exists(firmware_dir) or os.path.isfile(firmware_dir):
        print('*** ERROR: no directory ' + firmware_dir)
        return

    firmware_files = list(os.listdir(firmware_dir))
    bin_files = list(filter(lambda name: name.endswith('.bin'), firmware_files))
    common_dir = dir + '/' + firmware + '/common'
    run_file = None  # file to run at end of upload

    if len(bin_files) == 0:
        print('*** ERROR: no .bin files in ' + firmware_dir)
    elif len(bin_files) >= 2:
        print('*** ERROR: 2 or more .bin files in ' + firmware_dir)
    else:
        single_device = device_id is not None
        if device_id is not None:
            device_id = device_id_from_port(port, template, start)
        bin_file = firmware_dir + '/' + bin_files[0]

        print('###############################################################################')
        print('###################################### ' + device_id)
        print('###################################### ' + mac)
        print('###################################### ' + chip)
        print('###################################### ' + bin_file)
        if config:
            print('###################################### ' + config)
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
            # TODO: Add other configuration variables
            f.write('id = ' + repr(device_id) + '\n')
            f.write('mac = ' + repr(mac) + '\n')
            f.write('chip = ' + repr(chip) + '\n')
            if config:
                f.write(config + '\n')
            f.close()
            return filename

        def upload_dir(dir):

            nonlocal run_file

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
                    if file == '_flashtest.py':
                        run_file = local_path
                    else:
                        is_config = file == '_config.py'
                        print(local_path, config)
                        if is_config: local_path = generate_config()
                        put(local_path, remote_path)

        upload_dir('')

        if run_file:
            ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'run', run_file])

        print('------------ DONE with ' + port)

        if single_device:
            sys.exit(0)  # quit after this device done

def esptool_run(args):
    command = 'esptool ' + ' '.join(args)
    print(command)
    esptool.main(args)

def ampy_run(args):
    command = 'ampy ' + ' '.join(args)
    print(command)
    os.system(command)

# Start uploading firmware automatically when devices are connected

import threading

def main(port, dir, firmware, device_id, template, start, config):

    def serial_port_notification(port, connection):

        def handle_notification():
            if connection:
                print('##################################### connected: ' + port)
                detect_device_and_upload_firmware(port, dir, firmware, device_id, template, start, config)
            else:
                print('##################################### disconnected: ' + port)

        if device_id is not None:
            handle_notification()  # don't do it concurrently
        else:
            t = threading.Thread(target=handle_notification)
            t.start()

    if port is None:
        observe_serial_ports_for_changes(serial_port_notification)
    else:
        detect_device_and_upload_firmware(port, dir, firmware, device_id, template, start, config)

def cli():

    parser = argparse.ArgumentParser(
                prog = 'bulk_upload_firmware',
                description = 'Upload firmware to Espressif based microcontroller boards as soon\nas they are connected to a USB port, with sequentially allocated\nunique device ids.')
    parser.add_argument('--port', default=None)
    parser.add_argument('--dir', default='firmware')
    parser.add_argument('--firmware', default='default')
    parser.add_argument('--id', default=None)
    parser.add_argument('--template', default='DEV#')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--config', default=None)
    args = parser.parse_args()

    main(args.port, args.dir, args.firmware, args.id, args.template, args.start, args.config)

if __name__ == '__main__':
    cli()
