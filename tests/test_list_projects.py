"""Test AWX MCP functionality - list projects."""
import asyncio
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_list_projects():
    """Test listing AWX projects."""
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
    
    # Create client and list projects
    client = CompositeAWXClient(env, username, secret, is_token)
    
    async with client:
        print("\nTesting connection...")
        if not await client.test_connection():
            print("✗ Connection failed!")
            return
        print("✓ Connection successful")
        
        print("\nListing projects...")
        projects = await client.list_projects(page_size=10)
        
        if not projects:
            print("No projects found.")
            print("\nTip: You can create projects in AWX UI at http://localhost:30080")
        else:
            print(f"\nFound {len(projects)} project(s):\n")
            for project in projects:
                print(f"  [{project.id}] {project.name}")
                if project.description:
                    print(f"      Description: {project.description}")
                print(f"      SCM Type: {project.scm_type}")
                if project.scm_url:
                    print(f"      SCM URL: {project.scm_url}")
                print(f"      Status: {project.status}")
                print()

if __name__ == "__main__":
    asyncio.run(test_list_projects())
