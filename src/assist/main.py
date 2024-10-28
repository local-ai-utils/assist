import os
import yaml
from .plugin_loader import load_plugins
import sys
import json
import subprocess
from typing_extensions import override
from openai import OpenAI, AssistantEventHandler

plugins = []
config = {}
client = None

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
  def on_text_done(self, text) -> None:
    print(text.value)
    ##Text(annotations=[], value="I'm your personal assistant, ready to assist you with tasks and information.")
      
  def on_tool_call_done(self, tool_call):
    global plugins

    success = False
    failureReason = "Unknown"

    notify('AI Assist', f"Tool call: {tool_call.function.name}")

    function_name = tool_call.function.name
    plugin_name = function_name.split('--')[0]
    method_name = function_name.split('--')[1]

    if plugin_name in plugins:
      plugin = plugins[plugin_name]

      if method_name in dir(plugin['tools']):
        try:
          args = json.loads(tool_call.function.arguments)
          
          func = getattr(plugin['tools'], method_name)
          success = func(**args)
          print('tool done', success)

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
       thread_id=config['thread'],
       run_id=self.current_run.id,
       tool_outputs=[
         {
           "tool_call_id": tool_call.id,
           "output": json.dumps(output)
         }
       ],
       event_handler=EventHandler(),
    ) as stream:
      stream.until_done()
    ##FunctionToolCall(id='call_Q7ME5bR1LwC88e7VBiUXY8sZ', function=Function(arguments='{"categories":["reminder","call","Cody"],"note_text":"Remind me to call Cody."}', name='create_note', output=None), type='function', index=0)
 
def sendChat(prompt):
    notify('AI Assist', 'Prompting...')
    client.beta.threads.messages.create(
        thread_id=config['thread'],
        role="user",
        content=prompt
    )
    with client.beta.threads.runs.stream(
        thread_id=config['thread'],
        assistant_id=config['assistant'],
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

def create_note(text, categories):
    note_id = insert_note(text)

    # Handle categories
    for category in categories:
        category_id = create_category(category)
        assign_category(note_id, category_id)

def main():
  global plugins, config, client

  config_path = os.path.expanduser('~/.config/ai-utils.yaml')

  with open(config_path, 'r') as file:
      config = yaml.safe_load(file)

  client = OpenAI(api_key=config['keys']['openai'])
  plugins = load_plugins(config['plugins'], config)

  # Pass first argument as prompt
  if len(sys.argv) > 1:
      match sys.argv[1]:
        case "update_assistant":
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
            config['assistant'],
            tools=tools
          )

          print(response)

        case "prompt":
          if len(sys.argv) > 2:
            sendChat(sys.argv[2])
          else:
            print("Please provide a prompt")

          return
  else:
      print("prompt <msg> or update_assistant")

if __name__ == "__main__":
  main()