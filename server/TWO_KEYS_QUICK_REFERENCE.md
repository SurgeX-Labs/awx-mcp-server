# 🔑 Two Keys Quick Reference Card

## Overview

**YES, you need TWO different API keys for remote MCP server setup:**

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  VS Code ───[Key #2]──→ MCP Server ───[Key #1]──→ AAP/AWX      │
│  (Client)   MCP API Key   (Proxy)      AAP Token     (Target)   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key #1: AAP/AWX Token 🔐 (YOUR Credentials)

| Attribute | Details |
|-----------|---------|
| **Purpose** | Authenticate MCP server → AAP/AWX |
| **Who owns it** | You (each user has their own) |
| **Where to get** | AAP UI → Profile → Tokens |
| **Example** | `abc123xyz456def789...` |
| **Environment Variable** | `AAP_TOKEN` |
| **VS Code Field** | `env.AAP_TOKEN` or `secrets.X-AWX-Token` |
| **Required?** | ✅ **YES - Always** |

### How to Get Key #1:

1. Login to https://aap.devfg.surgexlabs.com
2. Navigate: Users → Your Profile → Tokens
3. Click "Create Token"
4. Copy token

### Save as Environment Variable:

**Windows PowerShell:**
```powershell
$env:AAP_TOKEN = "abc123xyz456..."
[System.Environment]::SetEnvironmentVariable('AAP_TOKEN', 'abc123xyz456...', 'User')
```

**Linux/macOS:**
```bash
export AAP_TOKEN="abc123xyz456..."
echo 'export AAP_TOKEN="abc123xyz456..."' >> ~/.bashrc
```

---

## Key #2: MCP Server API Key 🗝️ (Server Access)

| Attribute | Details |
|-----------|---------|
| **Purpose** | Authenticate VS Code → MCP Server |
| **Who owns it** | You (issued by MCP admin) |
| **Where to get** | MCP Server Administrator |
| **Example** | `awx_mcp_def789ghi012...` |
| **Environment Variable** | `MCP_API_KEY` |
| **VS Code Field** | `headers.X-API-Key` |
| **Required?** | ⚠️ **Optional (recommended for production)** |

### How to Get Key #2:

**Ask your MCP server admin to run:**

```bash
curl -X POST https://awx-mcp-server.surgexlabs.com/api/keys \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "your-name-vscode",
    "tenant_id": "your.email@company.com",
    "expires_days": 90
  }'
```

**They will give you**: `awx_mcp_def789ghi012...`

### Save as Environment Variable:

**Windows PowerShell:**
```powershell
$env:MCP_API_KEY = "awx_mcp_def789ghi012..."
[System.Environment]::SetEnvironmentVariable('MCP_API_KEY', 'awx_mcp_def789ghi012...', 'User')
```

**Linux/macOS:**
```bash
export MCP_API_KEY="awx_mcp_def789ghi012..."
echo 'export MCP_API_KEY="awx_mcp_def789ghi012..."' >> ~/.bashrc
```

---

## VS Code Configuration (Using Both Keys)

### Method 1: Environment Variables (Recommended)

**settings.json:**
```json
{
  "github.copilot.chat.mcpServers": {
    "surgexlabs-aap-dev": {
      "url": "https://awx-mcp-server.surgexlabs.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "${env:MCP_API_KEY}",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "env": {
        "AAP_TOKEN": "${env:AAP_TOKEN}"
      }
    }
  }
}
```

✅ **Best practice**: Keeps credentials out of settings.json

---

### Method 2: Direct in settings.json

**settings.json:**
```json
{
  "github.copilot.chat.mcpServers": {
    "surgexlabs-aap-dev": {
      "url": "https://awx-mcp-server.surgexlabs.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_def789ghi012...",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "secrets": {
        "X-AWX-Token": "abc123xyz456..."
      }
    }
  }
}
```

⚠️ **Warning**: Don't commit to Git!

---

### Method 3: Without MCP API Key (Development Only)

**settings.json:**
```json
{
  "github.copilot.chat.mcpServers": {
    "surgexlabs-aap-dev": {
      "url": "http://localhost:8000/mcp",
      "transport": "http",
      "headers": {
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "secrets": {
        "X-AWX-Token": "abc123xyz456..."
      }
    }
  }
}
```

⚠️ **Only use for local testing!**

---

## Quick Decision Tree

```
Do you have a remote MCP server?
│
├─ YES → You need both keys:
│   ├─ Key #1: AAP Token (from AAP UI)
│   └─ Key #2: MCP API Key (from MCP admin)
│
└─ NO (running locally) → You only need:
    └─ Key #1: AAP Token (from AAP UI)
```

---

## Complete Setup Checklist

### ✅ Prerequisites
- [ ] VS Code installed
- [ ] GitHub Copilot extension installed
- [ ] Active GitHub Copilot subscription
- [ ] Access to AAP instance (https://aap.devfg.surgexlabs.com)
- [ ] MCP server URL provided by admin

### ✅ Get Key #1 (AAP Token)
- [ ] Login to AAP
- [ ] Create personal token
- [ ] Save to `AAP_TOKEN` environment variable
- [ ] Verify: `echo $env:AAP_TOKEN` (PowerShell) or `echo $AAP_TOKEN` (bash)

### ✅ Get Key #2 (MCP API Key) - Optional
- [ ] Contact MCP server admin
- [ ] Receive MCP API key
- [ ] Save to `MCP_API_KEY` environment variable
- [ ] Verify: `echo $env:MCP_API_KEY` (PowerShell) or `echo $MCP_API_KEY` (bash)

### ✅ Configure VS Code
- [ ] Open settings.json (`Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)")
- [ ] Add MCP server configuration with both keys
- [ ] Reload VS Code window

### ✅ Test Connection
- [ ] Open GitHub Copilot Chat
- [ ] Try: `@surgexlabs-aap-dev List job templates`
- [ ] Verify you see results

---

## Testing Your Setup

### Test 1: Verify Environment Variables

**Windows PowerShell:**
```powershell
echo $env:AAP_TOKEN        # Should show: abc123xyz456...
echo $env:MCP_API_KEY      # Should show: awx_mcp_def789ghi012...
```

**Linux/macOS:**
```bash
echo $AAP_TOKEN            # Should show: abc123xyz456...
echo $MCP_API_KEY          # Should show: awx_mcp_def789ghi012...
```

### Test 2: Test MCP Server Connection

```bash
# Test health endpoint
curl https://awx-mcp-server.surgexlabs.com/health

# Test with your MCP API key
curl https://awx-mcp-server.surgexlabs.com/api/v1/environments \
  -H "X-API-Key: awx_mcp_def789ghi012..."
```

### Test 3: Test in Copilot Chat

```
@surgexlabs-aap-dev List all job templates
@surgexlabs-aap-dev Show AAP version
@surgexlabs-aap-dev What environments are configured?
```

---

## Troubleshooting

### ❌ Error: "401 Unauthorized"

**Cause**: Invalid MCP API Key (Key #2)

**Fix**:
1. Check `X-API-Key` header in settings.json
2. Verify MCP_API_KEY environment variable
3. Contact admin for new key

---

### ❌ Error: "403 Forbidden - Invalid AAP credentials"

**Cause**: Invalid AAP Token (Key #1)

**Fix**:
1. Test AAP token:
   ```bash
   curl https://aap.devfg.surgexlabs.com/api/v2/me/ \
     -H "Authorization: Bearer $AAP_TOKEN"
   ```
2. If invalid, get new token from AAP UI
3. Update AAP_TOKEN environment variable

---

### ❌ Error: "Cannot read environment variable"

**Cause**: Environment variable not set or VS Code not restarted

**Fix**:
1. Verify environment variable is set (see Test 1 above)
2. Completely **close and restart VS Code** (not just reload window)
3. On Windows, you may need to log out and log back in

---

## Security Best Practices

| ✅ DO | ❌ DON'T |
|-------|----------|
| Use environment variables | Commit keys to Git |
| Use HTTPS for remote servers | Share API keys with others |
| Set key expiration (90 days) | Disable SSL verification in production |
| Store AAP token in VS Code secrets | Put keys in public repositories |
| Use workspace settings | Use HTTP in production |

---

## Summary

**For surgexlabs AAP Remote Setup, you need:**

1. **AAP Token** from https://aap.devfg.surgexlabs.com (for AAP authentication)
2. **MCP API Key** from your MCP server admin (for MCP server access)

**Both saved as environment variables:**
- `AAP_TOKEN` = your AAP token
- `MCP_API_KEY` = your MCP API key

**Referenced in VS Code settings.json:**
```json
{
  "headers": {
    "X-API-Key": "${env:MCP_API_KEY}"
  },
  "env": {
    "AAP_TOKEN": "${env:AAP_TOKEN}"
  }
}
```

**✨ That's it! You're ready to use AWX MCP Server with GitHub Copilot!**

---

For detailed setup instructions, see:
- **[REMOTE_CLIENT_SETUP.md](REMOTE_CLIENT_SETUP.md)** - Complete remote setup guide
- **[AAP_SUPPORT.md](../AAP_SUPPORT.md)** - AAP-specific configuration
- **[QUICK_START.md](QUICK_START.md)** - Local setup (no Key #2 needed)
