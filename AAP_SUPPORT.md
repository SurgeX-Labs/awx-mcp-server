# Ansible Automation Platform (AAP) Support

## Overview

The **AWX MCP Server** now supports **Ansible Automation Platform (AAP)** in addition to the open-source AWX platform. AAP is Red Hat's commercially supported version of AWX/Ansible Tower with enterprise features, SLA support, and long-term maintenance.

## Supported Platforms

| Platform | Status | Description |
|----------|--------|-------------|
| **AWX** | ✅ Fully Supported | Open-source Ansible automation platform |
| **AAP (Controller)** | ✅ Fully Supported | Red Hat Ansible Automation Platform 2.x+ (automation controller) |
| **Ansible Tower** | ✅ Supported | Legacy Ansible Tower (now part of AAP) |

## Platform Differences

### AWX vs AAP

| Feature | AWX | AAP |
|---------|-----|-----|
| **License** | Apache 2.0 (Open Source) | Red Hat Subscription Required |
| **Support** | Community | Red Hat Enterprise Support + SLA |
| **Updates** | Rolling releases (frequent) | Scheduled releases (stable) |
| **Documentation** | Community docs | Official Red Hat docs |
| **API** | RESTful API v2 | RESTful API v2 (same) |
| **Authentication** | Basic, Token, OAuth2 | Basic, Token, OAuth2, SAML, LDAP, RADIUS |
| **Features** | Core automation features | Core + Enterprise (analytics, RBAC+, automation mesh) |
| **Deployment** | Kubernetes, Docker, OpenShift | Kubernetes, OpenShift, RHEL |
| **Certification** | N/A | Red Hat certified content |

### API Compatibility

**Good News**: AWX and AAP share the same REST API (v2), so the AWX MCP Server works identically with both platforms!

- ✅ Same endpoints: `/api/v2/job_templates/`, `/api/v2/jobs/`, etc.
- ✅ Same authentication: Token-based or username/password
- ✅ Same responses: JSON format is identical
- ⚠️ **Only difference**: AAP may have additional certified collections and content

## Configuration

### Environment Variables

You can specify the platform type using the `AWX_PLATFORM` environment variable:

```bash
# For AWX (default)
export AWX_BASE_URL="https://awx.example.com"
export AWX_PLATFORM="awx"
export AWX_TOKEN="your-awx-token"

# For AAP (Automation Controller)
export AWX_BASE_URL="https://aap-controller.example.com"
export AWX_PLATFORM="aap"
export AWX_TOKEN="your-aap-token"

# For Legacy Ansible Tower
export AWX_BASE_URL="https://tower.example.com"
export AWX_PLATFORM="tower"
export AWX_TOKEN="your-tower-token"
```

**Platform Type Values**:
- `awx` (default) - Open-source AWX
- `aap` - Ansible Automation Platform 2.x+ (automation controller)
- `tower` - Legacy Ansible Tower

### VS Code Settings

When configuring MCP servers in VS Code, specify the platform:

```json
{
  "mcpServers": {
    "aap-production": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://aap.company.com",
        "AWX_PLATFORM": "aap",
        "AWX_TOKEN": "stored-in-vscode-secrets"
      },
      "secrets": {
        "AWX_TOKEN": "aap-production-token"
      }
    },
    "awx-dev": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-dev.company.com",
        "AWX_PLATFORM": "awx"
      },
      "secrets": {
        "AWX_TOKEN": "awx-dev-token"
      }
    }
  }
}
```

### Remote Server Configuration

For remote server deployments, configure platform types in environment-specific configs:

**Docker Compose (AAP)**:
```yaml
version: '3.8'
services:
  awx-mcp-server:
    image: surgexlabs/awx-mcp-server:latest
    environment:
      - AWX_BASE_URL=https://aap.company.com
      - AWX_PLATFORM=aap
      - AWX_TOKEN=${AAP_TOKEN}
    ports:
      - "8000:8000"
```

**Kubernetes (AAP)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: awx-mcp-server-aap
spec:
  template:
    spec:
      containers:
      - name: awx-mcp-server
        image: surgexlabs/awx-mcp-server:latest
        env:
        - name: AWX_BASE_URL
          value: "https://aap-controller.company.com"
        - name: AWX_PLATFORM
          value: "aap"
        - name: AWX_TOKEN
          valueFrom:
            secretKeyRef:
              name: aap-credentials
              key: token
```

## Platform-Specific Configuration

### AAP (Ansible Automation Platform)

#### URL Structure

AAP 2.x uses **automation controller** as the API endpoint:

```bash
# AAP 2.x (recommended)
AWX_BASE_URL="https://aap-controller.example.com"

# Or if using the platform gateway
AWX_BASE_URL="https://aap.example.com/api/controller"
```

#### Authentication

AAP supports the same authentication as AWX:

**Token-based (recommended)**:
1. Log in to AAP UI
2. Navigate to **Users** → **Your User** → **Tokens**
3. Create a new token
4. Set as `AWX_TOKEN` environment variable

**Username/Password**:
```bash
export AWX_USERNAME="admin"
export AWX_PASSWORD="your-password"
export AWX_PLATFORM="aap"
```

#### SSL/TLS Verification

AAP typically uses Red Hat certificates:

```bash
# Production (verify SSL)
export AWX_VERIFY_SSL="true"

# Development/Self-Signed Certs
export AWX_VERIFY_SSL="false"
```

#### RBAC Considerations

AAP has enhanced RBAC (Role-Based Access Control):

- **System Administrator**: Full access to all features
- **System Auditor**: Read-only access
- **Job Template Admin**: Can create/modify templates
- **Execute**: Can run jobs only

**Recommendation**: Create a dedicated service account for MCP server with appropriate permissions.

### AWX (Open Source)

#### URL Structure

```bash
AWX_BASE_URL="https://awx.example.com"
```

#### Authentication

Same as AAP - token or username/password.

**Creating a Token in AWX**:
1. AWX UI → Users → Admin (or your user)
2. Click **Tokens** tab
3. **Add** → **Personal Access Token**
4. Set expiration and scope
5. Copy token immediately (shown only once)

### Ansible Tower (Legacy)

Ansible Tower has been rebranded to AAP, but Tower instances still work:

```bash
export AWX_BASE_URL="https://tower.example.com"
export AWX_PLATFORM="tower"
export AWX_TOKEN="your-tower-token"
```

**Note**: Tower uses the same API as AWX/AAP, so all features work identically.

## Platform Detection (Future)

While not currently implemented, future versions may auto-detect platform type by querying `/api/v2/ping/`:

```json
{
  "version": "24.6.0",
  "active_node": "aap-controller-1",
  "install_uuid": "...",
  "instance_group": "default",
  "license_type": "enterprise"  // or "open" for AWX
}
```

For now, explicitly set `AWX_PLATFORM` to avoid ambiguity.

## Usage Examples

### Connecting to AAP

**Python Script**:
```python
import os
from awx_mcp_server.domain import EnvironmentConfig, PlatformType
from awx_mcp_server.clients import CompositeAWXClient

env = EnvironmentConfig(
    name="aap-production",
    base_url="https://aap.company.com",
    platform_type=PlatformType.AAP,
    verify_ssl=True
)

client = CompositeAWXClient(env, "", os.getenv("AAP_TOKEN"), is_token=True)
templates = await client.list_job_templates()
```

**VS Code Copilot Chat**:
```
@workspace Connect to AAP at https://aap.company.com

@workspace List all job templates in AAP production

@workspace Run the "Deploy to Production" template in AAP
```

### Multi-Platform Setup

You can configure multiple platforms simultaneously:

**VS Code settings.json**:
```json
{
  "mcpServers": {
    "aap-prod": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://aap.company.com",
        "AWX_PLATFORM": "aap"
      }
    },
    "awx-dev": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-dev.company.com",
        "AWX_PLATFORM": "awx"
      }
    },
    "tower-legacy": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://tower.legacy.com",
        "AWX_PLATFORM": "tower"
      }
    }
  }
}
```

**Ask Copilot**:
```
@workspace Which platforms are configured?
@workspace List templates in AAP production
@workspace List templates in AWX dev
```

## Testing AAP Connectivity

### Test Connection

**Command Line**:
```bash
# Set environment
export AWX_BASE_URL="https://aap.company.com"
export AWX_PLATFORM="aap"
export AWX_TOKEN="your-token"

# Test connection (if CLI tool supports it)
python -m awx_mcp_server.cli env test
```

**VS Code**:
```
@workspace Test connection to AAP
@workspace What is the AAP version?
@workspace List 5 recent jobs in AAP
```

### Verify API Access

Use `curl` to test direct API access:

```bash
# Test AAP API
curl -k -H "Authorization: Bearer YOUR_TOKEN" \
  https://aap.company.com/api/v2/ping/

# Expected response
{
  "version": "4.5.0",
  "active_node": "aap-controller-1",
  ...
}
```

## Troubleshooting

### SSL Certificate Issues

**AAP Production** (Red Hat certs):
- Usually trusted by default
- If issues: `export AWX_VERIFY_SSL="false"` (not recommended for production)

**Self-Signed Certificates**:
```bash
# Trust certificate system-wide (Ubuntu/Debian)
sudo cp aap-cert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Or disable verification (testing only)
export AWX_VERIFY_SSL="false"
```

### Authentication Errors

**Error**: `401 Unauthorized`

**Solutions**:
1. Verify token is valid: Check AAP UI → Users → Your User → Tokens
2. Ensure token hasn't expired
3. Check RBAC permissions - user needs Execute permission on templates

**Error**: `403 Forbidden`

**Solution**: User lacks permissions. Grant appropriate role in AAP:
- AAP UI → Access → Users → Select User → Roles → Add Role

### Platform Type Mismatch

If you get unexpected behavior, verify platform type:

```bash
# Check configured platform
echo $AWX_PLATFORM

# View MCP server logs (if running in debug mode)
python -m awx_mcp_server --debug

# Logs should show:
# AWX_PLATFORM=aap
```

### API Version Compatibility

Both AWX and AAP use API v2. If you encounter issues:

```bash
# Check API version
curl -k https://aap.company.com/api/

# Expected: Links to /api/v2/
```

## Best Practices

### Production Deployments

1. **Use Token Authentication**: More secure than username/password
2. **Enable SSL Verification**: `AWX_VERIFY_SSL="true"` in production
3. **Create Service Accounts**: Dedicated MCP server user in AAP
4. **Set Appropriate RBAC**: Least privilege - only grant needed permissions
5. **Rotate Tokens Regularly**: AAP supports token expiration
6. **Specify Platform Type Explicitly**: Don't rely on defaults

### Development Environments

1. **Use AWX for Development**: Free and rapid updates
2. **Test Against AAP Before Production**: Validate on AAP staging environment
3. **Use Self-Signed Certs in Dev**: `AWX_VERIFY_SSL="false"` is OK for dev
4. **Keep Tokens Separate**: Different tokens for dev vs. production

### Hybrid Environments

If you have both AWX and AAP:

- **Development**: AWX (fast iteration, community features)
- **Staging**: AAP (test against production platform)
- **Production**: AAP (enterprise support, stability, certified content)

Configure all three in VS Code MCP settings for seamless switching.

## Migration Guide

### From AWX to AAP

1. **Export AWX Data**: Projects, inventories, templates
2. **Provision AAP**: Install AAP controller
3. **Import Data**: Use AAP migration tools or recreate
4. **Update Configuration**:
   ```bash
   # Old (AWX)
   export AWX_BASE_URL="https://awx.company.com"
   export AWX_PLATFORM="awx"
   
   # New (AAP)
   export AWX_BASE_URL="https://aap.company.com"
   export AWX_PLATFORM="aap"
   ```
5. **Test**: Verify all templates and jobs work
6. **Update Documentation**: Inform team of new URLs

### From Ansible Tower to AAP

No code changes needed! Just update:
```bash
export AWX_PLATFORM="aap"  # or keep "tower", both work
```

## Feature Parity

All AWX MCP Server features work identically on AWX, AAP, and Tower:

| Feature | AWX | AAP | Tower |
|---------|-----|-----|-------|
| List job templates | ✅ | ✅ | ✅ |
| Launch jobs | ✅ | ✅ | ✅ |
| Monitor jobs | ✅ | ✅ | ✅ |
| Update projects | ✅ | ✅ | ✅ |
| Manage inventories | ✅ | ✅ | ✅ |
| Browse resources | ✅ | ✅ | ✅ |
| Failure analysis | ✅ | ✅ | ✅ |
| Log querying | ✅ | ✅ | ✅ |

**No platform-specific code needed!**

## Additional Resources

### AAP Documentation
- **Red Hat AAP Docs**: https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/
- **AAP API Guide**: https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.4/html/automation_controller_api_guide/
- **AAP Installation**: https://access.redhat.com/documentation/en-us/red_hat_ansible_automation_platform/2.4/html/installing_ansible_automation_platform/

### AWX Documentation
- **AWX Project**: https://github.com/ansible/awx
- **AWX Operator**: https://github.com/ansible/awx-operator (Kubernetes)
- **Community Forum**: https://forum.ansible.com/c/awx/

### Ansible Tower (Legacy)
- **Tower Docs**: https://docs.ansible.com/ansible-tower/
- **Migration to AAP**: https://www.redhat.com/en/technologies/management/ansible/ansible-automation-platform-migration

## Summary

✅ **Full AAP Support**: Works identically to AWX  
✅ **Same API**: No code changes needed for AAP vs AWX  
✅ **Platform Agnostic**: One MCP server, multiple platforms  
✅ **Easy Configuration**: Just set `AWX_PLATFORM` env var  
✅ **Enterprise Ready**: Supports AAP's RBAC and security features  

**Configuration is as simple as**:
```bash
export AWX_PLATFORM="aap"
```

That's it! Everything else works the same.
