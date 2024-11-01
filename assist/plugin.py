__core = None
__config = {}

def config():
    global __config
    return __config

def core():
    global __core
    return __core

def register(core, plugin_config):
    global __core, __config
    __core = core
    __config = plugin_config
    return {
        "name": "assist"
    }
