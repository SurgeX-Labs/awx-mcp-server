# AWX MCP Server

**Industry-standard MCP server for AWX/Ansible Tower automation**

Control AWX/Ansible Tower through the Model Context Protocol (MCP). Use with GitHub Copilot, Claude, Cursor, or any MCP-compatible client.

---

## 🎯 Two Usage Modes

### 1. STDIO Mode (Industry Standard) ⭐ RECOMMENDED

Use with MCP clients (GitHub Copilot, Claude, Cursor):

```bash
pip install awx-mcp-server
```

Configure in your MCP client (see [QUICK_START.md](QUICK_START.md))

✅ **Works with:** GitHub Copilot, Claude Desktop, Cursor, Windsurf, any MCP client  
✅ **Pattern:** Standard MCP (like Postman MCP, Anthropic MCP)  
✅ **Setup:** Simple configuration in client settings  

### 2. HTTP/REST Mode (Alternative)

Deploy as a centralized HTTP server:

```bash
awx-mcp-server start --host 0.0.0.0 --port 8000
```

✅ **Use case:** Remote MCP server, multi-tenant deployments  
✅ **Deploy:** Docker, Kubernetes, cloud platforms  
✅ **Access:** HTTP transport over network  

---

## � Installation

### From PyPI (Stable)
```bash
pip install awx-mcp-server
```

### From GitHub (Latest)
```bash
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git
```

### For Development
```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server
pip install -e .
```

**See:** [GITHUB_INSTALLATION.md](GITHUB_INSTALLATION.md) for detailed GitHub installation guide

---

## 📚 Quick Start

### For MCP Clients (Recommended)

**See:** [QUICK_START.md](QUICK_START.md) for complete setup guide

**TL;DR:**
```bash
# Install (PyPI or GitHub)
pip install awx-mcp-server
# OR
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git

# Configure in VS Code settings.json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}"
      }
    }
  }
}

# Use with Copilot Chat
@workspace list AWX job templates
```

### For HTTP Server Deployment

**See:** [HTTP_DEPLOYMENT.md](HTTP_DEPLOYMENT.md) for deployment guide

**TL;DR:**

```bash
cd server
pip install -e .
awx-mcp-server start --host 0.0.0.0 --port 8000
```

Access API documentation at http://localhost:8000/docs

### Docker

```bash
docker build -t awx-mcp-server .
docker run -p 8000:8000 awx-mcp-server
```

### Kubernetes

```bash
kubectl apply -f deployment/kubernetes.yaml
```

### Helm

```bash
helm install awx-mcp-server deployment/helm/
```

## API Usage

### 1. Create API Key (Admin)

```bash
curl -X POST http://localhost:8000/api/keys \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "tenant_id": "tenant1",
    "expires_days": 90
  }'
```

Response:
```json
{
  "api_key": "awx_mcp_xxxxxxxxxxxxx",
  "name": "my-app",
  "tenant_id": "tenant1",
  "created_at": "2026-02-07T10:00:00",
  "expires_at": "2026-05-08T10:00:00"
}
```

### 2. Send MCP Messages

```bash
curl -X POST http://localhost:8000/messages \
  -H "X-API-Key: awx_mcp_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_templates",
      "arguments": {}
    }
  }'
```

### 3. Health Check

```bash
curl http://localhost:8000/health
```

### 4. Metrics (Requires Authentication)

```bash
curl http://localhost:8000/metrics \
  -H "X-API-Key: awx_mcp_xxxxxxxxxxxxx"
```

## Monitoring

The server includes built-in monitoring:

- **Request Tracking**: All API calls are logged
- **Prometheus Metrics**: Available at `/prometheus-metrics`
- **Usage Analytics**: Per-tenant usage statistics
- **Error Tracking**: Detailed error logs

## Configuration

Environment variables:

```bash
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# Security
ADMIN_TOKEN=your-secure-admin-token
API_KEY_EXPIRY_DAYS=90

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=info
```

## Deployment Guides

- [Docker Deployment](../docs/deployments/DOCKER.md)
- [Kubernetes Deployment](../docs/deployments/KUBERNETES.md)
- [Helm Charts](../docs/deployments/HELM.md)

## Architecture

```
┌─────────────┐
│   Client    │
│ Application │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│  FastAPI    │
│   Server    │
├─────────────┤
│ Monitoring  │
│   Layer     │
├─────────────┤
│  MCP Core   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AWX API    │
└─────────────┘
```

## Security Considerations

- Store API keys securely (use environment variables or secrets management)
- Use HTTPS in production
- Implement rate limiting
- Set appropriate CORS policies
- Rotate API keys regularly
- Use network policies in Kubernetes

## Support

For issues and questions, see [Main Documentation](../docs/README.md)
