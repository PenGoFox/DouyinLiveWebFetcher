import json

config = None

def loadConfig(filename):
    global config
    config = None
    with open(filename) as f:
        config = json.load(f)
    if config is None:
        return False
    else:
        return True

def getConfig():
    global config
    return config
