"""Tests for domain models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from awx_mcp.domain import (
    EnvironmentConfig,
    JobStatus,
    FailureCategory,
    Job,
    JobTemplate,
)


def test_environment_config_valid():
    """Test valid environment configuration."""
    config = EnvironmentConfig(
        name="production",
        base_url="https://awx.example.com",
        verify_ssl=True,
    )
    
    assert config.name == "production"
    assert str(config.base_url) == "https://awx.example.com/"
    assert config.verify_ssl is True
    assert config.env_id is not None


def test_environment_config_invalid_name():
    """Test invalid environment name."""
    with pytest.raises(ValidationError):
        EnvironmentConfig(
            name="prod uction!",  # Invalid characters
            base_url="https://awx.example.com",
        )


def test_environment_config_invalid_url():
    """Test invalid URL."""
    with pytest.raises(ValidationError):
        EnvironmentConfig(
            name="production",
            base_url="not-a-url",
        )


def test_job_status_enum():
    """Test job status enum values."""
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.SUCCESSFUL.value == "successful"
    assert JobStatus.FAILED.value == "failed"


def test_failure_category_enum():
    """Test failure category enum values."""
    assert FailureCategory.AUTH_FAILURE.value == "auth_failure"
    assert FailureCategory.SYNTAX_ERROR.value == "syntax_error"


def test_job_template():
    """Test job template model."""
    template = JobTemplate(
        id=1,
        name="Deploy Web App",
        description="Deploy web application",
        job_type="run",
        project=5,
        playbook="deploy.yml",
    )
    
    assert template.id == 1
    assert template.name == "Deploy Web App"
    assert template.playbook == "deploy.yml"


def test_job():
    """Test job model."""
    job = Job(
        id=100,
        name="Deploy Web App #100",
        status=JobStatus.RUNNING,
        playbook="deploy.yml",
        started=datetime.utcnow(),
    )
    
    assert job.id == 100
    assert job.status == JobStatus.RUNNING
    assert job.started is not None
