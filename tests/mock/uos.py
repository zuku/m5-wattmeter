import os

ENTRIES = [
    ('apps', 16384, 0),
    ('blocks', 16384, 0),
    ('boot.py', 32768, 0),
    ('emojiImg', 16384, 0),
    ('img', 16384, 0),
    ('main.py', 32768, 0),
    ('res', 16384, 0),
    ('temp.py', 32768, 0),
    ('test.py', 32768, 0),
    ('update', 16384, 0),
]
ADD_ENTRIES = []

def ilistdir(dir = None):
    return ENTRIES + ADD_ENTRIES

def listdir(dir = None):
    list = []
    for entry in ilistdir(dir):
        list.append(entry[0])
    return list

def remove(path):
    os.remove(path)
