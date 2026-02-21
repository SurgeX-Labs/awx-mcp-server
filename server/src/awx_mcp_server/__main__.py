"""Entry point for running awx_mcp_server as a module.

This allows the server to be run with: python -m awx_mcp_server
"""

import asyncio
import sys
from awx_mcp_server.mcp_server import main

__version__ = "1.1.6"

if __name__ == "__main__":
    # Handle --version flag
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"awx-mcp-server {__version__}")
        sys.exit(0)
    
    # Handle --help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"AWX MCP Server v{__version__}")
        print("\nUsage: python -m awx_mcp_server [OPTIONS]")
        print("\nOptions:")
        print("  --version, -v     Show version and exit")
        print("  --help, -h        Show this help message and exit")
        print("\nMCP Server Mode (default):")
        print("  Starts STDIO server for MCP client communication")
        print("\nEnvironment Variables:")
        print("  AWX_BASE_URL      AWX/AAP instance URL (required)")
        print("  AWX_TOKEN         AWX/AAP API token")
        print("  AWX_USERNAME      AWX/AAP username (alternative to token)")
        print("  AWX_PASSWORD      AWX/AAP password (alternative to token)")
        print("  AWX_PLATFORM      Platform type: awx (default), aap, or tower")
        print("  AWX_VERIFY_SSL    Verify SSL certificates (default: true)")
        print("  LOG_LEVEL         Logging level (debug|info|warning|error)")
        sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
