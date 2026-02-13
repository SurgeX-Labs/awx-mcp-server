"""MCP Server implementation for AWX integration."""

import asyncio
import os
from typing import Any, Optional
from uuid import uuid4

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
        """Get client for active environment, falling back to environment variables if no config exists."""
        try:
            # Try to get stored environment
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
            
        except (NoActiveEnvironmentError, Exception) as e:
            # Fall back to environment variables
            logger.info(f"No stored environment found, checking environment variables: {e}")
            
            awx_base_url = os.getenv("AWX_BASE_URL")
            awx_token = os.getenv("AWX_TOKEN")
            awx_username = os.getenv("AWX_USERNAME")
            awx_password = os.getenv("AWX_PASSWORD")
            awx_verify_ssl = os.getenv("AWX_VERIFY_SSL", "true").lower() == "true"
            
            # Debug logging
            logger.info(f"Environment variables: AWX_BASE_URL={awx_base_url}, AWX_TOKEN={'*' * 10 if awx_token else None}, AWX_USERNAME={awx_username}, AWX_VERIFY_SSL={awx_verify_ssl}")
            
            if not awx_base_url:
                raise NoActiveEnvironmentError(
                    "No active environment configured and AWX_BASE_URL environment variable not set"
                )
            
            # Create temporary environment from env vars
            temp_env = EnvironmentConfig(
                env_id=uuid4(),
                name="default",
                base_url=awx_base_url,
                verify_ssl=awx_verify_ssl,
                is_default=True,
                allowed_job_templates=[],
                allowed_inventories=[]
            )
            
            # Determine auth method
            if awx_token:
                logger.info("Using AWX_TOKEN from environment variables")
                client = CompositeAWXClient(temp_env, "", awx_token, is_token=True)
            elif awx_username and awx_password:
                logger.info("Using AWX_USERNAME/AWX_PASSWORD from environment variables")
                client = CompositeAWXClient(temp_env, awx_username, awx_password, is_token=False)
            else:
                raise NoActiveEnvironmentError(
                    "No active environment configured and neither AWX_TOKEN nor AWX_USERNAME/AWX_PASSWORD set"
                )
            
            return temp_env, client


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
        # System Info
        Tool(
            name="awx_system_info",
            description="Get AWX system information (config, dashboard, settings)",
            inputSchema={
                "type": "object",
                "properties": {
                    "info_type": {
                        "type": "string",
                        "description": "Type of info: config, dashboard, settings, me",
                        "enum": ["config", "dashboard", "settings", "me"],
                    },
                },
                "required": ["info_type"],
            },
        ),
        # Organizations
        Tool(
            name="awx_organizations_list",
            description="List AWX organizations",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter organizations by name"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_organization_get",
            description="Get AWX organization by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "number", "description": "Organization ID"},
                },
                "required": ["org_id"],
            },
        ),
        # Credentials
        Tool(
            name="awx_credentials_list",
            description="List AWX credentials",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter credentials by name"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_credential_types_list",
            description="List AWX credential types",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_credential_create",
            description="Create AWX credential",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Credential name"},
                    "credential_type": {"type": "number", "description": "Credential type ID"},
                    "organization": {"type": "number", "description": "Organization ID"},
                    "inputs": {"type": "object", "description": "Credential inputs (e.g., username, password)"},
                    "description": {"type": "string", "description": "Credential description"},
                },
                "required": ["name", "credential_type", "organization", "inputs"],
            },
        ),
        Tool(
            name="awx_credential_delete",
            description="Delete AWX credential",
            inputSchema={
                "type": "object",
                "properties": {
                    "credential_id": {"type": "number", "description": "Credential ID"},
                },
                "required": ["credential_id"],
            },
        ),
        # Discovery
        Tool(
            name="awx_templates_list",
            description="List AWX job templates (NOT for recent jobs or job history). Templates are playbook definitions, configurations, settings. This shows available templates to run, not execution history or recent activity. For recent jobs/runs/executions, use awx_jobs_list instead.",
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
            name="awx_template_create",
            description="Create AWX job template",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Template name"},
                    "inventory": {"type": "number", "description": "Inventory ID"},
                    "project": {"type": "number", "description": "Project ID"},
                    "playbook": {"type": "string", "description": "Playbook filename"},
                    "job_type": {"type": "string", "description": "Job type (run or check)", "enum": ["run", "check"]},
                    "description": {"type": "string", "description": "Template description"},
                    "extra_vars": {"type": "object", "description": "Extra variables"},
                    "limit": {"type": "string", "description": "Host limit pattern"},
                },
                "required": ["name", "inventory", "project", "playbook"],
            },
        ),
        Tool(
            name="awx_template_delete",
            description="Delete AWX job template",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "number", "description": "Template ID"},
                },
                "required": ["template_id"],
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
            name="awx_project_create",
            description="Create AWX project",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "organization": {"type": "number", "description": "Organization ID"},
                    "scm_type": {"type": "string", "description": "SCM type (git, svn, etc.)", "enum": ["git", "svn", "insights", "archive", ""]},
                    "scm_url": {"type": "string", "description": "SCM repository URL"},
                    "scm_branch": {"type": "string", "description": "SCM branch/tag/commit"},
                    "description": {"type": "string", "description": "Project description"},
                },
                "required": ["name", "organization"],
            },
        ),
        Tool(
            name="awx_project_delete",
            description="Delete AWX project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "number", "description": "Project ID"},
                },
                "required": ["project_id"],
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
            name="awx_inventory_create",
            description="Create AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Inventory name"},
                    "organization": {"type": "number", "description": "Organization ID"},
                    "description": {"type": "string", "description": "Inventory description"},
                    "variables": {"type": "object", "description": "Inventory variables"},
                },
                "required": ["name", "organization"],
            },
        ),
        Tool(
            name="awx_inventory_delete",
            description="Delete AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "inventory_id": {"type": "number", "description": "Inventory ID"},
                },
                "required": ["inventory_id"],
            },
        ),
        Tool(
            name="awx_inventory_groups_list",
            description="List groups in AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "inventory_id": {"type": "number", "description": "Inventory ID"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
                "required": ["inventory_id"],
            },
        ),
        Tool(
            name="awx_inventory_group_create",
            description="Create group in AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "inventory_id": {"type": "number", "description": "Inventory ID"},
                    "name": {"type": "string", "description": "Group name"},
                    "description": {"type": "string", "description": "Group description"},
                    "variables": {"type": "object", "description": "Group variables"},
                },
                "required": ["inventory_id", "name"],
            },
        ),
        Tool(
            name="awx_inventory_group_delete",
            description="Delete group from AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {"type": "number", "description": "Group ID"},
                },
                "required": ["group_id"],
            },
        ),
        Tool(
            name="awx_inventory_hosts_list",
            description="List hosts in AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "inventory_id": {"type": "number", "description": "Inventory ID"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
                "required": ["inventory_id"],
            },
        ),
        Tool(
            name="awx_inventory_host_create",
            description="Create host in AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "inventory_id": {"type": "number", "description": "Inventory ID"},
                    "name": {"type": "string", "description": "Host name"},
                    "description": {"type": "string", "description": "Host description"},
                    "variables": {"type": "object", "description": "Host variables"},
                },
                "required": ["inventory_id", "name"],
            },
        ),
        Tool(
            name="awx_inventory_host_delete",
            description="Delete host from AWX inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_id": {"type": "number", "description": "Host ID"},
                },
                "required": ["host_id"],
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
            description="Launch/execute/run/start a new AWX job from a template. Creates a new job execution instance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "number", "description": "Job template ID to execute"},
                    "extra_vars": {"type": "object", "description": "Extra variables (JSON) to pass to playbook"},
                    "limit": {"type": "string", "description": "Limit execution to specific hosts"},
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
            description="Get specific AWX job metadata and summary details including status, timing, template info, and playbook name. Use this to check a single job's current state, whether it succeeded or failed, and its start/finish times. Does NOT return console output or logs — use awx_job_stdout for that.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID from job execution"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_jobs_list",
            description="Show/list/display/view recent AWX jobs, job execution history, completed jobs, running jobs, failed jobs, job status, job runs, playbook executions. Use this when user asks to 'show recent jobs', 'list jobs', 'view jobs', 'get jobs', 'display job history', 'see recent activity', 'check job status', or any query about AWX job executions with timestamps and results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (successful, failed, running, etc.)"},
                    "created_after": {"type": "string", "description": "Filter by created date (ISO format)"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 25)"},
                },
            },
        ),
        Tool(
            name="awx_job_cancel",
            description="Cancel/stop/abort a currently running AWX job execution. Use this when user asks to 'cancel job', 'stop job', 'abort job', 'kill job', or any request to halt a running job.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_job_delete",
            description="Delete/remove an AWX job record from history. Use this when user asks to 'delete job', 'remove job', 'clean up job', or any request to permanently remove a job record.",
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
            description="Show/display/view/get the console output, stdout, logs, or terminal output of an AWX job execution. Use this when user asks to 'show job output', 'view job logs', 'display console output', 'get job stdout', 'show what the job printed', 'see the playbook output', 'show execution log', or any request to see the text/log output produced by a job run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID to retrieve output for"},
                    "format": {
                        "type": "string",
                        "description": "Output format (txt or json)",
                        "enum": ["txt", "json"],
                    },
                    "tail_lines": {"type": "number", "description": "Number of lines from end (omit to get all output)"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_job_events",
            description="Show/list/view/get detailed events, tasks, plays, and execution steps of an AWX job. Use this when user asks to 'show job events', 'view job tasks', 'list execution steps', 'see what tasks ran', 'show detailed job activity', 'view play-by-play execution', or any request about the individual task/play events within a job run. Can filter to show only failed events.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID to retrieve events for"},
                    "failed_only": {"type": "boolean", "description": "Show only failed events (default: false)"},
                    "page": {"type": "number", "description": "Page number (default: 1)"},
                    "page_size": {"type": "number", "description": "Page size (default: 100)"},
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="awx_job_failure_summary",
            description="Analyze/diagnose/debug/troubleshoot why an AWX job failed and get actionable fix suggestions. Use this when user asks 'why did job fail', 'analyze failure', 'debug job error', 'show failure summary', 'what went wrong with job', 'diagnose job problem', 'troubleshoot job', or any request to understand and fix a failed job execution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "number", "description": "Job ID of the failed job to analyze"},
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
            
            # System Info
            elif name == "awx_system_info":
                env, client = get_active_client()
                info_type = arguments["info_type"]
                
                async with client:
                    if info_type == "config":
                        data = await client.rest_client.get_config()
                        result = "AWX System Configuration:\n\n"
                        for key, value in data.items():
                            result += f"{key}: {value}\n"
                    elif info_type == "dashboard":
                        data = await client.rest_client.get_dashboard()
                        result = "AWX Dashboard:\n\n"
                        for key, value in data.items():
                            result += f"{key}: {value}\n"
                    elif info_type == "settings":
                        data = await client.rest_client.get_settings()
                        result = "AWX Settings:\n\n"
                        for key, value in data.items():
                            result += f"{key}: {value}\n"
                    elif info_type == "me":
                        data = await client.rest_client.get_me()
                        result = "Current User Info:\n\n"
                        result += f"ID: {data.get('id')}\n"
                        result += f"Username: {data.get('username')}\n"
                        result += f"Email: {data.get('email', 'N/A')}\n"
                        result += f"First Name: {data.get('first_name', 'N/A')}\n"
                        result += f"Last Name: {data.get('last_name', 'N/A')}\n"
                        result += f"Is Superuser: {data.get('is_superuser', False)}\n"
                    
                return [TextContent(type="text", text=result)]
            
            # Organizations
            elif name == "awx_organizations_list":
                env, client = get_active_client()
                async with client:
                    orgs = await client.rest_client.list_organizations(
                        name_filter=arguments.get("filter"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Organizations ({len(orgs)}):\n\n"
                for org in orgs:
                    result += f"ID: {org['id']} - {org['name']}\n"
                    if org.get('description'):
                        result += f"  Description: {org['description']}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_organization_get":
                env, client = get_active_client()
                org_id = arguments["org_id"]
                
                async with client:
                    org = await client.rest_client.get_organization(org_id)
                
                result = f"Organization {org_id}:\n\n"
                result += f"Name: {org['name']}\n"
                if org.get('description'):
                    result += f"Description: {org['description']}\n"
                result += f"ID: {org['id']}\n"
                
                return [TextContent(type="text", text=result)]
            
            # Credentials
            elif name == "awx_credentials_list":
                env, client = get_active_client()
                async with client:
                    creds = await client.rest_client.list_credentials(
                        name_filter=arguments.get("filter"),
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Credentials ({len(creds)}):\n\n"
                for cred in creds:
                    result += f"ID: {cred['id']} - {cred['name']}\n"
                    if cred.get('description'):
                        result += f"  Description: {cred['description']}\n"
                    result += f"  Type: {cred.get('credential_type')}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_credential_types_list":
                env, client = get_active_client()
                async with client:
                    types = await client.rest_client.list_credential_types(
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Credential Types ({len(types)}):\n\n"
                for ctype in types:
                    result += f"ID: {ctype['id']} - {ctype['name']}\n"
                    if ctype.get('description'):
                        result += f"  Description: {ctype['description']}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_credential_create":
                env, client = get_active_client()
                async with client:
                    cred = await client.rest_client.create_credential(
                        name=arguments["name"],
                        credential_type=arguments["credential_type"],
                        organization=arguments["organization"],
                        inputs=arguments["inputs"],
                        description=arguments.get("description", ""),
                    )
                
                result = f"✓ Credential created successfully\n\n"
                result += f"ID: {cred['id']}\n"
                result += f"Name: {cred['name']}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_credential_delete":
                env, client = get_active_client()
                cred_id = arguments["credential_id"]
                
                async with client:
                    await client.rest_client.delete_credential(cred_id)
                
                return [TextContent(type="text", text=f"Credential {cred_id} deleted successfully")]
            
            # Templates CRUD
            elif name == "awx_template_create":
                env, client = get_active_client()
                async with client:
                    template = await client.rest_client.create_job_template(
                        name=arguments["name"],
                        inventory=arguments["inventory"],
                        project=arguments["project"],
                        playbook=arguments["playbook"],
                        job_type=arguments.get("job_type", "run"),
                        description=arguments.get("description", ""),
                        extra_vars=arguments.get("extra_vars"),
                        limit=arguments.get("limit"),
                    )
                
                result = f"✓ Job template created successfully\n\n"
                result += f"ID: {template.id}\n"
                result += f"Name: {template.name}\n"
                result += f"Playbook: {template.playbook}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_template_delete":
                env, client = get_active_client()
                template_id = arguments["template_id"]
                
                async with client:
                    await client.rest_client.delete_job_template(template_id)
                
                return [TextContent(type="text", text=f"Job template {template_id} deleted successfully")]
            
            # Projects CRUD
            elif name == "awx_project_create":
                env, client = get_active_client()
                async with client:
                    project = await client.rest_client.create_project(
                        name=arguments["name"],
                        organization=arguments["organization"],
                        scm_type=arguments.get("scm_type", "git"),
                        scm_url=arguments.get("scm_url"),
                        scm_branch=arguments.get("scm_branch", "main"),
                        description=arguments.get("description", ""),
                    )
                
                result = f"✓ Project created successfully\n\n"
                result += f"ID: {project.id}\n"
                result += f"Name: {project.name}\n"
                if project.scm_url:
                    result += f"SCM: {project.scm_url}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_project_delete":
                env, client = get_active_client()
                project_id = arguments["project_id"]
                
                async with client:
                    await client.rest_client.delete_project(project_id)
                
                return [TextContent(type="text", text=f"Project {project_id} deleted successfully")]
            
            # Inventories CRUD
            elif name == "awx_inventory_create":
                env, client = get_active_client()
                async with client:
                    inventory = await client.rest_client.create_inventory(
                        name=arguments["name"],
                        organization=arguments["organization"],
                        description=arguments.get("description", ""),
                        variables=arguments.get("variables"),
                    )
                
                result = f"✓ Inventory created successfully\n\n"
                result += f"ID: {inventory.id}\n"
                result += f"Name: {inventory.name}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventory_delete":
                env, client = get_active_client()
                inventory_id = arguments["inventory_id"]
                
                async with client:
                    await client.rest_client.delete_inventory(inventory_id)
                
                return [TextContent(type="text", text=f"Inventory {inventory_id} deleted successfully")]
            
            # Inventory Groups
            elif name == "awx_inventory_groups_list":
                env, client = get_active_client()
                inventory_id = arguments["inventory_id"]
                
                async with client:
                    groups = await client.rest_client.list_inventory_groups(
                        inventory_id=inventory_id,
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Inventory {inventory_id} Groups ({len(groups)}):\n\n"
                for group in groups:
                    result += f"ID: {group['id']} - {group['name']}\n"
                    if group.get('description'):
                        result += f"  Description: {group['description']}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventory_group_create":
                env, client = get_active_client()
                inventory_id = arguments["inventory_id"]
                
                async with client:
                    group = await client.rest_client.create_inventory_group(
                        inventory_id=inventory_id,
                        name=arguments["name"],
                        description=arguments.get("description", ""),
                        variables=arguments.get("variables"),
                    )
                
                result = f"✓ Group created successfully\n\n"
                result += f"ID: {group['id']}\n"
                result += f"Name: {group['name']}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventory_group_delete":
                env, client = get_active_client()
                group_id = arguments["group_id"]
                
                async with client:
                    await client.rest_client.delete_inventory_group(group_id)
                
                return [TextContent(type="text", text=f"Group {group_id} deleted successfully")]
            
            # Inventory Hosts
            elif name == "awx_inventory_hosts_list":
                env, client = get_active_client()
                inventory_id = arguments["inventory_id"]
                
                async with client:
                    hosts = await client.rest_client.list_inventory_hosts(
                        inventory_id=inventory_id,
                        page=arguments.get("page", 1),
                        page_size=arguments.get("page_size", 25),
                    )
                
                result = f"Inventory {inventory_id} Hosts ({len(hosts)}):\n\n"
                for host in hosts:
                    result += f"ID: {host['id']} - {host['name']}\n"
                    if host.get('description'):
                        result += f"  Description: {host['description']}\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventory_host_create":
                env, client = get_active_client()
                inventory_id = arguments["inventory_id"]
                
                async with client:
                    host = await client.rest_client.create_inventory_host(
                        inventory_id=inventory_id,
                        name=arguments["name"],
                        description=arguments.get("description", ""),
                        variables=arguments.get("variables"),
                    )
                
                result = f"✓ Host created successfully\n\n"
                result += f"ID: {host['id']}\n"
                result += f"Name: {host['name']}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "awx_inventory_host_delete":
                env, client = get_active_client()
                host_id = arguments["host_id"]
                
                async with client:
                    await client.rest_client.delete_inventory_host(host_id)
                
                return [TextContent(type="text", text=f"Host {host_id} deleted successfully")]
            
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
            
            elif name == "awx_job_delete":
                env, client = get_active_client()
                job_id = arguments["job_id"]
                
                async with client:
                    await client.delete_job(job_id)
                
                return [TextContent(type="text", text=f"Job {job_id} deleted successfully")]
            
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
