"""Composite AWX client that intelligently chooses between CLI and REST."""

from typing import Any, Optional

from awx_mcp_server.clients.awxkit_client import AwxkitClient
from awx_mcp_server.clients.base import AWXClient
from awx_mcp_server.clients.rest_client import RestAWXClient
from awx_mcp_server.domain import EnvironmentConfig, Inventory, Job, JobEvent, JobTemplate, Project


class CompositeAWXClient(AWXClient):
    """
    Composite client that uses awxkit CLI for most operations,
    falling back to REST API for operations not well supported by CLI.
    """

    def __init__(
        self,
        config: EnvironmentConfig,
        username: Optional[str],
        secret: str,
        is_token: bool = False,
    ):
        """
        Initialize composite client.

        Args:
            config: Environment configuration
            username: Username (for password auth)
            secret: Password or token
            is_token: True if secret is a token
        """
        self.cli_client = AwxkitClient(config, username, secret, is_token)
        self.rest_client = RestAWXClient(config, username, secret, is_token)
        self.prefer_cli = False  # Prefer REST API (more reliable on Windows)

    async def __aenter__(self) -> "CompositeAWXClient":
        """Async context manager entry."""
        await self.rest_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.rest_client.__aexit__(exc_type, exc_val, exc_tb)

    async def test_connection(self) -> bool:
        """Test connection - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.test_connection()
            except Exception:
                pass
        return await self.rest_client.test_connection()

    async def list_job_templates(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[JobTemplate]:
        """List job templates - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.list_job_templates(name_filter, page, page_size)
            except Exception:
                pass
        return await self.rest_client.list_job_templates(name_filter, page, page_size)

    async def get_job_template(self, template_id: int) -> JobTemplate:
        """Get job template - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.get_job_template(template_id)
            except Exception:
                pass
        return await self.rest_client.get_job_template(template_id)

    async def list_projects(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Project]:
        """List projects - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.list_projects(name_filter, page, page_size)
            except Exception:
                pass
        return await self.rest_client.list_projects(name_filter, page, page_size)

    async def get_project(self, project_id: int) -> Project:
        """Get project - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.get_project(project_id)
            except Exception:
                pass
        return await self.rest_client.get_project(project_id)

    async def update_project(self, project_id: int, wait: bool = True) -> dict[str, Any]:
        """Update project - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.update_project(project_id, wait)
            except Exception:
                pass
        return await self.rest_client.update_project(project_id, wait)

    async def list_inventories(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Inventory]:
        """List inventories - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.list_inventories(name_filter, page, page_size)
            except Exception:
                pass
        return await self.rest_client.list_inventories(name_filter, page, page_size)

    async def launch_job(
        self,
        template_id: int,
        extra_vars: Optional[dict[str, Any]] = None,
        limit: Optional[str] = None,
        tags: Optional[list[str]] = None,
        skip_tags: Optional[list[str]] = None,
    ) -> Job:
        """Launch job - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.launch_job(
                    template_id, extra_vars, limit, tags, skip_tags
                )
            except Exception:
                pass
        return await self.rest_client.launch_job(template_id, extra_vars, limit, tags, skip_tags)

    async def get_job(self, job_id: int) -> Job:
        """Get job - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.get_job(job_id)
            except Exception:
                pass
        return await self.rest_client.get_job(job_id)

    async def list_jobs(
        self,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> list[Job]:
        """List jobs - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.list_jobs(status, created_after, page, page_size)
            except Exception:
                pass
        return await self.rest_client.list_jobs(status, created_after, page, page_size)

    async def cancel_job(self, job_id: int) -> dict[str, Any]:
        """Cancel job - prefer CLI."""
        if self.prefer_cli:
            try:
                return await self.cli_client.cancel_job(job_id)
            except Exception:
                pass
        return await self.rest_client.cancel_job(job_id)

    async def get_job_stdout(
        self, job_id: int, format: str = "txt", tail_lines: Optional[int] = None
    ) -> str:
        """Get job stdout - always use REST (CLI not well supported)."""
        return await self.rest_client.get_job_stdout(job_id, format, tail_lines)

    async def get_job_events(
        self, job_id: int, failed_only: bool = False, page: int = 1, page_size: int = 100
    ) -> list[JobEvent]:
        """Get job events - always use REST (CLI not well supported)."""
        return await self.rest_client.get_job_events(job_id, failed_only, page, page_size)
