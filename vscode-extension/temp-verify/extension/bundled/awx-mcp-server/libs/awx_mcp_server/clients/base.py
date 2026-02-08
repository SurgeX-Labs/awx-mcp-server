"""Base AWX client interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from awx_mcp_server.domain import Inventory, Job, JobEvent, JobTemplate, Project


class AWXClient(ABC):
    """Abstract base class for AWX clients."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to AWX.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def list_job_templates(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[JobTemplate]:
        """List job templates."""
        pass

    @abstractmethod
    async def get_job_template(self, template_id: int) -> JobTemplate:
        """Get job template by ID."""
        pass

    @abstractmethod
    async def list_projects(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Project]:
        """List projects."""
        pass

    @abstractmethod
    async def get_project(self, project_id: int) -> Project:
        """Get project by ID."""
        pass

    @abstractmethod
    async def update_project(self, project_id: int, wait: bool = True) -> dict[str, Any]:
        """Update project from SCM."""
        pass

    @abstractmethod
    async def list_inventories(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Inventory]:
        """List inventories."""
        pass

    @abstractmethod
    async def launch_job(
        self,
        template_id: int,
        extra_vars: Optional[dict[str, Any]] = None,
        limit: Optional[str] = None,
        tags: Optional[list[str]] = None,
        skip_tags: Optional[list[str]] = None,
    ) -> Job:
        """Launch job from template."""
        pass

    @abstractmethod
    async def get_job(self, job_id: int) -> Job:
        """Get job by ID."""
        pass

    @abstractmethod
    async def list_jobs(
        self,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> list[Job]:
        """List jobs."""
        pass

    @abstractmethod
    async def cancel_job(self, job_id: int) -> dict[str, Any]:
        """Cancel running job."""
        pass

    @abstractmethod
    async def get_job_stdout(
        self, job_id: int, format: str = "txt", tail_lines: Optional[int] = None
    ) -> str:
        """Get job stdout."""
        pass

    @abstractmethod
    async def get_job_events(
        self, job_id: int, failed_only: bool = False, page: int = 1, page_size: int = 100
    ) -> list[JobEvent]:
        """Get job events."""
        pass
