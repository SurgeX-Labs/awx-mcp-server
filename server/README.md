# AWX MCP Server

<!--mcp-name: io.github.SurgeX-Labs/awx-mcp-server-->

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=awx-mcp&inputs=%5B%7B%22id%22%3A%22awx-url%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20URL%22%7D%2C%7B%22id%22%3A%22awx-username%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20username%22%7D%2C%7B%22id%22%3A%22awx-password%22%2C%22type%22%3A%22promptString%22%2C%22description%22%3A%22Enter%20your%20AWX%20password%20or%20token%22%2C%22password%22%3Atrue%7D%5D&config=%7B%22command%22%3A%22python%22%2C%22args%22%3A%5B%22-m%22%2C%22awx_mcp_server%22%5D%2C%22env%22%3A%7B%22AWX_URL%22%3A%22%24%7Binput%3Aawx-url%7D%22%2C%22AWX_USERNAME%22%3A%22%24%7Binput%3Aawx-username%7D%22%2C%22AWX_PASSWORD%22%3A%22%24%7Binput%3Aawx-password%7D%22%7D%7D)
[![PyPI](https://img.shields.io/pypi/v/awx-mcp-server?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/awx-mcp-server/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green?style=for-the-badge)](https://registry.modelcontextprotocol.io/)

Control AWX/Ansible Tower through natural language - 76 tools for automation.

## Overview

The AWX MCP Server connects AWX/Ansible Tower to AI tools through the Model Context Protocol (MCP). It enables AI assistants like GitHub Copilot, Claude, and Cursor to manage infrastructure automation through natural language.

## Features

- **61 AWX Operations**: Manage job templates, projects, inventories, credentials, organizations, workflow templates, workflow jobs, notifications, and more
- **15 Local Ansible Tools**: Create playbooks, validate syntax, run tasks, manage roles, register projects
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

## AWX Operations (61 Tools)

### Environment Management
- `env_list` - List configured AWX environments
- `env_set_active` - Set the active AWX environment
- `env_get_active` - Get the current active environment
- `env_test_connection` - Test the AWX connection

### Job Templates
- `awx_templates_list` - List job templates
- `awx_template_create` - Create a job template
- `awx_template_delete` - Delete a job template

### Jobs (Execution, Monitoring & Diagnostics)
- `awx_job_launch` - Launch a job from a template
- `awx_job_get` - Get job status/details
- `awx_jobs_list` - List recent jobs / job history
- `awx_job_cancel` - Cancel a running job
- `awx_job_delete` - Delete a job record
- `awx_job_stdout` - View job console output/logs
- `awx_job_events` - View job events/tasks
- `awx_job_failure_summary` - Analyze a job failure with fix suggestions

### Projects
- `awx_projects_list` - List projects
- `awx_project_create` - Create a project
- `awx_project_delete` - Delete a project
- `awx_project_update` - Update/sync a project from SCM

### Inventories
- `awx_inventories_list` - List inventories
- `awx_inventory_create` - Create an inventory
- `awx_inventory_delete` - Delete an inventory

### Inventory Groups
- `awx_inventory_groups_list` - List groups in an inventory
- `awx_inventory_group_create` - Create a group in an inventory
- `awx_inventory_group_delete` - Delete a group

### Inventory Hosts
- `awx_inventory_hosts_list` - List hosts in an inventory
- `awx_inventory_host_create` - Create a host in an inventory
- `awx_inventory_host_delete` - Delete a host

### Organizations
- `awx_organizations_list` - List organizations
- `awx_organization_get` - Get an organization by ID

### Credentials
- `awx_credentials_list` - List credentials
- `awx_credential_types_list` - List credential types
- `awx_credential_create` - Create a credential
- `awx_credential_delete` - Delete a credential

### Workflow Job Templates
- `awx_workflow_templates_list` - List workflow job templates
- `awx_workflow_template_get` - Get workflow template details
- `awx_workflow_template_nodes` - Get the workflow template node graph
- `awx_workflow_template_survey` - Get workflow template survey spec
- `awx_workflow_template_schedules` - List workflow template schedules
- `awx_workflow_template_launch_config` - Get workflow template launch config

### Workflow Jobs
- `awx_workflow_job_launch` - Launch a workflow from a template
- `awx_workflow_job_get` - Get workflow job status/details
- `awx_workflow_jobs_list` - List recent workflow job runs
- `awx_workflow_job_cancel` - Cancel a running workflow job
- `awx_workflow_job_nodes` - Get per-node details of a workflow job
- `awx_workflow_job_relaunch` - Relaunch a previous workflow job
- `awx_workflow_job_delete` - Delete a workflow job record

### Notifications
- `awx_notification_templates_list` - List notification templates
- `awx_notification_template_get` - Get a notification template
- `awx_notification_template_create` - Create a notification template (Slack/email/webhook)
- `awx_notification_template_update` - Update a notification template
- `awx_notification_template_delete` - Delete a notification template
- `awx_notification_template_test` - Send a test notification
- `awx_notifications_list` - List sent notification history
- `awx_job_template_notifications_list` - List a job template's notifications
- `awx_job_template_notification_associate` - Attach a notification to a job template
- `awx_job_template_notification_disassociate` - Remove a notification from a job template
- `awx_workflow_template_notifications_list` - List a workflow template's notifications
- `awx_workflow_template_notification_associate` - Attach a notification to a workflow template
- `awx_workflow_template_notification_disassociate` - Remove a notification from a workflow template

### System
- `awx_system_info` - Get AWX config / dashboard / settings / current-user info

## Local Ansible Development (15 Tools)

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
- **[Query Reference](../AWX_MCP_QUERY_REFERENCE.md)** - All 76 tools with examples
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
