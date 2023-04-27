#!/bin/bash

which mpy-cross > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "mpy-cross command does not exist." >&2
    exit 2
fi

if [ ! -f "./dist/wattmeter.py" ]; then
    echo "wattmeter.py does not exist." >&2
    exit 3
fi
if [ -f "./dist/wattmeter.mpy" ]; then
    rm "./dist/wattmeter.mpy"
fi

mpy-cross ./dist/wattmeter.py

if [ -f "./dist/wattmeter.mpy" ]; then
    FILE_SIZE=`stat -c "%s" ./dist/wattmeter.mpy`
    echo "Name: ./dist/wattmeter.mpy"
    echo "Size: ${FILE_SIZE}"
    echo
else
    echo "Failed" >&2
    exit 4
fi

exit 0
