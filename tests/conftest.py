"""Test fixtures and configuration."""

import pytest


@pytest.fixture
def sample_job_template():
    """Sample job template data."""
    return {
        "id": 1,
        "name": "Deploy Web App",
        "description": "Deploy web application to production",
        "job_type": "run",
        "inventory": 5,
        "project": 3,
        "playbook": "deploy.yml",
        "extra_vars": {"environment": "production"},
    }


@pytest.fixture
def sample_job():
    """Sample job data."""
    return {
        "id": 100,
        "name": "Deploy Web App #100",
        "status": "successful",
        "job_template": 1,
        "inventory": 5,
        "project": 3,
        "playbook": "deploy.yml",
        "extra_vars": {"environment": "production"},
        "started": "2024-01-01T10:00:00Z",
        "finished": "2024-01-01T10:05:30Z",
        "elapsed": 330.5,
        "artifacts": {"deployed_version": "1.2.3"},
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "id": 3,
        "name": "Web App Project",
        "description": "Web application deployment playbooks",
        "scm_type": "git",
        "scm_url": "https://github.com/example/playbooks.git",
        "scm_branch": "main",
        "status": "successful",
    }
