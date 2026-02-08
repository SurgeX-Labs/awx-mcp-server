"""AWX CLI client using awxkit."""

import asyncio
import json
import subprocess
from typing import Any, Optional

from awx_mcp_server.clients.base import AWXClient
from awx_mcp_server.domain import (
    AWXClientError,
    EnvironmentConfig,
    Inventory,
    Job,
    JobEvent,
    JobStatus,
    JobTemplate,
    Project,
)


class AwxkitClient(AWXClient):
    """AWX client using awxkit CLI."""

    def __init__(
        self,
        config: EnvironmentConfig,
        username: Optional[str],
        secret: str,
        is_token: bool = False,
    ):
        """
        Initialize awxkit client.

        Args:
            config: Environment configuration
            username: Username (for password auth)
            secret: Password or token
            is_token: True if secret is a token
        """
        self.config = config
        self.base_url = str(config.base_url).rstrip("/")
        self.username = username
        self.secret = secret
        self.is_token = is_token

    async def _run_cli(
        self, args: list[str], timeout: int = 30
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Run awxkit CLI command.

        Args:
            args: CLI arguments
            timeout: Command timeout in seconds
        
        Returns:
            Parsed JSON response
        
        Raises:
            AWXClientError: If command fails
        """
        # Build environment with credentials
        env = {
            "TOWER_HOST": self.base_url,
            "TOWER_VERIFY_SSL": "true" if self.config.verify_ssl else "false",
        }
        
        if self.is_token:
            env["TOWER_OAUTH_TOKEN"] = self.secret
        else:
            env["TOWER_USERNAME"] = self.username or ""
            env["TOWER_PASSWORD"] = self.secret
        
        # Build command
        cmd = ["awx", "-f", "json"] + args
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise AWXClientError(f"awxkit command failed: {error_msg}")
            
            output = stdout.decode("utf-8", errors="replace").strip()
            if not output:
                return {}
            
            return json.loads(output)
        except asyncio.TimeoutError:
            raise AWXClientError(f"awxkit command timeout after {timeout}s")
        except json.JSONDecodeError as e:
            raise AWXClientError(f"Failed to parse awxkit output: {e}")
        except FileNotFoundError:
            raise AWXClientError(
                "awxkit not found. Please install: pip install awxkit"
            )
        except Exception as e:
            raise AWXClientError(f"awxkit command failed: {e}")

    async def test_connection(self) -> bool:
        """Test connection to AWX."""
        try:
            await self._run_cli(["ping"])
            return True
        except Exception:
            return False

    async def list_job_templates(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[JobTemplate]:
        """List job templates."""
        args = ["job_templates", "list", "--page", str(page), "--page-size", str(page_size)]
        
        if name_filter:
            args.extend(["--name", name_filter])
        
        data = await self._run_cli(args)
        results = data.get("results", []) if isinstance(data, dict) else data
        
        return [
            JobTemplate(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                job_type=item.get("job_type", "run"),
                inventory=item.get("inventory"),
                project=item["project"],
                playbook=item["playbook"],
                extra_vars=item.get("extra_vars", {}),
            )
            for item in results
        ]

    async def get_job_template(self, template_id: int) -> JobTemplate:
        """Get job template by ID."""
        data = await self._run_cli(["job_templates", "get", str(template_id)])
        
        return JobTemplate(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            job_type=data.get("job_type", "run"),
            inventory=data.get("inventory"),
            project=data["project"],
            playbook=data["playbook"],
            extra_vars=data.get("extra_vars", {}),
        )

    async def list_projects(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Project]:
        """List projects."""
        args = ["projects", "list", "--page", str(page), "--page-size", str(page_size)]
        
        if name_filter:
            args.extend(["--name", name_filter])
        
        data = await self._run_cli(args)
        results = data.get("results", []) if isinstance(data, dict) else data
        
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
            for item in results
        ]

    async def get_project(self, project_id: int) -> Project:
        """Get project by ID."""
        data = await self._run_cli(["projects", "get", str(project_id)])
        
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
        args = ["projects", "update", str(project_id)]
        if wait:
            args.append("--wait")
        
        data = await self._run_cli(args, timeout=300 if wait else 30)
        return data if isinstance(data, dict) else {}

    async def list_inventories(
        self, name_filter: Optional[str] = None, page: int = 1, page_size: int = 25
    ) -> list[Inventory]:
        """List inventories."""
        args = ["inventory", "list", "--page", str(page), "--page-size", str(page_size)]
        
        if name_filter:
            args.extend(["--name", name_filter])
        
        data = await self._run_cli(args)
        results = data.get("results", []) if isinstance(data, dict) else data
        
        return [
            Inventory(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                organization=item.get("organization"),
                total_hosts=item.get("total_hosts", 0),
                hosts_with_active_failures=item.get("hosts_with_active_failures", 0),
            )
            for item in results
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
        args = ["job_templates", "launch", str(template_id)]
        
        if extra_vars:
            args.extend(["--extra-vars", json.dumps(extra_vars)])
        if limit:
            args.extend(["--limit", limit])
        if tags:
            args.extend(["--job-tags", ",".join(tags)])
        if skip_tags:
            args.extend(["--skip-tags", ",".join(skip_tags)])
        
        data = await self._run_cli(args)
        return self._parse_job(data if isinstance(data, dict) else {})

    async def get_job(self, job_id: int) -> Job:
        """Get job by ID."""
        data = await self._run_cli(["jobs", "get", str(job_id)])
        return self._parse_job(data if isinstance(data, dict) else {})

    async def list_jobs(
        self,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> list[Job]:
        """List jobs."""
        args = ["jobs", "list", "--page", str(page), "--page-size", str(page_size)]
        
        if status:
            args.extend(["--status", status])
        
        data = await self._run_cli(args)
        results = data.get("results", []) if isinstance(data, dict) else data
        
        return [self._parse_job(item) for item in results]

    async def cancel_job(self, job_id: int) -> dict[str, Any]:
        """Cancel running job."""
        data = await self._run_cli(["jobs", "cancel", str(job_id)])
        return data if isinstance(data, dict) else {}

    async def get_job_stdout(
        self, job_id: int, format: str = "txt", tail_lines: Optional[int] = None
    ) -> str:
        """Get job stdout - not well supported by awxkit CLI, use REST."""
        raise NotImplementedError("Use REST client for stdout retrieval")

    async def get_job_events(
        self, job_id: int, failed_only: bool = False, page: int = 1, page_size: int = 100
    ) -> list[JobEvent]:
        """Get job events - not well supported by awxkit CLI, use REST."""
        raise NotImplementedError("Use REST client for job events")

    def _parse_job(self, data: dict[str, Any]) -> Job:
        """Parse job from CLI output."""
        from datetime import datetime
        
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
