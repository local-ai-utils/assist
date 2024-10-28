import importlib
import inspect
import inspect

def load_plugins(plugin_list, config):
    plugins = {}
    for plugin_name in plugin_list:
        try:
            module = importlib.import_module(f"{plugin_name}.plugin")
            if hasattr(module, 'register'):
                plugin_info = module.register(config)
                plugins[plugin_name] = plugin_info
            else:
                print(f"Warning: Plugin {plugin_name} does not have a register function.")
        except ImportError as e:
            print(f"Error: Could not import plugin {plugin_name}")
            # Print all details
            print(e)
    return plugins