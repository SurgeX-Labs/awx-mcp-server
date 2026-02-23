# AWX MCP Server

<!--mcp-name: io.github.SurgeX-Labs/awx-mcp-server-->

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=awx-mcp&inputs=%5B%7B%22id%22%3A%22awx-url%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20URL%22%7D%2C%7B%22id%22%3A%22awx-username%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20username%22%7D%2C%7B%22id%22%3A%22awx-password%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20password%20or%20token%22%2C%22password%22%3Atrue%7D%5D&config=%7B%22command%22%3A%22python%22%2C%22args%22%3A%5B%22-m%22%2C%22awx_mcp_server%22%5D%2C%22env%22%3A%7B%22AWX_URL%22%3A%22%24%7Binput%3Aawx-url%7D%22%2C%22AWX_USERNAME%22%3A%22%24%7Binput%3Aawx-username%7D%22%2C%22AWX_PASSWORD%22%3A%22%24%7Binput%3Aawx-password%7D%22%7D%7D)
[![PyPI](https://img.shields.io/pypi/v/awx-mcp-server?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/awx-mcp-server/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green?style=for-the-badge)](https://registry.modelcontextprotocol.io/)

Control AWX/Ansible Tower through natural language - 49 tools for automation.

## Overview

The AWX MCP Server connects AWX/Ansible Tower to AI tools through the Model Context Protocol (MCP). It enables AI assistants like GitHub Copilot, Claude, and Cursor to manage infrastructure automation through natural language.

## Features

- **35 AWX Operations**: Manage job templates, projects, inventories, credentials, organizations, and more
- **14 Local Ansible Tools**: Create playbooks, validate syntax, run tasks, manage roles, register projects
- **Natural Language Control**: Use plain English to launch jobs, check status, and manage resources
- **MCP Standard**: Works with any MCP-compatible AI assistant

## Installation

### VS Code (One-Click Install)

Click the button above to install in VS Code with GitHub Copilot, or manually configure:

1. Install the package:
   ```bash
   pip install awx-mcp-server
   ```

2. Open VS Code User Settings (JSON): `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

3. Add MCP server configuration:
   ```json
   {
     "github.copilot.chat.mcpServers": {
       "awx": {
         "command": "python",
         "args": ["-m", "awx_mcp_server"],
         "env": {
           "AWX_URL": "https://your-awx-instance.com",
           "AWX_USERNAME": "your-username", 
           "AWX_PASSWORD": "your-password"
         }
       }
     }
   }
   ```

4. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

### Other MCP Clients (Claude, Cursor, Windsurf, etc.)

```bash
pip install awx-mcp-server
```

Add to your MCP client configuration file:

```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_URL": "https://your-awx-instance.com",
        "AWX_USERNAME": "your-username",
        "AWX_PASSWORD": "your-password"
      }
    }
  }
}
```

### Example Usage

With the server configured, you can use natural language like:

- "List all job templates in AWX"
- "Launch the nginx deployment template"
- "Show me the last 5 job runs"
- "Create a playbook to install nginx"
- "What's the status of job 123?"

## AWX Operations (35 Tools)

### Job Templates & Jobs
- `awx_list_job_templates` - List all job templates
- `awx_get_job_template` - Get template details
- `awx_launch_job_template` - Launch a job from template
- `awx_list_jobs` - List job history
- `awx_get_job_status` - Check job status
- `awx_get_job_output` - Get job output/logs
- `awx_cancel_job` - Cancel running job
- `awx_relaunch_job` - Relaunch previous job

### Projects
- `awx_list_projects` - List all projects
- `awx_get_project` - Get project details
- `awx_create_project` - Create new project
- `awx_update_project` - Update project settings
- `awx_sync_project` - Sync project from SCM

### Inventories & Hosts
- `awx_list_inventories` - List all inventories
- `awx_get_inventory` - Get inventory details
- `awx_list_hosts` - List hosts in inventory
- `awx_get_host` - Get host details
- `awx_create_inventory` - Create new inventory
- `awx_add_host` - Add host to inventory

### Organizations & Teams
- `awx_list_organizations` - List organizations
- `awx_get_organization` - Get organization details
- `awx_list_teams` - List teams
- `awx_get_team` - Get team details

### Credentials
- `awx_list_credentials` - List credentials
- `awx_get_credential` - Get credential details
- `awx_list_credential_types` - List credential types

### Workflow Jobs
- `awx_list_workflow_job_templates` - List workflow templates
- `awx_launch_workflow_job` - Launch workflow
- `awx_get_workflow_job_status` - Check workflow status

### System
- `awx_ping` - Test connection
- `awx_get_config` - Get AWX version/config
- `awx_me` - Get current user info
- `awx_list_schedules` - List job schedules
- `awx_activity_stream` - Get activity logs

## Local Ansible Development (14 Tools)

### Playbook Management
- `create_playbook` - Generate playbook from description
- `validate_playbook` - Check playbook syntax
- `list_playbooks` - List stored playbooks
- `ansible_playbook` - Run playbook locally
- `ansible_task` - Run ad-hoc task
- `ansible_inventory` - List inventory hosts

### Role Management
- `ansible_role` - Run Ansible role
- `create_role_structure` - Create role directory
- `list_roles` - List available roles

### Project Management
- `register_project` - Register Ansible project
- `unregister_project` - Remove project
- `list_registered_projects` - List projects
- `project_playbooks` - List project playbooks
- `project_run_playbook` - Run project playbook
- `git_push_project` - Push project to Git

## Environment Variables

- `AWX_URL` - AWX instance URL (required)
- `AWX_USERNAME` - AWX username (optional if using token)
- `AWX_PASSWORD` - AWX password (optional if using token)
- `AWX_TOKEN` - AWX OAuth token (optional)
- `AWX_VERIFY_SSL` - Verify SSL certificates (default: true)

## Documentation

### Installation & Setup
- **[Quick Start](QUICK_START.md)** - Get started in 5 minutes with local setup
- **[Two Keys Quick Reference](TWO_KEYS_QUICK_REFERENCE.md)** - Understanding MCP API Key vs AAP Token
- **[Remote Client Setup](REMOTE_CLIENT_SETUP.md)** - Configure VS Code for remote MCP server
- **[Remote Deployment](REMOTE_DEPLOYMENT.md)** - Deploy server in Docker, Kubernetes, or cloud
- **[Install from Source](../INSTALL_FROM_SOURCE.md)** - Fork and customize for your organization

### Platform Support
- **[AAP Support](../AAP_SUPPORT.md)** - Configure for Ansible Automation Platform or Ansible Tower
- **[OS Compatibility](../OS_COMPATIBILITY.md)** - Windows, macOS, and Linux installation guides

### Advanced
- **[Query Reference](../AWX_MCP_QUERY_REFERENCE.md)** - All 49 tools with examples
- **[Vault Integration](VAULT_INTEGRATION.md)** - HashiCorp Vault for secrets management
- **[GitHub Installation](GITHUB_INSTALLATION.md)** - Install directly from GitHub

### Resources
- **GitHub Repository**: https://github.com/SurgeX-Labs/awx-mcp-server
- **PyPI Package**: https://pypi.org/project/awx-mcp-server/
- **MCP Protocol**: https://modelcontextprotocol.io/

## License

Apache License 2.0

## Support

- Issues: https://github.com/SurgeX-Labs/awx-mcp-server/issues
- Discussions: https://github.com/SurgeX-Labs/awx-mcp-server/discussions
