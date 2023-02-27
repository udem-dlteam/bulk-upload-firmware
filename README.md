# bulk-upload-firmware

Script to upload firmware to microcontroller boards based on Espressif
microcontrollers such as the ESP8266 and ESP32.

The microcontroller boards are flashed as soon as they are connected
to a USB port, with sequentially allocated unique device ids (unless the
--id option is used).

Dependencies:

    pip3 install adafruit-ampy
    pip3 install pyserial

Sample use:

    ./bulk_upload_firmware.sh --firmware micropython

    ./bulk_upload_firmware.sh --id "TTGO213" --config "ssid='mywifi'\npwd='mywifipw'"  # upload to single device

Options:

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
