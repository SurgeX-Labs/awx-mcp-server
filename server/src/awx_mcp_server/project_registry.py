"""Project registry for local Ansible development.

Allows users to register local Ansible project directories for easy
playbook discovery, inventory management, and execution before
pushing to AWX via SCM.
"""

import json
from pathlib import Path
from typing import Any, Optional

import yaml

from awx_mcp_server.utils import get_logger

logger = get_logger(__name__)

# Registry file location
REGISTRY_FILE = Path.home() / ".awx-mcp" / "project_registry.json"


def _load_registry() -> dict[str, Any]:
    """Load project registry from disk."""
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {"projects": {}, "default": None}
    return {"projects": {}, "default": None}


def _save_registry(registry: dict[str, Any]) -> None:
    """Save project registry to disk."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2, default=str), encoding="utf-8"
    )


def register_project(
    name: str,
    path: str,
    scm_url: Optional[str] = None,
    scm_branch: Optional[str] = None,
    inventory: Optional[str] = None,
    default_playbook: Optional[str] = None,
    description: Optional[str] = None,
    set_default: bool = False,
) -> dict[str, Any]:
    """
    Register a local Ansible project for easy reuse.

    Args:
        name: Project alias name
        path: Absolute path to project root directory
        scm_url: Git remote URL (for pushing to AWX)
        scm_branch: Git branch (default: main)
        inventory: Default inventory file relative to project root
        default_playbook: Default playbook filename
        description: Project description
        set_default: Set as the default project

    Returns:
        Dict with registration result
    """
    project_path = Path(path)
    if not project_path.is_dir():
        return {
            "status": "error",
            "message": f"Directory not found: {path}",
        }

    registry = _load_registry()

    # Auto-detect SCM info if not provided
    if not scm_url:
        git_config = project_path / ".git" / "config"
        if git_config.exists():
            try:
                config_text = git_config.read_text(encoding="utf-8")
                for line in config_text.split("\n"):
                    if "url = " in line:
                        scm_url = line.split("url = ", 1)[1].strip()
                        break
            except IOError:
                pass

    # Auto-detect inventory
    if not inventory:
        for inv_name in ["inventory", "inventory.yml", "inventory.ini", "hosts", "hosts.yml"]:
            if (project_path / inv_name).exists():
                inventory = inv_name
                break

    # Auto-detect default playbook
    if not default_playbook:
        for pb_name in ["site.yml", "main.yml", "playbook.yml"]:
            if (project_path / pb_name).exists():
                default_playbook = pb_name
                break

    project_info = {
        "name": name,
        "path": str(project_path.resolve()),
        "scm_url": scm_url,
        "scm_branch": scm_branch or "main",
        "inventory": inventory,
        "default_playbook": default_playbook,
        "description": description or "",
    }

    registry["projects"][name] = project_info

    if set_default or len(registry["projects"]) == 1:
        registry["default"] = name

    _save_registry(registry)

    return {
        "status": "registered",
        "project": project_info,
        "is_default": registry["default"] == name,
    }


def unregister_project(name: str) -> dict[str, Any]:
    """
    Remove a project from the registry.

    Args:
        name: Project alias name

    Returns:
        Dict with result
    """
    registry = _load_registry()

    if name not in registry["projects"]:
        return {"status": "error", "message": f"Project '{name}' not found in registry"}

    del registry["projects"][name]
    if registry["default"] == name:
        registry["default"] = next(iter(registry["projects"]), None)

    _save_registry(registry)

    return {"status": "removed", "project": name}


def list_projects() -> dict[str, Any]:
    """
    List all registered projects.

    Returns:
        Dict with project list and default
    """
    registry = _load_registry()

    projects = []
    for name, info in registry["projects"].items():
        project_path = Path(info["path"])
        info_copy = dict(info)
        info_copy["exists"] = project_path.is_dir()
        info_copy["is_default"] = (name == registry["default"])

        # Count playbooks
        if project_path.is_dir():
            yml_files = list(project_path.glob("*.yml")) + list(project_path.glob("*.yaml"))
            info_copy["playbook_count"] = len([
                f for f in yml_files
                if not f.name.startswith(".")
                and f.name not in ("requirements.yml", "galaxy.yml", "meta.yml")
            ])
        else:
            info_copy["playbook_count"] = 0

        projects.append(info_copy)

    return {
        "count": len(projects),
        "default": registry["default"],
        "projects": projects,
    }


def get_project(name: Optional[str] = None) -> dict[str, Any]:
    """
    Get a registered project by name (or default).

    Args:
        name: Project name (uses default if not specified)

    Returns:
        Dict with project info
    """
    registry = _load_registry()

    if not name:
        name = registry["default"]
    if not name or name not in registry["projects"]:
        return {
            "status": "error",
            "message": f"Project '{name}' not found" if name else "No default project set",
        }

    return {"status": "found", "project": registry["projects"][name]}


def discover_playbooks(
    project_name: Optional[str] = None,
    project_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Discover playbooks under a project root.

    Args:
        project_name: Registered project name
        project_path: Direct path to scan (overrides project_name)

    Returns:
        Dict with discovered playbooks
    """
    if project_path:
        root = Path(project_path)
    elif project_name:
        result = get_project(project_name)
        if result.get("status") == "error":
            return result
        root = Path(result["project"]["path"])
    else:
        # Use default project
        result = get_project()
        if result.get("status") == "error":
            return result
        root = Path(result["project"]["path"])

    if not root.is_dir():
        return {"status": "error", "message": f"Directory not found: {root}"}

    playbooks = []
    skip_names = {
        "requirements.yml", "galaxy.yml", "meta.yml",
        "requirements.yaml", "galaxy.yaml", "meta.yaml",
    }
    skip_dirs = {"roles", ".git", "collections", "venv", ".venv", "__pycache__", "node_modules"}

    for yml_file in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        # Skip files in certain directories
        if any(part in skip_dirs for part in yml_file.parts):
            continue
        if yml_file.name in skip_names:
            continue
        if yml_file.name.startswith("."):
            continue

        # Check if it looks like a playbook (list of plays with hosts key)
        try:
            content = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
            if isinstance(content, list) and content and isinstance(content[0], dict):
                if "hosts" in content[0] or "import_playbook" in content[0]:
                    rel_path = yml_file.relative_to(root)
                    plays = len(content)
                    hosts = content[0].get("hosts", "N/A")
                    playbooks.append({
                        "name": yml_file.name,
                        "relative_path": str(rel_path),
                        "full_path": str(yml_file),
                        "plays": plays,
                        "hosts": str(hosts),
                    })
        except Exception:
            continue

    # Also discover roles
    roles_dir = root / "roles"
    roles = []
    if roles_dir.is_dir():
        for d in sorted(roles_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                subdirs = [s.name for s in d.iterdir() if s.is_dir()]
                roles.append({"name": d.name, "directories": subdirs})

    return {
        "status": "success",
        "project_root": str(root),
        "playbooks": playbooks,
        "playbook_count": len(playbooks),
        "roles": roles,
        "role_count": len(roles),
    }


async def project_run_playbook(
    playbook: str,
    project_name: Optional[str] = None,
    extra_vars: Optional[dict[str, Any]] = None,
    limit: Optional[str] = None,
    tags: Optional[list[str]] = None,
    skip_tags: Optional[list[str]] = None,
    check_mode: bool = False,
    verbose: int = 0,
) -> dict[str, Any]:
    """
    Run a playbook using a registered project's inventory and environment.

    Args:
        playbook: Playbook filename (relative to project root)
        project_name: Registered project name (uses default if not specified)
        extra_vars: Extra variables
        limit: Host limit pattern
        tags: Tags to run
        skip_tags: Tags to skip
        check_mode: Dry-run mode
        verbose: Verbosity level

    Returns:
        Dict with execution result
    """
    from awx_mcp_server.playbook_manager import run_playbook

    result = get_project(project_name)
    if result.get("status") == "error":
        return result

    project = result["project"]
    project_path = Path(project["path"])

    # Resolve playbook path
    playbook_path = project_path / playbook
    if not playbook_path.exists():
        return {
            "status": "error",
            "message": f"Playbook '{playbook}' not found in project '{project['name']}' at {project_path}",
        }

    # Use project inventory if available
    inventory = None
    if project.get("inventory"):
        inv_path = project_path / project["inventory"]
        if inv_path.exists():
            inventory = str(inv_path)

    exec_result = await run_playbook(
        str(playbook_path),
        workspace=str(project_path),
        inventory=inventory,
        extra_vars=extra_vars,
        limit=limit,
        tags=tags,
        skip_tags=skip_tags,
        check_mode=check_mode,
        verbose=verbose,
    )

    exec_result["project"] = project["name"]
    return exec_result


async def git_push_project(
    project_name: Optional[str] = None,
    commit_message: Optional[str] = None,
    branch: Optional[str] = None,
    add_all: bool = True,
) -> dict[str, Any]:
    """
    Stage, commit, and push project changes to git remote.

    Args:
        project_name: Registered project name
        commit_message: Git commit message
        branch: Branch to push to (default: from project config)
        add_all: Whether to git add all changes

    Returns:
        Dict with push result
    """
    import asyncio

    result = get_project(project_name)
    if result.get("status") == "error":
        return result

    project = result["project"]
    project_path = Path(project["path"])
    branch = branch or project.get("scm_branch", "main")
    commit_message = commit_message or "Update playbooks via AWX MCP"

    # Check if it's a git repo
    if not (project_path / ".git").is_dir():
        return {
            "status": "error",
            "message": f"Project '{project['name']}' is not a git repository",
        }

    output_parts = []

    async def _run_git(*args: str) -> tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_path),
        )
        stdout, stderr = await proc.communicate()
        return (
            proc.returncode,
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
        )

    try:
        # Stage changes
        if add_all:
            rc, out, err = await _run_git("add", "-A")
            if rc != 0:
                return {"status": "error", "message": f"git add failed: {err}"}
            output_parts.append(f"Staged: {out or 'all changes'}")

        # Check if there are changes to commit
        rc, out, err = await _run_git("status", "--porcelain")
        if not out:
            return {
                "status": "no_changes",
                "message": "No changes to commit",
                "project": project["name"],
            }

        # Commit
        rc, out, err = await _run_git("commit", "-m", commit_message)
        if rc != 0:
            return {"status": "error", "message": f"git commit failed: {err}"}
        output_parts.append(f"Committed: {out.split(chr(10))[0]}")

        # Push
        rc, out, err = await _run_git("push", "origin", branch)
        if rc != 0:
            return {"status": "error", "message": f"git push failed: {err or out}"}
        output_parts.append(f"Pushed to origin/{branch}")

        return {
            "status": "pushed",
            "project": project["name"],
            "branch": branch,
            "message": commit_message,
            "output": "\n".join(output_parts),
        }
    except FileNotFoundError:
        return {"status": "error", "message": "git not found in PATH"}
