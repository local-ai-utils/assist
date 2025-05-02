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

    if 'instructions' not in __config:
        __config['instructions'] = """You are a personal assistant running on my local machine. You are mostly used via a terminal interface, or via voice commands and growl notifications.

- Do not ask the user questions, because they cannot respond. This is not a back-and-forth conversation. It is ask-and-response.
- Use short and concise responses, that are easily read at a glance in a notification or terminal window
- When working with embeddings, reformat the input data to be focused and clear, and remove any extraneous information, to make the embedding more accurate.
- Do not include any Markdown or HTML formatting - your interface is always just plain text. Feel free to use ASCII decorating for styling.
"""

    return {
        "name": "assist"
    }
