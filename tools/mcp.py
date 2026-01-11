"""MCP (Model Context Protocol) tool integration."""

import logging

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


async def get_mcp_tools() -> list:
    """Get all MCP tools from configured servers.

    Returns:
        List of available MCP tools, or empty list if connection fails.
    """
    try:
        client = MultiServerMCPClient(
            {
                # "ucagent": {
                #     "transport": "streamable_http",
                #     "url": "http://localhost:5000/mcp",
                #     "timeout": 30,
                # },
                "espagent": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8090/mcp",
                    "timeout": 30,
                },
            }
        )
        mcp_tools = await client.get_tools()
        return mcp_tools
    except Exception:
        logger.warning("! MCP connection failed")
        return []
