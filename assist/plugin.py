from local_ai_utils_core import LocalAIUtilsCore
from typing import Dict

__core = None
__config = {}

def config():
    global __config
    return __config

def core():
    global __core
    return __core

def register(core: LocalAIUtilsCore, plugin_config: Dict):
    global __core, __config
    __core = core
    __config = plugin_config
    return {
        "name": "assist"
    }
