# AWX MCP Standalone Server

**Fully self-contained** FastAPI server for centralized AWX MCP management.

## Features

- 🌐 **HTTP/REST API**: FastAPI-based RESTful interface
- 🔐 **Multi-tenant**: Isolated environments per API key
- 📊 **Monitoring**: Built-in metrics and request tracking
- 🚀 **Scalable**: Deploy on Docker, Kubernetes, or Helm
- 🔒 **Secure**: API key authentication with expiry
- 📦 **Self-contained**: No external dependencies (all AWX client code included)

## Quick Start

### Local Development

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
