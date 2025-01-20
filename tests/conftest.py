import pytest
from unittest.mock import patch, Mock
from openai import OpenAI

from assist.main import EventHandler, notify

from local_ai_utils_core.clients import ClientManager

@pytest.fixture(autouse=True)
def mock_notify():
    with patch('assist.main.notify') as mock_notify:
        yield mock_notify

@pytest.fixture(autouse=True)
def mock_openai_calls():
    with patch.object(ClientManager, 'open_ai') as mock_openai_class:
        mock_client = Mock(spec=OpenAI)
        mock_client.beta = Mock()
        mock_client.beta.assistants = Mock()
        mock_client.beta.threads = Mock()
        mock_client.beta.threads.runs = Mock()
        mock_client.beta.threads.messages = Mock()
        mock_client.beta.threads.messages.create = Mock()

        stream_mock = Mock()
        stream_cm_mock = Mock()
        stream_cm_mock.until_done = Mock()
        # Return a context manager
        stream_mock.return_value = Mock(__enter__=lambda x: x, __exit__=Mock(return_value=stream_cm_mock))

        mock_client.beta.threads.runs.stream = stream_mock
        mock_client.beta.threads.runs.submit_tool_outputs_stream = stream_mock

        update_mock = Mock(return_value="Mocked Assistant Response")
        mock_client.beta.assistants.update = update_mock

        mock_openai_class.return_value = mock_client
        yield mock_client

@pytest.fixture(autouse=True)
def mock_eventhandler():
    with patch('assist.main.EventHandler.current_run') as run_mock:
        run_mock.id = 1
        yield