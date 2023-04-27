import json

def dump(obj, stream):
    json.dump(obj, stream)

def dumps(obj):
    return json.dumps(obj)

def load(stream):
    return json.load(stream)

def loads(str):
    return json.loads(str)
