# AWX MCP - AI-Powered AWX/Ansible Automation

**Control AWX/Ansible Tower through AI using the Model Context Protocol (MCP)**

Integrate AWX automation with AI assistants like GitHub Copilot, Claude Desktop, or custom chatbots. Launch jobs, monitor executions, manage resources - all through natural language.

---

## 🎯 Two Deployment Options

### Option 1: VS Code Extension (For Developers)

<img src="https://img.shields.io/badge/VS%20Code-Extension-007ACC?logo=visualstudiocode" alt="VS Code Extension"/>

**Use Case**: Individual developers using GitHub Copilot in VS Code

**Features**:
- ✅ Direct GitHub Copilot Chat integration (`@awx` commands)
- ✅ MCP server runs locally in VS Code
- ✅ One-click AWX environment configuration
- ✅ Real-time job monitoring in chat
- ✅ No external server needed

**Best For**: Personal AWX automation, development workflows, quick testing

---

### Option 2: Standalone Web Server (For Teams/Chatbots)

<img src="https://img.shields.io/badge/FastAPI-Web%20Server-009688?logo=fastapi" alt="FastAPI Server"/>

**Use Case**: Teams, organizations, or custom chatbot integrations

**Features**:
- ✅ RESTful API for any chatbot/application
- ✅ Multi-tenant with API key authentication
- ✅ CLI tools for direct automation
- ✅ Docker, Kubernetes, Helm deployment
- ✅ Prometheus metrics & monitoring
- ✅ 16 AWX operations (templates, jobs, projects, inventories)

**Best For**: Team collaboration, production automation, chatbot backends, CI/CD integration

---

## 🚀 Quick Start

### Option 1: VS Code Extension

#### Prerequisites
- VS Code with GitHub Copilot extension
- Python 3.10+
- AWX/Ansible Tower instance

#### Installation

```bash
# Clone repository
git clone https://github.com/your-org/awx-mcp.git
cd awx-mcp/awx-mcp-python

# Install MCP server
cd shared
pip install -e .

# Build VS Code extension
cd ../vscode-extension
npm install
npm run package

# Install .vsix file in VS Code
code --install-extension awx-mcp-*.vsix
```

#### Configuration

1. Open VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run: `AWX: Configure Environment`
3. Enter your AWX details:
   - Environment name
   - AWX URL
   - Username/token
4. Test connection: `AWX: Test Connection`

#### Usage

Open GitHub Copilot Chat and use `@awx`:

```
@awx list job templates
@awx launch "Deploy Production" with environment=prod
@awx show recent jobs
@awx get job 123 output
@awx why did job 456 fail?
```

**See**: [vscode-extension/README.md](vscode-extension/README.md) for detailed guide

---

### Option 2: Standalone Web Server

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

Both VS Code extension and web server support all 16 operations:

### Environment Management
- `env_list` - List all configured AWX environments
- `env_test` - Test connection to AWX environment
- `env_get_active` - Get currently active environment

### Job Templates
- `list_job_templates` - List all job templates (with filtering)
- `get_job_template` - Get template details by name/ID

### Jobs
- `list_jobs` - List all jobs (filter by status, date)
- `get_job` - Get job details by ID
- `job_launch` - Launch job from template
- `job_cancel` - Cancel running job
- `job_stdout` - Get job output/logs
- `job_events` - Get job events (playbook tasks)

### Projects
- `list_projects` - List all projects
- `project_update` - Update project from SCM

### Inventories
- `list_inventories` - List all inventories
- `get_inventory` - Get inventory details

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
│  │   Chat    │◀─┼────────────────│   16 Tools   │
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
