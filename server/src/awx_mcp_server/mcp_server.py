"""MCP Server implementation for AWX integration.

Built on the modern MCP SDK (mcp>=2.0) high-level ``MCPServer`` API: each tool
is a typed async function registered with ``@mcp_server.tool``, and the input
schema is derived from the type hints. Tool names, descriptions, and text
output are unchanged from the pre-2.0 implementation.
"""

import asyncio
import functools
import inspect
import os
from typing import Any, Literal, Optional
from uuid import uuid4

from mcp.server import MCPServer

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
from awx_mcp_server import playbook_manager, project_registry

# Initialize logging
configure_logging()
logger = get_logger(__name__)


def create_mcp_server(tenant_id: Optional[str] = None) -> MCPServer:
    """
    Create MCP server instance.

    Args:
        tenant_id: Tenant ID for multi-tenant isolation (optional)

    Returns:
        Configured MCPServer instance
    """
    # Create MCP server
    mcp_server = MCPServer("awx-mcp-server")

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
            awx_platform = os.getenv("AWX_PLATFORM", "awx").lower()  # Default to AWX
            awx_verify_ssl = os.getenv("AWX_VERIFY_SSL", "true").lower() == "true"

            # Validate platform type
            from awx_mcp_server.domain import PlatformType
            try:
                platform_type = PlatformType(awx_platform)
            except ValueError:
                logger.warning(f"Invalid AWX_PLATFORM value '{awx_platform}', defaulting to 'awx'")
                platform_type = PlatformType.AWX

            # Debug logging
            logger.info(f"Environment variables: AWX_BASE_URL={awx_base_url}, AWX_PLATFORM={platform_type.value}, AWX_TOKEN={'*' * 10 if awx_token else None}, AWX_USERNAME={awx_username}, AWX_VERIFY_SSL={awx_verify_ssl}")

            if not awx_base_url:
                raise NoActiveEnvironmentError(
                    "No active environment configured and AWX_BASE_URL environment variable not set"
                )

            # Create temporary environment from env vars
            temp_env = EnvironmentConfig(
                env_id=uuid4(),
                name="default",
                base_url=awx_base_url,
                platform_type=platform_type,
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


    def tool_errors(func):
        """Log tool calls and turn exceptions into plain "Error: ..." text.

        This preserves the behavior of the pre-2.0 dispatcher, where any tool
        failure produced a normal text response rather than a protocol-level
        error. ``__signature__`` is copied so schema generation still sees the
        tool's real typed parameters through the wrapper.
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info("tool_call", tool=func.__name__, arguments=kwargs)
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("tool_error", tool=func.__name__, error=str(e))
                return f"Error: {str(e)}"
        wrapper.__signature__ = inspect.signature(func)
        return wrapper

    # Environment Management Tools

    @mcp_server.tool(name="env_list", description="List all configured AWX environments")
    @tool_errors
    async def env_list() -> str:
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

        return result

    @mcp_server.tool(name="env_set_active", description="Set the active AWX environment")
    @tool_errors
    async def env_set_active(env_name: str) -> str:
        config_manager.set_active(env_name)
        return f"Active environment set to: {env_name}"

    @mcp_server.tool(name="env_get_active", description="Get the currently active AWX environment")
    @tool_errors
    async def env_get_active() -> str:
        try:
            env = config_manager.get_active()
            return f"Active environment: {env.name}"
        except NoActiveEnvironmentError:
            return "No active environment set"

    @mcp_server.tool(name="env_test_connection", description="Test connection to an AWX environment")
    @tool_errors
    async def env_test_connection(env_name: str | None = None) -> str:
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
            return f"✓ Connection successful to {env.name}"
        else:
            return f"✗ Connection failed to {env.name}"

    # System Info

    @mcp_server.tool(
        name="awx_system_info",
        description="Get AWX system information (config, dashboard, settings)",
    )
    @tool_errors
    async def awx_system_info(info_type: Literal["config", "dashboard", "settings", "me"]) -> str:
        env, client = get_active_client()

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

        return result

    # Organizations

    @mcp_server.tool(name="awx_organizations_list", description="List AWX organizations")
    @tool_errors
    async def awx_organizations_list(
        filter: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()
        async with client:
            orgs = await client.rest_client.list_organizations(
                name_filter=filter,
                page=page,
                page_size=page_size,
            )

        result = f"Organizations ({len(orgs)}):\n\n"
        for org in orgs:
            result += f"ID: {org['id']} - {org['name']}\n"
            if org.get('description'):
                result += f"  Description: {org['description']}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_organization_get", description="Get AWX organization by ID")
    @tool_errors
    async def awx_organization_get(org_id: int) -> str:
        env, client = get_active_client()

        async with client:
            org = await client.rest_client.get_organization(org_id)

        result = f"Organization {org_id}:\n\n"
        result += f"Name: {org['name']}\n"
        if org.get('description'):
            result += f"Description: {org['description']}\n"
        result += f"ID: {org['id']}\n"

        return result

    # Credentials

    @mcp_server.tool(name="awx_credentials_list", description="List AWX credentials")
    @tool_errors
    async def awx_credentials_list(
        filter: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()
        async with client:
            creds = await client.rest_client.list_credentials(
                name_filter=filter,
                page=page,
                page_size=page_size,
            )

        result = f"Credentials ({len(creds)}):\n\n"
        for cred in creds:
            result += f"ID: {cred['id']} - {cred['name']}\n"
            if cred.get('description'):
                result += f"  Description: {cred['description']}\n"
            result += f"  Type: {cred.get('credential_type')}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_credential_types_list", description="List AWX credential types")
    @tool_errors
    async def awx_credential_types_list(page: int = 1, page_size: int = 25) -> str:
        env, client = get_active_client()
        async with client:
            types = await client.rest_client.list_credential_types(
                page=page,
                page_size=page_size,
            )

        result = f"Credential Types ({len(types)}):\n\n"
        for ctype in types:
            result += f"ID: {ctype['id']} - {ctype['name']}\n"
            if ctype.get('description'):
                result += f"  Description: {ctype['description']}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_credential_create", description="Create AWX credential")
    @tool_errors
    async def awx_credential_create(
        name: str,
        credential_type: int,
        organization: int,
        inputs: dict[str, Any],
        description: str = "",
    ) -> str:
        env, client = get_active_client()
        async with client:
            cred = await client.rest_client.create_credential(
                name=name,
                credential_type=credential_type,
                organization=organization,
                inputs=inputs,
                description=description,
            )

        result = f"✓ Credential created successfully\n\n"
        result += f"ID: {cred['id']}\n"
        result += f"Name: {cred['name']}\n"

        return result

    @mcp_server.tool(name="awx_credential_delete", description="Delete AWX credential")
    @tool_errors
    async def awx_credential_delete(credential_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_credential(credential_id)

        return f"Credential {credential_id} deleted successfully"

    # Discovery

    @mcp_server.tool(
        name="awx_templates_list",
        description="List AWX job templates (NOT for recent jobs or job history). Templates are playbook definitions, configurations, settings. This shows available templates to run, not execution history or recent activity. For recent jobs/runs/executions, use awx_jobs_list instead.",
    )
    @tool_errors
    async def awx_templates_list(
        filter: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()
        async with client:
            templates = await client.list_job_templates(
                name_filter=filter,
                page=page,
                page_size=page_size,
            )

        result = f"Job Templates ({len(templates)}):\n\n"
        for tmpl in templates:
            result += f"ID: {tmpl.id} - {tmpl.name}\n"
            if tmpl.description:
                result += f"  Description: {tmpl.description}\n"
            result += f"  Playbook: {tmpl.playbook}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_template_create", description="Create AWX job template")
    @tool_errors
    async def awx_template_create(
        name: str,
        inventory: int,
        project: int,
        playbook: str,
        job_type: Literal["run", "check"] = "run",
        description: str = "",
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
    ) -> str:
        env, client = get_active_client()
        async with client:
            template = await client.rest_client.create_job_template(
                name=name,
                inventory=inventory,
                project=project,
                playbook=playbook,
                job_type=job_type,
                description=description,
                extra_vars=extra_vars,
                limit=limit,
            )

        result = f"✓ Job template created successfully\n\n"
        result += f"ID: {template.id}\n"
        result += f"Name: {template.name}\n"
        result += f"Playbook: {template.playbook}\n"

        return result

    @mcp_server.tool(name="awx_template_delete", description="Delete AWX job template")
    @tool_errors
    async def awx_template_delete(template_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_job_template(template_id)

        return f"Job template {template_id} deleted successfully"

    @mcp_server.tool(name="awx_projects_list", description="List AWX projects")
    @tool_errors
    async def awx_projects_list(
        filter: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()
        async with client:
            projects = await client.list_projects(
                name_filter=filter,
                page=page,
                page_size=page_size,
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

        return result

    @mcp_server.tool(name="awx_project_create", description="Create AWX project")
    @tool_errors
    async def awx_project_create(
        name: str,
        organization: int,
        scm_type: Literal["git", "svn", "insights", "archive", ""] = "git",
        scm_url: str | None = None,
        scm_branch: str = "main",
        description: str = "",
    ) -> str:
        env, client = get_active_client()
        async with client:
            project = await client.rest_client.create_project(
                name=name,
                organization=organization,
                scm_type=scm_type,
                scm_url=scm_url,
                scm_branch=scm_branch,
                description=description,
            )

        result = f"✓ Project created successfully\n\n"
        result += f"ID: {project.id}\n"
        result += f"Name: {project.name}\n"
        if project.scm_url:
            result += f"SCM: {project.scm_url}\n"

        return result

    @mcp_server.tool(name="awx_project_delete", description="Delete AWX project")
    @tool_errors
    async def awx_project_delete(project_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_project(project_id)

        return f"Project {project_id} deleted successfully"

    @mcp_server.tool(name="awx_inventories_list", description="List AWX inventories")
    @tool_errors
    async def awx_inventories_list(
        filter: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()
        async with client:
            inventories = await client.list_inventories(
                name_filter=filter,
                page=page,
                page_size=page_size,
            )

        result = f"Inventories ({len(inventories)}):\n\n"
        for inv in inventories:
            result += f"ID: {inv.id} - {inv.name}\n"
            if inv.description:
                result += f"  Description: {inv.description}\n"
            result += f"  Total Hosts: {inv.total_hosts}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_inventory_create", description="Create AWX inventory")
    @tool_errors
    async def awx_inventory_create(
        name: str,
        organization: int,
        description: str = "",
        variables: dict[str, Any] | None = None,
    ) -> str:
        env, client = get_active_client()
        async with client:
            inventory = await client.rest_client.create_inventory(
                name=name,
                organization=organization,
                description=description,
                variables=variables,
            )

        result = f"✓ Inventory created successfully\n\n"
        result += f"ID: {inventory.id}\n"
        result += f"Name: {inventory.name}\n"

        return result

    @mcp_server.tool(name="awx_inventory_delete", description="Delete AWX inventory")
    @tool_errors
    async def awx_inventory_delete(inventory_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_inventory(inventory_id)

        return f"Inventory {inventory_id} deleted successfully"

    @mcp_server.tool(name="awx_inventory_groups_list", description="List groups in AWX inventory")
    @tool_errors
    async def awx_inventory_groups_list(
        inventory_id: int,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()

        async with client:
            groups = await client.rest_client.list_inventory_groups(
                inventory_id=inventory_id,
                page=page,
                page_size=page_size,
            )

        result = f"Inventory {inventory_id} Groups ({len(groups)}):\n\n"
        for group in groups:
            result += f"ID: {group['id']} - {group['name']}\n"
            if group.get('description'):
                result += f"  Description: {group['description']}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_inventory_group_create", description="Create group in AWX inventory")
    @tool_errors
    async def awx_inventory_group_create(
        inventory_id: int,
        name: str,
        description: str = "",
        variables: dict[str, Any] | None = None,
    ) -> str:
        env, client = get_active_client()

        async with client:
            group = await client.rest_client.create_inventory_group(
                inventory_id=inventory_id,
                name=name,
                description=description,
                variables=variables,
            )

        result = f"✓ Group created successfully\n\n"
        result += f"ID: {group['id']}\n"
        result += f"Name: {group['name']}\n"

        return result

    @mcp_server.tool(name="awx_inventory_group_delete", description="Delete group from AWX inventory")
    @tool_errors
    async def awx_inventory_group_delete(group_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_inventory_group(group_id)

        return f"Group {group_id} deleted successfully"

    @mcp_server.tool(name="awx_inventory_hosts_list", description="List hosts in AWX inventory")
    @tool_errors
    async def awx_inventory_hosts_list(
        inventory_id: int,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()

        async with client:
            hosts = await client.rest_client.list_inventory_hosts(
                inventory_id=inventory_id,
                page=page,
                page_size=page_size,
            )

        result = f"Inventory {inventory_id} Hosts ({len(hosts)}):\n\n"
        for host in hosts:
            result += f"ID: {host['id']} - {host['name']}\n"
            if host.get('description'):
                result += f"  Description: {host['description']}\n"
            result += "\n"

        return result

    @mcp_server.tool(name="awx_inventory_host_create", description="Create host in AWX inventory")
    @tool_errors
    async def awx_inventory_host_create(
        inventory_id: int,
        name: str,
        description: str = "",
        variables: dict[str, Any] | None = None,
    ) -> str:
        env, client = get_active_client()

        async with client:
            host = await client.rest_client.create_inventory_host(
                inventory_id=inventory_id,
                name=name,
                description=description,
                variables=variables,
            )

        result = f"✓ Host created successfully\n\n"
        result += f"ID: {host['id']}\n"
        result += f"Name: {host['name']}\n"

        return result

    @mcp_server.tool(name="awx_inventory_host_delete", description="Delete host from AWX inventory")
    @tool_errors
    async def awx_inventory_host_delete(host_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.rest_client.delete_inventory_host(host_id)

        return f"Host {host_id} deleted successfully"

    @mcp_server.tool(name="awx_project_update", description="Update AWX project from SCM")
    @tool_errors
    async def awx_project_update(project_id: int, wait: bool = True) -> str:
        env, client = get_active_client()

        async with client:
            result_data = await client.update_project(project_id, wait)

        return f"Project {project_id} update initiated. Result: {result_data}"

    # Execution

    @mcp_server.tool(
        name="awx_job_launch",
        description="Launch/execute/run/start a new AWX job from a template. Creates a new job execution instance.",
    )
    @tool_errors
    async def awx_job_launch(
        template_id: int,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: list[str] | None = None,
        skip_tags: list[str] | None = None,
    ) -> str:
        env, client = get_active_client()

        # Get template to check allowlist
        async with client:
            template = await client.get_job_template(template_id)
            check_allowlist(env, template_id, template.name)

            job = await client.launch_job(
                template_id=template_id,
                extra_vars=extra_vars,
                limit=limit,
                tags=tags,
                skip_tags=skip_tags,
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

        return result

    @mcp_server.tool(
        name="awx_job_get",
        description="Get specific AWX job metadata and summary details including status, timing, template info, and playbook name. Use this to check a single job's current state, whether it succeeded or failed, and its start/finish times. Does NOT return console output or logs — use awx_job_stdout for that.",
    )
    @tool_errors
    async def awx_job_get(job_id: int) -> str:
        env, client = get_active_client()

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

        return result

    @mcp_server.tool(
        name="awx_jobs_list",
        description="Show/list/display/view recent AWX jobs, job execution history, completed jobs, running jobs, failed jobs, job status, job runs, playbook executions. Use this when user asks to 'show recent jobs', 'list jobs', 'view jobs', 'get jobs', 'display job history', 'see recent activity', 'check job status', or any query about AWX job executions with timestamps and results.",
    )
    @tool_errors
    async def awx_jobs_list(
        status: str | None = None,
        created_after: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> str:
        env, client = get_active_client()

        async with client:
            jobs = await client.list_jobs(
                status=status,
                created_after=created_after,
                page=page,
                page_size=page_size,
            )

        result = f"Recent Jobs ({len(jobs)}):\n\n"
        for job in jobs:
            result += f"ID: {job.id} - {job.name}\n"
            result += f"  Status: {job.status.value}\n"
            result += f"  Playbook: {job.playbook}\n"
            if job.started:
                result += f"  Started: {job.started.isoformat()}\n"
            result += "\n"

        return result

    @mcp_server.tool(
        name="awx_job_cancel",
        description="Cancel/stop/abort a currently running AWX job execution. Use this when user asks to 'cancel job', 'stop job', 'abort job', 'kill job', or any request to halt a running job.",
    )
    @tool_errors
    async def awx_job_cancel(job_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.cancel_job(job_id)

        return f"Job {job_id} cancellation requested"

    @mcp_server.tool(
        name="awx_job_delete",
        description="Delete/remove an AWX job record from history. Use this when user asks to 'delete job', 'remove job', 'clean up job', or any request to permanently remove a job record.",
    )
    @tool_errors
    async def awx_job_delete(job_id: int) -> str:
        env, client = get_active_client()

        async with client:
            await client.delete_job(job_id)

        return f"Job {job_id} deleted successfully"

    # Diagnostics

    @mcp_server.tool(
        name="awx_job_stdout",
        description="Show/display/view/get the console output, stdout, logs, or terminal output of an AWX job execution. Use this when user asks to 'show job output', 'view job logs', 'display console output', 'get job stdout', 'show what the job printed', 'see the playbook output', 'show execution log', or any request to see the text/log output produced by a job run.",
    )
    @tool_errors
    async def awx_job_stdout(
        job_id: int,
        format: Literal["txt", "json"] = "txt",
        tail_lines: int | None = None,
    ) -> str:
        env, client = get_active_client()

        async with client:
            stdout = await client.get_job_stdout(job_id, format, tail_lines)

        return f"Job {job_id} Output:\n\n{stdout}"

    @mcp_server.tool(
        name="awx_job_events",
        description="Show/list/view/get detailed events, tasks, plays, and execution steps of an AWX job. Use this when user asks to 'show job events', 'view job tasks', 'list execution steps', 'see what tasks ran', 'show detailed job activity', 'view play-by-play execution', or any request about the individual task/play events within a job run. Can filter to show only failed events.",
    )
    @tool_errors
    async def awx_job_events(
        job_id: int,
        failed_only: bool = False,
        page: int = 1,
        page_size: int = 100,
    ) -> str:
        env, client = get_active_client()

        async with client:
            events = await client.get_job_events(
                job_id=job_id,
                failed_only=failed_only,
                page=page,
                page_size=page_size,
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

        return result

    @mcp_server.tool(
        name="awx_job_failure_summary",
        description="Analyze/diagnose/debug/troubleshoot why an AWX job failed and get actionable fix suggestions. Use this when user asks 'why did job fail', 'analyze failure', 'debug job error', 'show failure summary', 'what went wrong with job', 'diagnose job problem', 'troubleshoot job', or any request to understand and fix a failed job execution.",
    )
    @tool_errors
    async def awx_job_failure_summary(job_id: int) -> str:
        env, client = get_active_client()

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

        return result

    # ── Local Ansible Development Tools ──

    @mcp_server.tool(
        name="create_playbook",
        description="Create/write/generate an Ansible playbook YAML file locally. Use this when user asks to 'create a playbook', 'write a playbook', 'generate a playbook', 'make a new playbook', or wants to author Ansible YAML content before running it on AWX.",
    )
    @tool_errors
    async def create_playbook(
        name: str,
        content: str | dict[str, Any] | list[Any],
        workspace: str | None = None,
        overwrite: bool = False,
    ) -> str:
        pb_result = playbook_manager.create_playbook(
            name=name,
            content=content,
            workspace=workspace,
            overwrite=overwrite,
        )
        if pb_result["status"] == "created":
            result = f"✅ Playbook created: {pb_result['name']}\n"
            result += f"Path: {pb_result['path']}\n"
            result += f"Plays: {pb_result['plays']}\n\n"
            result += f"Preview:\n```yaml\n{pb_result['preview']}\n```"
        else:
            result = f"❌ {pb_result['message']}"
        return result

    @mcp_server.tool(
        name="validate_playbook",
        description="Validate/check/lint Ansible playbook syntax using ansible-playbook --syntax-check. Use this when user asks to 'validate playbook', 'check playbook syntax', 'lint playbook', 'verify playbook', or wants to ensure a playbook is syntactically correct before running it.",
    )
    @tool_errors
    async def validate_playbook(
        playbook: str,
        workspace: str | None = None,
        inventory: str | None = None,
    ) -> str:
        val_result = await playbook_manager.validate_playbook(
            playbook=playbook,
            workspace=workspace,
            inventory=inventory,
        )
        if val_result["status"] == "valid":
            result = f"✅ Playbook syntax is valid: {val_result['playbook']}\n"
            if val_result.get("output"):
                result += f"\n{val_result['output']}"
        elif val_result["status"] == "invalid":
            result = f"❌ Playbook has syntax errors: {val_result['playbook']}\n\n"
            result += f"Errors:\n{val_result['errors']}"
        else:
            result = f"❌ {val_result['message']}"
        return result

    @mcp_server.tool(
        name="ansible_playbook",
        description="Execute/run an Ansible playbook locally for development and testing. Use this when user asks to 'run playbook locally', 'execute playbook', 'test playbook', 'dry-run playbook', or wants to run a playbook in their dev environment before pushing to AWX. Supports check mode (dry-run), extra vars, tags, and host limits.",
    )
    @tool_errors
    async def ansible_playbook(
        playbook: str,
        workspace: str | None = None,
        inventory: str | None = None,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: list[str] | None = None,
        skip_tags: list[str] | None = None,
        check_mode: bool = False,
        verbose: int = 0,
    ) -> str:
        exec_result = await playbook_manager.run_playbook(
            playbook=playbook,
            workspace=workspace,
            inventory=inventory,
            extra_vars=extra_vars,
            limit=limit,
            tags=tags,
            skip_tags=skip_tags,
            check_mode=check_mode,
            verbose=verbose,
        )
        if exec_result["status"] == "error":
            result = f"❌ {exec_result['message']}"
        else:
            mode = " (CHECK MODE)" if exec_result.get("check_mode") else ""
            status_icon = "✅" if exec_result["status"] == "successful" else "❌"
            result = f"{status_icon} Playbook execution{mode}: {exec_result['status']}\n"
            result += f"Playbook: {exec_result['playbook']}\n\n"
            result += f"Output:\n{exec_result['stdout']}"
            if exec_result.get("stderr"):
                result += f"\n\nStderr:\n{exec_result['stderr']}"
        return result

    @mcp_server.tool(
        name="ansible_task",
        description="Run an ad-hoc Ansible task/module locally. Use this when user asks to 'run ansible module', 'execute ad-hoc task', 'ping hosts', 'run shell command with ansible', 'test ansible module', or wants to run a single Ansible module without a playbook. Defaults to connection=local for localhost.",
    )
    @tool_errors
    async def ansible_task(
        module: str,
        args: str | None = None,
        hosts: str = "localhost",
        inventory: str | None = None,
        extra_vars: dict[str, Any] | None = None,
        connection: str = "local",
        become: bool = False,
    ) -> str:
        task_result = await playbook_manager.run_adhoc_task(
            module=module,
            args=args,
            hosts=hosts,
            inventory=inventory,
            extra_vars=extra_vars,
            connection=connection,
            become=become,
        )
        if task_result["status"] == "error":
            result = f"❌ {task_result['message']}"
        else:
            status_icon = "✅" if task_result["status"] == "successful" else "❌"
            result = f"{status_icon} Ad-hoc task: {task_result['module']} on {task_result['hosts']}\n\n"
            result += f"Output:\n{task_result['stdout']}"
            if task_result.get("stderr"):
                result += f"\n\nStderr:\n{task_result['stderr']}"
        return result

    @mcp_server.tool(
        name="ansible_role",
        description="Execute/run an Ansible role locally by generating a temporary playbook. Use this when user asks to 'run a role', 'execute role', 'test role locally', or wants to apply a specific role from their project without writing a full playbook.",
    )
    @tool_errors
    async def ansible_role(
        role: str,
        hosts: str = "localhost",
        workspace: str | None = None,
        inventory: str | None = None,
        extra_vars: dict[str, Any] | None = None,
        connection: str = "local",
    ) -> str:
        role_result = await playbook_manager.run_role(
            role=role,
            hosts=hosts,
            workspace=workspace,
            inventory=inventory,
            extra_vars=extra_vars,
            connection=connection,
        )
        if role_result["status"] == "error":
            result = f"❌ {role_result['message']}"
        else:
            status_icon = "✅" if role_result["status"] == "successful" else "❌"
            result = f"{status_icon} Role execution: {role_result['role']} - {role_result['status']}\n\n"
            result += f"Output:\n{role_result['stdout']}"
            if role_result.get("stderr"):
                result += f"\n\nStderr:\n{role_result['stderr']}"
        return result

    @mcp_server.tool(
        name="create_role_structure",
        description="Scaffold/generate/create an Ansible role directory structure with standard subdirectories (tasks, handlers, templates, files, vars, defaults, meta). Use this when user asks to 'create a role', 'scaffold a role', 'generate role skeleton', 'init role structure', or wants to set up a new role from scratch.",
    )
    @tool_errors
    async def create_role_structure(
        name: str,
        workspace: str | None = None,
        include_dirs: list[str] | None = None,
    ) -> str:
        role_result = playbook_manager.create_role_structure(
            name=name,
            workspace=workspace,
            include_dirs=include_dirs,
        )
        if role_result["status"] == "created":
            result = f"✅ Role scaffolded: {role_result['role']}\n"
            result += f"Path: {role_result['path']}\n"
            result += f"Directories: {', '.join(role_result['directories'])}\n\n"
            result += "Files created:\n"
            for f in role_result["files"]:
                result += f"  - {f}\n"
        else:
            result = f"❌ {role_result['message']}"
        return result

    @mcp_server.tool(
        name="list_playbooks",
        description="List/show/display all Ansible playbooks in the workspace or project directory. Use this when user asks to 'list playbooks', 'show my playbooks', 'what playbooks exist', 'find playbooks'.",
    )
    @tool_errors
    async def list_playbooks(workspace: str | None = None) -> str:
        pb_result = playbook_manager.list_playbooks(
            workspace=workspace,
        )
        result = f"Playbooks in {pb_result['workspace']} ({pb_result['count']}):\n\n"
        for pb in pb_result["playbooks"]:
            plays_info = f" ({pb['plays']} plays)" if pb.get("plays") else ""
            result += f"  📄 {pb['name']}{plays_info} - {pb['size']} bytes\n"
        if not pb_result["playbooks"]:
            result += "  (none found)\n"
        return result

    @mcp_server.tool(
        name="list_roles",
        description="List/show/display all Ansible roles in the workspace. Use this when user asks to 'list roles', 'show my roles', 'what roles exist'.",
    )
    @tool_errors
    async def list_roles(workspace: str | None = None) -> str:
        roles_result = playbook_manager.list_roles(
            workspace=workspace,
        )
        result = f"Roles in {roles_result['workspace']} ({roles_result['count']}):\n\n"
        for role in roles_result["roles"]:
            result += f"  📁 {role['name']} - dirs: {', '.join(role['directories'])}\n"
        if not roles_result["roles"]:
            result += "  (none found)\n"
        return result

    @mcp_server.tool(
        name="ansible_inventory",
        description="List/show Ansible inventory hosts and groups using ansible-inventory. Use this when user asks to 'list inventory hosts', 'show inventory groups', 'display local inventory', 'what hosts are in my inventory file'.",
    )
    @tool_errors
    async def ansible_inventory(
        inventory: str = "localhost,",
        workspace: str | None = None,
    ) -> str:
        inv_result = await playbook_manager.ansible_inventory_list(
            inventory=inventory,
            workspace=workspace,
        )
        if inv_result["status"] == "success":
            data = inv_result["data"]
            if isinstance(data, dict):
                import json as _json
                result = f"Inventory: {inv_result['inventory']}\n\n"
                result += _json.dumps(data, indent=2, default=str)
            else:
                result = str(data)
        else:
            result = f"❌ {inv_result['message']}"
        return result

    # ── Project Registry Tools ──

    @mcp_server.tool(
        name="register_project",
        description="Register/add a local Ansible project directory for easy reuse. Use this when user asks to 'register project', 'add project', 'set up project', 'configure my ansible project'. Auto-detects git remote URL, inventory, and default playbook.",
    )
    @tool_errors
    async def register_project(
        name: str,
        path: str,
        scm_url: str | None = None,
        scm_branch: str | None = None,
        inventory: str | None = None,
        default_playbook: str | None = None,
        description: str | None = None,
        set_default: bool = False,
    ) -> str:
        reg_result = project_registry.register_project(
            name=name,
            path=path,
            scm_url=scm_url,
            scm_branch=scm_branch,
            inventory=inventory,
            default_playbook=default_playbook,
            description=description,
            set_default=set_default,
        )
        if reg_result["status"] == "registered":
            proj = reg_result["project"]
            result = f"✅ Project registered: {proj['name']}\n"
            result += f"Path: {proj['path']}\n"
            if proj.get("scm_url"):
                result += f"SCM: {proj['scm_url']} ({proj['scm_branch']})\n"
            if proj.get("inventory"):
                result += f"Inventory: {proj['inventory']}\n"
            if proj.get("default_playbook"):
                result += f"Default playbook: {proj['default_playbook']}\n"
            if reg_result.get("is_default"):
                result += "⭐ Set as default project\n"
        else:
            result = f"❌ {reg_result['message']}"
        return result

    @mcp_server.tool(
        name="unregister_project",
        description="Remove/unregister a local Ansible project from the registry. Use when user asks to 'remove project', 'unregister project', 'delete project registration'.",
    )
    @tool_errors
    async def unregister_project(name: str) -> str:
        unreg_result = project_registry.unregister_project(
            name=name,
        )
        if unreg_result["status"] == "removed":
            result = f"✅ Project '{unreg_result['project']}' removed from registry"
        else:
            result = f"❌ {unreg_result['message']}"
        return result

    @mcp_server.tool(
        name="list_registered_projects",
        description="List/show all registered local Ansible projects and the default. Use this when user asks to 'list my projects', 'show registered projects', 'what projects are configured'.",
    )
    @tool_errors
    async def list_registered_projects() -> str:
        proj_result = project_registry.list_projects()
        result = f"Registered Projects ({proj_result['count']}):\n\n"
        for proj in proj_result["projects"]:
            default_marker = " ⭐" if proj.get("is_default") else ""
            exists_marker = "" if proj.get("exists") else " ⚠️ (path not found)"
            result += f"📂 {proj['name']}{default_marker}{exists_marker}\n"
            result += f"   Path: {proj['path']}\n"
            if proj.get("scm_url"):
                result += f"   SCM: {proj['scm_url']} ({proj.get('scm_branch', 'main')})\n"
            if proj.get("inventory"):
                result += f"   Inventory: {proj['inventory']}\n"
            result += f"   Playbooks: {proj.get('playbook_count', 0)}\n\n"
        if not proj_result["projects"]:
            result += "  (none registered)\n"
        return result

    @mcp_server.tool(
        name="project_playbooks",
        description="Discover/find/list playbooks and roles under a registered project root. Use this when user asks to 'show project playbooks', 'find playbooks in project', 'discover playbooks', 'what playbooks does project have', 'list project roles'.",
    )
    @tool_errors
    async def project_playbooks(
        project_name: str | None = None,
        project_path: str | None = None,
    ) -> str:
        disc_result = project_registry.discover_playbooks(
            project_name=project_name,
            project_path=project_path,
        )
        if disc_result.get("status") == "error":
            result = f"❌ {disc_result['message']}"
        else:
            result = f"Project: {disc_result['project_root']}\n\n"
            result += f"Playbooks ({disc_result['playbook_count']}):\n"
            for pb in disc_result["playbooks"]:
                result += f"  📄 {pb['relative_path']} ({pb['plays']} plays, hosts: {pb['hosts']})\n"
            if not disc_result["playbooks"]:
                result += "  (none found)\n"
            result += f"\nRoles ({disc_result['role_count']}):\n"
            for role in disc_result["roles"]:
                result += f"  📁 {role['name']} - {', '.join(role['directories'])}\n"
            if not disc_result["roles"]:
                result += "  (none found)\n"
        return result

    @mcp_server.tool(
        name="project_run_playbook",
        description="Run a playbook using a registered project's inventory and environment. Use this when user asks to 'run project playbook', 'execute playbook from project', 'test project playbook locally'. Automatically uses the project's configured inventory.",
    )
    @tool_errors
    async def project_run_playbook(
        playbook: str,
        project_name: str | None = None,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: list[str] | None = None,
        skip_tags: list[str] | None = None,
        check_mode: bool = False,
        verbose: int = 0,
    ) -> str:
        run_result = await project_registry.project_run_playbook(
            playbook=playbook,
            project_name=project_name,
            extra_vars=extra_vars,
            limit=limit,
            tags=tags,
            skip_tags=skip_tags,
            check_mode=check_mode,
            verbose=verbose,
        )
        if run_result.get("status") == "error":
            result = f"❌ {run_result['message']}"
        else:
            mode = " (CHECK MODE)" if run_result.get("check_mode") else ""
            status_icon = "✅" if run_result["status"] == "successful" else "❌"
            result = f"{status_icon} Project playbook execution{mode}: {run_result['status']}\n"
            result += f"Project: {run_result.get('project', 'N/A')}\n"
            result += f"Playbook: {run_result['playbook']}\n\n"
            result += f"Output:\n{run_result['stdout']}"
            if run_result.get("stderr"):
                result += f"\n\nStderr:\n{run_result['stderr']}"
        return result

    @mcp_server.tool(
        name="git_push_project",
        description="Stage, commit, and push project changes to git remote (GitHub/GitLab). Use this when user asks to 'push to git', 'commit and push', 'push playbook changes', 'push project to github', 'publish changes'. After pushing, use awx_project_update to sync AWX.",
    )
    @tool_errors
    async def git_push_project(
        project_name: str | None = None,
        commit_message: str | None = None,
        branch: str | None = None,
        add_all: bool = True,
    ) -> str:
        push_result = await project_registry.git_push_project(
            project_name=project_name,
            commit_message=commit_message,
            branch=branch,
            add_all=add_all,
        )
        if push_result["status"] == "pushed":
            result = f"✅ Changes pushed to git!\n"
            result += f"Project: {push_result['project']}\n"
            result += f"Branch: {push_result['branch']}\n"
            result += f"Commit: {push_result['message']}\n\n"
            result += push_result["output"]
            result += "\n\n💡 Next: Use 'awx_project_update' to sync AWX with the latest changes."
        elif push_result["status"] == "no_changes":
            result = f"ℹ️ {push_result['message']}"
        else:
            result = f"❌ {push_result['message']}"
        return result

    return mcp_server


async def main() -> None:
    """Run MCP server in stdio mode (for local VSCode integration)."""
    logger.info("starting_stdio_server")

    # Create server without tenant isolation for local use
    mcp_server = create_mcp_server()

    await mcp_server.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
