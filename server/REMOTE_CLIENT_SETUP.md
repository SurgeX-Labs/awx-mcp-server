# Remote MCP Server - Client Setup Guide

## Overview

This guide shows how to configure **VS Code GitHub Copilot Chat** to communicate with a **remote AWX MCP Server** (HTTP mode), where:

- 🌐 **Server runs remotely** (Docker, Kubernetes, cloud, or remote machine)
- 💻 **Client runs in VS Code** (your local workstation)
- 🔐 **Credentials stored on client side** (in VS Code secrets)
- 🏢 **Multi-user/Multi-tenant** support (each user has their own config)

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  VS Code (Client)               │
│  ┌───────────────────────────┐  │
│  │ GitHub Copilot Chat       │  │
│  │                           │  │
│  │ "Launch job in AAP"       │  │
│  └───────────┬───────────────┘  │
│              │                  │
│  ┌───────────▼───────────────┐  │
│  │ MCP Client (HTTP/SSE)     │  │
│  │ - User credentials        │  │
│  │ - AAP environment config  │  │
│  └───────────┬───────────────┘  │
└──────────────┼──────────────────┘
               │ HTTPS
               │
┌──────────────▼──────────────────┐
│  Remote MCP Server              │
│  (Docker/K8s/Cloud)             │
│  ┌──────────────────────────┐   │
│  │ HTTP Server (Port 8000)  │   │
│  │ - API Key authentication │   │
│  │ - AAP API calls          │   │
│  └──────────────────────────┘   │
│              │                  │
│              ▼                  │
│     https://aap.devfg.surgexlabs.com/  │
└─────────────────────────────────┘
```

**Key Points**:
- Client stores: User credentials, AAP URL, environment config
- Server handles: API routing, job execution, monitoring
- Communication: HTTP/SSE (MCP over HTTP)

---

## 🔑 Two Keys Explained

### **Key #1: AAP/AWX Token** (Your AAP Credentials)

```
MCP Server ─────[AAP Token]────> AAP/AWX
```

- **Purpose**: Authenticates the MCP server to your AAP/AWX instance
- **Who needs it**: Every user (your personal credentials)
- **Where to get**: From your AAP UI → Profile → Tokens
- **Where stored**: VS Code secrets (client-side, encrypted)
- **Format**: `abc123xyz...` (Bearer token)
- **VS Code field**: `secrets.X-AWX-Token`
- **Required**: ✅ **YES - Always required**

### **Key #2: MCP Server API Key** (Server Access Control)

```
VS Code ─────[MCP API Key]────> MCP Server
```

- **Purpose**: Authenticates your VS Code client to the remote MCP server
- **Who needs it**: Every user (prevents unauthorized access to MCP server)
- **Where to get**: From your MCP server administrator
- **Where stored**: VS Code settings.json or environment variable
- **Format**: `awx_mcp_abc123xyz...`
- **VS Code field**: `headers.X-API-Key`
- **Required**: ⚠️ **Optional (but recommended for production)**

### Authentication Flow

```
1. VS Code                    2. MCP Server               3. AAP/AWX
   (Copilot Chat)                (Remote)                    (Target)
   
   "Launch job" ───Key #2──> Validates API Key ───Key #1──> Executes job
   (MCP API Key)              Receives AAP Token            (AAP Token)
                              Proxies request ───────────>  Returns result
```

---

## � Prerequisites

### VS Code Requirements

**You only need**:
- ✅ **VS Code** (version 1.80+)
- ✅ **GitHub Copilot Extension** (includes built-in MCP client support)
- ✅ **Active GitHub Copilot subscription**

**You do NOT need**:
- ❌ Separate MCP server extension
- ❌ Additional MCP-related extensions
- ❌ Python installed locally (server handles Python execution)

The **GitHub Copilot extension** already includes MCP protocol support. Just configure `settings.json` and you're ready!

---

## �🚀 Quick Start

### Step 1: Start Remote Server

**On the server (Docker)**:
```bash
docker run -d \
  -p 8000:8000 \
  --name awx-mcp-server \
  surgexlabs/awx-mcp-server:latest
```

**Or on Kubernetes**:
```bash
kubectl apply -f deployment/kubernetes.yaml
```

**Or locally for testing**:
```bash
python -m awx_mcp_server.cli start --host 0.0.0.0 --port 8000
```

Verify server is running:
```bash
curl http://your-server:8000/health
# Should return: {"status":"healthy"...}
```

### Step 2: Get MCP Server API Key (Optional - Recommended for Production)

The MCP server supports **two authentication modes**:

#### **Option A: With API Key Authentication** (Production - Recommended)

**Ask your MCP server admin to create an API key for you**:

```bash
# Admin runs this on the server (requires admin token)
curl -X POST http://your-server:8000/api/keys \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john-doe-vscode",
    "tenant_id": "john.doe@company.com",
    "expires_days": 90
  }'
```

**Response**:
```json
{
  "api_key": "awx_mcp_abc123xyz...",
  "name": "john-doe-vscode",
  "tenant_id": "john.doe@company.com",
  "created_at": "2026-02-21T12:00:00",
  "expires_at": "2026-05-21T12:00:00"
}
```

**Save this API key** - you'll use it in VS Code configuration.

**To save as environment variable** (optional):
```powershell
# Windows PowerShell
$env:MCP_API_KEY = "awx_mcp_abc123xyz..."

# Or permanently
[System.Environment]::SetEnvironmentVariable('MCP_API_KEY', 'awx_mcp_abc123xyz...', 'User')
```

```bash
# Linux/macOS
export MCP_API_KEY="awx_mcp_abc123xyz..."

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export MCP_API_KEY="awx_mcp_abc123xyz..."' >> ~/.bashrc
```

#### **Option B: Without API Key** (Testing/Development Only)

If your MCP server is running without API key enforcement, you can skip this step. **Not recommended for production!**

### Step 3: Get Your AAP/AWX Token

**This is YOUR personal AAP authentication token:**

1. **Log in to your AAP instance**: https://aap.devfg.surgexlabs.com

2. **Navigate to**: Users → Your Profile → Tokens

3. **Click "Create Token"** or "Add Token"

4. **Copy the token** (it will look like: `abc123xyz...`)

5. **Save as environment variable** (optional):

**Windows PowerShell**:
```powershell
$env:AAP_TOKEN = "your-aap-token-here"

# Or permanently in User environment
[System.Environment]::SetEnvironmentVariable('AAP_TOKEN', 'your-aap-token-here', 'User')

# Verify
echo $env:AAP_TOKEN
```

**Linux/macOS**:
```bash
export AAP_TOKEN="your-aap-token-here"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export AAP_TOKEN="your-aap-token-here"' >> ~/.bashrc

# Verify
echo $AAP_TOKEN
```

**Note**: You'll add this token to VS Code secrets in the next step.

### Step 4: Configure VS Code

**Open VS Code Settings** (`Ctrl+,` or `Cmd+,`):

1. Search for: `chat.mcp`
2. Click **"Edit in settings.json"**
3. Add the remote server configuration:

---

## 📝 VS Code Configuration

### Configuration Mode A: With API Key (Production)

**VS Code settings.json** - Using API key authentication:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-mcp-server.com:8000/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_abc123xyz...",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "secrets": {
        "X-AWX-Token": "your-aap-token"
      }
    }
  }
}
```

### Configuration Mode B: Without API Key (Development Only)

**VS Code settings.json** - No MCP API key required:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-mcp-server.com:8000/mcp",
      "transport": "http",
      "headers": {
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "secrets": {
        "X-AWX-Token": "your-aap-token"
      }
    }
  }
}
```

### Configuration Mode C: Using Environment Variables

**VS Code settings.json** - Reference environment variables:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-mcp-server.com:8000/mcp",
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

**Then your tokens are stored in environment variables** (set in Step 2 & 3).

---

## 🔑 Understanding the Two Keys

| Key | Purpose | Where to Get | Where Stored | Required? |
|-----|---------|--------------|--------------|-----------|
| **MCP API Key** | Authenticate VS Code → MCP Server | MCP Server Admin | `headers.X-API-Key` | Optional (recommended) |
| **AAP Token** | Authenticate MCP Server → AAP | Your AAP Profile | `secrets.X-AWX-Token` | **Required** |

**Configuration Breakdown**:

| Field | Description |
|-------|-------------|
| `url` | Remote MCP server endpoint |
| `transport` | Use `"http"` for remote servers |
| `headers.X-API-Key` | MCP server API key (from Step 2) |
| `headers.X-AWX-Base-URL` | Your AAP base URL |
| `headers.X-AWX-Platform` | Platform type: `aap`, `awx`, or `tower` |
| `secrets.X-AWX-Token` | Your AAP authentication token |

### Option 2: SSE Transport (Server-Sent Events)

For real-time updates and job monitoring:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-mcp-server.com:8000/mcp/sse",
      "transport": "sse",
      "headers": {
        "X-API-Key": "awx_mcp_abc123xyz...",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap"
      },
      "secrets": {
        "X-AWX-Token": "your-aap-token"
      }
    }
  }
}
```

---

## 🌐 Server URL Examples

### Localhost (Testing)

```json
{
  "url": "http://localhost:8000/mcp"
}
```

### Remote Server (HTTP)

```json
{
  "url": "http://awx-mcp-server.company.com:8000/mcp"
}
```

### Remote Server (HTTPS with SSL)

```json
{
  "url": "https://awx-mcp-server.company.com/mcp"
}
```

### Kubernetes Service (Internal)

```json
{
  "url": "http://awx-mcp-server.default.svc.cluster.local:8000/mcp"
}
```

### Behind Load Balancer

```json
{
  "url": "https://api.company.com/awx-mcp/mcp"
}
```

---

## 🔐 Storing Credentials in VS Code

### AAP/AWX Token

**Store in VS Code secrets** (recommended):

1. **Settings.json**:
```json
{
  "mcpServers": {
    "awx-remote": {
      "secrets": {
        "X-AWX-Token": "your-aap-token"
      }
    }
  }
}
```

2. VS Code will prompt you to enter the token
3. Token is encrypted and stored securely
4. **Never commit to Git!**

### Alternative: Environment Variables

If you prefer environment variables:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-server:8000/mcp",
      "env": {
        "AWX_TOKEN": "${env:AAP_TOKEN}"
      }
    }
  }
}
```

Then set in your shell:
```bash
export AAP_TOKEN="your-aap-token"
```

### Using Username/Password (Alternative)

If not using tokens:

```json
{
  "mcpServers": {
    "awx-remote": {
      "headers": {
        "X-AWX-Username": "your-username"
      },
      "secrets": {
        "X-AWX-Password": "your-password"
      }
    }
  }
}
```

---

## 🏢 Multi-Environment Setup

Configure multiple AAP instances:

```json
{
  "mcpServers": {
    "aap-production": {
      "url": "https://mcp-server.company.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_prod_key",
        "X-AWX-Base-URL": "https://aap.prod.surgexlabs.com",
        "X-AWX-Platform": "aap",
        "X-Environment": "production"
      },
      "secrets": {
        "X-AWX-Token": "prod-token"
      }
    },
    "aap-dev": {
      "url": "https://mcp-server.company.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_dev_key",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap",
        "X-Environment": "development"
      },
      "secrets": {
        "X-AWX-Token": "dev-token"
      }
    },
    "awx-test": {
      "url": "https://mcp-server.company.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_test_key",
        "X-AWX-Base-URL": "https://awx-test.company.com",
        "X-AWX-Platform": "awx",
        "X-Environment": "test"
      },
      "secrets": {
        "X-AWX-Token": "test-token"
      }
    }
  }
}
```

**Usage in Copilot Chat**:
```
@aap-production List job templates
@aap-dev Launch "Deploy App" job
@awx-test Show recent jobs
```

---

## 🧪 Testing the Configuration

### 1. Verify Server Connection

**In VS Code Terminal**:
```bash
# Test server health
curl http://your-server:8000/health

# Test API with your key
curl http://your-server:8000/api/v1/environments \
  -H "X-API-Key: awx_mcp_abc123xyz..."
```

### 2. Test in Copilot Chat

**Open Copilot Chat** and try:

```
@awx-remote Help

@awx-remote List all job templates

@awx-remote Show AAP version

@awx-remote What environments are configured?
```

### 3. Test Job Launch

```
@awx-remote Launch "Deploy Application" job template

@awx-remote Show status of job 123

@awx-remote Get output from job 123
```

---

## 🔒 Security Best Practices

### ✅ Do's

1. **Use HTTPS** for remote servers:
   ```json
   {"url": "https://mcp-server.company.com/mcp"}
   ```

2. **Store tokens in VS Code secrets**:
   ```json
   {"secrets": {"X-AWX-Token": "token-here"}}
   ```

3. **Use API key authentication**:
   ```json
   {"headers": {"X-API-Key": "awx_mcp_..."}}
   ```

4. **Limit API key scope** (create per-user keys)

5. **Set token expiration** (90 days recommended)

6. **Use SSL certificate verification**:
   ```json
   {"headers": {"X-AWX-Verify-SSL": "true"}}
   ```

### ❌ Don'ts

1. **Don't commit credentials to Git**
   - Add `settings.json` to `.gitignore`
   - Use workspace settings, not user settings

2. **Don't use HTTP in production**
   - Always use HTTPS with valid certificates

3. **Don't share API keys**
   - Each user should have their own key

4. **Don't disable SSL verification in production**
   ```json
   // ❌ Bad (only for dev/testing)
   {"headers": {"X-AWX-Verify-SSL": "false"}}
   ```

---

## 🌐 Network Configuration

### Corporate Proxy

If behind a corporate proxy:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "https://mcp-server.company.com/mcp",
      "proxy": {
        "http": "http://proxy.company.com:8080",
        "https": "http://proxy.company.com:8080"
      },
      "headers": {
        "X-API-Key": "your-key"
      }
    }
  }
}
```

### VPN Required

If MCP server is only accessible via VPN:

1. Connect to VPN first
2. Configure VS Code with internal URL:
   ```json
   {"url": "http://mcp-server.internal:8000/mcp"}
   ```

### Firewall Rules

Ensure these ports are open:

| Source | Destination | Port | Protocol |
|--------|-------------|------|----------|
| Your Workstation | MCP Server | 8000 | HTTP/HTTPS |
| MCP Server | AAP Server | 443 | HTTPS |

---

## 📊 Complete Configuration Example (surgexlabs AAP)

Based on your AAP URL: `https://aap.devfg.surgexlabs.com`

```json
{
  "mcpServers": {
    "surgexlabs-aap-dev": {
      "url": "https://awx-mcp-server.surgexlabs.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_surgexlabs_dev_key_abc123",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap",
        "X-AWX-Verify-SSL": "true",
        "X-Environment": "development"
      },
      "secrets": {
        "X-AWX-Token": "surgexlabs-aap-dev-token"
      }
    }
  }
}
```

**Steps**:

1. **Get AAP Token**:
   - Log in to https://aap.devfg.surgexlabs.com
   - Go to **Users** → **Your Profile** → **Tokens**
   - Create new token, copy it

2. **Get MCP Server API Key**:
   ```bash
   curl -X POST https://awx-mcp-server.surgexlabs.com/api/keys \
     -H "Content-Type: application/json" \
     -d '{"name":"your-name-vscode","tenant_id":"your-email"}'
   ```

3. **Add to VS Code**:
   - Open settings.json
   - Paste configuration above
   - Replace API key and add AAP token to secrets

4. **Test**:
   ```
   @surgexlabs-aap-dev List job templates
   @surgexlabs-aap-dev Launch "Deploy to Dev" job
   ```

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to MCP server"

**Check**:
```bash
# Test server is running
curl http://your-server:8000/health

# Test network connectivity
ping your-server-hostname

# Test firewall
telnet your-server 8000
```

**Solution**: Ensure server is running and accessible.

### Issue: "401 Unauthorized"

**Check**:
- API key is correct in `X-API-Key` header
- API key hasn't expired
- Token is correctly stored in VS Code secrets

**Solution**: Regenerate API key or check token.

### Issue: "403 Forbidden - Invalid AAP credentials"

**Check**:
- AAP token is valid (test with curl):
  ```bash
  curl https://aap.devfg.surgexlabs.com/api/v2/me/ \
    -H "Authorization: Bearer YOUR_TOKEN"
  ```

**Solution**: Get new AAP token from AAP UI.

### Issue: "SSL Certificate Error"

**Temporary Fix** (testing only):
```json
{"headers": {"X-AWX-Verify-SSL": "false"}}
```

**Proper Fix**:
1. Install surgexlabs CA certificate on your workstation
2. Configure VS Code to trust it
3. Use `X-AWX-Verify-SSL: "true"`

### Issue: "Connection timeout"

**Check**:
- VPN connection (if required)
- Corporate proxy settings
- Firewall rules

**Solution**: Configure proxy in VS Code settings.

---

## 📚 Additional Configuration Options

### Custom Headers

Add custom headers for tracking:

```json
{
  "headers": {
    "X-API-Key": "your-key",
    "X-User-Email": "your.name@company.com",
    "X-Department": "DevOps",
    "X-Cost-Center": "CC-12345"
  }
}
```

### Request Timeout

Set longer timeout for slow networks:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-server:8000/mcp",
      "timeout": 60000  // 60 seconds (milliseconds)
    }
  }
}
```

### Retry Configuration

Configure retry behavior:

```json
{
  "mcpServers": {
    "awx-remote": {
      "url": "http://your-server:8000/mcp",
      "retry": {
        "maxAttempts": 3,
        "backoff": "exponential"
      }
    }
  }
}
```

---

## 🎯 Quick Reference

### Minimal Configuration

```json
{
  "mcpServers": {
    "awx": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-API-Key": "your-mcp-key",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com"
      },
      "secrets": {
        "X-AWX-Token": "your-aap-token"
      }
    }
  }
}
```

### Production Configuration

```json
{
  "mcpServers": {
    "aap-prod": {
      "url": "https://awx-mcp.company.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "awx_mcp_prod_key",
        "X-AWX-Base-URL": "https://aap.company.com",
        "X-AWX-Platform": "aap",
        "X-AWX-Verify-SSL": "true"
      },
      "secrets": {
        "X-AWX-Token": "prod-token"
      }
    }
  }
}
```

---

## ✅ Verification Checklist

Before using in production:

- [ ] Remote MCP server is running and accessible
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] API key created and stored in VS Code
- [ ] AAP token created and stored in VS Code secrets
- [ ] AAP base URL configured correctly (no `/api/v2/`)
- [ ] Platform type set (`aap`, `awx`, or `tower`)
- [ ] SSL verification enabled (`X-AWX-Verify-SSL: "true"`)
- [ ] HTTPS used for remote server (not HTTP)
- [ ] Copilot Chat can list job templates
- [ ] Can successfully launch a test job
- [ ] Credentials not committed to Git

---

## 🎓 Getting Both Keys - Complete Walkthrough

### Scenario: Setting Up for surgexlabs AAP Development Environment

Here's the **complete step-by-step flow** to get both keys and configure VS Code:

#### **Step 1: Get Key #1 (AAP Token) - Your Personal Credentials**

1. **Open browser** → Navigate to https://aap.devfg.surgexlabs.com

2. **Log in** with your LDAP/SSO credentials

3. **Click**: Users (left sidebar) → Your username → Tokens tab

4. **Click "Add"** or "Create Token" button

5. **Copy the token** (looks like: `abc123xyz456...`)

6. **Save to environment variable** (Windows PowerShell):
   ```powershell
   # Set for current session
   $env:AAP_TOKEN = "abc123xyz456..."
   
   # Set permanently
   [System.Environment]::SetEnvironmentVariable('AAP_TOKEN', 'abc123xyz456...', 'User')
   
   # Verify it's saved
   echo $env:AAP_TOKEN
   ```

   **Or** (Linux/macOS):
   ```bash
   # Set for current session
   export AAP_TOKEN="abc123xyz456..."
   
   # Set permanently (add to ~/.bashrc or ~/.zshrc)
   echo 'export AAP_TOKEN="abc123xyz456..."' >> ~/.bashrc
   source ~/.bashrc
   
   # Verify
   echo $AAP_TOKEN
   ```

✅ **You now have Key #1 saved in environment variable `AAP_TOKEN`**

---

#### **Step 2: Get Key #2 (MCP API Key) - Server Access Token**

**Contact your MCP server administrator** and request an API key. They will run:

```bash
# Admin creates your API key
curl -X POST https://awx-mcp-server.surgexlabs.com/api/keys \
  -H "Authorization: Bearer admin-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john-doe-vscode",
    "tenant_id": "john.doe@surgexlabs.com",
    "expires_days": 90
  }'
```

**Admin sends you the API key**: `awx_mcp_def789ghi012...`

**Save to environment variable** (Windows PowerShell):
```powershell
# Set for current session
$env:MCP_API_KEY = "awx_mcp_def789ghi012..."

# Set permanently
[System.Environment]::SetEnvironmentVariable('MCP_API_KEY', 'awx_mcp_def789ghi012...', 'User')

# Verify
echo $env:MCP_API_KEY
```

**Or** (Linux/macOS):
```bash
# Set for current session
export MCP_API_KEY="awx_mcp_def789ghi012..."

# Set permanently
echo 'export MCP_API_KEY="awx_mcp_def789ghi012..."' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $MCP_API_KEY
```

✅ **You now have Key #2 saved in environment variable `MCP_API_KEY`**

---

#### **Step 3: Configure VS Code with Both Keys**

**Open VS Code** → `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

**Add this configuration**:

```json
{
  "github.copilot.chat.mcpServers": {
    "surgexlabs-aap-dev": {
      "url": "https://awx-mcp-server.surgexlabs.com/mcp",
      "transport": "http",
      "headers": {
        "X-API-Key": "${env:MCP_API_KEY}",
        "X-AWX-Base-URL": "https://aap.devfg.surgexlabs.com",
        "X-AWX-Platform": "aap",
        "X-AWX-Verify-SSL": "true"
      },
      "env": {
        "AAP_TOKEN": "${env:AAP_TOKEN}"
      }
    }
  }
}
```

**What this does**:
- `${env:MCP_API_KEY}` → Reads Key #2 from your environment variable
- `${env:AAP_TOKEN}` → Reads Key #1 from your environment variable
- Both keys are loaded automatically when VS Code starts

---

#### **Step 4: Reload VS Code**

```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

#### **Step 5: Test the Connection**

Open **GitHub Copilot Chat** and try:

```
@surgexlabs-aap-dev List all job templates

@surgexlabs-aap-dev Show AAP version

@surgexlabs-aap-dev Launch "Deploy to Dev" job
```

✅ **If you see results, both keys are working!**

---

### Alternative: Store Keys Directly in settings.json

If you prefer NOT to use environment variables:

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

**⚠️ Warning**: 
- **DO NOT commit this file to Git** if it contains actual keys!
- Use workspace settings, not user settings
- Add `.vscode/settings.json` to `.gitignore`

---

### Summary Table

| Key | Environment Variable | VS Code Field | Example Value |
|-----|---------------------|---------------|---------------|
| **Key #1** (AAP Token) | `AAP_TOKEN` | `env.AAP_TOKEN` or `secrets.X-AWX-Token` | `abc123xyz456...` |
| **Key #2** (MCP API Key) | `MCP_API_KEY` | `headers.X-API-Key` | `awx_mcp_def789ghi012...` |

---

## 📖 Related Documentation

- **[Remote Deployment Guide](REMOTE_DEPLOYMENT.md)** - How to deploy the remote server
- **[AAP Support](../AAP_SUPPORT.md)** - AAP-specific configuration
- **[OS Compatibility](../OS_COMPATIBILITY.md)** - Client OS requirements
- **[Install from Source](../INSTALL_FROM_SOURCE.md)** - Customize the server

---

**✨ You're now ready to use the remote AWX MCP Server with VS Code Copilot Chat!**

**Test it**:
```
@awx-remote List all job templates in AAP
@awx-remote Launch "Deploy Application" job with environment=dev
@awx-remote Show recent jobs
```
