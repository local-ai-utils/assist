import json
import subprocess
from typing import Any, Dict, AnyStr

from typing_extensions import override
from openai import AssistantEventHandler

from local_ai_utils_core import LocalAIUtilsCore
from assist.plugin import config

NOTIFY_CMD = '''
on run argv
display notification (item 2 of argv) with title (item 1 of argv)
end run
'''

def notify(title: AnyStr, text: AnyStr):
    subprocess.call(['osascript', '-e', NOTIFY_CMD, title, text])
 
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler): 
  @override
  def __init__(self, core: LocalAIUtilsCore):
    self.core = core
    super().__init__()
     
  @override
  def on_text_done(self, text: AnyStr) -> None:
    print(text.value)
    ##Text(annotations=[], value="I'm your personal assistant, ready to assist you with tasks and information.")
      
  def on_tool_call_done(self, tool_call: Dict):
    plugin_config = config()
    client = self.core.clients.open_ai()

    success = False
    failure_reason = "Unknown"

    notify('AI Assist', f"Tool call: {tool_call.function.name}")

    function_name = tool_call.function.name
    plugin_name, method_name = function_name.split('--')

    plugins = self.core.getPlugins()
    if plugin_name in plugins:
      plugin = plugins[plugin_name]

      if method_name in dir(plugin['tools']):
        try:
          args = json.loads(tool_call.function.arguments)
          
          func = getattr(plugin['tools'], method_name)
          result = func(**args)
          success = result is True

          if not success:
            failure_reason = str(result)

        except Exception as e:
          failure_reason = str(e)
      else:
        failure_reason = f"Tool {method_name} not found in plugin {plugin_name}"
    else:
      failure_reason = f"Plugin {plugin_name} not found"

    output = {
       'success': success
    }
    if not success:
      print('Failure: ', failure_reason)
      output["error"] = failure_reason

    self._submit_tool_outputs(client, plugin_config, tool_call, output)

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
    ##FunctionToolCall(id='call_Q7ME5bR1LwC88e7VBiUXY8sZ', function=Function(arguments='{"categories":["reminder","call","Cody"],"note_text":"Remind me to call Cody."}', name='create_note', output=None), type='function', index=0)
 
def sendChat(core: LocalAIUtilsCore, prompt: AnyStr):
    plugin_config = config()
    client = core.clients.open_ai()

    notify('AI Assist', 'Prompting...')
    client.beta.threads.messages.create(
        thread_id=plugin_config['thread'],
        role="user",
        content=prompt
    )
    with client.beta.threads.runs.stream(
        thread_id=plugin_config['thread'],
        assistant_id=plugin_config['assistant'],
        event_handler=EventHandler(core),
    ) as stream:
        stream.until_done()

def update_assistant():
  core = LocalAIUtilsCore()
  client = core.clients.open_ai()
  plugin_config = config()

  plugins = core.getPlugins()
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

  response = client.beta.assistants.update(
    plugin_config['assistant'],
    tools=tools
  )

  print(response)
  
def prompt(prompt: AnyStr):
  core = LocalAIUtilsCore()
  sendChat(core, prompt)