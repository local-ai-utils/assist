from unittest.mock import patch, ANY, Mock

from assist.main import EventHandler, sendChat, update_assistant, prompt
from local_ai_utils_core import LocalAIUtilsCore

def test_prompt_calls_send_chat():
    with patch('assist.main.sendChat', return_value=None) as mock_send_chat:
        prompt("Hi")
        mock_send_chat.assert_called_once_with(ANY, "Hi")

def test_prompt_creates_core():
    with patch('local_ai_utils_core.LocalAIUtilsCore.__init__', return_value=None) as mock_init:
        with patch('assist.main.sendChat', return_value=None):
            prompt("Hi")
            mock_init.assert_called_once()

def test_update_assistant_creates_core():
    core = LocalAIUtilsCore()
    with patch('local_ai_utils_core.LocalAIUtilsCore.__new__', return_value=core) as mock_init:
        update_assistant()
        mock_init.assert_called_once()

def test_update_assistant_updates_assistant(mock_openai_calls):
    mock_openai_calls.beta.assistants.update.reset_mock()
    update_assistant()
    mock_openai_calls.beta.assistants.update.assert_called_once()

def test_update_assistant_loads_one_plugin(mock_openai_calls):
    mock_openai_calls.beta.assistants.update.reset_mock()

    with patch('local_ai_utils_core.LocalAIUtilsCore.getPlugins') as mock_getPlugins:
        mock_getPlugins.return_value = {
            'plugin1': {'name': 'plugin1', 'functions': [{'name': 'func1'}]}
        }
        update_assistant()

    mock_openai_calls.beta.assistants.update.assert_called_once_with(ANY, tools=[{
        "type": "function",
        "function": {
            'name': 'plugin1--func1'
        }
    }])


def test_update_assistant_loads_two_plugins(mock_openai_calls):
    mock_openai_calls.beta.assistants.update.reset_mock()

    with patch('local_ai_utils_core.LocalAIUtilsCore.getPlugins') as mock_getPlugins:
        mock_getPlugins.return_value = {
            'plugin1': {'name': 'plugin1', 'functions': [{'name': 'func1'}]},
            'plugin2': {'name': 'plugin2', 'functions': [{'name': 'func1'}]}
        }
        update_assistant()

    mock_openai_calls.beta.assistants.update.assert_called_once_with(ANY, tools=[
        {
            "type": "function",
            "function": {
                'name': 'plugin1--func1'
            }
        },
        {
            "type": "function",
            "function": {
                'name': 'plugin2--func1'
            }
        }
    ])

def test_update_assistant_prints_response():
    with patch('builtins.print') as mock_print:
        update_assistant()
        mock_print.assert_called_once_with('Mocked Assistant Response')

def test_send_chat_notifies(mock_notify):
    core = LocalAIUtilsCore()
    sendChat(core, "Hi")
    mock_notify.assert_called_once_with('AI Assist', 'Prompting...')

def test_send_chat_creates_thread_with_prompt(mock_openai_calls):
    core = LocalAIUtilsCore()
    mock_openai_calls.beta.threads.messages.create.reset_mock()
    sendChat(core, "Hi")
    mock_openai_calls.beta.threads.messages.create.assert_called_once_with(thread_id=ANY, role="user", content="Hi")

def test_event_handler_prints_text():
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('builtins.print') as mock_print:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_text_done(ret)
        mock_print.assert_called_once_with('Hello')

def test_event_handler_tool_done_notifies(mock_notify):
    core = LocalAIUtilsCore()
    handler = EventHandler(core)
    tool_call = Mock()
    tool_call.function = Mock()
    tool_call.function.name = 'plugin--func'
    tool_call.function.id = 1
    handler.on_tool_call_done(tool_call)
    mock_notify.assert_called_once_with('AI Assist', 'Tool call: plugin--func')


def test_event_handler_tool_done_fails_for_missing_functions():
    core = LocalAIUtilsCore()
    handler = EventHandler(core)
    with patch('local_ai_utils_core.LocalAIUtilsCore.getPlugins') as mock_getPlugins:
        mock_getPlugins.return_value = {
            'plugin': {'name': 'plugin', 'functions': [{'name': 'func'}], 'tools': {}},
        }
        with patch('assist.main.EventHandler._submit_tool_outputs') as tool_output:
            ret = Mock()
            func = Mock()
            ret.value = 'Hello'
            ret.function = func
            func.name = 'plugin--notafunc'
            handler.on_tool_call_done(ret)
            # Get the output of the tool call
            output = tool_output.call_args[0][3]
            print(output)
            assert output['success'] == False
            assert output['error'] == 'Tool notafunc not found in plugin plugin'

def test_event_handler_tool_done_fails_for_missing_plugins():
    core = LocalAIUtilsCore()
    handler = EventHandler(core)
    with patch('local_ai_utils_core.LocalAIUtilsCore.getPlugins') as mock_getPlugins:
        mock_getPlugins.return_value = {
            'plugin': {'name': 'plugin', 'functions': [{'name': 'func'}], 'tools': {}},
        }
        with patch('assist.main.EventHandler._submit_tool_outputs') as tool_output:
            ret = Mock()
            func = Mock()
            ret.value = 'Hello'
            ret.function = func
            func.name = 'notaplugin--func'
            handler.on_tool_call_done(ret)
            output = tool_output.call_args[0][3]
            assert output['success'] == False
            assert output['error'] == 'Plugin notaplugin not found'
"""
def test_event_handler_tool_done_calls_tools():
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('assist.main.notify') as mock_notify:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_tool_done(ret)
        mock_notify.assert_called_once_with('AI Assist', 'Tool Done')

def test_event_handler_tool_done_prints_tool_errors():
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('builtins.print') as mock_print:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_tool_done(ret)
        mock_print.assert_called_once_with('Tool Error: Hello')

def test_event_handler_tool_done_updates_successful_tool_calls():
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('assist.main.notify') as mock_notify:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_tool_done(ret)
        mock_notify.assert_called_once_with('AI Assist', 'Tool Done')

def test_event_handler_tool_done_updates_failed_tool_calls():
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('assist.main.notify') as mock_notify:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_tool_done(ret)
        mock_notify.assert_called_once_with('AI Assist', 'Tool Done')

def test_event_handler_submit_outputs_submits_outputs(mock_openai_calls):
    core = LocalAIUtilsCore
    handler = EventHandler(core)
    with patch('assist.main.notify') as mock_notify:
        ret = Mock()
        ret.value = 'Hello'
        handler.on_submit_outputs(ret)
        mock_notify.assert_called_once_with('AI Assist', 'Tool Done')
"""