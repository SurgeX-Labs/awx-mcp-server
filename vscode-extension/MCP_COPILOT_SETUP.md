# AWX MCP Server - GitHub Copilot Chat Configuration

## Industry Standard MCP Configuration (No Extension Needed)

Configure AWX MCP Server directly with GitHub Copilot Chat following industry best practices.

---

## 🎯 What This Is

This guide shows you how to use **awx-mcp-server** directly with GitHub Copilot Chat, **without needing the VS Code extension**.

This follows the **industry standard** MCP (Model Context Protocol) pattern used by:
- Postman MCP Server
- Anthropic Claude MCP Servers
- OpenAI MCP implementations

---

## ✅ Prerequisites

1. **Python 3.10+** installed
2. **VS Code** with **GitHub Copilot** extension
3. **AWX/Ansible Tower** instance with API access

---

## 🚀 Quick Start

### Step 1: Install AWX MCP Server

```bash
pip install awx-mcp-server
```

Verify installation:
```bash
python -m awx_mcp_server --version
```

### Step 2: Store AWX API Token

**Option A: Environment Variables**
```powershell
# PowerShell (Windows)
$env:AWX_BASE_URL = "https://awx.example.com"
$env:AWX_TOKEN = "your-awx-api-token-here"
```

```bash
# Bash (Mac/Linux)
export AWX_BASE_URL="https://awx.example.com"
export AWX_TOKEN="your-awx-api-token-here"
```

**Option B: VS Code Secret Storage** (Recommended)

1. Open VS Code User Settings (JSON): `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
2. Use VS Code secret storage (configure in next step)

### Step 3: Configure GitHub Copilot MCP

**Option A: User Settings (Recommended)**

Open VS Code User Settings (JSON):
```
Ctrl+Shift+P → "Preferences: Open User Settings (JSON)"
```

Add MCP server configuration:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "your-token-here"
      }
    }
  }
}
```

**Option B: Workspace Settings (Project-specific)**

Create or edit `.vscode/settings.json` in your project:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.your-company.com",
        "AWX_TOKEN": "${secret:awx-token}"
      }
    }
  }
}
```

**Using Secrets (Secure):**

Instead of hardcoding tokens, use VS Code secrets:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-api-token}"
      }
    }
  }
}
```

Then store the secret:
```
Ctrl+Shift+P → "GitHub: Store Secret"
Name: awx-api-token
Value: your-actual-token
```

### Step 4: Reload VS Code

```
Ctrl+Shift+P → "Developer: Reload Window"
```

### Step 5: Test with GitHub Copilot Chat

Open Copilot Chat: `Ctrl+Shift+P` → "GitHub Copilot: Open Chat"

Try these commands:

```
@workspace list AWX job templates

@workspace show me recent AWX jobs

@workspace what inventories are available in AWX?

@workspace launch the "Deploy Production" job template
```

GitHub Copilot will automatically discover and use AWX MCP tools!

---

## 🔧 Configuration Options

### Basic Configuration

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "your-token"
      }
    }
  }
}
```

### Advanced Configuration

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-production": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-prod.example.com",
        "AWX_TOKEN": "${secret:awx-prod-token}",
        "AWX_VERIFY_SSL": "true",
        "LOG_LEVEL": "info"
      }
    },
    "awx-staging": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-staging.example.com",
        "AWX_TOKEN": "${secret:awx-staging-token}",
        "AWX_VERIFY_SSL": "false",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

### Using Username/Password Instead of Token

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_USERNAME": "admin",
        "AWX_PASSWORD": "${secret:awx-password}",
        "AWX_VERIFY_SSL": "true"
      }
    }
  }
}
```

---

## 🌍 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWX_BASE_URL` | ✅ Yes | - | AWX instance URL (e.g., `https://awx.example.com`) |
| `AWX_TOKEN` | ⚠️ Yes* | - | AWX API token |
| `AWX_USERNAME` | ⚠️ No* | - | Username for password authentication |
| `AWX_PASSWORD` | ⚠️ No* | - | Password for password authentication |
| `AWX_VERIFY_SSL` | No | `true` | Verify SSL certificates (`true` or `false`) |
| `LOG_LEVEL` | No | `info` | Logging level (`debug`, `info`, `warning`, `error`) |

*Either `AWX_TOKEN` or `AWX_USERNAME`+`AWX_PASSWORD` required.

---

## 📊 Available MCP Tools

Once configured, GitHub Copilot can use these AWX tools:

### Job Templates
- `list_job_templates` - List all job templates
- `get_job_template` - Get details of a specific template
- `launch_job_template` - Launch a job from template

### Jobs
- `list_jobs` - List recent jobs
- `get_job` - Get job details and status
- `get_job_output` - Get job stdout/stderr
- `cancel_job` - Cancel a running job

### Inventories
- `list_inventories` - List all inventories
- `get_inventory` - Get inventory details
- `list_inventory_hosts` - List hosts in inventory

### Projects
- `list_projects` - List all projects
- `get_project` - Get project details
- `update_project` - Sync project from SCM

### Workflows
- `list_workflow_templates` - List workflow templates
- `launch_workflow` - Launch a workflow

GitHub Copilot will automatically select and invoke these tools based on your natural language queries!

---

## 💡 Usage Examples

### List Resources

```
User: @workspace show me all AWX job templates

Copilot: [Invokes list_job_templates tool]
Here are your AWX job templates:
1. Deploy Production App
2. Restart Nginx Servers
3. Database Backup
...
```

### Launch Job

```
User: @workspace launch the "Deploy Production App" job template with environment=prod

Copilot: [Invokes launch_job_template tool]
Job launched successfully!
Job ID: 12345
Status: Running
URL: https://awx.example.com/#/jobs/12345
```

### Check Job Status

```
User: @workspace what's the status of job 12345?

Copilot: [Invokes get_job tool]
Job 12345: Deploy Production App
Status: Successful
Duration: 2m 34s
Started: 2026-02-12 10:15:00
Finished: 2026-02-12 10:17:34
```

### Complex Query

```
User: @workspace find any failed jobs in the last 24 hours and show me their error messages

Copilot: [Invokes list_jobs with filters, then get_job_output for each]
Found 2 failed jobs:

1. Job 12340 - Deploy Staging App
   Error: Connection timeout to staging-server-01
   
2. Job 12338 - Database Migration
   Error: Table already exists: user_profiles
```

---

## 🔒 Security Best Practices

### 1. Use Secrets, Not Plain Text

❌ **Bad:**
```json
"env": {
  "AWX_TOKEN": "my-actual-token-12345"
}
```

✅ **Good:**
```json
"env": {
  "AWX_TOKEN": "${secret:awx-token}"
}
```

### 2. Use Per-Environment Tokens

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-prod": {
      "env": {
        "AWX_BASE_URL": "https://awx-prod.example.com",
        "AWX_TOKEN": "${secret:awx-prod-token}"
      }
    },
    "awx-dev": {
      "env": {
        "AWX_BASE_URL": "https://awx-dev.example.com",
        "AWX_TOKEN": "${secret:awx-dev-token}"
      }
    }
  }
}
```

### 3. Workspace vs User Settings

**User Settings** (global):
- Use for personal AWX instances
- Applies to all projects

**Workspace Settings** (project-specific):
- Use for team/project AWX instances
- `.vscode/settings.json` (can be committed, use secrets!)
- Different teams use different AWX instances

---

## 🐛 Troubleshooting

### Issue: Copilot doesn't see AWX tools

**Check:**
1. MCP server configured in settings?
   ```json
   "github.copilot.chat.mcpServers": { "awx": {...} }
   ```

2. Python path correct?
   ```bash
   which python  # Mac/Linux
   where python  # Windows
   ```

3. awx-mcp-server installed?
   ```bash
   python -m awx_mcp_server --version
   ```

**Solution:**
```
Ctrl+Shift+P → "Developer: Reload Window"
```

### Issue: Authentication failed

**Check:**
1. AWX_BASE_URL correct? (include https://)
2. Token valid?
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://awx.example.com/api/v2/me
   ```

**Solution:**
- Regenerate token in AWX UI
- Update secret: `Ctrl+Shift+P` → "GitHub: Store Secret"

### Issue: SSL certificate error

**Solution:**
Add to configuration:
```json
"env": {
  "AWX_VERIFY_SSL": "false"
}
```

**Warning:** Only use `false` for self-signed certificates in dev/test environments!

### Issue: Python not found

**Solution:**
Specify full path:
```json
"command": "C:\\Python312\\python.exe",  // Windows
"command": "/usr/local/bin/python3",      // Mac/Linux
```

---

## 🔄 Updating AWX MCP Server

```bash
pip install --upgrade awx-mcp-server
```

Then reload VS Code:
```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

## 🎨 Optional: Add VS Code Extension

The AWX MCP Extension provides additional UI features:

**Install Extension:**
```
Ctrl+Shift+P → "Extensions: Install"
Search: "AWX MCP Extension"
```

**Extension Features:**
- 📊 Sidebar views (instances, jobs, metrics)
- 🌲 Tree view of resources
- 🎨 Webview configuration UI
- 📈 Real-time job monitoring

**Note:** Extension is OPTIONAL. MCP server works standalone!

---

## 📚 Comparison: MCP Only vs Extension

| Feature | MCP Only (This Guide) | MCP + Extension |
|---------|----------------------|-----------------|
| **Installation** | `pip install awx-mcp-server` | Extension from marketplace |
| **Configuration** | Manual (settings.json) | Automatic configuration UI |
| **Chat Integration** | ✅ GitHub Copilot | ✅ GitHub Copilot + @awx |
| **UI** | None (chat only) | Sidebar views, tree providers |
| **Portability** | Works with Claude, Cursor, etc. | VS Code only |
| **Complexity** | Low (1 component) | Medium (extension + server) |
| **Updates** | `pip install --upgrade` | Extension auto-updates |

**Choose:**
- **MCP Only:** If you want standard, portable, simple setup
- **MCP + Extension:** If you want rich UI, automatic setup, one-click experience

---

## 🌟 Industry Standard Benefits

Following the pure MCP pattern (like Postman) gives you:

✅ **Portability** - Works with any MCP client (Copilot, Claude, Cursor, etc.)  
✅ **Simplicity** - One component, standard configuration  
✅ **Maintainability** - Clear separation, well-documented  
✅ **Future-proof** - Follows MCP specification and best practices  
✅ **Community** - Standard pattern used by major vendors  

---

## 📖 Additional Resources

- **MCP Specification:** https://modelcontextprotocol.io
- **AWX API Documentation:** https://docs.ansible.com/automation-controller/latest/html/controllerapi/
- **GitHub Copilot MCP:** https://code.visualstudio.com/docs/copilot/copilot-mcp-servers
- **Postman MCP (Reference):** https://github.com/postmanlabs/postman-mcp-server

---

## 🆘 Support

**Issues:**
- GitHub: https://github.com/SurgeX-Labs/awx-mcp-server/issues
- MCP Server: `awx-mcp-server` package (PyPI)

**Extension (Optional):**
- Extension ID: `surgexlabs.awx-mcp-extension`
- Marketplace: VS Code Extensions

---

**Last Updated:** February 12, 2026  
**AWX MCP Server:** 1.0.0  
**Pattern:** Industry Standard (Postman-style MCP) ✅  
**Works With:** GitHub Copilot, Claude, Cursor, any MCP client
