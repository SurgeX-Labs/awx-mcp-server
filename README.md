# AWX MCP - AI-Powered AWX/AAP/Ansible Automation

**Industry-standard MCP server for AWX/AAP/Ansible Tower automation**

The AWX MCP Server connects **AWX**, **Ansible Automation Platform (AAP)**, and **Ansible Tower** to AI tools, giving AI agents and assistants the ability to manage job templates, launch and monitor jobs, manage inventories and projects, and automate infrastructure workflows through natural language interactions.

**Designed for developers who want to integrate their AI tools with AWX/AAP/Tower automation capabilities.**

**✨ Supports AWX (open source), AAP (Red Hat), and Ansible Tower (legacy) - same API, same features!**

---

## 🎯 Usage Patterns

### Primary: MCP Server (Industry Standard) ⭐ RECOMMENDED

<img src="https://img.shields.io/badge/MCP-Server-green?logo=python" alt="MCP Server"/>

**Standard MCP implementation using STDIO transport (like Postman MCP, Claude MCP)**

**Use Case**: AI assistants (GitHub Copilot, Claude, Cursor) + AWX automation

**Features**:
- ✅ Works with any MCP client (Copilot, Claude, Cursor, Windsurf, etc.)
- ✅ Industry standard pattern (STDIO transport)
- ✅ Simple installation: `pip install git+https://github.com/USERNAME/awx-mcp-server.git`
- ✅ Portable across all MCP-compatible tools
- ✅ 18+ AWX operations (templates, jobs, projects, inventories)

**Best For**: AI-powered automation, natural language AWX control, any MCP client

---

### Optional: VS Code Extension (UI Enhancement)

<img src="https://img.shields.io/badge/VS%20Code-Optional-007ACC?logo=visualstudiocode" alt="VS Code Extension"/>

**Optional UI features for VS Code users**

**Use Case**: VS Code users who want additional UI (sidebar views, tree providers)

**Features**:
- ✅ Sidebar with AWX instances, jobs, metrics
- ✅ Tree view of AWX resources
- ✅ Configuration webview
- ✅ Auto-configures MCP (or respects manual setup)

**Best For**: VS Code users wanting rich UI alongside MCP functionality

---

## 🚀 Quick Start

### Installation Methods

You have **three ways** to install and run the AWX MCP Server:

| Method | Best For | Installation |
|--------|----------|--------------|
| **📦 PyPI (pip)** | Quick install, production use | `pip install awx-mcp-server` |
| **🔧 From Source** | Customization, development, enterprise forks | Clone from GitHub, edit code |
| **🐳 Docker** | Containerized deployment, teams | `docker run surgexlabs/awx-mcp-server` |

**→ For customization and running from your own repository, see [INSTALL_FROM_SOURCE.md](INSTALL_FROM_SOURCE.md)**

---

### Option 1: PyPI Installation (Recommended for Quick Start)

#### Install from PyPI

```bash
# Install the MCP server
pip install awx-mcp-server

# Verify installation
python -m awx_mcp_server --version
```

#### Configure for VS Code

**Edit VS Code settings.json** (`Ctrl+,` → Search "chat.mcp"):

```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://your-awx.com"
      },
      "secrets": {
        "AWX_TOKEN": "your-awx-token"
      }
    }
  }
}
```

**Restart VS Code** and the MCP server will be available in Copilot Chat.

---

### Option 2: Install from Source (For Customization)

**Perfect for**: Forking, customization, enterprise deployments, contributing

**Quick install**:
```bash
# Clone the repository (or your fork)
git clone https://github.com/SurgeX-Labs/awx-mcp-server.git
cd awx-mcp-server/awx-mcp-python/server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Install in editable mode
pip install -e .

# Verify
python -m awx_mcp_server --version
```

**VS Code configuration** (use venv Python):
```json
{
  "mcpServers": {
    "awx": {
      "command": "/path/to/awx-mcp-server/awx-mcp-python/server/venv/bin/python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://your-awx.com"
      },
      "secrets": {
        "AWX_TOKEN": "your-token"
      }
    }
  }
}
```

**📖 Full Guide**: See [INSTALL_FROM_SOURCE.md](INSTALL_FROM_SOURCE.md) for:
- Forking the repository
- Making customizations to the code
- Running from your own fork/repository
- Building custom Docker images from source
- Enterprise deployment and CI/CD

---

### Option 3: Remote Server Mode (Team/Enterprise)

#### Prerequisites
- Python 3.10+
- AWX/Ansible Tower instance
- (Optional) Docker or Kubernetes

#### Quick Start with Docker

```bash
cd awx-mcp-python/server

# Start server with monitoring stack
docker-compose up -d

# Server available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Metrics: http://localhost:8000/prometheus-metrics
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
```

#### Quick Start with Python

```bash
cd awx-mcp-python/server

# Install
pip install -e .

# Configure AWX environment (interactive)
awx-mcp-server env list

# Start server
awx-mcp-server start --host 0.0.0.0 --port 8000
```

#### CLI Usage

```bash
# List job templates
awx-mcp-server templates list

# Launch job
awx-mcp-server jobs launch "Deploy App" --extra-vars '{"env":"prod"}'

# Monitor job
awx-mcp-server jobs get 123
awx-mcp-server jobs stdout 123

# Manage projects
awx-mcp-server projects list
awx-mcp-server projects update "My Project"

# List inventories
awx-mcp-server inventories list
```

#### REST API Usage

```bash
# Create API key (first time)
curl -X POST http://localhost:8000/api/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "chatbot", "tenant_id": "team1", "expires_days": 90}'

# List job templates
curl http://localhost:8000/api/v1/job-templates \
  -H "X-API-Key: awx_mcp_xxxxx"

# Launch job
curl -X POST http://localhost:8000/api/v1/jobs/launch \
  -H "X-API-Key: awx_mcp_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"template_name": "Deploy App", "extra_vars": {"env": "prod"}}'

# Get job status
curl http://localhost:8000/api/v1/jobs/123 \
  -H "X-API-Key: awx_mcp_xxxxx"

# Get job output
curl http://localhost:8000/api/v1/jobs/123/stdout \
  -H "X-API-Key: awx_mcp_xxxxx"
```

#### Kubernetes Deployment

```bash
cd server/deployment/helm

helm install awx-mcp-server . \
  --set replicaCount=3 \
  --set autoscaling.enabled=true \
  --set taskPods.enabled=true
```

**See**: [server/README.md](server/README.md) for detailed guide

---

## 🎨 Integration Examples

### Integrate with Custom Chatbot

```python
import httpx

class AWXChatbot:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def handle_message(self, user_message: str):
        """Process user message and call AWX API"""
        if "list templates" in user_message.lower():
            return await self.list_templates()
        elif "launch" in user_message.lower():
            template_name = self.extract_template_name(user_message)
            return await self.launch_job(template_name)
        elif "job status" in user_message.lower():
            job_id = self.extract_job_id(user_message)
            return await self.get_job(job_id)
    
    async def list_templates(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/job-templates",
                headers=self.headers
            )
            return response.json()
    
    async def launch_job(self, template_name: str, extra_vars: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/jobs/launch",
                headers=self.headers,
                json={"template_name": template_name, "extra_vars": extra_vars}
            )
            return response.json()
    
    async def get_job(self, job_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/jobs/{job_id}",
                headers=self.headers
            )
            return response.json()

# Usage
chatbot = AWXChatbot(api_key="awx_mcp_xxxxx")
response = await chatbot.handle_message("list all job templates")
```

### Integrate with Slack Bot

```python
from slack_bolt.async_app import AsyncApp
import httpx

app = AsyncApp(token="xoxb-your-token")
awx_api_key = "awx_mcp_xxxxx"
awx_base_url = "http://localhost:8000"

@app.message("awx")
async def handle_awx_command(message, say):
    text = message['text']
    
    if "launch" in text:
        # Extract template name from message
        template = extract_template(text)
        
        # Call AWX API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{awx_base_url}/api/v1/jobs/launch",
                headers={"X-API-Key": awx_api_key},
                json={"template_name": template}
            )
            job = response.json()
        
        await say(f"✅ Job launched! ID: {job['id']}, Status: {job['status']}")
```

---

## 🔧 Available AWX Operations

Both the VS Code extension and the MCP server support all **76 tools** — **61 AWX operations** (below) plus **15 local Ansible development tools** (see [`server/README.md`](server/README.md)). The [Query Reference](AWX_MCP_QUERY_REFERENCE.md) has example prompts for every tool.

### Environment Management
- `env_list` - List configured AWX environments
- `env_set_active` - Set the active AWX environment
- `env_get_active` - Get the current active environment
- `env_test_connection` - Test the AWX connection

### System
- `awx_system_info` - Get AWX config / dashboard / settings / current-user info

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

### Inventories, Groups & Hosts
- `awx_inventories_list` - List inventories
- `awx_inventory_create` - Create an inventory
- `awx_inventory_delete` - Delete an inventory
- `awx_inventory_groups_list` - List groups in an inventory
- `awx_inventory_group_create` - Create a group in an inventory
- `awx_inventory_group_delete` - Delete a group
- `awx_inventory_hosts_list` - List hosts in an inventory
- `awx_inventory_host_create` - Create a host in an inventory
- `awx_inventory_host_delete` - Delete a host

### Organizations & Credentials
- `awx_organizations_list` - List organizations
- `awx_organization_get` - Get an organization by ID
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

---

## 📦 Project Structure

```
awx-mcp-python/
├── vscode-extension/          # VS Code extension with GitHub Copilot
│   ├── src/                   # Extension TypeScript source
│   ├── package.json           # Extension manifest
│   ├── README.md              # Extension guide
│   └── CHANGELOG.md
│
│
├── server/                    # Standalone web server
│   ├── src/awx_mcp_server/
│   │   ├── cli.py             # CLI commands (468 lines)
│   │   ├── http_server.py     # FastAPI REST API
│   │   ├── mcp_server.py      # MCP server integration
│   │   ├── monitoring.py      # Prometheus metrics
│   │   ├── task_pods.py       # Kubernetes task pods
│   │   ├── clients/           # AWX clients (self-contained)
│   │   ├── storage/           # Config & credentials
│   │   └── domain/            # Models & exceptions
│   ├── deployment/
│   │   ├── docker-compose.yml # Docker Compose stack
│   │   ├── Dockerfile         # Container image
│   │   └── helm/              # Kubernetes Helm chart
│   ├── pyproject.toml
│   └── README.md
│
└── tests/                     # Shared test suite
    ├── test_*.py
    └── conftest.py
```

---

## 🏗️ Architecture

### VS Code Extension Architecture

```
┌─────────────────┐
│   VS Code IDE   │
│                 │
│  ┌───────────┐  │     stdio      ┌──────────────┐
│  │  GitHub   │──┼────transport───▶│  MCP Server  │
│  │  Copilot  │  │    (local)     │   (shared)   │
│  │   Chat    │◀─┼────────────────│   76 Tools   │
│  └───────────┘  │                └──────────────┘
│                 │                        │
│  ┌───────────┐  │                        │
│  │ @awx Chat │  │                        │
│  │Participant│  │                        ▼
│  └───────────┘  │                 ┌──────────────┐
└─────────────────┘                 │     AWX      │
                                    │   Instance   │
                                    └──────────────┘
```

**Flow**:
1. User types `@awx list templates` in Copilot Chat
2. Extension sends MCP request to local server via stdio
3. MCP server calls AWX REST API
4. Results returned to Copilot Chat
5. AI formats response naturally

### Web Server Architecture

```
┌──────────────┐      REST API       ┌──────────────┐
│   Chatbot    │────────────────────▶│  FastAPI     │
│  /Custom App │   (HTTP/JSON)       │   Server     │
└──────────────┘                     └──────────────┘
                                            │
┌──────────────┐      REST API       │
│   Slack Bot  │────────────────────▶│
└──────────────┘                     │
                                     │
┌──────────────┐         CLI         │
│   Terminal   │────────────────────▶│
│   Scripts    │   (commands)        │
└──────────────┘                     │
                                     │
                              ┌──────┴───────┐
                              │              │
                              │   Clients    │
                              │  REST + CLI  │
                              │              │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │     AWX      │
                              │   Instance   │
                              └──────────────┘
```

**Flow**:
1. Client (chatbot/CLI) sends HTTP request with API key
2. FastAPI server authenticates request
3. Server calls AWX API via composite client
4. Results returned as JSON
5. Client formats for end user (Slack, terminal, etc.)

---

## 🔒 Security

### VS Code Extension
- Credentials stored in VS Code secure storage
- Local server only (no network exposure)
- Environment-based isolation

### Web Server
- API key authentication (SHA-256 hashed)
- Multi-tenant isolation
- Configurable key expiration
- HTTPS recommended for production
- Environment variables for secrets

---

## 🚢 Deployment Options

### For VS Code Extension
- Install extension from .vsix file
- MCP server runs automatically when VS Code starts
- No additional infrastructure needed

### For Web Server

#### Development
```bash
cd server
pip install -e .
awx-mcp-server start
```

#### Production - Docker
```bash
cd server
docker-compose up -d
```
Includes: Server, Prometheus, Grafana

#### Production - Kubernetes
```bash
cd server/deployment/helm
helm install awx-mcp-server . \
  --set autoscaling.enabled=true \
  --set taskPods.enabled=true \
  --set ingress.enabled=true
```
Features:
- Horizontal Pod Autoscaling (HPA)
- Task pods (ephemeral Job per operation)
- Prometheus monitoring
- Ingress support

---

## 🛠️ Development

### Prerequisites
- Python 3.10+
- Node.js 18+ (for VS Code extension)
- Docker (optional)
- Kubernetes cluster (optional)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/awx-mcp.git
cd awx-mcp/awx-mcp-python

# Install shared package (for VS Code extension)
cd shared
pip install -e ".[dev]"

# Install server
cd ../server
pip install -e ".[dev]"

# Install extension dependencies
cd ../vscode-extension
npm install

# Run tests
cd ../tests
pytest -v
```

### Running Tests

```bash
# Server tests
cd server
pytest tests/ -v --cov

# Integration tests
cd tests
pytest test_mcp_integration.py -v
```

### Building VS Code Extension

```bash
cd vscode-extension
npm run package
# Generates awx-mcp-*.vsix file
```

---

## 📊 Monitoring (Web Server)

Access monitoring dashboards:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Metrics Endpoint**: http://localhost:8000/prometheus-metrics

### Available Metrics

- `awx_mcp_requests_total` - Total requests by tenant/endpoint
- `awx_mcp_request_duration_seconds` - Request latency
- `awx_mcp_active_connections` - Active connections per tenant
- `awx_mcp_tool_calls_total` - MCP tool invocations
- `awx_mcp_errors_total` - Error count by type

---

## 📚 Documentation

### Installation & Setup
- **[Install from PyPI](https://pypi.org/project/awx-mcp-server/)** - Quick install with `pip install awx-mcp-server`
- **[Install from Source](INSTALL_FROM_SOURCE.md)** - Fork, customize, and run from your own repository
- **[OS Compatibility](OS_COMPATIBILITY.md)** - Windows, macOS, and Linux installation and configuration

### Platform Support
- **[AAP Support Guide](AAP_SUPPORT.md)** - Complete guide for Ansible Automation Platform, AWX, and Ansible Tower

### Deployment Architectures
- **[Deployment Architecture](DEPLOYMENT_ARCHITECTURE.md)** - Single-user vs Team/Enterprise deployment options
- **[Remote Deployment Guide](server/REMOTE_DEPLOYMENT.md)** - Docker, Kubernetes, and cloud deployment
- **[Dual-Mode Quick Start](DUAL_MODE_QUICKSTART.md)** - Quick reference for choosing deployment mode

### Advanced Features (Planned)
- **[Vault Integration](server/VAULT_INTEGRATION.md)** - HashiCorp Vault, AWS Secrets Manager, Azure Key Vault support (v2.0.0)
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Current features and roadmap

### Additional Resources
- **[MCP Copilot Setup](vscode-extension/MCP_COPILOT_SETUP.md)** - VS Code MCP configuration
- **[Quick Reference](docs/QUICKREF.md)** - Common commands and examples
- **[AWX MCP Query Reference](AWX_MCP_QUERY_REFERENCE.md)** - Natural language query examples

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

### Code Style
- Python: Follow PEP 8, use type hints
- TypeScript: Follow ESLint rules
- Write tests for new features
- Update documentation

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🆘 Support

- **Issues**: https://github.com/your-org/awx-mcp/issues
- **Discussions**: https://github.com/your-org/awx-mcp/discussions
- **Documentation**: See README files in subdirectories

---

## 🎉 Quick Reference

### VS Code Extension Commands

- `Ctrl+Shift+P` → `AWX: Configure Environment`
- `Ctrl+Shift+P` → `AWX: Test Connection`
- `Ctrl+Shift+P` → `AWX: Switch Environment`
- In Copilot Chat: `@awx <your command>`

### Web Server CLI Commands

```bash
awx-mcp-server start                    # Start HTTP server
awx-mcp-server env list                 # List environments
awx-mcp-server templates list           # List templates
awx-mcp-server jobs launch "Template"   # Launch job
awx-mcp-server jobs get 123             # Get job details
awx-mcp-server projects list            # List projects
awx-mcp-server inventories list         # List inventories
```

### Web Server API Endpoints

```
POST   /api/keys                         # Create API key
GET    /api/v1/environments              # List environments
GET    /api/v1/job-templates             # List templates
POST   /api/v1/jobs/launch               # Launch job
GET    /api/v1/jobs/{id}                 # Get job
GET    /api/v1/jobs/{id}/stdout          # Get output
GET    /api/v1/projects                  # List projects
GET    /api/v1/inventories               # List inventories
GET    /health                           # Health check
GET    /prometheus-metrics               # Metrics
GET    /docs                             # API documentation
```

---

**Made with ❤️ for AWX automation and AI integration**
