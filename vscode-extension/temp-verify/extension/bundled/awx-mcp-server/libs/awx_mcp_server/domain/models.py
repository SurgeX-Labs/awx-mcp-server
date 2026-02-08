"""Core domain models for AWX MCP Server."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class JobStatus(str, Enum):
    """AWX job status."""

    PENDING = "pending"
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ERROR = "error"
    CANCELED = "canceled"


class FailureCategory(str, Enum):
    """Classification of job failure root causes."""

    INVENTORY_ISSUE = "inventory_issue"
    AUTH_FAILURE = "auth_failure"
    MISSING_VARIABLE = "missing_variable"
    SYNTAX_ERROR = "syntax_error"
    MODULE_FAILURE = "module_failure"
    CONNECTION_TIMEOUT = "connection_timeout"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


class EnvironmentConfig(BaseModel):
    """AWX environment configuration (no secrets)."""

    env_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    base_url: HttpUrl
    verify_ssl: bool = True
    is_default: bool = False
    
    # Optional defaults
    default_organization: Optional[str] = None
    default_project: Optional[str] = None
    default_inventory: Optional[str] = None
    
    # Allowlists
    allowed_job_templates: list[str] = Field(default_factory=list)
    allowed_inventories: list[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate environment name."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Name must be alphanumeric with hyphens/underscores only")
        return v

    class Config:
        """Pydantic config."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class CredentialType(str, Enum):
    """Type of credential."""

    PASSWORD = "password"
    TOKEN = "token"


class JobTemplate(BaseModel):
    """AWX job template."""

    id: int
    name: str
    description: Optional[str] = None
    job_type: str
    inventory: Optional[int] = None
    project: int
    playbook: str
    extra_vars: dict[str, Any] = Field(default_factory=dict)


class Project(BaseModel):
    """AWX project."""

    id: int
    name: str
    description: Optional[str] = None
    scm_type: Optional[str] = None
    scm_url: Optional[str] = None
    scm_branch: Optional[str] = None
    status: Optional[str] = None


class Inventory(BaseModel):
    """AWX inventory."""

    id: int
    name: str
    description: Optional[str] = None
    organization: Optional[int] = None
    total_hosts: int = 0
    hosts_with_active_failures: int = 0


class Job(BaseModel):
    """AWX job."""

    id: int
    name: str
    status: JobStatus
    job_template: Optional[int] = None
    inventory: Optional[int] = None
    project: Optional[int] = None
    playbook: str
    extra_vars: dict[str, Any] = Field(default_factory=dict)
    started: Optional[datetime] = None
    finished: Optional[datetime] = None
    elapsed: Optional[float] = None
    artifacts: dict[str, Any] = Field(default_factory=dict)


class JobEvent(BaseModel):
    """AWX job event."""

    id: int
    event: str
    event_level: int
    failed: bool
    changed: bool
    task: Optional[str] = None
    play: Optional[str] = None
    role: Optional[str] = None
    host: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    event_data: dict[str, Any] = Field(default_factory=dict)


class FailureAnalysis(BaseModel):
    """Analysis of job failure."""

    job_id: int
    category: FailureCategory
    task_name: Optional[str] = None
    play_name: Optional[str] = None
    role_name: Optional[str] = None
    file_path: Optional[str] = None
    host: Optional[str] = None
    error_message: Optional[str] = None
    stderr: Optional[str] = None
    suggested_fixes: list[str] = Field(default_factory=list)
    failed_events_count: int = 0


class AuditLog(BaseModel):
    """Audit log entry."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str
    user: str
    action: str
    job_template: Optional[str] = None
    job_id: Optional[int] = None
    success: bool
    error: Optional[str] = None
