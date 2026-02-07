"""Test AWX MCP functionality - cancel job."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_job_cancel():
    """Test canceling a running job."""
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
        
        # Get job ID from command line or prompt
        if len(sys.argv) > 1:
            job_id = int(sys.argv[1])
        else:
            # Show running jobs
            print("\nRunning jobs:")
            running_jobs = await client.list_jobs(status='running', page_size=10)
            
            if not running_jobs:
                print("No running jobs found.")
                
                # Show pending jobs
                pending_jobs = await client.list_jobs(status='pending', page_size=10)
                if pending_jobs:
                    print("\nPending jobs:")
                    for job in pending_jobs:
                        print(f"  [{job.id}] {job.name}")
                
                return
            
            for job in running_jobs:
                print(f"  [{job.id}] {job.name}")
                if hasattr(job, 'elapsed'):
                    print(f"      Elapsed: {job.elapsed}s")
            
            job_id_str = input("\nEnter job ID to cancel: ").strip()
            if not job_id_str:
                print("No job ID provided.")
                return
            job_id = int(job_id_str)
        
        # Get current job status
        print(f"\nChecking job {job_id} status...")
        job = await client.get_job(job_id)
        
        print(f"  Current status: {job.status}")
        
        if job.status.lower() not in ('running', 'pending', 'waiting'):
            print(f"\n⚠ Job is not running (status: {job.status})")
            print("Only running, pending, or waiting jobs can be canceled.")
            return
        
        # Confirm cancellation
        confirm = input(f"\n⚠ Cancel job {job_id} '{job.name}'? (y/N): ").strip().lower()
        
        if confirm != 'y':
            print("Cancellation aborted.")
            return
        
        # Cancel job
        print(f"\nCanceling job {job_id}...")
        result = await client.cancel_job(job_id)
        
        print(f"\n✓ Job cancellation requested!")
        
        # Wait a moment and check status
        await asyncio.sleep(2)
        updated_job = await client.get_job(job_id)
        
        print(f"  Updated status: {updated_job.status}")
        
        if updated_job.status.lower() == 'canceled':
            print(f"\n✓ Job successfully canceled.")
        else:
            print(f"\n⏳ Cancellation in progress. Current status: {updated_job.status}")
            print(f"   Check status again with: python tests/test_job_get.py {job_id}")

if __name__ == "__main__":
    asyncio.run(test_job_cancel())
