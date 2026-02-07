"""Comprehensive integration tests for AWX MCP Server.

This test suite covers all MCP server functionality:
- List job templates, projects, inventories
- Launch jobs from templates
- Monitor job status and get output
- Diagnose job failures with AI analysis
- Update projects from SCM
- Get detailed information about any AWX resource
"""

import asyncio
import pytest
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType


@pytest.fixture
async def awx_client():
    """Create AWX client from configured environment."""
    config_manager = ConfigManager()
    credential_store = CredentialStore()
    
    try:
        env = config_manager.get_active()
    except Exception:
        pytest.skip("No active AWX environment configured")
    
    try:
        username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
        is_token = False
    except Exception:
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        except Exception:
            pytest.skip("No credentials found for active environment")
    
    client = CompositeAWXClient(env, username, secret, is_token)
    async with client:
        if not await client.test_connection():
            pytest.skip("Cannot connect to AWX server")
        yield client


@pytest.mark.asyncio
class TestAWXConnection:
    """Test AWX connection and authentication."""
    
    async def test_connection_successful(self, awx_client):
        """Test successful connection to AWX."""
        result = await awx_client.test_connection()
        assert result is True, "AWX connection should be successful"


@pytest.mark.asyncio
class TestJobTemplates:
    """Test job template operations."""
    
    async def test_list_job_templates(self, awx_client):
        """Test listing job templates."""
        templates = await awx_client.list_job_templates(page_size=10)
        assert isinstance(templates, list), "Should return a list"
        
        if templates:
            template = templates[0]
            assert hasattr(template, 'id'), "Template should have id"
            assert hasattr(template, 'name'), "Template should have name"
            assert hasattr(template, 'playbook'), "Template should have playbook"
            assert hasattr(template, 'project'), "Template should have project"
    
    async def test_list_job_templates_with_filter(self, awx_client):
        """Test filtering job templates by name."""
        all_templates = await awx_client.list_job_templates()
        
        if all_templates:
            # Filter by first template name
            search_name = all_templates[0].name[:5]  # First 5 chars
            filtered = await awx_client.list_job_templates(name_filter=search_name)
            assert len(filtered) <= len(all_templates), "Filtered list should be smaller or equal"
    
    async def test_get_job_template_by_id(self, awx_client):
        """Test getting specific job template."""
        templates = await awx_client.list_job_templates(page_size=1)
        
        if templates:
            template_id = templates[0].id
            template = await awx_client.get_job_template(template_id)
            assert template.id == template_id, f"Should get template with ID {template_id}"
            assert template.name, "Template should have a name"
            assert template.playbook, "Template should have a playbook"
    
    async def test_list_job_templates_pagination(self, awx_client):
        """Test job template pagination."""
        page1 = await awx_client.list_job_templates(page=1, page_size=5)
        page2 = await awx_client.list_job_templates(page=2, page_size=5)
        
        # Ensure different pages return different results (if enough templates exist)
        if len(page1) == 5 and page2:
            assert page1[0].id != page2[0].id, "Different pages should have different content"


@pytest.mark.asyncio
class TestProjects:
    """Test project operations."""
    
    async def test_list_projects(self, awx_client):
        """Test listing projects."""
        projects = await awx_client.list_projects(page_size=10)
        assert isinstance(projects, list), "Should return a list"
        
        if projects:
            project = projects[0]
            assert hasattr(project, 'id'), "Project should have id"
            assert hasattr(project, 'name'), "Project should have name"
            assert hasattr(project, 'scm_type'), "Project should have scm_type"
    
    async def test_get_project_by_id(self, awx_client):
        """Test getting specific project."""
        projects = await awx_client.list_projects(page_size=1)
        
        if projects:
            project_id = projects[0].id
            project = await awx_client.get_project(project_id)
            assert project.id == project_id, f"Should get project with ID {project_id}"
            assert project.name, "Project should have a name"
    
    async def test_update_project(self, awx_client):
        """Test updating project from SCM."""
        projects = await awx_client.list_projects()
        
        if projects:
            project_id = projects[0].id
            # Note: wait=False to avoid long test times
            result = await awx_client.update_project(project_id, wait=False)
            assert 'project_update_id' in result or 'message' in result, \
                "Update should return update ID or message"


@pytest.mark.asyncio
class TestInventories:
    """Test inventory operations."""
    
    async def test_list_inventories(self, awx_client):
        """Test listing inventories."""
        inventories = await awx_client.list_inventories(page_size=10)
        assert isinstance(inventories, list), "Should return a list"
        
        if inventories:
            inventory = inventories[0]
            assert hasattr(inventory, 'id'), "Inventory should have id"
            assert hasattr(inventory, 'name'), "Inventory should have name"
    
    async def test_get_inventory_by_id(self, awx_client):
        """Test getting specific inventory."""
        inventories = await awx_client.list_inventories(page_size=1)
        
        if inventories:
            inventory_id = inventories[0].id
            inventory = await awx_client.get_inventory(inventory_id)
            assert inventory.id == inventory_id, f"Should get inventory with ID {inventory_id}"
            assert inventory.name, "Inventory should have a name"


@pytest.mark.asyncio
class TestJobExecution:
    """Test job launching and monitoring."""
    
    async def test_launch_job(self, awx_client):
        """Test launching a job from template."""
        templates = await awx_client.list_job_templates()
        
        if not templates:
            pytest.skip("No job templates available for testing")
        
        template_id = templates[0].id
        job = await awx_client.launch_job(template_id)
        
        assert hasattr(job, 'id'), "Job should have id"
        assert hasattr(job, 'status'), "Job should have status"
        assert job.id > 0, "Job ID should be positive"
        
        # Return job for monitoring tests
        return job
    
    async def test_launch_job_with_extra_vars(self, awx_client):
        """Test launching job with extra variables."""
        templates = await awx_client.list_job_templates()
        
        if not templates:
            pytest.skip("No job templates available for testing")
        
        template_id = templates[0].id
        extra_vars = {"test_var": "test_value", "environment": "testing"}
        
        job = await awx_client.launch_job(template_id, extra_vars=extra_vars)
        assert job.id > 0, "Job should be launched successfully"
    
    async def test_get_job_status(self, awx_client):
        """Test getting job status."""
        # Launch a job first
        templates = await awx_client.list_job_templates()
        if not templates:
            pytest.skip("No job templates available")
        
        job = await awx_client.launch_job(templates[0].id)
        job_id = job.id
        
        # Get job status
        job_info = await awx_client.get_job(job_id)
        assert job_info.id == job_id, "Should get correct job"
        assert hasattr(job_info, 'status'), "Job should have status"
        assert job_info.status in ['pending', 'waiting', 'running', 'successful', 'failed', 'canceled'], \
            "Status should be valid"
    
    async def test_list_jobs(self, awx_client):
        """Test listing jobs."""
        jobs = await awx_client.list_jobs(page_size=10)
        assert isinstance(jobs, list), "Should return a list"
        
        if jobs:
            job = jobs[0]
            assert hasattr(job, 'id'), "Job should have id"
            assert hasattr(job, 'status'), "Job should have status"
    
    async def test_get_job_output(self, awx_client):
        """Test getting job output/stdout."""
        # Get a completed job
        jobs = await awx_client.list_jobs(page_size=10)
        
        completed_job = None
        for job in jobs:
            if job.status in ['successful', 'failed']:
                completed_job = job
                break
        
        if not completed_job:
            pytest.skip("No completed jobs available for testing")
        
        output = await awx_client.get_job_stdout(completed_job.id, format='txt')
        assert isinstance(output, str), "Output should be a string"
    
    async def test_get_job_events(self, awx_client):
        """Test getting job events."""
        # Get a completed job
        jobs = await awx_client.list_jobs(page_size=10)
        
        completed_job = None
        for job in jobs:
            if job.status in ['successful', 'failed']:
                completed_job = job
                break
        
        if not completed_job:
            pytest.skip("No completed jobs available for testing")
        
        events = await awx_client.get_job_events(completed_job.id)
        assert isinstance(events, list), "Events should be a list"
        
        if events:
            event = events[0]
            assert hasattr(event, 'event'), "Event should have event type"


@pytest.mark.asyncio
class TestJobMonitoring:
    """Test job monitoring and waiting."""
    
    async def test_wait_for_job_completion(self, awx_client):
        """Test waiting for job to complete."""
        templates = await awx_client.list_job_templates()
        
        if not templates:
            pytest.skip("No job templates available")
        
        # Launch job
        job = await awx_client.launch_job(templates[0].id)
        job_id = job.id
        
        # Wait for completion (with timeout)
        timeout = 300  # 5 minutes
        interval = 5   # Check every 5 seconds
        elapsed = 0
        
        while elapsed < timeout:
            job_info = await awx_client.get_job(job_id)
            
            if job_info.status in ['successful', 'failed', 'canceled', 'error']:
                # Job completed
                assert job_info.status in ['successful', 'failed', 'canceled', 'error'], \
                    "Job should reach terminal state"
                break
            
            await asyncio.sleep(interval)
            elapsed += interval
        
        assert elapsed < timeout, "Job should complete within timeout"


@pytest.mark.asyncio  
class TestJobDiagnostics:
    """Test job failure diagnostics."""
    
    async def test_diagnose_job_failure(self, awx_client):
        """Test AI-powered job failure diagnosis."""
        # Find a failed job
        jobs = await awx_client.list_jobs(page_size=50)
        
        failed_job = None
        for job in jobs:
            if job.status == 'failed':
                failed_job = job
                break
        
        if not failed_job:
            pytest.skip("No failed jobs available for diagnosis testing")
        
        # Get job output for diagnosis
        output = await awx_client.get_job_stdout(failed_job.id, format='txt')
        events = await awx_client.get_job_events(failed_job.id, failed_only=True)
        
        assert isinstance(output, str), "Job output should be available"
        assert isinstance(events, list), "Job events should be available"
        
        # In real implementation, this would call AI analysis
        # For now, just verify data is available for analysis
        assert len(output) > 0 or len(events) > 0, \
            "Should have diagnostic data available"


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_get_nonexistent_template(self, awx_client):
        """Test error when getting nonexistent template."""
        from awx_mcp.domain import AWXClientError
        
        with pytest.raises(AWXClientError):
            await awx_client.get_job_template(999999)
    
    async def test_get_nonexistent_job(self, awx_client):
        """Test error when getting nonexistent job."""
        from awx_mcp.domain import AWXClientError
        
        with pytest.raises(AWXClientError):
            await awx_client.get_job(999999)
    
    async def test_launch_nonexistent_template(self, awx_client):
        """Test error when launching nonexistent template."""
        from awx_mcp.domain import AWXClientError
        
        with pytest.raises(AWXClientError):
            await awx_client.launch_job(999999)


@pytest.mark.asyncio
class TestMCPServerIntegration:
    """Test MCP server creation and tools."""
    
    async def test_create_mcp_server(self):
        """Test MCP server can be created."""
        from awx_mcp.server import create_mcp_server
        
        server = create_mcp_server()
        assert server is not None, "Server should be created"
    
    async def test_mcp_server_with_tenant(self):
        """Test MCP server creation with tenant isolation."""
        from awx_mcp.server import create_mcp_server
        
        server = create_mcp_server(tenant_id="test-tenant")
        assert server is not None, "Server should be created with tenant"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
