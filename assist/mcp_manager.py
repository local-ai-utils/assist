import tempfile
import yaml
import copy
from mcp_agent.mcp.mcp_aggregator import MCPAggregator
from mcp_agent.config import get_settings
import logging
from local_ai_utils_core.ui import get_ui

log = logging.getLogger(__name__)
ui = get_ui()

class MCPManager:
    def __init__(self, config):
        self.server_configs = config
        self._tools = None
        self._mcp_aggregator = None

    @classmethod
    def to_openai_function(cls, tool):
        funct = copy.deepcopy(tool)
        
        if "properties" not in funct:
            funct["properties"] = {}

        if "inputSchema" in funct:
            funct["parameters"] = funct["inputSchema"]
            del funct["inputSchema"]

        if "annotations" in funct:
            del funct["annotations"]

        if "properties" in funct:
            del funct["properties"]

        return funct
    
    def config_tempfile(self):
        temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False)
        yaml.dump({
            'mcp': self.server_configs,
            'logger': {
                'type': 'none'
            }
        }, temp_file)
        temp_file.close()

        return temp_file.name
    
    async def mcp_aggregator(self):
        if self._mcp_aggregator is None:
            config_file = self.config_tempfile()

            # It's not entirely clear why
            # but I have to manually load settings before updating the registry
            get_settings(config_file)

            self._mcp_aggregator = await MCPAggregator.create(server_names=self.server_configs['servers'].keys())
            self._mcp_aggregator.context.server_registry.registry = self._mcp_aggregator.context.server_registry.load_registry_from_file(self.config_tempfile())

        return self._mcp_aggregator
    
    async def get_tools(self):
        if self._tools is not None:
            return self._tools
       
        mcp_aggregator = await self.mcp_aggregator()
        async with mcp_aggregator:
            tools = await mcp_aggregator.list_tools()
            self._tools = tools.tools
            return self._tools

    async def openai_tools(self):
        return [self.to_openai_function(tool.dict()) for tool in await self.get_tools()]
    
    async def confirm_tool_execution(self, tool_id: str, arguments: dict):
        splits =  tool_id.split('_')
        server_name = splits[0]
        tool_name = '_'.join(splits[1:])

        server_config = self.server_configs['servers'][server_name]

        if 'skip_confirmation' in server_config and tool_name in server_config['skip_confirmation']:
            log.info(f"Skipping confirmation for tool: {tool_id}. Tool is in skip_confirmation list.")
            return True
        else:
            return await ui.confirm(f"Running tool: {tool_id} with arguments: {arguments}")

    async def run_tool(self, tool_id: str, arguments: dict):
        mcp_aggregator = await self.mcp_aggregator()
                
        if await self.confirm_tool_execution(tool_id, arguments):
            results = await mcp_aggregator.call_tool(name=tool_id, arguments=arguments)
            return True, results.content[0].text
        else:
            return (False, "Tool execution rejected by user.")
        