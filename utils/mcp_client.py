
import asyncio
import json
import sys
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.logger import setup_logger

logger = setup_logger("mcp_client")

class MCPClientWrapper:
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        """Connects to the MCP server via stdio."""
        logger.info(f"Connecting to MCP server at {self.server_script_path}...")
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path],
            env=os.environ.copy()
        )

        self._client_context = stdio_client(server_params)
        self.read, self.write = await self._client_context.__aenter__()
        
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        
        await self.session.initialize()
        logger.info("Connected to MCP server.")

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Calls a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("MCP Client is not connected.")
        
        logger.info(f"- Invoking tool {tool_name} -")
        try:
            result = await self.session.call_tool(tool_name, arguments)
            # result is typically a CallToolResult, we want to parse the text content
            # The result.content is a list of Content objects (TextContent, ImageContent, etc.)
            
            final_output = []
            for content in result.content:
                if content.type == "text":
                    final_output.append(content.text)
            
            # Combine text and try to parse as JSON if it looks like it, otherwise return raw
            full_text = "".join(final_output)
            try:
                return json.loads(full_text)
            except json.JSONDecodeError:
                return full_text
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise

    async def close(self):
        """Closes the connection."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
        logger.info("MCP Client disconnected.")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
