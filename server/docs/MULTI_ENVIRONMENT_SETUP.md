# Multi-Environment Setup Guide

## Overview

The AWX MCP Server supports managing multiple AWX/AAP environments (Local, Dev, Staging, Production) with easy switching between them in GitHub Copilot Chat.

---

## 🎯 Architecture

```
GitHub Copilot Chat
       │
       ├─ Select "awx-local" ──────> Local AWX (localhost:30080)
       │
       ├─ Select "awx-dev" ────────> Dev AWX (dev.example.com)
       │
       ├─ Select "awx-staging" ────> Staging AWX (staging.example.com)
       │
       └─ Select "awx-production" ─> Production AWX (prod.example.com)
```

**Key Features**:
- ✅ Multiple MCP servers configured in VS Code
- ✅ Each server points to different AWX environment
- ✅ Switch environments via Copilot Chat dropdown
- ✅ Separate credentials for each environment
- ✅ All transactions logged with environment context

---

## 📝 Configuration

### Method 1: HTTP Remote Server (Recommended for Teams)

Configure multiple MCP servers in `mcp.json`, each pointing to the same remote MCP server but with different AWX credentials:

**File**: `%APPDATA%\Code\User\mcp.json` (Windows) or `~/.config/Code/User/mcp.json` (Linux/Mac)

```json
{
	"servers": {
		"awx-local": {
			"type": "http",
			"url": "http://localhost:8000/mcp",
			"headers": {
				"X-AWX-Base-URL": "http://localhost:30080",
				"X-AWX-Username": "admin",
				"X-AWX-Password": "your-local-password",
				"X-AWX-Platform": "awx",
				"X-AWX-Verify-SSL": "false"
			}
		},
		"awx-dev": {
			"type": "http",
			"url": "http://localhost:8000/mcp",
			"headers": {
				"X-AWX-Base-URL": "https://awx-dev.example.com",
				"X-AWX-Username": "dev-user",
				"X-AWX-Password": "dev-password",
				"X-AWX-Platform": "awx",
				"X-AWX-Verify-SSL": "true"
			}
		},
		"awx-staging": {
			"type": "http",
			"url": "http://localhost:8000/mcp",
			"headers": {
				"X-AWX-Base-URL": "https://awx-staging.example.com",
				"X-AWX-Username": "staging-user",
				"X-AWX-Password": "staging-password",
				"X-AWX-Platform": "awx",
				"X-AWX-Verify-SSL": "true"
			}
		},
		"aap-production": {
			"type": "http",
			"url": "http://localhost:8000/mcp",
			"headers": {
				"X-AWX-Base-URL": "https://aap.example.com",
				"X-AWX-Token": "your-production-token",
				"X-AWX-Platform": "aap",
				"X-AWX-Verify-SSL": "true"
			}
		}
	},
	"inputs": []
}
```

### Method 2: STDIO Local Mode (Recommended for Individual Users)

Configure multiple MCP servers in `settings.json`, each with separate environment variables:

**File**: `.vscode/settings.json` or `%APPDATA%\Code\User\settings.json`

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-local": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "http://localhost:30080",
        "AWX_USERNAME": "admin",
        "AWX_PASSWORD": "your-local-password",
        "AWX_PLATFORM": "awx",
        "AWX_VERIFY_SSL": "false"
      }
    },
    "awx-dev": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-dev.example.com",
        "AWX_USERNAME": "dev-user",
        "AWX_PASSWORD": "dev-password",
        "AWX_PLATFORM": "awx",
        "AWX_VERIFY_SSL": "true"
      }
    },
    "awx-staging": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-staging.example.com",
        "AWX_TOKEN": "staging-api-token",
        "AWX_PLATFORM": "awx",
        "AWX_VERIFY_SSL": "true"
      }
    },
    "aap-production": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://aap.example.com",
        "AWX_TOKEN": "production-api-token",
        "AWX_PLATFORM": "aap",
        "AWX_VERIFY_SSL": "true"
      }
    }
  }
}
```

---

## 🔄 How to Switch Environments

### In GitHub Copilot Chat

1. Open Copilot Chat panel (Ctrl+Shift+I or Cmd+Shift+I)
2. Click the **MCP server dropdown** (top of chat panel)
3. Select your desired environment:
   - `awx-local` - Local development
   - `awx-dev` - Development environment
   - `awx-staging` - Staging environment
   - `aap-production` - Production environment

4. Start querying:
   ```
   list job templates
   show recent jobs
   launch template "Deploy App"
   ```

**The MCP server will automatically use the credentials for the selected environment!**

---

## 📊 Environment-Specific Configurations

### Local Development
```json
{
  "awx-local": {
    "headers": {
      "X-AWX-Base-URL": "http://localhost:30080",
      "X-AWX-Username": "admin",
      "X-AWX-Password": "admin",
      "X-AWX-Platform": "awx",
      "X-AWX-Verify-SSL": "false"  // ⚠️ Disable SSL for local
    }
  }
}
```

### Development Environment
```json
{
  "awx-dev": {
    "headers": {
      "X-AWX-Base-URL": "https://awx-dev.example.com",
      "X-AWX-Token": "dev_token_abc123",  // Using token instead of password
      "X-AWX-Platform": "awx",
      "X-AWX-Verify-SSL": "true"  // ✅ Enable SSL
    }
  }
}
```

### Staging Environment
```json
{
  "awx-staging": {
    "headers": {
      "X-AWX-Base-URL": "https://awx-staging.example.com",
      "X-AWX-Token": "staging_token_xyz789",
      "X-AWX-Platform": "awx",
      "X-AWX-Verify-SSL": "true"
    }
  }
}
```

### Production Environment (AAP)
```json
{
  "aap-production": {
    "headers": {
      "X-AWX-Base-URL": "https://aap.example.com",
      "X-AWX-Token": "prod_token_secure_12345",
      "X-AWX-Platform": "aap",  // ⚠️ Use 'aap' for Automation Platform
      "X-AWX-Verify-SSL": "true"
    }
  }
}
```

---

## 🔐 Security Best Practices

### For Local/Dev Environments
- ✅ Use username/password for convenience
- ⚠️ OK to disable SSL verification for local only
- ✅ Store passwords in `mcp.json` (not committed to Git)

### For Staging/Production
- ✅ **Always use API tokens** instead of passwords
- ✅ **Enable SSL verification** (`X-AWX-Verify-SSL": "true"`)
- ✅ Rotate tokens regularly (every 90 days)
- ✅ Use separate tokens for each environment
- ✅ Never commit credentials to Git
- ✅ Consider using environment variables instead of hardcoded values

### Token Rotation Workflow
```bash
# 1. Generate new token in AWX/AAP UI
# 2. Test new token
curl https://aap.example.com/api/v2/me/ \
  -H "Authorization: Token NEW_TOKEN"

# 3. Update mcp.json with new token
# 4. Reload VS Code: Ctrl+Shift+P → "Developer: Reload Window"
# 5. Test in Copilot Chat
# 6. Revoke old token in AWX/AAP UI
```

---

## 📝 Transaction Logging

All transactions are automatically logged with environment context. The MCP server logs include:

**Log Fields**:
- `timestamp` - When the request occurred
- `environment` - Which AWX environment (extracted from X-AWX-Base-URL header)
- `tenant_id` - User/tenant identifier
- `method` - MCP method (tools/call, tools/list, etc.)
- `tool_name` - AWX tool being called
- `status` - Success/failure
- `duration_ms` - Request duration
- `error` - Error message if failed

**Example Log Output**:
```json
{
  "timestamp": "2026-02-23T01:30:45Z",
  "level": "info",
  "event": "mcp_message_received",
  "tenant_id": "default",
  "environment": "https://awx-dev.example.com",
  "method": "tools/call",
  "tool_name": "awx_templates_list"
}
```

**View Logs**:
```bash
# HTTP server logs
docker logs awx-mcp-server

# Or if running locally
tail -f ~/.local/share/awx-mcp-server/logs/mcp-server.log
```

---

## 🚀 Quick Start Checklist

### Setup
- [ ] Install MCP server: `pip install awx-mcp-server` (for STDIO mode)
- [ ] Start HTTP server: `docker-compose up -d` (for HTTP mode)
- [ ] Create `mcp.json` with all environments
- [ ] Add credentials for each environment
- [ ] Reload VS Code

### Usage
- [ ] Open GitHub Copilot Chat
- [ ] Select environment from dropdown
- [ ] Query: `list job templates`
- [ ] Verify correct environment (check logs)
- [ ] Switch to another environment
- [ ] Query again to confirm switch worked

---

## 🛠️ Troubleshooting

### Issue: Can't see environment dropdown
**Solution**: Reload VS Code after editing `mcp.json`

### Issue: Wrong environment being used
**Solution**: 
1. Check which MCP server is selected in dropdown
2. Restart selected MCP server: Ctrl+Shift+P → "MCP: Restart Server: [server-name]"

### Issue: Authentication failed
**Solution**:
1. Verify credentials in `mcp.json` or `settings.json`
2. Test credentials directly:
   ```bash
   curl https://awx.example.com/api/v2/me/ \
     -H "Authorization: Token YOUR_TOKEN"
   ```
3. Check token expiration in AWX/AAP UI

### Issue: SSL verification errors
**Solution**:
- For production: Fix SSL certificate issues
- For dev/local only: Set `"X-AWX-Verify-SSL": "false"`

---

## 📚 Related Documentation

- [Production Readiness Checklist](./PRODUCTION_READINESS.md)
- [Security Best Practices](./SECURITY.md)
- [Logging and Monitoring](./LOGGING.md)
- [Quick Start Guide](../QUICK_START.md)

---

## 💡 Example Workflow

```
Developer Workflow:

1. Morning: Switch to "awx-local"
   - Test new playbook locally
   - "create playbook deploy_app.yml"
   - "run playbook deploy_app.yml in check mode"

2. Afternoon: Switch to "awx-dev"
   - Deploy to dev environment
   - "update AWX project 1 from SCM"
   - "launch job template 5"

3. Evening: Switch to "awx-staging"
   - Test in staging
   - "show recent jobs"
   - "launch job template 5"

4. Next Day: Switch to "aap-production"
   - Production deployment
   - "list job templates"
   - "launch template 'Production Deploy'"
   - "show output for job 123"
```

---

## ✅ Production Ready

This multi-environment setup is production-ready with:
- ✅ Secure credential management
- ✅ SSL verification for prod/staging
- ✅ Comprehensive transaction logging
- ✅ Easy environment switching
- ✅ Separate tokens per environment
- ✅ Token rotation support
