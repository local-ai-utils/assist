# Local AI Utils - Assist
A plugin for [local-ai-utils](https://github.com/local-ai-utils/core), adding the ability to interact with an LLM Assistant. It is exposed as a CLI utility named `assist`, which can be sent a prompt. It also adds tool support that other LAIU plugins can tie in to.

![Assist Demo](/docs/assist.gif)

## Quickstart

### Installation
Currently installation is only supported via the GitHub remote.
```
pip install git+https://github.com/local-ai-utils/core
```

### Configuration
Then update your `ai-utils.yml` file.

- `assist.assitant` is an [OpenAI Assistant](https://platform.openai.com/docs/api-reference/assistants/object) `id`
- `assist.thread` is an [OpenAI Thread](https://platform.openai.com/docs/api-reference/threads/object) that has been started with the above assitant
- `keys.openai` is your [Open AI secret key](https://platform.openai.com/settings/organization/api-keys).

### Usage
```
$ # Run once for new installs, and whenever new plugins are added
$ assist update_assistant
<outputs the configuration details of your assistant>


$ assist prompt "Make a note to call Joe"
OK, I've created a note to call Joe!
```

## Configuration
All three configuration fields below are required.

`~/.config/ai-utils.yaml`
```
plugins:
    assist:
        assistant: "asst_123"
        thread: "thread_321"
keys:
    openai: "sk-proj-abc"
```

> [!WARNING]
> There is a known bug right now that failed tool calls can leave a Thread in a broken state. If encountered, you will see errors referencing an inability to create new runs on threads that are in-progress. You can reset this by generating a new thread, and updating `assist.thread` in your `ai-utils.yml`.

## Plugin Tools

When `local-ai-utils-assist` is installed, all other LAIU plugins can now make use of the `functions` keyword in their PluginConfig object. This key can be passed an array of objects matching the [OpenAI Function Definition](https://platform.openai.com/docs/guides/function-calling). See the [notes plugin](https://github.com/local-ai-utils/notes/blob/main/src/notes/plugin.py#L7) for an example.