"""Test AWX MCP functionality - update project from SCM."""
import asyncio
import sys
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_project_update():
    """Test updating a project from SCM (git sync)."""
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
        
        # Get project ID from command line or prompt
        if len(sys.argv) > 1:
            project_id = int(sys.argv[1])
        else:
            # Show available projects
            print("\nAvailable projects:")
            projects = await client.list_projects(page_size=20)
            
            if not projects:
                print("No projects found.")
                print("\nTip: Create a project in AWX first.")
                return
            
            for project in projects:
                status_icon = {
                    'successful': '✓',
                    'failed': '✗',
                    'running': '⟳',
                    'pending': '⏳',
                    'never updated': '○'
                }.get(project.status.lower(), '•')
                
                print(f"  [{project.id}] {status_icon} {project.name}")
                if project.scm_type:
                    print(f"      SCM: {project.scm_type}")
                if project.scm_url:
                    print(f"      URL: {project.scm_url}")
                print(f"      Status: {project.status}")
            
            project_id_str = input("\nEnter project ID to update: ").strip()
            if not project_id_str:
                print("No project ID provided.")
                return
            project_id = int(project_id_str)
        
        # Check if we should wait
        wait = '--wait' in sys.argv or '-w' in sys.argv
        
        # Update project
        print(f"\nUpdating project {project_id} from SCM...")
        update_job = await client.update_project(project_id, wait=False)
        
        print(f"\n✓ Project update initiated!")
        print(f"  Update Job ID: {update_job.id}")
        print(f"  Status: {update_job.status}")
        
        if not wait:
            wait_input = input("\nWait for update to complete? (Y/n): ").strip().lower()
            wait = wait_input != 'n'
        
        if wait:
            print("\nWaiting for project update to complete...")
            
            while True:
                await asyncio.sleep(3)
                
                # Get update job status
                job_status = await client.get_job(update_job.id)
                status = job_status.status.lower()
                
                if status in ('successful', 'failed', 'error', 'canceled'):
                    break
                
                print(f"  Status: {status}...")
            
            # Final status
            status_emoji = '✓' if status == 'successful' else '✗'
            print(f"\n{status_emoji} Project update {status}!")
            
            if status == 'successful':
                print(f"\n✓ Project {project_id} successfully updated from SCM.")
                print(f"\n💡 You can now run job templates that use this project.")
            else:
                print(f"\n✗ Project update failed!")
                print(f"\n💡 View update logs:")
                print(f"   python tests/test_job_stdout.py {update_job.id}")
                print(f"   python tests/test_job_failure_summary.py {update_job.id}")
        else:
            print(f"\n💡 Check update status later:")
            print(f"   python tests/test_job_get.py {update_job.id}")

if __name__ == "__main__":
    asyncio.run(test_project_update())
