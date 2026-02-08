"""Entry point for running awx_mcp_server as a module.

This allows the server to be run with: python -m awx_mcp_server
"""

import asyncio
import sys
from awx_mcp_server.mcp_server import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
