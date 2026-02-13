# AWX MCP Server - Quick Start Guide

## Industry Standard MCP Configuration

This is the **recommended** way to use AWX MCP Server - configure it directly with your MCP client (GitHub Copilot, Claude, Cursor, etc.)

---

## 🚀 Installation

### Step 1: Install from PyPI

```bash
pip install awx-mcp-server
```

Verify installation:
```bash
python -m awx_mcp_server --version
# Output: awx-mcp-server 1.0.0
```

---

## ⚙️ Configuration

### For GitHub Copilot (VS Code)

**Option A: User Settings (Global)**

1. Open VS Code User Settings (JSON):
   ```
   Ctrl+Shift+P → "Preferences: Open User Settings (JSON)"
   ```

2. Add MCP server configuration:

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

3. Store your AWX token:
   ```
   Ctrl+Shift+P → "GitHub: Store Secret"
   Name: awx-token
   Value: your-awx-api-token
   ```

4. Reload VS Code:
   ```
   Ctrl+Shift+P → "Developer: Reload Window"
   ```

**Option B: Workspace Settings (Project-specific)**

Create `.vscode/settings.json` in your project:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.your-company.com",
        "AWX_TOKEN": "${secret:awx-token}",
        "AWX_VERIFY_SSL": "true"
      }
    }
  }
}
```

### For Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "your-awx-token"
      }
    }
  }
}
```

### For Cursor

Add to Cursor settings (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "your-awx-token"
      }
    }
  }
}
```

---

## 🎯 Usage

### With GitHub Copilot Chat

Open Copilot Chat and try these commands:

```
@workspace list AWX job templates

@workspace show me recent failed jobs

@workspace launch the "Deploy Production" job template

@workspace what inventories are available?

@workspace get output from job 12345
```

### With Claude Desktop

Simply ask Claude:

```
List my AWX job templates

Show me the last 10 jobs

Launch the "Restart Nginx" job template
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWX_BASE_URL` | ✅ Yes | AWX instance URL (e.g., `https://awx.example.com`) |
| `AWX_TOKEN` | ⚠️ Yes* | AWX API token |
| `AWX_USERNAME` | ⚠️ No* | Username (if not using token) |
| `AWX_PASSWORD` | ⚠️ No* | Password (if not using token) |
| `AWX_VERIFY_SSL` | No | Verify SSL certificates (default: `true`) |
| `LOG_LEVEL` | No | Logging level: `debug`, `info`, `warning`, `error` (default: `info`) |

*Either `AWX_TOKEN` or `AWX_USERNAME` + `AWX_PASSWORD` required.

---

## 🔐 Getting an AWX API Token

1. Log in to your AWX instance
2. Click your username (top right) → **Token**
3. Click **Add** button
4. Set **Application** and **Scope** (Read + Write recommended)
5. Click **Save**
6. Copy the token immediately (it won't be shown again!)

---

## 📊 Available Tools

Once configured, your MCP client can use these AWX tools:

### Job Management
- `list_job_templates` - List all job templates
- `get_job_template` - Get template details
- `launch_job_template` - Launch a job
- `list_jobs` - List recent jobs (with filters)
- `get_job` - Get job details
- `get_job_output` - Get job stdout/stderr
- `cancel_job` - Cancel a running job

### Inventory Management
- `list_inventories` - List all inventories
- `get_inventory` - Get inventory details
- `list_inventory_hosts` - List hosts in inventory

### Project Management
- `list_projects` - List all projects
- `get_project` - Get project details
- `update_project` - Sync project from SCM

### Workflow Management
- `list_workflow_templates` - List workflow templates
- `launch_workflow` - Launch a workflow

### System
- `list_credentials` - List credentials
- `list_organizations` - List organizations
- `get_system_health` - Get system health metrics

---

## 💡 Multiple AWX Instances

You can configure multiple AWX instances:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-production": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-prod.example.com",
        "AWX_TOKEN": "${secret:awx-prod-token}"
      }
    },
    "awx-staging": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://awx-staging.example.com",
        "AWX_TOKEN": "${secret:awx-staging-token}"
      }
    }
  }
}
```

Then use: `@workspace use awx-production to list job templates`

---

## 🐛 Troubleshooting

### MCP server not detected

1. Verify installation:
   ```bash
   python -m awx_mcp_server --version
   ```

2. Check Python path in configuration
3. Reload your MCP client (VS Code, Claude, etc.)

### Authentication errors

1. Verify `AWX_BASE_URL` is correct (include `https://`)
2. Test token with curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://awx.example.com/api/v2/me
   ```
3. Regenerate token in AWX if needed

### SSL certificate errors

Add to configuration:
```json
"env": {
  "AWX_VERIFY_SSL": "false"
}
```

**Note:** Only disable SSL verification for self-signed certificates in dev/test environments.

### Connection timeouts

1. Check AWX instance is accessible from your machine
2. Verify firewall rules
3. Test with: `curl https://awx.example.com/api/v2/ping/`

---

## 🔄 Updating

```bash
pip install --upgrade awx-mcp-server
```

Then reload your MCP client.

---

## 📖 Additional Resources

- **Full Documentation:** [README.md](README.md)
- **GitHub Repository:** https://github.com/SurgeX-Labs/awx-mcp-server
- **Issues & Support:** https://github.com/SurgeX-Labs/awx-mcp-server/issues
- **MCP Specification:** https://modelcontextprotocol.io
- **AWX API Docs:** https://docs.ansible.com/automation-controller/

---

## 🎨 Optional: VS Code Extension

For additional UI features (sidebar views, tree providers, configuration webview), install the **AWX MCP Extension** from VS Code Marketplace:

```
Ctrl+Shift+P → "Extensions: Install Extensions"
Search: "AWX MCP Extension"
Publisher: SurgeXlabs
```

**Note:** Extension is **optional**. The MCP server works perfectly without it!

---

**Pattern:** Industry Standard (Postman-style) ✅  
**Works With:** GitHub Copilot, Claude, Cursor, any MCP client  
**Installation:** `pip install awx-mcp-server`  
**Configuration:** Direct in MCP client settings
