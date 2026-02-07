"""Test AWX MCP functionality - get job status."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_job_get():
    """Test getting job status and details."""
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
            # Show recent jobs
            print("\nRecent jobs:")
            jobs = await client.list_jobs(page_size=5)
            if jobs:
                for job in jobs:
                    status_emoji = {
                        'successful': '✓',
                        'failed': '✗',
                        'running': '⟳',
                        'pending': '⏳',
                        'canceled': '⊘'
                    }.get(job.status.lower(), '•')
                    print(f"  [{job.id}] {status_emoji} {job.name} - {job.status}")
            
            job_id_str = input("\nEnter job ID to check: ").strip()
            if not job_id_str:
                print("No job ID provided.")
                return
            job_id = int(job_id_str)
        
        # Get job details
        print(f"\nFetching job {job_id} details...")
        job = await client.get_job(job_id)
        
        status_emoji = {
            'successful': '✓',
            'failed': '✗',
            'running': '⟳',
            'pending': '⏳',
            'canceled': '⊘'
        }.get(job.status.lower(), '•')
        
        print(f"\n{status_emoji} Job Details:")
        print(f"  Job ID: {job.id}")
        print(f"  Name: {job.name}")
        print(f"  Status: {job.status}")
        
        if hasattr(job, 'job_template_name'):
            print(f"  Template: {job.job_template_name}")
        
        if hasattr(job, 'created'):
            print(f"  Created: {job.created}")
        
        if hasattr(job, 'started') and job.started:
            print(f"  Started: {job.started}")
        
        if hasattr(job, 'finished') and job.finished:
            print(f"  Finished: {job.finished}")
        
        if hasattr(job, 'elapsed'):
            print(f"  Elapsed: {job.elapsed}s")
        
        if hasattr(job, 'launched_by'):
            print(f"  Launched by: {job.launched_by}")
        
        print(f"\n  URL: {env.base_url}/#/jobs/playbook/{job.id}")
        
        # Suggest next actions
        if job.status.lower() == 'failed':
            print(f"\n💡 Next steps:")
            print(f"   View output: python tests/test_job_stdout.py {job_id}")
            print(f"   Analyze failure: python tests/test_job_failure_summary.py {job_id}")
        elif job.status.lower() == 'running':
            print(f"\n💡 Job is still running. Check again in a moment.")
            print(f"   Cancel job: python tests/test_job_cancel.py {job_id}")

if __name__ == "__main__":
    asyncio.run(test_job_get())
