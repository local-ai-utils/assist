from local_ai_utils_core import LocalAIUtilsCore
from typing import Dict
import logging
from .mcp_manager import MCPManager
from local_ai_utils_core.ui import get_ui
__core = None
__config = {}
__mcp_manager = None

log = logging.getLogger(__name__)
ui = get_ui()

def config():
    global __config
    return __config

def core():
    global __core
    return __core

def get_mcp_manager():
    global __mcp_manager
    return __mcp_manager

# This creates a callable function for each MCP tool that:
# 1. Takes the arguments needed for the MCP tool
# 2. Passes them to the appropriate MCP tool via run_tool
# 3. Returns results in the expected (success, result) format
async def create_mcp_tool_func(tool_name):
    async def mcp_tool_func(**kwargs):
        global __mcp_manager
        if not __mcp_manager:
            raise ValueError("MCP Manager not initialized")
        
        return await __mcp_manager.run_tool(tool_id=tool_name, arguments=kwargs)

    return mcp_tool_func

async def get_mcp_functions(mcpConfig):
  global __mcp_manager
  if not __mcp_manager:
    __mcp_manager = MCPManager(mcpConfig)
    
  return await __mcp_manager.openai_tools()

async def build_mcp_tools(mcp_functions):
    tools = {}
    
    for func in mcp_functions:
        if 'name' in func:
            tools[func['name'].split('--')[-1]] = await create_mcp_tool_func(func['name'])
    
    return tools

async def register(core: LocalAIUtilsCore, plugin_config: Dict):
    global __core, __config, __mcp_manager, ui
    __core = core
    __config = plugin_config

    if 'instructions' not in __config:
        __config['instructions'] = """You are a personal assistant running on my local machine. You are mostly used via a terminal interface, or via voice commands and growl notifications.

- Do not ask the user questions, because they cannot respond. This is not a back-and-forth conversation. It is ask-and-response.
- Use short and concise responses, that are easily read at a glance in a notification or terminal window
- When working with embeddings, reformat the input data to be focused and clear, and remove any extraneous information, to make the embedding more accurate.
- Do not include any Markdown or HTML formatting - your interface is always just plain text. Feel free to use ASCII decorating for styling.
"""

    mcp_functions = await get_mcp_functions(plugin_config.get('mcp', {}))
    
    tools = await build_mcp_tools(mcp_functions)

    return {
        "name": "assist",
        "functions": mcp_functions,
        "tools": tools
    }
