"""Test AWX MCP functionality - environment management."""
import asyncio
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.domain import CredentialType, NoActiveEnvironmentError

async def test_env_management():
    """Test environment management operations."""
    print("=" * 70)
    print("AWX MCP Server - Environment Management Tests")
    print("=" * 70)
    
    config_manager = ConfigManager()
    credential_store = CredentialStore()
    
    # Test 1: List environments
    print("\n[Test 1] List Environments")
    print("-" * 70)
    
    environments = config_manager.list()
    
    if not environments:
        print("⚠ No environments configured.")
        print("\nTo add an environment, run:")
        print("  python -m awx_mcp.cli env add --name local --url http://localhost:30080 --token TOKEN")
        return
    
    print(f"Found {len(environments)} environment(s):\n")
    for env in environments:
        is_active = "✓ ACTIVE" if env.is_default else ""
        print(f"  [{env.env_id}] {env.name} {is_active}")
        print(f"      URL: {env.base_url}")
        print(f"      Verify SSL: {env.verify_ssl}")
        if env.allowed_job_templates:
            print(f"      Allowed Templates: {', '.join(env.allowed_job_templates[:3])}")
        print()
    
    # Test 2: Get active environment
    print("\n[Test 2] Get Active Environment")
    print("-" * 70)
    
    try:
        active_env = config_manager.get_active()
        print(f"✓ Active environment: {active_env.name}")
        print(f"  Environment ID: {active_env.env_id}")
        print(f"  Base URL: {active_env.base_url}")
        print(f"  Verify SSL: {active_env.verify_ssl}")
    except NoActiveEnvironmentError:
        print("✗ No active environment set!")
        print("\nSet an active environment with:")
        print(f"  python -m awx_mcp.cli env set-default {environments[0].name}")
        return
    
    # Test 3: Check credentials
    print("\n[Test 3] Check Credentials")
    print("-" * 70)
    
    try:
        # Try password auth first
        username, secret = credential_store.get_credential(active_env.env_id, CredentialType.PASSWORD)
        print(f"✓ Password authentication configured")
        print(f"  Username: {username}")
        print(f"  Secret: {'*' * len(secret)}")
    except Exception:
        try:
            # Try token auth
            username, secret = credential_store.get_credential(active_env.env_id, CredentialType.TOKEN)
            print(f"✓ Token authentication configured")
            print(f"  Username: {username}")
            print(f"  Token: {secret[:8]}...{secret[-8:]}")
        except Exception as e:
            print(f"✗ No credentials found: {e}")
            print("\nRe-add environment with credentials:")
            print(f"  python -m awx_mcp.cli env add --name {active_env.name} --url {active_env.base_url} --token TOKEN")
            return
    
    # Test 4: Test connection
    print("\n[Test 4] Test Connection to AWX")
    print("-" * 70)
    
    from awx_mcp.clients import CompositeAWXClient
    
    # Determine credential type
    try:
        username, secret = credential_store.get_credential(active_env.env_id, CredentialType.PASSWORD)
        is_token = False
    except Exception:
        username, secret = credential_store.get_credential(active_env.env_id, CredentialType.TOKEN)
        is_token = True
    
    client = CompositeAWXClient(active_env, username, secret, is_token)
    
    async with client:
        print(f"Testing connection to {active_env.base_url}...")
        
        if await client.test_connection():
            print(f"✓ Connection successful!")
        else:
            print(f"✗ Connection failed!")
            print("\nPossible issues:")
            print("  • AWX server is not running")
            print("  • Incorrect URL or credentials")
            print("  • Network/firewall issues")
            print("  • SSL certificate problems (try --no-verify-ssl)")
            return
    
    # Test 5: Switch environments (if multiple exist)
    print("\n[Test 5] Environment Switching")
    print("-" * 70)
    
    if len(environments) > 1:
        print(f"Multiple environments available:")
        for env in environments:
            is_active = " (ACTIVE)" if env.is_default else ""
            print(f"  • {env.name}{is_active}")
        
        print(f"\nTo switch environments:")
        for env in environments:
            if not env.is_default:
                print(f"  python -m awx_mcp.cli env set-default {env.name}")
                break
    else:
        print(f"Only one environment configured: {active_env.name}")
        print(f"\nTo add another environment:")
        print(f"  python -m awx_mcp.cli env add --name staging --url https://awx-staging.local --token TOKEN")
    
    # Test 6: Allowlist check (if configured)
    print("\n[Test 6] Template Allowlist")
    print("-" * 70)
    
    if active_env.allowed_job_templates:
        print(f"✓ Template allowlist configured ({len(active_env.allowed_job_templates)} templates)")
        print(f"\nAllowed templates:")
        for template in active_env.allowed_job_templates:
            print(f"  • {template}")
        
        print(f"\n⚠ Only these templates can be launched via MCP.")
    else:
        print(f"○ No allowlist configured - all templates allowed")
        print(f"\nTo restrict to specific templates:")
        print(f"  Edit config file: ~/.awx-mcp/config.json")
        print(f'  Add: "allowed_job_templates": ["template1", "template2"]')
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ {len(environments)} environment(s) configured")
    print(f"✓ Active environment: {active_env.name}")
    print(f"✓ Connection: Working")
    print(f"\n🎉 Environment management is working correctly!")
    print(f"\n💡 Next steps:")
    print(f"   • List templates: python tests/test_list_templates.py")
    print(f"   • List projects: python tests/test_list_projects.py")
    print(f"   • List jobs: python tests/test_list_jobs.py")
    print(f"   • Launch job: python tests/test_job_launch.py")

if __name__ == "__main__":
    asyncio.run(test_env_management())
