"""Test AWX MCP functionality - get job events."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_job_events():
    """Test getting job events."""
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
        
        # Parse command line arguments
        failed_only = '--failed-only' in sys.argv or '-f' in sys.argv
        
        # Get job ID
        job_id = None
        for arg in sys.argv[1:]:
            if arg.isdigit():
                job_id = int(arg)
                break
        
        if not job_id:
            # Show recent jobs
            print("\nRecent jobs:")
            jobs = await client.list_jobs(page_size=5)
            
            if not jobs:
                print("No jobs found.")
                return
            
            for job in jobs:
                status_emoji = {
                    'successful': '✓',
                    'failed': '✗',
                    'running': '⟳',
                }.get(job.status.lower(), '•')
                print(f"  [{job.id}] {status_emoji} {job.name} - {job.status}")
            
            job_id_str = input("\nEnter job ID to view events: ").strip()
            if not job_id_str:
                print("No job ID provided.")
                return
            job_id = int(job_id_str)
        
        # Get job events
        filter_msg = " (failed only)" if failed_only else ""
        print(f"\nFetching job {job_id} events{filter_msg}...")
        
        events = await client.get_job_events(job_id, failed_only=failed_only, page_size=100)
        
        if not events:
            if failed_only:
                print("\n✓ No failed events found!")
            else:
                print("\nNo events found for this job.")
            return
        
        # Display events
        print(f"\nFound {len(events)} event(s):\n")
        print("=" * 70)
        
        for event in events:
            event_type = event.get('event', 'unknown')
            
            # Emoji for event type
            emoji = {
                'runner_on_ok': '✓',
                'runner_on_failed': '✗',
                'runner_on_unreachable': '⚠',
                'runner_on_skipped': '⊙',
                'playbook_on_start': '▶',
                'playbook_on_stats': '■',
            }.get(event_type, '•')
            
            print(f"{emoji} {event_type}")
            
            if 'task' in event and event['task']:
                print(f"   Task: {event['task']}")
            
            if 'host' in event and event['host']:
                print(f"   Host: {event['host']}")
            
            if 'play' in event and event['play']:
                print(f"   Play: {event['play']}")
            
            # Show error details for failed events
            if 'failed' in event_type or event.get('failed', False):
                if 'event_data' in event and 'res' in event['event_data']:
                    res = event['event_data']['res']
                    
                    if 'msg' in res:
                        print(f"   Message: {res['msg']}")
                    
                    if 'stderr' in res and res['stderr']:
                        print(f"   Stderr: {res['stderr'][:200]}")
                    
                    if 'stdout' in res and res['stdout']:
                        print(f"   Stdout: {res['stdout'][:200]}")
            
            print()
        
        print("=" * 70)
        
        # Get job status
        job = await client.get_job(job_id)
        status_emoji = '✓' if job.status.lower() == 'successful' else '✗'
        print(f"\n{status_emoji} Job Status: {job.status}")
        
        if job.status.lower() in ('failed', 'error') and not failed_only:
            print(f"\n💡 Show only failed events:")
            print(f"   python tests/test_job_events.py {job_id} --failed-only")
            print(f"\n💡 Analyze this failure:")
            print(f"   python tests/test_job_failure_summary.py {job_id}")

if __name__ == "__main__":
    asyncio.run(test_job_events())
