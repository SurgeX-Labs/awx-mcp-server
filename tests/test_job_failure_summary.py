"""Test AWX MCP functionality - analyze job failure."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType
from awx_mcp.utils import analyze_job_failure

async def test_job_failure_summary():
    """Test analyzing job failure and getting actionable suggestions."""
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
            # Show recent failed jobs
            print("\nRecent failed jobs:")
            jobs = await client.list_jobs(page_size=20)
            failed_jobs = [j for j in jobs if j.status.lower() in ('failed', 'error')]
            
            if not failed_jobs:
                print("No failed jobs found.")
                print("\nTip: This tool analyzes failed jobs to provide actionable suggestions.")
                return
            
            for job in failed_jobs[:10]:
                print(f"  [{job.id}] ✗ {job.name}")
                if hasattr(job, 'finished') and job.finished:
                    print(f"      Finished: {job.finished}")
            
            job_id_str = input("\nEnter job ID to analyze: ").strip()
            if not job_id_str:
                print("No job ID provided.")
                return
            job_id = int(job_id_str)
        
        # Get job status
        print(f"\nAnalyzing job {job_id}...")
        job = await client.get_job(job_id)
        
        if job.status.lower() not in ('failed', 'error'):
            print(f"\n⚠ Job status is '{job.status}', not 'failed'.")
            print("This tool is designed to analyze failed jobs.")
            
            if job.status.lower() == 'running':
                print("\nJob is still running. Wait for it to complete.")
            elif job.status.lower() == 'successful':
                print("\nJob completed successfully. No failure analysis needed.")
            
            return
        
        # Get job events and stdout
        print("Gathering job details...")
        events = await client.get_job_events(job_id, failed_only=True, page_size=100)
        stdout = await client.get_job_stdout(job_id, format='txt')
        
        # Analyze failure
        print("\n" + "=" * 70)
        print(f"FAILURE ANALYSIS - JOB {job_id}")
        print("=" * 70)
        
        analysis = analyze_job_failure(job, events, stdout)
        
        print(f"\n📋 Summary:")
        print(f"   {analysis['summary']}")
        
        if analysis.get('error_type'):
            print(f"\n🔍 Error Type:")
            print(f"   {analysis['error_type']}")
        
        if analysis.get('failed_tasks'):
            print(f"\n✗ Failed Tasks:")
            for task in analysis['failed_tasks']:
                print(f"   • {task}")
        
        if analysis.get('error_messages'):
            print(f"\n💬 Error Messages:")
            for msg in analysis['error_messages'][:5]:  # Show first 5
                print(f"   • {msg}")
        
        if analysis.get('suggestions'):
            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(analysis['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        
        # Additional context
        print(f"\n📊 Job Details:")
        print(f"   Job ID: {job.id}")
        print(f"   Name: {job.name}")
        print(f"   Status: {job.status}")
        if hasattr(job, 'finished'):
            print(f"   Finished: {job.finished}")
        print(f"   URL: {env.base_url}/#/jobs/playbook/{job.id}")
        
        print("\n" + "=" * 70)
        
        # Next steps
        print(f"\n📖 Next Steps:")
        print(f"   View full output: python tests/test_job_stdout.py {job_id}")
        print(f"   View all events: python tests/test_job_events.py {job_id}")
        print(f"   View failed events: python tests/test_job_events.py {job_id} --failed-only")

if __name__ == "__main__":
    asyncio.run(test_job_failure_summary())
