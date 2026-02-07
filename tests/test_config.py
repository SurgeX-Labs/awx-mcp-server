"""Tests for configuration manager."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from awx_mcp.storage import ConfigManager
from awx_mcp.domain import (
    EnvironmentConfig,
    EnvironmentNotFoundError,
    EnvironmentAlreadyExistsError,
    NoActiveEnvironmentError,
)


@pytest.fixture
def temp_config():
    """Create temporary config directory."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        yield config_path


@pytest.fixture
def config_manager(temp_config):
    """Create config manager with temporary storage."""
    return ConfigManager(temp_config)


def test_add_environment(config_manager):
    """Test adding environment."""
    env = EnvironmentConfig(
        name="test",
        base_url="https://awx.test.com",
    )
    
    config_manager.add_environment(env)
    
    retrieved = config_manager.get_environment("test")
    assert retrieved.name == "test"
    assert str(retrieved.base_url) == "https://awx.test.com/"


def test_add_duplicate_environment(config_manager):
    """Test adding duplicate environment."""
    env = EnvironmentConfig(
        name="test",
        base_url="https://awx.test.com",
    )
    
    config_manager.add_environment(env)
    
    with pytest.raises(EnvironmentAlreadyExistsError):
        config_manager.add_environment(env)


def test_get_nonexistent_environment(config_manager):
    """Test getting non-existent environment."""
    with pytest.raises(EnvironmentNotFoundError):
        config_manager.get_environment("nonexistent")


def test_list_environments(config_manager):
    """Test listing environments."""
    env1 = EnvironmentConfig(name="env1", base_url="https://awx1.test.com")
    env2 = EnvironmentConfig(name="env2", base_url="https://awx2.test.com")
    
    config_manager.add_environment(env1)
    config_manager.add_environment(env2)
    
    envs = config_manager.list_environments()
    assert len(envs) == 2
    assert {e.name for e in envs} == {"env1", "env2"}


def test_active_environment(config_manager):
    """Test active environment management."""
    env = EnvironmentConfig(
        name="test",
        base_url="https://awx.test.com",
    )
    
    config_manager.add_environment(env)
    
    # First environment is automatically active
    active = config_manager.get_active()
    assert active.name == "test"
    
    # Add another and set it as active
    env2 = EnvironmentConfig(
        name="test2",
        base_url="https://awx2.test.com",
    )
    config_manager.add_environment(env2)
    config_manager.set_active("test2")
    
    active = config_manager.get_active()
    assert active.name == "test2"


def test_no_active_environment(config_manager):
    """Test when no active environment."""
    with pytest.raises(NoActiveEnvironmentError):
        config_manager.get_active()


def test_delete_environment(config_manager):
    """Test deleting environment."""
    env = EnvironmentConfig(
        name="test",
        base_url="https://awx.test.com",
    )
    
    config_manager.add_environment(env)
    config_manager.delete_environment("test")
    
    with pytest.raises(EnvironmentNotFoundError):
        config_manager.get_environment("test")


def test_update_environment(config_manager):
    """Test updating environment."""
    env = EnvironmentConfig(
        name="test",
        base_url="https://awx.test.com",
        verify_ssl=True,
    )
    
    config_manager.add_environment(env)
    
    # Update
    env.verify_ssl = False
    config_manager.update_environment("test", env)
    
    updated = config_manager.get_environment("test")
    assert updated.verify_ssl is False
