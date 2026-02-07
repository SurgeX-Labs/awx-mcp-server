"""CLI interface for AWX MCP Server."""

import asyncio
import getpass
import sys
from pathlib import Path
from typing import Optional

import click
from pydantic import HttpUrl
from rich.console import Console
from rich.table import Table

from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import CredentialType, EnvironmentConfig
from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.utils import configure_logging, get_logger

console = Console()
configure_logging()
logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool) -> None:
    """AWX MCP Server CLI."""
    if debug:
        configure_logging(debug=True)


@cli.group()
def env() -> None:
    """Manage AWX environments."""
    pass


@env.command("add")
@click.option("--name", required=True, help="Environment name")
@click.option("--url", required=True, help="AWX base URL")
@click.option("--username", help="Username (for password auth)")
@click.option("--token", help="Personal access token (alternative to password)")
@click.option("--verify-ssl/--no-verify-ssl", default=True, help="Verify SSL certificates")
@click.option("--set-default", is_flag=True, help="Set as default environment")
def env_add(
    name: str,
    url: str,
    username: Optional[str],
    token: Optional[str],
    verify_ssl: bool,
    set_default: bool,
) -> None:
    """Add a new AWX environment."""
    try:
        # Validate URL
        parsed_url = HttpUrl(url)
        
        # Get credentials
        if token:
            secret = token
            cred_type = CredentialType.TOKEN
            username_val = None
        else:
            if not username:
                username = click.prompt("Username")
            password = getpass.getpass("Password: ")
            secret = password
            cred_type = CredentialType.PASSWORD
            username_val = username
        
        # Create environment config
        config = EnvironmentConfig(
            name=name,
            base_url=parsed_url,
            verify_ssl=verify_ssl,
            is_default=set_default,
        )
        
        # Test connection
        console.print(f"Testing connection to {url}...")
        client = CompositeAWXClient(config, username_val, secret, cred_type == CredentialType.TOKEN)
        
        async def test() -> bool:
            async with client:
                return await client.test_connection()
        
        if not asyncio.run(test()):
            console.print("[red]✗ Connection test failed[/red]")
            if not click.confirm("Add environment anyway?"):
                return
        else:
            console.print("[green]✓ Connection successful[/green]")
        
        # Save configuration
        config_manager = ConfigManager()
        config_manager.add_environment(config)
        
        # Store credentials
        credential_store = CredentialStore()
        credential_store.store_credential(config.env_id, cred_type, username_val, secret)
        
        console.print(f"[green]✓ Environment '{name}' added successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@env.command("list")
def env_list() -> None:
    """List all AWX environments."""
    try:
        config_manager = ConfigManager()
        envs = config_manager.list_environments()
        active_name = config_manager.get_active_name()
        
        if not envs:
            console.print("No environments configured")
            return
        
        table = Table(title="AWX Environments")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="white")
        table.add_column("SSL Verify", style="white")
        table.add_column("Active", style="green")
        
        for env in envs:
            table.add_row(
                env.name,
                str(env.base_url),
                "✓" if env.verify_ssl else "✗",
                "✓" if env.name == active_name else "",
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@env.command("remove")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def env_remove(name: str, yes: bool) -> None:
    """Remove an AWX environment."""
    try:
        config_manager = ConfigManager()
        env = config_manager.get_environment(name)
        
        if not yes:
            if not click.confirm(f"Remove environment '{name}'?"):
                return
        
        # Delete credentials
        credential_store = CredentialStore()
        credential_store.delete_credential(env.env_id)
        
        # Delete configuration
        config_manager.delete_environment(name)
        
        console.print(f"[green]✓ Environment '{name}' removed[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@env.command("set-default")
@click.argument("name")
def env_set_default(name: str) -> None:
    """Set default/active environment."""
    try:
        config_manager = ConfigManager()
        config_manager.set_active(name)
        console.print(f"[green]✓ Active environment set to '{name}'[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@env.command("test")
@click.argument("name", required=False)
def env_test(name: Optional[str]) -> None:
    """Test connection to environment."""
    try:
        config_manager = ConfigManager()
        credential_store = CredentialStore()
        
        if name:
            env = config_manager.get_environment(name)
        else:
            env = config_manager.get_active()
        
        # Get credentials
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
            is_token = False
        except Exception:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        
        # Test connection
        console.print(f"Testing connection to '{env.name}'...")
        client = CompositeAWXClient(env, username, secret, is_token)
        
        async def test() -> bool:
            async with client:
                return await client.test_connection()
        
        if asyncio.run(test()):
            console.print(f"[green]✓ Connection successful to '{env.name}'[/green]")
        else:
            console.print(f"[red]✗ Connection failed to '{env.name}'[/red]")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def serve(debug: bool) -> None:
    """Start MCP server in stdio mode (for local VSCode integration)."""
    if debug:
        configure_logging(debug=True)
    
    from awx_mcp_server.server import main
    
    asyncio.run(main())


@cli.command("serve-http")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def serve_http(host: str, port: int, debug: bool) -> None:
    """Start MCP server in HTTP/SSE mode (for remote access)."""
    if debug:
        configure_logging(debug=True)
    
    console.print(f"[green]Starting AWX MCP HTTP Server on {host}:{port}[/green]")
    console.print(f"[cyan]SSE endpoint: http://{host}:{port}/sse[/cyan]")
    console.print(f"[cyan]Health check: http://{host}:{port}/health[/cyan]")
    console.print(f"[cyan]API docs: http://{host}:{port}/docs[/cyan]")
    
    from awx_mcp_server.http_server import start_http_server
    
    asyncio.run(start_http_server(host=host, port=port, debug=debug))


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
