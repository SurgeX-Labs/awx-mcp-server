"""Playbook and role management for local Ansible development.

Provides tools for creating, validating, and running Ansible playbooks
and roles locally before pushing to AWX via SCM.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

import yaml

from awx_mcp_server.utils import get_logger

logger = get_logger(__name__)

# Default workspace for playbooks
DEFAULT_WORKSPACE = Path.home() / ".awx-mcp" / "playbooks"


def _ensure_workspace(workspace: Optional[str] = None) -> Path:
    """Ensure workspace directory exists and return path."""
    ws = Path(workspace) if workspace else DEFAULT_WORKSPACE
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def create_playbook(
    name: str,
    content: str | dict | list,
    workspace: Optional[str] = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Create an Ansible playbook file from YAML string or dict/list.

    Args:
        name: Playbook filename (e.g., 'deploy.yml')
        content: YAML string, dict, or list of plays
        workspace: Directory to create playbook in (default: ~/.awx-mcp/playbooks)
        overwrite: Whether to overwrite existing file

    Returns:
        Dict with path, status, and content preview
    """
    ws = _ensure_workspace(workspace)

    # Ensure .yml extension
    if not name.endswith(('.yml', '.yaml')):
        name += '.yml'

    playbook_path = ws / name

    if playbook_path.exists() and not overwrite:
        return {
            "status": "error",
            "message": f"Playbook '{name}' already exists. Use overwrite=true to replace.",
            "path": str(playbook_path),
        }

    # Convert content to YAML if needed
    if isinstance(content, str):
        # Validate it's valid YAML
        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                return {"status": "error", "message": "Empty or invalid YAML content"}
            yaml_content = content
        except yaml.YAMLError as e:
            return {"status": "error", "message": f"Invalid YAML: {e}"}
    elif isinstance(content, (dict, list)):
        # If it's a single play dict, wrap in list
        if isinstance(content, dict):
            content = [content]
        yaml_content = yaml.dump(content, default_flow_style=False, sort_keys=False)
        parsed = content
    else:
        return {"status": "error", "message": "Content must be a YAML string, dict, or list"}

    # Validate structure - playbook must be a list of plays
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return {"status": "error", "message": "Playbook must be a list of plays (YAML list)"}

    # Write playbook
    playbook_path.write_text(yaml_content, encoding="utf-8")

    return {
        "status": "created",
        "path": str(playbook_path),
        "name": name,
        "plays": len(parsed),
        "preview": yaml_content[:500],
    }


async def validate_playbook(
    playbook: str,
    workspace: Optional[str] = None,
    inventory: Optional[str] = None,
) -> dict[str, Any]:
    """
    Validate playbook syntax using ansible-playbook --syntax-check.

    Args:
        playbook: Playbook filename or full path
        workspace: Workspace directory (if playbook is just a name)
        inventory: Optional inventory file/path for validation

    Returns:
        Dict with validation result
    """
    # Resolve playbook path
    playbook_path = Path(playbook)
    if not playbook_path.is_absolute():
        ws = _ensure_workspace(workspace)
        playbook_path = ws / playbook

    if not playbook_path.exists():
        return {
            "status": "error",
            "message": f"Playbook not found: {playbook_path}",
        }

    cmd = ["ansible-playbook", "--syntax-check"]
    if inventory:
        cmd.extend(["-i", inventory])
    else:
        cmd.extend(["-i", "localhost,"])
    cmd.append(str(playbook_path))

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(playbook_path.parent),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode == 0:
            return {
                "status": "valid",
                "message": "Playbook syntax is valid",
                "playbook": str(playbook_path),
                "output": stdout_text or stderr_text,
            }
        else:
            return {
                "status": "invalid",
                "message": "Playbook has syntax errors",
                "playbook": str(playbook_path),
                "errors": stderr_text or stdout_text,
                "returncode": process.returncode,
            }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "ansible-playbook not found. Install Ansible: pip install ansible",
        }
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "Syntax check timed out after 60 seconds",
        }


async def run_playbook(
    playbook: str,
    workspace: Optional[str] = None,
    inventory: Optional[str] = None,
    extra_vars: Optional[dict[str, Any]] = None,
    limit: Optional[str] = None,
    tags: Optional[list[str]] = None,
    skip_tags: Optional[list[str]] = None,
    check_mode: bool = False,
    verbose: int = 0,
) -> dict[str, Any]:
    """
    Execute an Ansible playbook locally.

    Args:
        playbook: Playbook filename or full path
        workspace: Workspace directory
        inventory: Inventory file/string (default: localhost)
        extra_vars: Extra variables dict
        limit: Host limit pattern
        tags: Tags to run
        skip_tags: Tags to skip
        check_mode: Dry-run mode (--check)
        verbose: Verbosity level (0-4)

    Returns:
        Dict with execution result
    """
    playbook_path = Path(playbook)
    if not playbook_path.is_absolute():
        ws = _ensure_workspace(workspace)
        playbook_path = ws / playbook

    if not playbook_path.exists():
        return {"status": "error", "message": f"Playbook not found: {playbook_path}"}

    cmd = ["ansible-playbook"]

    # Inventory
    if inventory:
        cmd.extend(["-i", inventory])
    else:
        cmd.extend(["-i", "localhost,", "-c", "local"])

    # Extra vars
    if extra_vars:
        cmd.extend(["-e", json.dumps(extra_vars)])

    # Limit
    if limit:
        cmd.extend(["--limit", limit])

    # Tags
    if tags:
        cmd.extend(["--tags", ",".join(tags)])
    if skip_tags:
        cmd.extend(["--skip-tags", ",".join(skip_tags)])

    # Check mode
    if check_mode:
        cmd.append("--check")

    # Verbosity
    if verbose > 0:
        cmd.append("-" + "v" * min(verbose, 4))

    cmd.append(str(playbook_path))

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(playbook_path.parent),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        return {
            "status": "successful" if process.returncode == 0 else "failed",
            "playbook": str(playbook_path),
            "returncode": process.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text if stderr_text else None,
            "check_mode": check_mode,
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "ansible-playbook not found. Install Ansible: pip install ansible",
        }
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "Playbook execution timed out after 300 seconds",
        }


async def run_adhoc_task(
    module: str,
    args: Optional[str] = None,
    hosts: str = "localhost",
    inventory: Optional[str] = None,
    extra_vars: Optional[dict[str, Any]] = None,
    connection: str = "local",
    become: bool = False,
) -> dict[str, Any]:
    """
    Run an ad-hoc Ansible task.

    Args:
        module: Ansible module name (e.g., 'ping', 'shell', 'copy')
        args: Module arguments string
        hosts: Host pattern (default: localhost)
        inventory: Inventory file/string
        extra_vars: Extra variables
        connection: Connection type (default: local)
        become: Use privilege escalation

    Returns:
        Dict with task result
    """
    cmd = ["ansible", hosts]

    # Module
    cmd.extend(["-m", module])

    # Module args
    if args:
        cmd.extend(["-a", args])

    # Inventory
    if inventory:
        cmd.extend(["-i", inventory])
    else:
        cmd.extend(["-i", f"{hosts},"])

    # Connection
    cmd.extend(["-c", connection])

    # Extra vars
    if extra_vars:
        cmd.extend(["-e", json.dumps(extra_vars)])

    # Become
    if become:
        cmd.append("--become")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        return {
            "status": "successful" if process.returncode == 0 else "failed",
            "module": module,
            "hosts": hosts,
            "returncode": process.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text if stderr_text else None,
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "ansible not found. Install Ansible: pip install ansible",
        }
    except asyncio.TimeoutError:
        return {"status": "error", "message": "Ad-hoc task timed out after 120 seconds"}


async def run_role(
    role: str,
    hosts: str = "localhost",
    workspace: Optional[str] = None,
    inventory: Optional[str] = None,
    extra_vars: Optional[dict[str, Any]] = None,
    connection: str = "local",
) -> dict[str, Any]:
    """
    Execute an Ansible role by generating a temporary playbook.

    Args:
        role: Role name or path
        hosts: Target hosts
        workspace: Workspace directory containing roles
        inventory: Inventory file/string
        extra_vars: Extra variables
        connection: Connection type

    Returns:
        Dict with execution result
    """
    ws = _ensure_workspace(workspace)

    # Generate temporary playbook to run the role
    temp_playbook = {
        "name": f"Run role: {role}",
        "hosts": hosts,
        "connection": connection,
        "roles": [role],
    }
    if extra_vars:
        temp_playbook["vars"] = extra_vars

    temp_file = ws / f"_temp_role_{role.replace('/', '_')}.yml"
    try:
        temp_file.write_text(
            yaml.dump([temp_playbook], default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        result = await run_playbook(
            str(temp_file),
            workspace=workspace,
            inventory=inventory,
        )
        result["role"] = role
        return result
    finally:
        # Clean up temp playbook
        if temp_file.exists():
            temp_file.unlink()


def create_role_structure(
    name: str,
    workspace: Optional[str] = None,
    include_dirs: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Scaffold an Ansible role directory structure.

    Args:
        name: Role name
        workspace: Workspace where roles/ lives
        include_dirs: Which subdirs to include (default: all standard dirs)

    Returns:
        Dict with created structure
    """
    ws = _ensure_workspace(workspace)
    roles_dir = ws / "roles"
    role_path = roles_dir / name

    if role_path.exists():
        return {
            "status": "error",
            "message": f"Role '{name}' already exists at {role_path}",
        }

    standard_dirs = include_dirs or [
        "tasks",
        "handlers",
        "templates",
        "files",
        "vars",
        "defaults",
        "meta",
    ]

    created_files = []

    for subdir in standard_dirs:
        dir_path = role_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)

        # Create main.yml for each dir (except templates/files)
        if subdir not in ("templates", "files"):
            main_file = dir_path / "main.yml"
            if subdir == "tasks":
                content = f"---\n# Tasks for role: {name}\n- name: Example task\n  ansible.builtin.debug:\n    msg: \"Role {name} is running\"\n"
            elif subdir == "handlers":
                content = f"---\n# Handlers for role: {name}\n"
            elif subdir == "vars":
                content = f"---\n# Vars for role: {name}\n"
            elif subdir == "defaults":
                content = f"---\n# Default variables for role: {name}\n"
            elif subdir == "meta":
                content = (
                    f"---\n# Meta for role: {name}\n"
                    "galaxy_info:\n"
                    f"  role_name: {name}\n"
                    "  author: AWX MCP\n"
                    "  description: Auto-generated role\n"
                    "  min_ansible_version: '2.9'\n"
                    "  platforms: []\n"
                    "  galaxy_tags: []\n"
                    "dependencies: []\n"
                )
            else:
                content = f"---\n# {subdir} for role: {name}\n"

            main_file.write_text(content, encoding="utf-8")
            created_files.append(str(main_file.relative_to(ws)))

    # Create README
    readme = role_path / "README.md"
    readme.write_text(
        f"# {name}\n\nAnsible role generated by AWX MCP Server.\n\n"
        "## Requirements\n\nNone.\n\n"
        "## Role Variables\n\nSee `defaults/main.yml`.\n\n"
        "## Example Playbook\n\n```yaml\n- hosts: all\n  roles:\n"
        f"    - {name}\n```\n",
        encoding="utf-8",
    )
    created_files.append(str(readme.relative_to(ws)))

    return {
        "status": "created",
        "role": name,
        "path": str(role_path),
        "directories": standard_dirs,
        "files": created_files,
    }


def list_playbooks(workspace: Optional[str] = None) -> dict[str, Any]:
    """
    List playbooks in workspace.

    Args:
        workspace: Workspace directory

    Returns:
        Dict with list of playbooks
    """
    ws = _ensure_workspace(workspace)
    playbooks = []

    for f in sorted(ws.glob("*.yml")) + sorted(ws.glob("*.yaml")):
        if f.name.startswith("_temp_"):
            continue
        try:
            content = yaml.safe_load(f.read_text(encoding="utf-8"))
            plays = len(content) if isinstance(content, list) else 1
        except Exception:
            plays = None

        playbooks.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "plays": plays,
        })

    return {
        "workspace": str(ws),
        "count": len(playbooks),
        "playbooks": playbooks,
    }


def list_roles(workspace: Optional[str] = None) -> dict[str, Any]:
    """
    List roles in workspace.

    Args:
        workspace: Workspace directory

    Returns:
        Dict with list of roles
    """
    ws = _ensure_workspace(workspace)
    roles_dir = ws / "roles"

    if not roles_dir.exists():
        return {"workspace": str(ws), "count": 0, "roles": []}

    roles = []
    for d in sorted(roles_dir.iterdir()):
        if d.is_dir():
            subdirs = [s.name for s in d.iterdir() if s.is_dir()]
            roles.append({
                "name": d.name,
                "path": str(d),
                "directories": subdirs,
            })

    return {
        "workspace": str(ws),
        "count": len(roles),
        "roles": roles,
    }


async def ansible_inventory_list(
    inventory: str = "localhost,",
    workspace: Optional[str] = None,
) -> dict[str, Any]:
    """
    List inventory hosts and groups using ansible-inventory.

    Args:
        inventory: Inventory file, path, or host list
        workspace: Working directory

    Returns:
        Dict with inventory graph
    """
    ws = _ensure_workspace(workspace)

    cmd = ["ansible-inventory", "-i", inventory, "--list"]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(ws),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)

        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode == 0:
            try:
                inventory_data = json.loads(stdout_text)
            except json.JSONDecodeError:
                inventory_data = stdout_text

            return {
                "status": "success",
                "inventory": inventory,
                "data": inventory_data,
            }
        else:
            return {
                "status": "error",
                "message": stderr_text or stdout_text,
                "returncode": process.returncode,
            }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "ansible-inventory not found. Install Ansible: pip install ansible",
        }
    except asyncio.TimeoutError:
        return {"status": "error", "message": "Inventory listing timed out"}
