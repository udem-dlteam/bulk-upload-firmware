This repository contains a script to upload firmware to devices based
on Espressif ESP8266 and ESP32 microcontrollers such as the TTGO
T-display and many others.

Devices are flashed as soon as they are connected to a USB port, with
sequentially allocated unique device ids (unless the --id option specifies
a single id, see below).

# Installation

    On macOS and linux, these commands must be entered at the shell.
    On Windows the Windows Subsystem for Linux (WSL) must be started
    by entering "wsl" at the start menu and this will open a shell.

    Most systems already have python3 installed, but if this is not
    the case then use the standard procedure to install it, for example:

    $ brew install python3                # macOS

    $ sudo apt-get install python3        # Ubuntu linux or Windows + WSL
    $ sudo apt-get install python3-pip

    Then install the dependencies (all platforms):

    $ pip3 install pyserial
    $ pip3 install adafruit-ampy
    $ export PATH=~/.local/bin:$PATH      # this line needed on Windows + WSL to access ampy

    Then clone this repository with:

    $ git clone git@github.com:udem-dlteam/bulk-upload-firmware
    $ cd bulk-upload-firmware

    When the script bulk-upload-firmware.sh is first executed it will
    install the esptool required for flashing the device.

# Sample use to upload firmware to a device

    $ ./bulk_upload_firmware.sh --id "TTGO213"  # upload default firmware to single device

    $ ./bulk_upload_firmware.sh --firmware micropython  # bulk upload of micropython firmware

    $ ./bulk_upload_firmware.sh --config "ssid='mywifi'\npwd='mywifipw'"  # bulk upload of default firmware

# Command line options

    --port <port>      Select specific serial port. If this option is not
                       specified the script will continuously scan all the
                       USB ports for new connections, and the uploads will
                       be done concurrently (useful for bulk uploading).

    --dir <dir>        Select a directory that contains the available
                       firmware.  Defaults to the "firmware" subdirectory.

    --firmware <name>  Select a specific firmware from the firmware
                       directory.  Defaults to "default".

    --id <id>          Select an id for the device.  If <id> does not contain
                       a "#" then it will be assigned to the device and the
                       program will exit after the upload.  If the id contains
                       one or more contiguous "#" then it is a template for
                       generating ids. Each "#" will be replaced by a digit.
                       Defaults to "DEV#".

    --start <N>        The starting sequence number. Defaults to 0.

    --config <config>  Python code to add to generated _config.py file.
                       Any "\n" is replaced with a newline.
