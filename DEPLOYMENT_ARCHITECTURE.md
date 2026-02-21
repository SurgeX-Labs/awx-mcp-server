# AWX MCP Server - Deployment Architecture

## Overview

The AWX MCP Server supports two deployment modes to accommodate different use cases:

1. **Single User Mode** - Local installation for individual developers
2. **Team/Enterprise Mode** - Remote server for teams and organizations

---

## 🖥️ Single User Mode (Local)

### Architecture

```
┌─────────────────┐
│   VS Code       │
│  (MCP Client)   │
│                 │
│  ┌───────────┐  │
│  │  Copilot  │  │
│  └─────┬─────┘  │
│        │        │
│    STDIO MCP    │
│        │        │
│  ┌─────▼─────┐  │
│  │AWX MCP    │  │
│  │Server     │  │
│  │(Local)    │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ HTTPS
         │
    ┌────▼────┐
    │   AWX   │
    │ Instance│
    └─────────┘
```

### Use Case
- Individual developers
- Personal projects
- Development/testing environments
- Offline or low-latency requirements

### Installation

```bash
pip install awx-mcp-server
```

### VS Code Configuration

**Option A: Credentials in VS Code Settings (Current)**
```json
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
```

**Option B: Multiple AWX Environments**
```json
{
  "github.copilot.chat.mcpServers": {
    "awx-dev": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-dev.example.com",
        "AWX_TOKEN": "${secret:awx-dev-token}",
        "AWX_ENVIRONMENT": "development"
      }
    },
    "awx-prod": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-prod.example.com",
        "AWX_TOKEN": "${secret:awx-prod-token}",
        "AWX_ENVIRONMENT": "production"
      }
    }
  }
}
```

### Pros
- ✅ Simple setup
- ✅ No server infrastructure needed
- ✅ Low latency (local execution)
- ✅ Works offline (if AWX is accessible)
- ✅ Full control over credentials

### Cons
- ❌ Each user installs separately
- ❌ Version management per user
- ❌ Credentials stored locally
- ❌ No centralized audit logs

---

## 🌐 Team/Enterprise Mode (Remote Server)

### Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  VS Code 1   │  │  VS Code 2   │  │  Claude App  │
│              │  │              │  │              │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ Copilot  │ │  │ │ Copilot  │ │  │ │  Claude  │ │
│ └────┬─────┘ │  │ └────┬─────┘ │  │ └────┬─────┘ │
└──────┼───────┘  └──────┼───────┘  └──────┼───────┘
       │                 │                 │
       │    HTTP/SSE     │                 │
       └────────┬────────┴─────────────────┘
                │
         ┌──────▼───────┐
         │   Ingress    │
         │ (TLS/Auth)   │
         └──────┬───────┘
                │
    ┌───────────▼──────────────┐
    │  AWX MCP Server Cluster  │
    │  ┌────────────────────┐  │
    │  │  Load Balancer     │  │
    │  └─────────┬──────────┘  │
    │            │              │
    │  ┌─────────▼─────────┐   │
    │  │  MCP Server Pod 1 │   │
    │  │  MCP Server Pod 2 │   │
    │  │  MCP Server Pod 3 │   │
    │  └─────────┬─────────┘   │
    │            │              │
    │  ┌─────────▼─────────┐   │
    │  │ Credential Vault  │   │
    │  │ (Future)          │   │
    │  └───────────────────┘   │
    └──────────┬───────────────┘
               │ HTTPS
          ┌────▼────┐
          │   AWX   │
          │Instance │
          └─────────┘
```

### Use Case
- Development teams
- Enterprise organizations
- Centralized management
- Compliance requirements
- Multi-tenant environments

### Deployment Options

#### 1. Docker Compose
```bash
docker-compose up -d
```

#### 2. Kubernetes/OpenShift
```bash
kubectl apply -f deployment/kubernetes.yaml
```

#### 3. Cloud Platforms
- AWS ECS/EKS
- Azure Container Instances/AKS
- Google Cloud Run/GKE
- Red Hat OpenShift

---

## 🔐 Credential Management

### Option 1: Client-Provided Credentials (Implemented)

Credentials are passed from the client (VS Code) to the remote server for each session.

**VS Code Configuration:**
```json
{
  "github.copilot.chat.mcpServers": {
    "awx-remote": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-sse",
        "https://awx-mcp.company.com"
      ],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}"
      }
    }
  }
}
```

**How It Works:**
1. VS Code stores AWX credentials locally (in secrets)
2. Client passes credentials to remote MCP server on connection
3. Server uses credentials to connect to AWX
4. Credentials are NOT stored on server
5. Each session is isolated

**Pros:**
- ✅ User controls their own credentials
- ✅ No credential storage on server
- ✅ Easy to switch AWX environments
- ✅ Works with existing secret managers

**Cons:**
- ⚠️ Credentials sent over network (requires TLS)
- ⚠️ No credential rotation without user action

---

### Option 2: Vault/Secret Manager (Placeholder - Future Enhancement)

Centralized credential storage using enterprise secret management.

**Supported Platforms (Future):**
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Google Secret Manager
- GitHub Secrets
- Kubernetes Secrets
- CyberArk
- 1Password Secrets Automation

**Configuration Example (Future):**
```yaml
# config/vault-config.yaml
credential_provider: "vault"

vault:
  address: "https://vault.company.com"
  auth_method: "kubernetes"
  secret_path: "secret/awx/{environment}/{user}"
  
aws_secrets:
  region: "us-east-1"
  secret_name: "awx/credentials/{user}"
  
azure_keyvault:
  vault_url: "https://company.vault.azure.net"
  secret_name: "awx-credentials"
```

**See:** `server/src/awx_mcp_server/storage/vault_integration.py` (placeholder)

---

## 🔄 Environment Switching

Both modes support multiple AWX environments:

### Single User Mode
Configure multiple MCP servers in VS Code:
- `awx-dev` → Development AWX
- `awx-staging` → Staging AWX
- `awx-prod` → Production AWX

Switch by selecting different MCP server in VS Code.

### Team/Enterprise Mode
Use environment parameter in requests:
```json
{
  "awx_environment": "production",
  "awx_base_url": "https://awx-prod.example.com"
}
```

Or configure server-side environments in `config/environments.yaml`.

---

## 📊 Comparison Matrix

| Feature | Single User | Team/Enterprise |
|---------|-------------|-----------------|
| **Setup Complexity** | Low | Medium-High |
| **Infrastructure** | None | Kubernetes/Cloud |
| **Credential Storage** | Local (VS Code) | Client-provided or Vault |
| **Multi-User** | No | Yes |
| **Centralized Logs** | No | Yes |
| **Version Management** | Per-user | Centralized |
| **High Availability** | No | Yes |
| **Cost** | Free | Infrastructure cost |
| **Latency** | Very Low | Low (network) |
| **Security Audit** | Limited | Full audit trail |
| **Compliance** | Individual | Enterprise-ready |

---

## 🚀 Migration Path

### From Single User to Team/Enterprise

1. **Deploy remote server:**
   ```bash
   kubectl apply -f deployment/kubernetes.yaml
   ```

2. **Update VS Code configuration:**
   ```json
   {
     "github.copilot.chat.mcpServers": {
       "awx": {
         "command": "npx",
         "args": ["@modelcontextprotocol/server-sse", "https://awx-mcp.company.com"],
         "env": {
           "AWX_BASE_URL": "https://awx.example.com",
           "AWX_TOKEN": "${secret:awx-token}"
         }
       }
     }
   }
   ```

3. **Verify connection:**
   ```bash
   curl https://awx-mcp.company.com/health
   ```

No changes to workflow or queries needed!

---

## 📁 Configuration Files

### Single User Mode
- `.vscode/settings.json` - VS Code MCP configuration
- `~/.config/awx-mcp/` - Local credentials (optional)

### Team/Enterprise Mode
- `deployment/docker-compose.yml` - Docker deployment
- `deployment/kubernetes.yaml` - K8s deployment
- `config/environments.yaml` - AWX environment definitions
- `config/vault-config.yaml` - Vault integration (future)
- `deployment/helm/` - Helm chart for enterprise deployment

---

## 📖 Next Steps

### For Single User Setup
👉 See: [QUICK_START.md](server/QUICK_START.md)

### For Team/Enterprise Setup
👉 See: [REMOTE_DEPLOYMENT.md](server/REMOTE_DEPLOYMENT.md)

### For Vault Integration
👉 See: [VAULT_INTEGRATION.md](server/VAULT_INTEGRATION.md) (future)

---

## 🔒 Security Considerations

### Single User Mode
- ✅ Store tokens in VS Code secrets
- ✅ Use HTTPS for AWX connections
- ✅ Rotate tokens regularly
- ⚠️ Credentials on local machine

### Team/Enterprise Mode
- ✅ TLS/SSL for all connections
- ✅ Authentication at ingress
- ✅ Network policies
- ✅ Audit logging
- ✅ Credential rotation (with vault)
- ✅ Multi-tenant isolation
- ⚠️ Requires infrastructure security
