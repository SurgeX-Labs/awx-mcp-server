"""Regression test: job templates with a null `project` must not crash listing.

AWX returns `project: null` for job templates whose linked project has been
deleted (orphaned templates) or removed via other edge-case configurations.
`JobTemplate.project` was previously a required `int`, so any such template
raised a pydantic ValidationError and aborted the whole page of results.
"""

import pytest

from awx_mcp_server.domain.models import JobTemplate
from awx_mcp_server.clients.rest_client import RestAWXClient
from awx_mcp_server.domain.models import EnvironmentConfig


def test_job_template_allows_null_project():
    """JobTemplate should accept a missing/null project."""
    template = JobTemplate(
        id=1,
        name="Orphaned Template",
        job_type="run",
        playbook="deploy.yml",
    )

    assert template.project is None


@pytest.mark.asyncio
async def test_list_job_templates_skips_null_project_without_raising(monkeypatch):
    """A null-project item in the results must not abort list_job_templates."""
    config = EnvironmentConfig(name="test", base_url="https://awx.example.com")
    client = RestAWXClient(config, username=None, secret="token", is_token=True)

    async def fake_request(method, endpoint, **kwargs):
        return {
            "results": [
                {
                    "id": 1,
                    "name": "Normal Template",
                    "job_type": "run",
                    "inventory": 5,
                    "project": 3,
                    "playbook": "deploy.yml",
                },
                {
                    "id": 2,
                    "name": "Orphaned Template",
                    "job_type": "run",
                    "inventory": 5,
                    "project": None,
                    "playbook": "cleanup.yml",
                },
            ]
        }

    monkeypatch.setattr(client, "_request", fake_request)

    templates = await client.list_job_templates()

    assert len(templates) == 2
    assert templates[0].project == 3
    assert templates[1].project is None
