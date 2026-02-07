"""Test AWX MCP functionality - list jobs."""
import asyncio
from datetime import datetime, timedelta
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_list_jobs():
    """Test listing AWX jobs."""
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
    
    # Create client and list jobs
    client = CompositeAWXClient(env, username, secret, is_token)
    
    async with client:
        print("\nTesting connection...")
        if not await client.test_connection():
            print("✗ Connection failed!")
            return
        print("✓ Connection successful")
        
        # List all jobs
        print("\nListing recent jobs...")
        jobs = await client.list_jobs(page_size=10)
        
        if not jobs:
            print("No jobs found.")
            print("\nTip: Launch a job template to see jobs here")
        else:
            print(f"\nFound {len(jobs)} job(s):\n")
            for job in jobs:
                status_emoji = {
                    'successful': '✓',
                    'failed': '✗',
                    'running': '⟳',
                    'pending': '⏳',
                    'canceled': '⊘'
                }.get(job.status.lower(), '•')
                
                print(f"  [{job.id}] {status_emoji} {job.name}")
                print(f"      Status: {job.status}")
                if hasattr(job, 'job_template_name'):
                    print(f"      Template: {job.job_template_name}")
                if hasattr(job, 'created'):
                    print(f"      Created: {job.created}")
                if hasattr(job, 'finished') and job.finished:
                    print(f"      Finished: {job.finished}")
                print()
        
        # List only running jobs
        print("\nListing running jobs...")
        running_jobs = await client.list_jobs(status='running', page_size=10)
        
        if running_jobs:
            print(f"\nFound {len(running_jobs)} running job(s):\n")
            for job in running_jobs:
                print(f"  [{job.id}] ⟳ {job.name}")
                if hasattr(job, 'elapsed'):
                    print(f"      Elapsed: {job.elapsed}s")
                print()
        else:
            print("No running jobs.")

if __name__ == "__main__":
    asyncio.run(test_list_jobs())
