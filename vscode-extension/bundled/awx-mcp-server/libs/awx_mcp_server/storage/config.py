"""Configuration management for AWX environments."""

import json
from pathlib import Path
from typing import Optional
from uuid import UUID

from awx_mcp_server.domain import (
    EnvironmentAlreadyExistsError,
    EnvironmentConfig,
    EnvironmentNotFoundError,
    NoActiveEnvironmentError,
)


class ConfigManager:
    """Manage AWX environment configurations."""

    def __init__(self, config_path: Optional[Path] = None, tenant_id: Optional[str] = None):
        """
        Initialize config manager.

        Args:
            config_path: Path to config file (default: ~/.awx-mcp/config.json)
            tenant_id: Tenant ID for multi-tenant isolation (optional)
        """
        if config_path is None:
            base_dir = Path.home() / ".awx-mcp"
            if tenant_id:
                # Use tenant-specific directory for isolation
                config_path = base_dir / tenant_id / "config.json"
            else:
                config_path = base_dir / "config.json"
        
        self.config_path = config_path
        self.tenant_id = tenant_id
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._environments: dict[str, EnvironmentConfig] = {}
        self._active_env: Optional[str] = None
        self._load()

    def add_environment(self, env: EnvironmentConfig) -> None:
        """
        Add new environment.

        Args:
            env: Environment configuration
        
        Raises:
            EnvironmentAlreadyExistsError: If environment name already exists
        """
        if env.name in self._environments:
            raise EnvironmentAlreadyExistsError(f"Environment '{env.name}' already exists")
        
        self._environments[env.name] = env
        
        # Set as default if first environment or explicitly marked
        if len(self._environments) == 1 or env.is_default:
            self.set_active(env.name)
        
        self._save()

    def update_environment(self, name: str, env: EnvironmentConfig) -> None:
        """
        Update existing environment.

        Args:
            name: Current environment name
            env: Updated environment configuration
        
        Raises:
            EnvironmentNotFoundError: If environment doesn't exist
        """
        if name not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{name}' not found")
        
        # Handle name change
        if name != env.name:
            if env.name in self._environments:
                raise EnvironmentAlreadyExistsError(f"Environment '{env.name}' already exists")
            del self._environments[name]
            if self._active_env == name:
                self._active_env = env.name
        
        self._environments[env.name] = env
        self._save()

    def delete_environment(self, name: str) -> None:
        """
        Delete environment.

        Args:
            name: Environment name
        
        Raises:
            EnvironmentNotFoundError: If environment doesn't exist
        """
        if name not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{name}' not found")
        
        del self._environments[name]
        
        # Clear active if this was active
        if self._active_env == name:
            self._active_env = None
            # Set first remaining as active
            if self._environments:
                self._active_env = next(iter(self._environments.keys()))
        
        self._save()

    def get_environment(self, name: str) -> EnvironmentConfig:
        """
        Get environment by name.

        Args:
            name: Environment name
        
        Returns:
            Environment configuration
        
        Raises:
            EnvironmentNotFoundError: If environment doesn't exist
        """
        if name not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{name}' not found")
        return self._environments[name]

    def get_environment_by_id(self, env_id: UUID) -> EnvironmentConfig:
        """
        Get environment by ID.

        Args:
            env_id: Environment UUID
        
        Returns:
            Environment configuration
        
        Raises:
            EnvironmentNotFoundError: If environment doesn't exist
        """
        for env in self._environments.values():
            if env.env_id == env_id:
                return env
        raise EnvironmentNotFoundError(f"Environment with ID '{env_id}' not found")

    def list_environments(self) -> list[EnvironmentConfig]:
        """
        List all environments.

        Returns:
            List of all environment configurations
        """
        return list(self._environments.values())

    def set_active(self, name: str) -> None:
        """
        Set active environment.

        Args:
            name: Environment name
        
        Raises:
            EnvironmentNotFoundError: If environment doesn't exist
        """
        if name not in self._environments:
            raise EnvironmentNotFoundError(f"Environment '{name}' not found")
        
        self._active_env = name
        self._save()

    def get_active(self) -> EnvironmentConfig:
        """
        Get active environment.

        Returns:
            Active environment configuration
        
        Raises:
            NoActiveEnvironmentError: If no active environment
        """
        if not self._active_env:
            raise NoActiveEnvironmentError("No active environment set")
        return self._environments[self._active_env]

    def get_active_name(self) -> Optional[str]:
        """
        Get active environment name.

        Returns:
            Active environment name or None
        """
        return self._active_env

    def _load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
            
            self._active_env = data.get("active_environment")
            
            for env_data in data.get("environments", []):
                env = EnvironmentConfig.model_validate(env_data)
                self._environments[env.name] = env
        except Exception as e:
            # Log error but don't fail startup
            print(f"Warning: Failed to load config: {e}")

    def _save(self) -> None:
        """Save configuration to file."""
        data = {
            "active_environment": self._active_env,
            "environments": [env.model_dump(mode="json") for env in self._environments.values()],
        }
        
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)
