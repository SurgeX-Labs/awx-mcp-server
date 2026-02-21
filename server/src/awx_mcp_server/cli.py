"""CLI for AWX MCP Remote Server."""

import asyncio
import json
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from awx_mcp_server.http_server import start_http_server

console = Console()

# Import local components
from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import CredentialType


@click.group()
@click.version_option(version="1.1.6")
def main():
    """AWX MCP Remote Server - CLI and API for AWX/AAP automation."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def start(host: str, port: int, debug: bool):
    """Start the HTTP server."""
    console.print(f"[bold green]Starting AWX MCP Server on {host}:{port}[/bold green]")
    console.print(f"[dim]Debug mode: {debug}[/dim]")
    console.print(f"\n[bold]API Documentation:[/bold] http://{host}:{port}/docs")
    console.print(f"[bold]Health Check:[/bold] http://{host}:{port}/health")
    console.print(f"[bold]Metrics:[/bold] http://{host}:{port}/prometheus-metrics\n")
    
    asyncio.run(start_http_server(host=host, port=port, debug=debug))


async def get_client():
    """Get AWX client for active environment."""
    config_manager = ConfigManager()
    credential_store = CredentialStore()
    
    env = config_manager.get_active()
    
    try:
        username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
        is_token = False
    except:
        username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
        is_token = True
    
    return CompositeAWXClient(env, username, secret, is_token)


# Environment Management Commands

@main.group()
def env():
    """Manage AWX environments."""
    pass


@env.command("list")
def env_list():
    """List all configured environments."""
    config_manager = ConfigManager()
    envs = config_manager.list()
    
    if not envs:
        console.print("[yellow]No environments configured[/yellow]")
        return
    
    table = Table(title="AWX Environments")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="green")
    table.add_column("Active", style="magenta")
    
    active = config_manager.get_active()
    for e in envs:
        table.add_row(e.name, str(e.base_url), "✓" if e.env_id == active.env_id else "")
    
    console.print(table)


@env.command("test")
@click.option("--env-name", help="Environment to test (defaults to active)")
def env_test(env_name):
    """Test connection to AWX environment."""
    async def test():
        client = await get_client()
        result = await client.test_connection()
        if result:
            console.print("[green]✓ Connection successful[/green]")
        else:
            console.print("[red]✗ Connection failed[/red]")
            sys.exit(1)
    
    asyncio.run(test())


# Job Template Commands

@main.group()
def templates():
    """Manage job templates."""
    pass


@templates.command("list")
@click.option("--filter", help="Filter templates by name")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=25, help="Results per page")
def templates_list(filter, page, page_size):
    """List job templates."""
    async def list_templates():
        client = await get_client()
        results = await client.list_job_templates(
            name_filter=filter,
            page=page,
            page_size=page_size
        )
        
        if not results:
            console.print("[yellow]No templates found[/yellow]")
            return
        
        table = Table(title="Job Templates")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        
        for t in results:
            table.add_row(str(t.id), t.name, t.description or "")
        
        console.print(table)
    
    asyncio.run(list_templates())


@templates.command("get")
@click.argument("name")
def templates_get(name):
    """Get template details."""
    async def get_template():
        client = await get_client()
        template = await client.get_job_template(name)
        
        console.print(JSON(json.dumps({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "job_type": template.job_type,
            "inventory": template.inventory,
            "project": template.project,
            "playbook": template.playbook,
            "extra_vars": template.extra_vars
        }, indent=2)))
    
    asyncio.run(get_template())


# Job Commands

@main.group()
def jobs():
    """Manage jobs."""
    pass


@jobs.command("list")
@click.option("--status", help="Filter by status (failed, running, successful)")
@click.option("--page", default=1, help="Page number")
@click.option("--page-size", default=10, help="Results per page")
def jobs_list(status, page, page_size):
    """List jobs."""
    async def list_jobs():
        client = await get_client()
        results = await client.list_jobs(
            status=status,
            page=page,
            page_size=page_size
        )
        
        if not results:
            console.print("[yellow]No jobs found[/yellow]")
            return
        
        table = Table(title="Jobs")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="white")
        
        for j in results:
            table.add_row(
                str(j.id),
                j.name,
                j.status,
                str(j.started) if j.started else "Not started"
            )
        
        console.print(table)
    
    asyncio.run(list_jobs())


@jobs.command("get")
@click.argument("job_id", type=int)
def jobs_get(job_id):
    """Get job details."""
    async def get_job():
        client = await get_client()
        job = await client.get_job(job_id)
        
        console.print(f"\n[bold]Job {job.id}:[/bold] {job.name}")
        console.print(f"[bold]Status:[/bold] {job.status}")
        console.print(f"[bold]Started:[/bold] {job.started}")
        console.print(f"[bold]Finished:[/bold] {job.finished}")
        console.print(f"[bold]Elapsed:[/bold] {job.elapsed}s\n")
    
    asyncio.run(get_job())


@jobs.command("launch")
@click.argument("template_name")
@click.option("--extra-vars", help="Extra variables (JSON)")
def jobs_launch(template_name, extra_vars):
    """Launch a job from template."""
    async def launch_job():
        client = await get_client()
        extra_vars_dict = json.loads(extra_vars) if extra_vars else None
        
        job = await client.launch_job(template_name, extra_vars_dict)
        
        console.print(f"[green]✓ Job launched[/green]")
        console.print(f"[bold]Job ID:[/bold] {job.id}")
        console.print(f"[bold]Name:[/bold] {job.name}")
        console.print(f"[bold]Status:[/bold] {job.status}")
    
    asyncio.run(launch_job())


@jobs.command("cancel")
@click.argument("job_id", type=int)
def jobs_cancel(job_id):
    """Cancel a running job."""
    async def cancel_job():
        client = await get_client()
        await client.cancel_job(job_id)
        console.print(f"[green]✓ Job {job_id} canceled[/green]")
    
    asyncio.run(cancel_job())


@jobs.command("stdout")
@click.argument("job_id", type=int)
def jobs_stdout(job_id):
    """Get job output."""
    async def get_stdout():
        client = await get_client()
        output = await client.get_job_stdout(job_id)
        console.print(output)
    
    asyncio.run(get_stdout())


@jobs.command("events")
@click.argument("job_id", type=int)
@click.option("--page", default=1)
@click.option("--page-size", default=50)
def jobs_events(job_id, page, page_size):
    """Get job events."""
    async def get_events():
        client = await get_client()
        events = await client.get_job_events(job_id, page, page_size)
        
        for event in events[:20]:  # Show first 20
            console.print(f"[cyan]{event.event}[/cyan] - {event.task or 'N/A'}")
            if event.stdout:
                console.print(f"  {event.stdout[:100]}")
        
        if len(events) > 20:
            console.print(f"\n[dim]... and {len(events) - 20} more events[/dim]")
    
    asyncio.run(get_events())


# Project Commands

@main.group()
def projects():
    """Manage projects."""
    pass


@projects.command("list")
@click.option("--page", default=1)
@click.option("--page-size", default=25)
def projects_list(page, page_size):
    """List projects."""
    async def list_projects():
        client = await get_client()
        results = await client.list_projects(page=page, page_size=page_size)
        
        table = Table(title="Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("SCM Type", style="yellow")
        table.add_column("URL", style="blue")
        
        for p in results:
            table.add_row(
                str(p.id),
                p.name,
                p.scm_type or "N/A",
                p.scm_url or "N/A"
            )
        
        console.print(table)
    
    asyncio.run(list_projects())


@projects.command("update")
@click.argument("name")
def projects_update(name):
    """Update project from SCM."""
    async def update_project():
        client = await get_client()
        await client.update_project(name)
        console.print(f"[green]✓ Project '{name}' update initiated[/green]")
    
    asyncio.run(update_project())


# Inventory Commands

@main.group()
def inventories():
    """Manage inventories."""
    pass


@inventories.command("list")
@click.option("--page", default=1)
@click.option("--page-size", default=25)
def inventories_list(page, page_size):
    """List inventories."""
    async def list_inventories():
        client = await get_client()
        results = await client.list_inventories(page=page, page_size=page_size)
        
        table = Table(title="Inventories")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="white")
        
        for inv in results:
            table.add_row(str(inv.id), inv.name, inv.description or "")
        
        console.print(table)
    
    asyncio.run(list_inventories())


if __name__ == "__main__":
    main()
