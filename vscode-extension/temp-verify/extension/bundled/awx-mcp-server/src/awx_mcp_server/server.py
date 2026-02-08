"""MCP Server implementation for AWX integration."""

import asyncio
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import (
    AllowlistViolationError,
    AuditLog,
    CredentialType,
    EnvironmentConfig,
    NoActiveEnvironmentError,
)
from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.utils import analyze_job_failure, configure_logging, get_logger

# Initialize logging
configure_logging()
logger = get_logger(__name__)


def create_mcp_server(tenant_id: Optional[str] = None) -> Server:
    """
    Create MCP server instance.
    
    Args:
        tenant_id: Tenant ID for multi-tenant isolation (optional)
    
    Returns:
        Configured MCP Server instance
    """
    # Create MCP server
    mcp_server = Server("awx-mcp-server")
    
    # Initialize storage with tenant context
    config_manager = ConfigManager(tenant_id=tenant_id)
    credential_store = CredentialStore(tenant_id=tenant_id)


    def get_active_client() -> tuple[EnvironmentConfig, CompositeAWXClient]:
        """Get client for active environment."""
        env = config_manager.get_active()
        
        # Determine credential type
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
            is_token = False
        except Exception:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        
        client = CompositeAWXClient(env, username, secret, is_token)
        return env, client


    def check_allowlist(env: EnvironmentConfig, template_id: int, template_name: str) -> None:
        """Check if template is in allowlist."""
        if env.allowed_job_templates and template_name not in env.allowed_job_templates:
            raise AllowlistViolationError(
                f"Template '{template_name}' not in allowlist for environment '{env.name}'"
            )

    # Environment Management Tools

    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            # Environment Management
            Tool(
                name="env_list",
            description="List all configured AWX environments",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="env_set_active",
            description="Set the active AWX environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "env_name": {"type": "string", "description": "Environment name"},
                },
                "required": ["env_name"],
            },
        ),
        Tool(
            name="env_get_active",
            description="Get the currently active AWX environment",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="env_test_connection",
            description="Test connection to an AWX environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "env_name": {
                        "type": "string",
                        "description": "Environment name (optional, uses active if not specified)",
                    },
                },
            },
        ),
        # Discovery
        Tool(
            name="awx_templates_list",
            description="List AWX job templates",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter templates by name"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_projects_list",
            description="List AWX projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter projects by name"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_inventories_list",
            description="List AWX inventories",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter inventories by name"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_project_update",
            description="Update AWX project from SCM",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "number", "description": "Project ID"},
                    "wait": {"type": "boolean", "description": "Wait for update to complete"},
                },
                "required": ["project_id"],
            },
        ),
        # Execution
        Tool(
            name="awx_job_launch",
            description="Launch an AWX job from template",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "number", "description": "Job template ID"},
                    "extra_vars": {"type": "object", "description": "Extra variables (JSON)"},
                    "limit": {"type": "string", "description": "Limit hosts"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ansible tags to run",
                    },
                    "skip_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ansible tags to skip",
                    },
                },
                "required": ["template_id"],
            },
        ),
        Tool(
            name="awx_job_get",
            description="Get AWX job status and details",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_jobs_list",
            description="List AWX jobs",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status"},
                    "created_after": {"type": "string", "description": "Filter by created date"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_job_cancel",
            description="Cancel a running AWX job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                },
                "required": ["job_id"],
            },
        ),
        # Diagnostics
        Tool(
            name="awx_job_stdout",
            description="Get AWX job stdout/output",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                    "format": {
                        "type": "string",
                        "description": "Output format (txt or json)",
                        "enum": ["txt", "json"],
                    },
                    "tail_lines": {"type": "number", "description": "Number of lines from end"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_job_events",
            description="Get AWX job events",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                    "failed_only": {"type": "boolean", "description": "Show only failed events"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 100)"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_job_failure_summary",
            description="Analyze job failure and get actionable suggestions",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                },
                "required": ["job_id"],
            },
        ),
    ]


    @mcp_server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls."""
        try:
            logger.info("tool_call", tool=name, arguments=arguments)
            
            if name == "env_list":
                envs = config_manager.list_environments()
                active_name = config_manager.get_active_name()
                
                result = "Configured AWX Environments:\n\n"
                for env in envs:
                    marker = "* " if env.name == active_name else "  "
                    result += f"{marker}{env.name}\n"
                    result += f"  URL: {env.base_url}\n"
                    result += f"  SSL Verify: {env.verify_ssl}\n"
                    if env.default_organization:
                        result += f"  Default Org: {env.default_organization}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "env_set_active":
                env_name = arguments["env_name"]
                config_manager.set_active(env_name)
                return [TextContent(type="text", text=f"Active environment set to: {env_name}")]
            
            elif name == "env_get_active":
                try:
                    env = config_manager.get_active()
                    return [TextContent(type="text", text=f"Active environment: {env.name}")]
                except NoActiveEnvironmentError:
                    return [TextContent(type="text", text="No active environment set")]
            
            elif name == "env_test_connection":
                env_name = arguments.get("env_name")
                
                if env_name:
                    env = config_manager.get_environment(env_name)
                    try:
                        username, secret = credential_store.get_credential(
                            env.env_id, CredentialType.PASSWORD
                        )
                        is_token = False
                    except Exception:
                        username, secret = credential_store.get_credential(
                            env.env_id, CredentialType.TOKEN
                        )
                        is_token = True
                    
                    client = CompositeAWXClient(env, username, secret, is_token)
                else:
                    env, client = get_active_client()
                
                async with client:
                    success = await client.test_connection()
                
                if success:
                    return [TextContent(type="text", text=f"✓ Connection successful to {env.name}")]
                else:
                    return [TextContent(type="text", text=f"✗ Connection failed to {env.name}")]
            
            elif name == "awx_templates_list":
                env, client = get_active_client()
                async with client:
                    templates = await client.list_job_templates(
                        name_filter=arguments.get("filter"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Job Templates ({len(templates)}):\n\n"
                for tmpl in templates:
                    result += f"ID: {tmpl.id} - {tmpl.name}\n"
                    if tmpl.description:
                        result += f"  Description: {tmpl.description}\n"
                    result += f"  Playbook: {tmpl.playbook}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_projects_list":
                env, client = get_active_client()
                async with client:
                    projects = await client.list_projects(
                        name_filter=arguments.get("filter"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Projects ({len(projects)}):\n\n"
                for proj in projects:
                    result += f"ID: {proj.id} - {proj.name}\n"
                    if proj.description:
                        result += f"  Description: {proj.description}\n"
                    if proj.scm_url:
                        result += f"  SCM: {proj.scm_type} - {proj.scm_url}\n"
                    if proj.scm_branch:
                        result += f"  Branch: {proj.scm_branch}\n"
                    result += f"  Status: {proj.status}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventories_list":
                env, client = get_active_client()
                async with client:
                    inventories = await client.list_inventories(
                        name_filter=arguments.get("filter"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Inventories ({len(inventories)}):\n\n"
                for inv in inventories:
                    result += f"ID: {inv.id} - {inv.name}\n"
                    if inv.description:
                        result += f"  Description: {inv.description}\n"
                    result += f"  Total Hosts: {inv.total_hosts}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_project_update":
                env, client = get_active_client()
                project_id = arguments["project_id"]
                wait = arguments.get("wait", True)
                
                async with client:
                    result_data = await client.update_project(project_id, wait)
                
                return [
                    TextContent(
                        type="text",
                        text=f"Project {project_id} update initiated. Result: {result_data}",
                    )
                ]
            
            elif name == "awx_job_launch":
                env, client = get_active_client()
                template_id = arguments["template_id"]
                
                # Get template to check allowlist
                async with client:
                    template = await client.get_job_template(template_id)
                    check_allowlist(env, template_id, template.name)
                    
                    job = await client.launch_job(
                        template_id=template_id,
                        extra_vars=arguments.get("extra_vars"),
                        limit=arguments.get("limit"),
                        tags=arguments.get("tags"),
                        skip_tags=arguments.get("skip_tags"),
                    )
                
                # Audit log
                logger.info(
                    "job_launched",
                    environment=env.name,
                    template=template.name,
                    job_id=job.id,
                )
                
                result = f"✓ Job launched successfully\n\n"
                result += f"Job ID: {job.id}\n"
                result += f"Name: {job.name}\n"
                result += f"Status: {job.status.value}\n"
                result += f"Playbook: {job.playbook}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_job_get":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                
                async with client:
                    job = await client.get_job(job_id)
                
                result = f"Job {job_id} Details:\n\n"
                result += f"Name: {job.name}\n"
                result += f"Status: {job.status.value}\n"
                result += f"Playbook: {job.playbook}\n"
                if job.started:
                    result += f"Started: {job.started.isoformat()}\n"
                if job.finished:
                    result += f"Finished: {job.finished.isoformat()}\n"
                if job.elapsed:
                    result += f"Elapsed: {job.elapsed}s\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_jobs_list":
                env, client = get_active_client()
                
                async with client:
                    jobs = await client.list_jobs(
                        status=arguments.get("status"),
                        created_after=arguments.get("created_after"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Recent Jobs ({len(jobs)}):\n\n"
                for job in jobs:
                    result += f"ID: {job.id} - {job.name}\n"
                    result += f"  Status: {job.status.value}\n"
                    result += f"  Playbook: {job.playbook}\n"
                    if job.started:
                        result += f"  Started: {job.started.isoformat()}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_job_cancel":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                
                async with client:
                    result_data = await client.cancel_job(job_id)
                
                return [TextContent(type="text", text=f"Job {job_id} cancellation requested")]
            
            elif name == "awx_job_stdout":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                format = arguments.get("format", "txt")
                tail_lines = arguments.get("tail_lines")
                
                async with client:
                    stdout = await client.get_job_stdout(job_id, format, tail_lines)
                
                result = f"Job {job_id} Output:\n\n{stdout}"
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_job_events":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                failed_only = arguments.get("failed_only", False)
                
                async with client:
                    events = await client.get_job_events(
                        job_id=job_id,
                        failed_only=failed_only,
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 100),
                    )
                
                result = f"Job {job_id} Events ({len(events)}):\n\n"
                for event in events:
                    if event.task:
                        result += f"Task: {event.task}\n"
                    if event.host:
                        result += f"  Host: {event.host}\n"
                    result += f"  Event: {event.event}\n"
                    result += f"  Failed: {event.failed}\n"
                    if event.stdout:
                        result += f"  Output: {event.stdout[:200]}...\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_job_failure_summary":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                
                async with client:
                    # Get job events and stdout
                    events = await client.get_job_events(job_id, failed_only=True)
                    stdout = await client.get_job_stdout(job_id, "txt", 500)
                
                # Analyze failure
                analysis = analyze_job_failure(job_id, events, stdout)
                
                result = f"Job {job_id} Failure Analysis:\n\n"
                result += f"Category: {analysis.category.value}\n"
                result += f"Failed Events: {analysis.failed_events_count}\n\n"
                
                if analysis.task_name:
                    result += f"Failed Task: {analysis.task_name}\n"
                if analysis.play_name:
                    result += f"Play: {analysis.play_name}\n"
                if analysis.host:
                    result += f"Host: {analysis.host}\n"
                
                if analysis.error_message:
                    result += f"\nError Message:\n{analysis.error_message}\n"
                
                if analysis.suggested_fixes:
                    result += "\n🔧 Suggested Fixes:\n\n"
                    for i, fix in enumerate(analysis.suggested_fixes, 1):
                        result += f"{i}. {fix}\n"
                
                return [TextContent(type="text", text=result)]
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            logger.error("tool_error", tool=name, error=str(e))
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return mcp_server


async def main() -> None:
    """Run MCP server in stdio mode (for local VSCode integration)."""
    logger.info("starting_stdio_server")
    
    # Create server without tenant isolation for local use
    mcp_server = create_mcp_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
