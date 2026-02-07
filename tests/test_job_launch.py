"""Test AWX MCP functionality - launch job."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_job_launch():
    """Test launching a job from template."""
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
    
    # Create client
    client = CompositeAWXClient(env, username, secret, is_token)
    
    async with client:
        print("\nTesting connection...")
        if not await client.test_connection():
            print("✗ Connection failed!")
            return
        print("✓ Connection successful")
        
        # List templates first
        print("\nListing available templates...")
        templates = await client.list_job_templates(page_size=5)
        
        if not templates:
            print("✗ No job templates found!")
            print("\nPlease create a job template in AWX first.")
            return
        
        print(f"\nAvailable templates:")
        for template in templates:
            print(f"  [{template.id}] {template.name}")
        
        # Get template ID from user
        print("\n" + "=" * 70)
        template_id = input("Enter template ID to launch (or press Enter to skip): ").strip()
        
        if not template_id:
            print("Skipped job launch.")
            return
        
        try:
            template_id = int(template_id)
        except ValueError:
            print(f"✗ Invalid template ID: {template_id}")
            return
        
        # Optional: Get extra vars
        print("\nOptional: Enter extra variables as JSON (or press Enter to skip)")
        print("Example: {\"version\": \"1.2.3\", \"environment\": \"production\"}")
        extra_vars_str = input("Extra vars: ").strip()
        
        extra_vars = None
        if extra_vars_str:
            import json
            try:
                extra_vars = json.loads(extra_vars_str)
            except json.JSONDecodeError as e:
                print(f"✗ Invalid JSON: {e}")
                return
        
        # Launch job
        print(f"\nLaunching job from template {template_id}...")
        job = await client.launch_job(
            template_id=template_id,
            extra_vars=extra_vars
        )
        
        print(f"\n✓ Job launched successfully!")
        print(f"  Job ID: {job.id}")
        print(f"  Job Name: {job.name}")
        print(f"  Status: {job.status}")
        print(f"  URL: {env.base_url}/#/jobs/playbook/{job.id}")
        
        # Wait for job to complete (optional)
        wait = input("\nWait for job to complete? (y/N): ").strip().lower()
        
        if wait == 'y':
            print("\nWaiting for job to complete...")
            import time
            while True:
                job_status = await client.get_job(job.id)
                status = job_status.status.lower()
                
                if status in ('successful', 'failed', 'error', 'canceled'):
                    break
                
                print(f"  Status: {status}...")
                await asyncio.sleep(5)
            
            print(f"\n{'✓' if status == 'successful' else '✗'} Job {status}!")
            print(f"  Job ID: {job.id}")
            print(f"  Final Status: {job_status.status}")
            
            if status != 'successful':
                print(f"\nView logs with: python tests/test_job_stdout.py {job.id}")

if __name__ == "__main__":
    asyncio.run(test_job_launch())
