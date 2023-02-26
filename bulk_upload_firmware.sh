#!/bin/sh

FIRMWARE="$1"

if [ "$FIRMWARE" = "" ] ; then
    FIRMWARE="codeboot-ttgo"
fi

if [ ! -e "firmware/$FIRMWARE" ] ; then
    printf "firmware \"$FIRMWARE\" does not exist\n"
    exit 1
fi

ESPTOOL_PY_DIR=esptool-py
ESPTOOL_PY_URL=https://github.com/espressif/esptool.git
ESPTOOL_PY_VERSION=901017fedde62a8fe5d94a5e4517d66e35613c33

get_tool()
{
    TOOL="$1"

    # check if tool is installed

    if ! which "$TOOL" > /dev/null; then

        printf "*** installing $TOOL"

        # use the appropriate installer to install tool $TOOL

        if which "brew" > /dev/null; then
            printf "*** installing $TOOL with brew"
            brew install "$TOOL"
        else
            printf "*** don't know how to install $TOOL"
            exit 1
        fi
    fi
}

# get esptool-py

if [ -e "$ESPTOOL_PY_DIR" ] ; then
    printf "*** $ESPTOOL_PY_DIR already installed... skipping\n"
else
    printf "*** cloning $ESPTOOL_PY_URL to $ESPTOOL_PY_DIR\n"
    git clone "$ESPTOOL_PY_URL" "$ESPTOOL_PY_DIR"
    (cd "$ESPTOOL_PY_DIR" ; git checkout -f "$ESPTOOL_PY_VERSION" )
fi

export PYTHONPATH=`pwd`/$ESPTOOL_PY_DIR:$PYTHONPATH

esptool()
{
    python3 -m esptool $*
}

#esptool --port /dev/tty.usbmodem56230379101 ...
python3 bulk_upload_firmware.py "$FIRMWARE"
