import json
import logging
import asyncio
from typing import Any, Dict, AnyStr
from datetime import datetime
from typing_extensions import override
from openai import AssistantEventHandler

from local_ai_utils_core import LocalAIUtilsCore
from local_ai_utils_core.ui import get_ui
from .plugin import config
from .mcp_manager import MCPManager

logging.getLogger().setLevel(logging.WARNING)
log = logging.getLogger(__name__)
ui = get_ui()
 
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler): 
  @override
  def __init__(self, core: LocalAIUtilsCore):
    self.core = core
    self.mcp_manager = MCPManager(config().get('mcp', {}))
    self._pending_tasks = set()
    
    super().__init__()
     
  @override
  def on_text_done(self, text: AnyStr) -> None:
    task = asyncio.create_task(ui.message(text.value))
    self._pending_tasks.add(task)
    task.add_done_callback(self._pending_tasks.discard)
      
  @override
  def on_tool_call_done(self, tool_call: Dict):
    task = asyncio.create_task(self._handle_tool_call(tool_call))
    self._pending_tasks.add(task)
    task.add_done_callback(self._pending_tasks.discard)
    
  async def _handle_tool_call(self, tool_call: Dict):
    plugin_config = config()
    client = self.core.clients.open_ai()

    success = False
    failure_reason = "Unknown"
    result = None

    ui.info(f"Tool call: {tool_call.function.name}")

    function_name = tool_call.function.name
    
    plugin_or_server_name, method_name = function_name.split('--', 1) if '--' in function_name else (function_name, None)

    if method_name:
        plugins = await self.core.plugins.plugins()
        if plugin_or_server_name in plugins:
            plugin = plugins[plugin_or_server_name]

            if method_name in plugin['tools']:
                try:
                    args = json.loads(tool_call.function.arguments)
                    func = plugin['tools'][method_name]
                    success, result = await func(**args)

                    if not success:
                      failure_reason = result

                except Exception as e:
                    log.error(f"Error running local plugin tool {function_name}: {e}", exc_info=True)
                    failure_reason = str(e)
                    success = False
            else:
                failure_reason = f"Tool {method_name} not found in plugin {plugin_or_server_name}"
        else:
            failure_reason = f"Plugin {plugin_or_server_name} not found"
    else:
        failure_reason = f"Invalid tool name format: {function_name}. Expected 'plugin_name--tool_name' or 'mcp_server_name--tool_name'."

    output = {
       'success': success,
       'result': result
    }
    
    if not success:
      log.error(f"Tool call {function_name} failed: {failure_reason}")
      output["error"] = failure_reason

    try:
      self._submit_tool_outputs(client, plugin_config, tool_call, output)
    except Exception as e:
      log.error(f"Error submitting tool outputs: {e}", exc_info=True)

  def _submit_tool_outputs(self, client: Any, plugin_config: Dict, tool_call: Any, output: Dict) -> None:
    with client.beta.threads.runs.submit_tool_outputs_stream(
       thread_id=plugin_config['thread'],
       run_id=self.current_run.id,
       tool_outputs=[
         {
           "tool_call_id": tool_call.id,
           "output": json.dumps(output)
         }
       ],
       event_handler=EventHandler(self.core),
    ) as stream:
      stream.until_done()
 
def wrap_prompt_with_context(prompt: AnyStr):
  return f"""
  ===CONTEXT===
  Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

  ===USER PROMPT===
  {prompt}
  """

def sendChat(core: LocalAIUtilsCore, prompt: AnyStr, handler):
    plugin_config = config()
    client = core.clients.open_ai()

    ui.info('Prompting...')
    client.beta.threads.messages.create(
        thread_id=plugin_config['thread'],
        role="user",
        content=wrap_prompt_with_context(prompt)
    )
    with client.beta.threads.runs.stream(
        thread_id=plugin_config['thread'],
        assistant_id=plugin_config['assistant'],
        event_handler=handler,
    ) as stream:
        stream.until_done()

async def update_assistant():
  core = LocalAIUtilsCore()
  client = core.clients.open_ai()
  plugins = await core.plugins.plugins()
  plugin_config = config()

  client.beta.assistants.update(
    plugin_config['assistant'],
    tools=build_tool_config(plugins),
    instructions=plugin_config['instructions']
  )

  await ui.message('Assistant updated.')

def build_tool_config(plugins):
  tools = []
  for plugin in plugins:
      plugin = plugins[plugin]
      if 'functions' in plugin:
        for function in plugin['functions']:
          toolFunc = function.copy()
          toolFunc['name'] = f"{plugin['name']}--{toolFunc['name']}"
          tools.append({
            "type": "function",
            "function": toolFunc
          })

  return tools

async def wait_for_tasks(handler: EventHandler):
  while handler._pending_tasks:
    pending = handler._pending_tasks
    if pending:
      await asyncio.wait(pending, return_when=asyncio.ALL_COMPLETED)
    else:
      break

async def prompt(prompt: AnyStr):
  core = LocalAIUtilsCore()
  await core.plugins.plugins()
  handler = EventHandler(core)

  sendChat(core, prompt, handler)
  await wait_for_tasks(handler)