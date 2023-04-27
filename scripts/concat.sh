#!/bin/bash

if [ -f "./dist/wattmeter.py" ]; then
    rm "./dist/wattmeter.py"
fi

cat ./wattmeter/*.py > ./dist/._wattmeter.py
if [ $? -ne 0 ]; then
    echo "Concatenation failed." >&2
    exit 2
fi
mv ./dist/._wattmeter.py ./dist/wattmeter.py
if [ $? -ne 0 ]; then
    echo "Rename failed." >&2
    exit 3
fi

if [ -f "./dist/wattmeter.py" ]; then
    FILE_SIZE=`stat -c "%s" ./dist/wattmeter.py`
    echo "Name: ./dist/wattmeter.py"
    echo "Size: ${FILE_SIZE}"
    echo
else
    echo "Failed" >&2
    exit 4
fi

exit 0
