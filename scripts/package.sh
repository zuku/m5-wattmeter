#!/bin/bash

which zip > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "zip command does not exist." >&2
    exit 2
fi

if [ ! -f "./dist/wattmeter.py" ]; then
    echo "wattmeter.py does not exist." >&2
    echo "run build first" >&2
    exit 3
fi
if [ ! -f "./dist/wattmeter.mpy" ]; then
    echo "wattmeter.mpy does not exist." >&2
    echo "run build first" >&2
    exit 4
fi

rm -f "./dist/package.zip"
rm -rf "./dist/tmp"
mkdir "./dist/tmp"
mkdir "./dist/tmp/misc"
mkdir "./dist/tmp/release"
mkdir "./dist/tmp/release/apps"

echo "./dist/wattmeter.mpy -> ./dist/tmp/release/wattmeter.mpy"
cp "./dist/wattmeter.mpy" "./dist/tmp/release/"
echo "./m5wm.py -> ./dist/tmp/release/apps/m5wm.py"
cp "./m5wm.py" "./dist/tmp/release/apps/"
echo "./config/required.json -> ./dist/tmp/release/wmconfig.json"
cp "./config/required.json" "./dist/tmp/release/wmconfig.json"

echo "./dist/wattmeter.py -> ./dist/tmp/misc/wattmeter.py"
cp "./dist/wattmeter.py" "./dist/tmp/misc/"
echo "./config/full.json -> ./dist/tmp/misc/wmconfig.full.json"
cp "./config/full.json" "./dist/tmp/misc/wmconfig.full.json"
echo "./LICENSE -> ./dist/tmp/LICENSE"
cp "./LICENSE" "./dist/tmp/"
echo "./readme.txt -> ./dist/tmp/readme.txt"
cp "./readme.txt" "./dist/tmp/"
echo
echo "Create archive file"
cd "./dist/tmp"
zip "../package.zip" -r *
cd "../../"
rm -rf "./dist/tmp"

echo
if [ -f "./dist/package.zip" ]; then
    FILE_SIZE=`stat -c "%s" ./dist/package.zip`
    echo "Name: ./dist/package.zip"
    echo "Size: ${FILE_SIZE}"
    echo
else
    echo "Failed" >&2
    exit 5
fi

exit 0
