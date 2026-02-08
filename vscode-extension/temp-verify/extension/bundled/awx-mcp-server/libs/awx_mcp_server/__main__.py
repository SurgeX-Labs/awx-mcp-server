"""Entry point for running AWX MCP as a module."""

import asyncio
from awx_mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
