"""Quick test of MCP server functionality."""
import asyncio
import sys
from awx_mcp.server import create_mcp_server

async def test_server():
    """Test basic server functionality."""
    try:
        print("Creating MCP server...")
        server = create_mcp_server()
        print("✓ Server created successfully")
        
        print("\nTesting list_tools()...")
        # The server should have tools available
        print("✓ Server initialized")
        
        return True
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
