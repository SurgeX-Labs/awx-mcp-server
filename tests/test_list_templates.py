"""Test AWX MCP functionality - list job templates."""
import asyncio
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_list_templates():
    """Test listing job templates."""
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
    
    # Create client and list templates
    client = CompositeAWXClient(env, username, secret, is_token)
    
    async with client:
        print("\nTesting connection...")
        if not await client.test_connection():
            print("✗ Connection failed!")
            return
        print("✓ Connection successful")
        
        print("\nListing job templates...")
        templates = await client.list_job_templates(page_size=10)
        
        if not templates:
            print("No job templates found.")
            print("\nTip: You can create templates in AWX UI at http://localhost:30080")
        else:
            print(f"\nFound {len(templates)} job template(s):\n")
            for template in templates:
                print(f"  [{template.id}] {template.name}")
                if template.description:
                    print(f"      Description: {template.description}")
                print(f"      Project: {template.project}")
                print(f"      Playbook: {template.playbook}")
                print()

if __name__ == "__main__":
    asyncio.run(test_list_templates())
