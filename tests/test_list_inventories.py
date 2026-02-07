"""Test AWX MCP functionality - list inventories."""
import asyncio
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_list_inventories():
    """Test listing AWX inventories."""
    print("Loading AWX configuration...")
    
    config_manager = ConfigManager()
    credential_store = CredentialStore()
    
    # Get active environment
    env = config_manager.get_active()
    print(f"✓ Active environment: {env.name} ({env.base_url})")
    
    # Get credentials
    try:
        username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
        is_token = False
    except Exception:
        username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
        is_token = True
    
    print(f"✓ Using {'token' if is_token else 'password'} authentication")
    
    # Create client and list inventories
    client = CompositeAWXClient(env, username, secret, is_token)
    
    async with client:
        print("\nTesting connection...")
        if not await client.test_connection():
            print("✗ Connection failed!")
            return
        print("✓ Connection successful")
        
        print("\nListing inventories...")
        inventories = await client.list_inventories(page_size=10)
        
        if not inventories:
            print("No inventories found.")
            print("\nTip: You can create inventories in AWX UI at http://localhost:30080")
        else:
            print(f"\nFound {len(inventories)} inventor(ies):\n")
            for inventory in inventories:
                print(f"  [{inventory.id}] {inventory.name}")
                if inventory.description:
                    print(f"      Description: {inventory.description}")
                if hasattr(inventory, 'total_hosts'):
                    print(f"      Hosts: {inventory.total_hosts}")
                if hasattr(inventory, 'total_groups'):
                    print(f"      Groups: {inventory.total_groups}")
                print()

if __name__ == "__main__":
    asyncio.run(test_list_inventories())
