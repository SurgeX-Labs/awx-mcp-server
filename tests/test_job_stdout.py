"""Test AWX MCP functionality - get job output/stdout."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_job_stdout():
    """Test getting job output/stdout."""
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
            # Show recent completed jobs
            print("\nRecent completed jobs:")
            jobs = await client.list_jobs(page_size=10)
            completed_jobs = [j for j in jobs if j.status.lower() in ('successful', 'failed', 'error')]
            
            if not completed_jobs:
                print("No completed jobs found.")
                return
            
            for job in completed_jobs[:5]:
                status_emoji = '✓' if job.status.lower() == 'successful' else '✗'
                print(f"  [{job.id}] {status_emoji} {job.name} - {job.status}")
            
            job_id_str = input("\nEnter job ID to view output: ").strip()
            if not job_id_str:
                print("No job ID provided.")
                return
            job_id = int(job_id_str)
        
        # Get job stdout
        print(f"\nFetching job {job_id} output...")
        
        # Option to get last N lines or full output
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            tail_lines = int(sys.argv[2])
            print(f"(Showing last {tail_lines} lines)")
            stdout = await client.get_job_stdout(job_id, format='txt', tail_lines=tail_lines)
        else:
            print("(Full output - use 'python test_job_stdout.py <job_id> <lines>' to limit)")
            stdout = await client.get_job_stdout(job_id, format='txt')
        
        # Display output
        print("\n" + "=" * 70)
        print(f"JOB {job_id} OUTPUT")
        print("=" * 70)
        print(stdout)
        print("=" * 70)
        
        # Get job status
        job = await client.get_job(job_id)
        status_emoji = '✓' if job.status.lower() == 'successful' else '✗'
        print(f"\n{status_emoji} Job Status: {job.status}")
        
        if job.status.lower() in ('failed', 'error'):
            print(f"\n💡 Analyze this failure:")
            print(f"   python tests/test_job_failure_summary.py {job_id}")
            print(f"   python tests/test_job_events.py {job_id} --failed-only")

if __name__ == "__main__":
    asyncio.run(test_job_stdout())
