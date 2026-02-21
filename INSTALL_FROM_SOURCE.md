# Installing and Running from Source (GitHub)

This guide shows how to install, customize, and run the AWX MCP Server directly from the GitHub repository instead of using `pip install`. This is ideal for:

- 🔧 **Customizing the server** for your specific needs
- 👥 **Contributing** to the project
- 🧪 **Testing** the latest development version
- 🏢 **Enterprise deployments** with custom modifications
- 📚 **Learning** how the server works

---

## 🚀 Quick Start (Community Use)

### 1. Fork the Repository (Optional but Recommended)

**Why Fork?** So you can make customizations and push changes to your own repository.

1. Go to https://github.com/SurgeX-Labs/awx-mcp-server
2. Click **"Fork"** button (top right)
3. This creates a copy under your GitHub account: `https://github.com/YOUR-USERNAME/awx-mcp-server`

### 2. Clone the Repository

**Clone from your fork** (if you forked):
```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server
```

**Or clone the original** (read-only access):
```bash
git clone https://github.com/SurgeX-Labs/awx-mcp-server.git
cd awx-mcp-server
```

### 3. Install Dependencies

**Create a virtual environment** (recommended):

**Windows**:
```powershell
cd awx-mcp-python\server
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux**:
```bash
cd awx-mcp-python/server
python3 -m venv venv
source venv/bin/activate
```

**Install in editable mode**:
```bash
pip install -e .
```

This installs the package in "editable" mode - any changes you make to the code will be immediately active without reinstalling.

### 4. Verify Installation

```bash
# Check version
python -m awx_mcp_server --version

# Check CLI
python -m awx_mcp_server.cli --help

# Test MCP server
python -m awx_mcp_server --help
```

### 5. Run the Server

**Single-user mode (STDIO/MCP)**:
```bash
# Set environment variables
export AWX_BASE_URL="https://your-awx.com"
export AWX_TOKEN="your-token"

# Run MCP server
python -m awx_mcp_server
```

**Team/Enterprise mode (HTTP Server)**:
```bash
python -m awx_mcp_server.cli start --host 0.0.0.0 --port 8000
```

---

## 📝 VS Code Configuration (Source Installation)

### Option 1: Run from Your Local Clone

This runs the server from your local source code directory:

**Edit VS Code settings.json**:
```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": [
        "-m",
        "awx_mcp_server"
      ],
      "cwd": "C:/path/to/your/clone/awx-mcp-server/awx-mcp-python/server",
      "env": {
        "PYTHONPATH": "C:/path/to/your/clone/awx-mcp-server/awx-mcp-python/server/src",
        "AWX_BASE_URL": "https://your-awx.com"
      },
      "secrets": {
        "AWX_TOKEN": "your-awx-token"
      }
    }
  }
}
```

**Key settings**:
- `cwd`: Working directory where the code lives
- `PYTHONPATH`: Tells Python where to find the source code
- Adjust paths for your OS (Windows uses `\`, macOS/Linux use `/`)

### Option 2: Run from Virtual Environment

If you installed with `pip install -e .`, you can use the venv Python:

**Windows**:
```json
{
  "mcpServers": {
    "awx": {
      "command": "C:/path/to/awx-mcp-server/awx-mcp-python/server/venv/Scripts/python.exe",
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

**macOS/Linux**:
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

---

## 🔧 Making Customizations

### Example 1: Add Custom Tool/Function

**Edit**: `awx-mcp-python/server/src/awx_mcp_server/mcp_server.py`

```python
@mcp_server.call_tool()
async def awx_custom_report(name: str) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """
    Generate a custom report for your organization.
    
    Args:
        name: Report type (daily, weekly, monthly)
    """
    try:
        env, client = await get_active_client()
        
        # Your custom logic here
        jobs = await client.list_jobs(page_size=50)
        
        # Custom report formatting
        report = f"# Custom Report: {name}\n\n"
        report += f"Total Jobs: {len(jobs)}\n"
        # ... add your custom reporting logic
        
        return [TextContent(type="text", text=report)]
        
    except Exception as e:
        logger.error(f"Custom report error: {e}")
        raise
```

### Example 2: Add Custom Authentication

**Edit**: `awx-mcp-python/server/src/awx_mcp_server/auth.py`

```python
def custom_auth_provider():
    """Custom authentication for your environment."""
    # Your custom auth logic
    token = get_token_from_vault()  # Your vault integration
    return token
```

### Example 3: Add Custom Configuration

**Edit**: `awx-mcp-python/server/src/awx_mcp_server/domain/models.py`

```python
class EnvironmentConfig(BaseModel):
    """Environment configuration."""
    
    # ... existing fields ...
    
    # Add your custom fields
    custom_field: Optional[str] = None
    organization_id: Optional[str] = None
    custom_defaults: dict[str, Any] = Field(default_factory=dict)
```

### Testing Your Changes

After making changes, test immediately (no reinstall needed with `-e`):

```bash
# Test the MCP server
python -m awx_mcp_server --help

# Test CLI
python -m awx_mcp_server.cli --help

# Run automated tests
pytest tests/
```

---

## 🏢 Enterprise Fork & Customization

### 1. Fork to Your Organization

```bash
# Fork on GitHub to your organization account
# Then clone your organization's fork
git clone https://github.com/YOUR-ORG/awx-mcp-server.git
cd awx-mcp-server
```

### 2. Create Custom Branch

```bash
# Create a branch for your customizations
git checkout -b enterprise-customizations

# Make your changes
# Edit files in awx-mcp-python/server/src/awx_mcp_server/
```

### 3. Commit Your Changes

```bash
git add .
git commit -m "Add enterprise customizations"
git push origin enterprise-customizations
```

### 4. Install from Your Fork

**On developer machines**:
```bash
pip install git+https://github.com/YOUR-ORG/awx-mcp-server.git@enterprise-customizations
```

**For development**:
```bash
git clone https://github.com/YOUR-ORG/awx-mcp-server.git -b enterprise-customizations
cd awx-mcp-server/awx-mcp-python/server
pip install -e .
```

### 5. Keep Updated from Upstream

```bash
# Add upstream remote (original repo)
git remote add upstream https://github.com/SurgeX-Labs/awx-mcp-server.git

# Fetch updates from upstream
git fetch upstream

# Merge upstream changes into your branch
git checkout enterprise-customizations
git merge upstream/main

# Resolve conflicts if any, then push
git push origin enterprise-customizations
```

---

## 🐳 Docker Deployment from Source

### Build Custom Docker Image

**Create Dockerfile** in `awx-mcp-python/`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy source code
COPY server/ /app/

# Install dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "-m", "awx_mcp_server.cli", "start", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run**:
```bash
# Build image
docker build -t your-org/awx-mcp-server:custom -f awx-mcp-python/Dockerfile awx-mcp-python/

# Run container
docker run -p 8000:8000 \
  -e AWX_BASE_URL=https://your-awx.com \
  -e AWX_TOKEN=your-token \
  your-org/awx-mcp-server:custom
```

**Push to your registry**:
```bash
docker tag your-org/awx-mcp-server:custom your-registry.com/awx-mcp-server:custom
docker push your-registry.com/awx-mcp-server:custom
```

---

## ☸️ Kubernetes Deployment from Source

### Deploy Your Custom Image

**Create deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: awx-mcp-server-custom
spec:
  replicas: 3
  selector:
    matchLabels:
      app: awx-mcp-server
  template:
    metadata:
      labels:
        app: awx-mcp-server
    spec:
      containers:
      - name: awx-mcp-server
        image: your-registry.com/awx-mcp-server:custom
        ports:
        - containerPort: 8000
        env:
        - name: AWX_BASE_URL
          value: "https://your-awx.com"
        - name: AWX_TOKEN
          valueFrom:
            secretKeyRef:
              name: awx-credentials
              key: token
```

**Deploy**:
```bash
kubectl apply -f deployment.yaml
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

**Create `.github/workflows/build-and-deploy.yml`** in your fork:

```yaml
name: Build and Deploy Custom MCP Server

on:
  push:
    branches: [enterprise-customizations]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd awx-mcp-python/server
          pip install -e .
          pip install pytest
      
      - name: Run tests
        run: |
          cd awx-mcp-python/server
          pytest tests/ || true
      
      - name: Build Docker image
        run: |
          docker build -t your-registry.com/awx-mcp-server:${{ github.sha }} \
            -f awx-mcp-python/Dockerfile awx-mcp-python/
      
      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin your-registry.com
          docker push your-registry.com/awx-mcp-server:${{ github.sha }}
          docker tag your-registry.com/awx-mcp-server:${{ github.sha }} your-registry.com/awx-mcp-server:latest
          docker push your-registry.com/awx-mcp-server:latest
```

---

## 📚 Common Customization Scenarios

### Scenario 1: Add Company-Specific Defaults

**Edit**: `awx-mcp-python/server/src/awx_mcp_server/mcp_server.py`

```python
# Add company defaults
COMPANY_DEFAULTS = {
    "organization": "MyCompany",
    "default_inventory": "Production-Inventory",
    "default_project": "MyCompany-Playbooks",
}

# Use in your tools
async def get_active_client():
    env, client = await get_client_with_env()
    
    # Apply company defaults
    env.default_organization = COMPANY_DEFAULTS["organization"]
    env.default_inventory = COMPANY_DEFAULTS["default_inventory"]
    
    return env, client
```

### Scenario 2: Add Custom Monitoring

**Create**: `awx-mcp-python/server/src/awx_mcp_server/custom_monitoring.py`

```python
import structlog
from prometheus_client import Counter, Histogram

company_job_counter = Counter(
    'company_awx_jobs_total',
    'Total jobs launched by company',
    ['department', 'environment']
)

def track_company_job(department: str, env: str):
    """Track company-specific job metrics."""
    company_job_counter.labels(department=department, environment=env).inc()
```

### Scenario 3: Add LDAP Authentication

**Edit**: `awx-mcp-python/server/src/awx_mcp_server/auth.py`

```python
import ldap

def authenticate_with_ldap(username: str, password: str) -> bool:
    """Authenticate user against company LDAP."""
    try:
        conn = ldap.initialize('ldap://company-ldap.com')
        conn.simple_bind_s(f'uid={username},ou=users,dc=company,dc=com', password)
        return True
    except ldap.INVALID_CREDENTIALS:
        return False
```

---

## 🧪 Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-custom-feature
```

### 2. Make Changes

Edit files in `awx-mcp-python/server/src/awx_mcp_server/`

### 3. Test Locally

```bash
# Run MCP server
python -m awx_mcp_server

# Or HTTP server
python -m awx_mcp_server.cli start --debug
```

### 4. Commit and Push

```bash
git add .
git commit -m "Add custom feature"
git push origin feature/my-custom-feature
```

### 5. Create Pull Request

If contributing back to upstream:
- Go to your fork on GitHub
- Click "New Pull Request"
- Select your feature branch
- Submit PR to `SurgeX-Labs/awx-mcp-server`

---

## 📦 Building Custom Python Package

If you want to distribute your customized version:

### 1. Update Package Metadata

**Edit**: `awx-mcp-python/server/pyproject.toml`

```toml
[project]
name = "awx-mcp-server-mycompany"
version = "1.1.6-custom"
description = "AWX MCP Server - MyCompany Custom Edition"
authors = [
    {name = "MyCompany", email = "devops@mycompany.com"}
]
```

### 2. Build Package

```bash
cd awx-mcp-python/server
python -m build
```

### 3. Upload to Private PyPI

```bash
# Upload to your company's private PyPI server
twine upload --repository-url https://pypi.mycompany.com dist/*
```

### 4. Install from Private PyPI

```bash
pip install --index-url https://pypi.mycompany.com awx-mcp-server-mycompany
```

---

## 🔐 Security Considerations

When running from source:

1. **Review Code**: Audit all code before deployment
2. **Secrets Management**: Don't commit secrets to your fork
3. **Access Control**: Restrict who can push to your fork
4. **Dependency Scanning**: Run security scans on dependencies
5. **Private Repository**: Consider making your fork private

```bash
# Scan dependencies for vulnerabilities
pip install safety
safety check
```

---

## 📖 Directory Structure

Understanding the structure helps with customization:

```
awx-mcp-server/
├── awx-mcp-python/
│   ├── server/
│   │   ├── src/
│   │   │   └── awx_mcp_server/
│   │   │       ├── __init__.py
│   │   │       ├── __main__.py          # Entry point
│   │   │       ├── mcp_server.py        # MCP tools & resources
│   │   │       ├── cli.py               # CLI commands
│   │   │       ├── http_server.py       # HTTP server
│   │   │       ├── clients/             # AWX API clients
│   │   │       ├── domain/              # Data models
│   │   │       ├── storage/             # Config & credentials
│   │   │       └── utils/               # Utilities
│   │   ├── pyproject.toml               # Package config
│   │   ├── tests/                       # Unit tests
│   │   └── README.md
│   ├── docs/                            # Documentation
│   └── vscode-extension/                # VS Code extension
└── README.md
```

---

## 🆘 Troubleshooting

### Issue: Changes not taking effect

**Solution**: Ensure you installed in editable mode:
```bash
pip uninstall awx-mcp-server
pip install -e .
```

### Issue: Import errors

**Solution**: Check PYTHONPATH:
```bash
export PYTHONPATH=/path/to/awx-mcp-server/awx-mcp-python/server/src:$PYTHONPATH
```

### Issue: VS Code can't find the module

**Solution**: Use full path to Python in venv:
```json
{
  "command": "/full/path/to/venv/bin/python"
}
```

---

## 📚 Additional Resources

- **Original Repo**: https://github.com/SurgeX-Labs/awx-mcp-server
- **Issues**: https://github.com/SurgeX-Labs/awx-mcp-server/issues
- **Contributing Guide**: See CONTRIBUTING.md
- **MCP Documentation**: https://modelcontextprotocol.io/

---

## 🤝 Contributing Back

If you make improvements that could benefit everyone:

1. Fork the original repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. Engage with maintainer feedback

**We welcome contributions!**

---

## ✅ Quick Reference

**Clone and install**:
```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server/awx-mcp-python/server
pip install -e .
```

**Run MCP server**:
```bash
python -m awx_mcp_server
```

**Run HTTP server**:
```bash
python -m awx_mcp_server.cli start --host 0.0.0.0 --port 8000
```

**Update from upstream**:
```bash
git remote add upstream https://github.com/SurgeX-Labs/awx-mcp-server.git
git fetch upstream
git merge upstream/main
```

**Build custom Docker image**:
```bash
docker build -t your-org/awx-mcp-server:custom -f awx-mcp-python/Dockerfile awx-mcp-python/
```

---

**✨ Now you can customize and run the AWX MCP Server from your own repository!**
