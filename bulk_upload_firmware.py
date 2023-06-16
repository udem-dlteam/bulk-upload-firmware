#!/usr/bin/env python3

# bulk_upload_firmware.py

# This module is used to automatically install firmware when devices are
# connected to the computer's USB ports.

import sys, os, re, time, argparse, subprocess
import esptool

# Detect newly connected serial ports of interest

serial_port_pattern = {
    'darwin': r'tty\.wchusbserial.*|tty\.usbserial.*|tty\.usbmodem.*',
    'linux': r'ttyUSB.*|ttyACM.*|ttyS[0-9]',
}

# Detect devices with know names

device_id_patterns = [
    { 'name': 'BLINX', 'patterns': ['BLX([0-9][0-9]*)'] },
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
            else:
                p = subprocess.run(["udevadm", "info", "-a", "-n", port], check=True, capture_output=True)
                name = subprocess.run(['grep', '-Eo', 'BLINX[0-9][0-9][0-9]'], input=p.stdout, capture_output=True)
                return name.stdout.decode('ascii').split()[0]
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

def detect_device_and_upload_firmware(port, firmware_dir, device_id, start, ident):
    dev = get_device(port)
    if dev:
        chip = get_chip(dev)
        if chip:
            mac = get_mac(dev)
            if mac:
                upload(port, firmware_dir, device_id, start, ident, dev, chip, mac)

def upload(port, firmware_dir, device_id, start, ident, dev, chip, mac):

    chip_dir = firmware_dir + '/' + chip

    if not os.path.exists(chip_dir) or not os.path.isdir(chip_dir):
        print('*** ERROR: no directory ' + chip_dir)
        return

    firmware_files = list(os.listdir(chip_dir))
    bin_files = list(filter(lambda name: name.endswith('.bin'), firmware_files))
    common_dir = firmware_dir + '/common'
    run_file = None  # file to run at end of upload

    if len(bin_files) == 0:
        print('*** ERROR: no .bin files in ' + chip_dir)
    elif len(bin_files) >= 2:
        print('*** ERROR: 2 or more .bin files in ' + chip_dir)
    else:
        single_device = not ('#' in device_id)
        if not single_device:
            device_id = device_id_from_port(port, device_id, start)
        bin_file = chip_dir + '/' + bin_files[0]

        print('###############################################################################')
        print('###################################### ' + device_id)
        print('###################################### ' + mac)
        print('###################################### ' + chip)
        print('###################################### ' + bin_file)
        if ident:
            print('###################################### ' + ident)
        print('###############################################################################')

#        return

        baud = '460800'
        baud = '115200'  # play it safe (seems to cause problems on Windows running under Parallels desktop)

        esptool_run(['--port', port, '--baud', baud, 'erase_flash'])
        esptool_run(['--port', port, '--baud', baud, 'write_flash', '-z', '0x0', bin_file])

        dev._port.close()  # release serial port so ampy can use it

        delay = '0.3'
        baud = '115200'

        def generate_ident(file):
            filename = 'idents/' + device_id + '.' + file
            f = open(filename, 'w')
            # TODO: Add other configuration variables
            f.write('id = ' + repr(device_id) + '\n')
            f.write('mac = ' + repr(mac) + '\n')
            f.write('chip = ' + repr(chip) + '\n')
            if ident:
                f.write(ident.replace('\\n','\n') + '\n')
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
                elif file.endswith('.py') or file.endswith('.mpy'):
                    if file.endswith('_test.py'):
                        run_file = local_path
                    else:
                        is_ident = file.endswith('_ident.py')
                        print(local_path, ident)
                        if is_ident: local_path = generate_ident(file)
                        put(local_path, remote_path)

        upload_dir('')

        if run_file:
            ampy_run(['--port', port, '--baud', baud, '--delay', delay, 'run', '--no-output', run_file])

        print('##################################### done with ' + device_id)

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

def main(port, firmware_dir, device_id, start, ident, bulk):

    def serial_port_notification(port, connection):

        def handle_notification():
            if connection:
                print('##################################### connected: ' + port)
                detect_device_and_upload_firmware(port, firmware_dir, device_id, start, ident)
            else:
                print('##################################### disconnected: ' + port)

        if bulk:
            t = threading.Thread(target=handle_notification)
            t.start()
        else:
            handle_notification()  # don't do it concurrently

    if port is None:
        observe_serial_ports_for_changes(serial_port_notification)
    else:
        detect_device_and_upload_firmware(port, firmware_dir, device_id, start, ident)

def cli():

    parser = argparse.ArgumentParser(
                prog = 'bulk_upload_firmware',
                description = 'Upload firmware to Espressif based microcontroller boards allowing\nupload to be done for multiple devices as soon as they are connected to\na USB port, with sequentially allocated unique device ids (--bulk flag).')
    parser.add_argument('--port', default=None)
    parser.add_argument('--dir', default='firmware/default')
    parser.add_argument('--id', default='DEV#')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--ident', default='')
    parser.add_argument('--bulk', action='store_true')
    args = parser.parse_args()

    main(args.port, args.dir, args.id, args.start, args.ident, args.bulk)

if __name__ == '__main__':
    cli()
