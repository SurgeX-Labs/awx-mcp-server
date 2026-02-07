"""Custom exceptions for AWX MCP Server."""


class AWXMCPError(Exception):
    """Base exception for AWX MCP errors."""

    pass


class EnvironmentNotFoundError(AWXMCPError):
    """Environment not found."""

    pass


class EnvironmentAlreadyExistsError(AWXMCPError):
    """Environment already exists with this name."""

    pass


class NoActiveEnvironmentError(AWXMCPError):
    """No active environment set."""

    pass


class CredentialError(AWXMCPError):
    """Credential storage or retrieval error."""

    pass


class AWXClientError(AWXMCPError):
    """AWX client operation error."""

    pass


class AWXAuthenticationError(AWXClientError):
    """AWX authentication failed."""

    pass


class AWXConnectionError(AWXClientError):
    """Failed to connect to AWX."""

    pass


class AWXPermissionError(AWXClientError):
    """Insufficient permissions for AWX operation."""

    pass


class JobNotFoundError(AWXClientError):
    """Job not found."""

    pass


class TemplateNotFoundError(AWXClientError):
    """Job template not found."""

    pass


class ProjectNotFoundError(AWXClientError):
    """Project not found."""

    pass


class AllowlistViolationError(AWXMCPError):
    """Operation blocked by allowlist."""

    pass


class ConfigurationError(AWXMCPError):
    """Configuration error."""

    pass


class ValidationError(AWXMCPError):
    """Validation error."""

    pass
