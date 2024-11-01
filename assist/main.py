import json
import subprocess
from typing_extensions import override
from openai import AssistantEventHandler
from local_ai_utils_core import LocalAIUtilsCore
from local_ai_utils_assist.plugin import config

NOTIFY_CMD = '''
on run argv
display notification (item 2 of argv) with title (item 1 of argv)
end run
'''

def notify(title, text):
    subprocess.call(['osascript', '-e', NOTIFY_CMD, title, text])
 
# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler): 
  @override
  def __init__(self, core):
    self.core = core
    super().__init__()
     
  @override
  def on_text_done(self, text) -> None:
    print(text.value)
    ##Text(annotations=[], value="I'm your personal assistant, ready to assist you with tasks and information.")
      
  def on_tool_call_done(self, tool_call):
    plugin_config = config()
    client = self.core.clients.open_ai()

    success = False
    failureReason = "Unknown"

    notify('AI Assist', f"Tool call: {tool_call.function.name}")

    function_name = tool_call.function.name
    plugin_name = function_name.split('--')[0]
    method_name = function_name.split('--')[1]

    plugins = self.core.getPlugins()
    if plugin_name in plugins:
      plugin = plugins[plugin_name]

      if method_name in dir(plugin['tools']):
        try:
          args = json.loads(tool_call.function.arguments)
          
          func = getattr(plugin['tools'], method_name)
          success = func(**args)

          if success is not True:
            failureReason = success
            success = False

        except Exception as e:
          failureReason = str(e)

    output = {
       success: success
    }
    if not success:
      print('Failure: ', failureReason)
      output["error"] = failureReason

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
 
def sendChat(core, prompt):
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
  
def prompt(prompt):
  core = LocalAIUtilsCore()
  sendChat(core, prompt)