"""AWX REST API client implementation."""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from awx_mcp_server.clients.base import AWXClient
from awx_mcp_server.domain import (
    AWXAuthenticationError,
    AWXClientError,
    AWXConnectionError,
    EnvironmentConfig,
    Inventory,
    Job,
    JobEvent,
    JobStatus,
    JobTemplate,
    Project,
)


class RestAWXClient(AWXClient):
    """AWX REST API client."""

    def __init__(
        self,
        config: EnvironmentConfig,
        username: Optional[str],
        secret: str,
        is_token: bool = False,
    ):
        """
        Initialize REST client.

        Args:
            config: Environment configuration
            username: Username (for password auth)
            secret: Password or token
            is_token: True if secret is a token
        """
        self.config = config
        self.base_url = str(config.base_url).rstrip("/")
        
        # Setup auth
        if is_token:
            self.auth = None
            self.headers = {"Authorization": f"Bearer {secret}"}
        else:
            self.auth = httpx.BasicAuth(username or "", secret)
            self.headers = {}
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=self.auth,
            headers=self.headers,
            verify=config.verify_ssl,
            timeout=30.0,
        )

    async def __aenter__(self) -> "RestAWXClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    def _parse_extra_vars(self, extra_vars: Any) -> dict[str, Any]:
        """
        Parse extra_vars field from AWX API.
        
        Args:
            extra_vars: Extra vars value (can be dict, string, or empty)
        
        Returns:
            Parsed dictionary
        """
        if isinstance(extra_vars, dict):
            return extra_vars
        if isinstance(extra_vars, str):
            if extra_vars.strip():
                try:
                    return json.loads(extra_vars)
                except json.JSONDecodeError:
                    return {}
        return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
        
        Returns:
            Response JSON
        
        Raises:
            AWXAuthenticationError: Authentication failed
            AWXConnectionError: Connection failed
            AWXClientError: Other client errors
        """
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            
            if response.status_code == 401:
                raise AWXAuthenticationError("Authentication failed")
            elif response.status_code == 403:
                raise AWXAuthenticationError("Permission denied")
            elif response.status_code >= 400:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except Exception:
                    pass
                raise AWXClientError(f"API error {response.status_code}: {error_detail}")
            
            return response.json()
        except httpx.ConnectError as e:
            raise AWXConnectionError(f"Failed to connect to AWX: {e}")
        except httpx.TimeoutException as e:
            raise AWXConnectionError(f"Request timeout: {e}")
        except (AWXAuthenticationError, AWXConnectionError, AWXClientError):
            raise
        except Exception as e:
            raise AWXClientError(f"Request failed: {e}")

    async def test_connection(self) -> bool:
        """Test connection to AWX."""
        try:
            await self._request("GET", "/api/v2/ping/")
            return True
        except Exception:
            return False

    async def list_job_templates(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[JobTemplate]:
        """List job templates."""
        params = {"page": page, "page_size": page_size}
        if name_filter:
            params["name__icontains"] = name_filter
        
        data = await self._request("GET", "/api/v2/job_templates/", params=params)
        
        templates = []
        for item in data.get("results", []):
            templates.append(JobTemplate(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                job_type=item.get("job_type", "run"),
                inventory=item.get("inventory"),
                project=item["project"],
                playbook=item["playbook"],
                extra_vars=self._parse_extra_vars(item.get("extra_vars", {})),
            ))
        
        return templates

    async def get_job_template(self, template_id: int) -> JobTemplate:
        """Get job template by ID."""
        data = await self._request("GET", f"/api/v2/job_templates/{template_id}/")
        
        return JobTemplate(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            job_type=data.get("job_type", "run"),
            inventory=data.get("inventory"),
            project=data["project"],
            playbook=data["playbook"],
            extra_vars=self._parse_extra_vars(data.get("extra_vars", {})),
        )

    async def list_projects(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Project]:
        """List projects."""
        params = {"page": page, "page_size": page_size}
        if name_filter:
            params["name__icontains"] = name_filter
        
        data = await self._request("GET", "/api/v2/projects/", params=params)
        
        return [
            Project(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                scm_type=item.get("scm_type"),
                scm_url=item.get("scm_url"),
                scm_branch=item.get("scm_branch"),
                status=item.get("status"),
            )
            for item in data.get("results", [])
        ]

    async def get_project(self, project_id: int) -> Project:
        """Get project by ID."""
        data = await self._request("GET", f"/api/v2/projects/{project_id}/")
        
        return Project(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            scm_type=data.get("scm_type"),
            scm_url=data.get("scm_url"),
            scm_branch=data.get("scm_branch"),
            status=data.get("status"),
        )

    async def update_project(self, project_id: int, wait: bool = True) -> dict[str, Any]:
        """Update project from SCM."""
        data = await self._request("POST", f"/api/v2/projects/{project_id}/update/")
        
        if wait and "id" in data:
            # Wait for project update to complete
            update_id = data["id"]
            for _ in range(60):  # Wait up to 60 seconds
                status_data = await self._request(
                    "GET", f"/api/v2/project_updates/{update_id}/"
                )
                status = status_data.get("status")
                if status in ["successful", "failed", "error", "canceled"]:
                    break
                await asyncio.sleep(1)
        
        return data

    async def list_inventories(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Inventory]:
        """List inventories."""
        params = {"page": page, "page_size": page_size}
        if name_filter:
            params["name__icontains"] = name_filter
        
        data = await self._request("GET", "/api/v2/inventories/", params=params)
        
        return [
            Inventory(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                organization=item.get("organization"),
                total_hosts=item.get("total_hosts", 0),
                hosts_with_active_failures=item.get("hosts_with_active_failures", 0),
            )
            for item in data.get("results", [])
        ]

    async def launch_job(
        self,
        template_id: int,
        extra_vars: Optional[dict[str, Any]] = None,
        limit: Optional[str] = None,
        tags: Optional[list[str]] = None,
        skip_tags: Optional[list[str]] = None,
    ) -> Job:
        """Launch job from template."""
        payload: dict[str, Any] = {}
        
        if extra_vars:
            payload["extra_vars"] = extra_vars
        if limit:
            payload["limit"] = limit
        if tags:
            payload["job_tags"] = ",".join(tags)
        if skip_tags:
            payload["skip_tags"] = ",".join(skip_tags)
        
        data = await self._request(
            "POST", f"/api/v2/job_templates/{template_id}/launch/", json=payload
        )
        
        return self._parse_job(data)

    async def get_job(self, job_id: int) -> Job:
        """Get job by ID."""
        data = await self._request("GET", f"/api/v2/jobs/{job_id}/")
        return self._parse_job(data)

    async def list_jobs(
        self,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> list[Job]:
        """List jobs."""
        params = {"page": page, "page_size": page_size, "order_by": "-id"}
        if status:
            params["status"] = status
        if created_after:
            params["created__gt"] = created_after
        
        data = await self._request("GET", "/api/v2/jobs/", params=params)
        
        return [self._parse_job(item) for item in data.get("results", [])]

    async def cancel_job(self, job_id: int) -> dict[str, Any]:
        """Cancel running job."""
        return await self._request("POST", f"/api/v2/jobs/{job_id}/cancel/")

    async def get_job_stdout(
        self, job_id: int, format: str = "txt", tail_lines: Optional[int] = None
    ) -> str:
        """Get job stdout."""
        params = {"format": format}
        
        data = await self._request(
            "GET", f"/api/v2/jobs/{job_id}/stdout/", params=params
        )
        
        content = data.get("content", "")
        
        if tail_lines and content:
            lines = content.split("\n")
            content = "\n".join(lines[-tail_lines:])
        
        return content

    async def get_job_events(
        self, job_id: int, failed_only: bool = False, page: int = 1, page_size: int = 100
    ) -> list[JobEvent]:
        """Get job events."""
        params = {"page": page, "page_size": page_size, "order_by": "counter"}
        if failed_only:
            params["failed"] = "true"
        
        data = await self._request("GET", f"/api/v2/jobs/{job_id}/job_events/", params=params)
        
        return [
            JobEvent(
                id=item["id"],
                event=item["event"],
                event_level=item.get("event_level", 0),
                failed=item.get("failed", False),
                changed=item.get("changed", False),
                task=item.get("task"),
                play=item.get("play"),
                role=item.get("role"),
                host=item.get("host_name"),
                stdout=item.get("stdout"),
                stderr=item.get("event_data", {}).get("res", {}).get("stderr"),
                event_data=item.get("event_data", {}),
            )
            for item in data.get("results", [])
        ]

    def _parse_job(self, data: dict[str, Any]) -> Job:
        """Parse job from API response."""
        started = None
        finished = None
        
        if data.get("started"):
            try:
                started = datetime.fromisoformat(data["started"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        if data.get("finished"):
            try:
                finished = datetime.fromisoformat(data["finished"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        return Job(
            id=data["id"],
            name=data["name"],
            status=JobStatus(data["status"]),
            job_template=data.get("job_template"),
            inventory=data.get("inventory"),
            project=data.get("project"),
            playbook=data.get("playbook", ""),
            extra_vars=data.get("extra_vars", {}),
            started=started,
            finished=finished,
            elapsed=data.get("elapsed"),
            artifacts=data.get("artifacts", {}),
        )
