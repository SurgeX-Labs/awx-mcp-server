# AWX MCP Extension for VS Code

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://marketplace.visualstudio.com/items?itemName=awx-mcp-team.awx-mcp-extension)
[![VS Code](https://img.shields.io/badge/VS%20Code-1.85.0+-007ACC.svg)](https://code.visualstudio.com/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

Integrate AWX/Ansible Tower with GitHub Copilot through the Model Context Protocol (MCP). Manage your infrastructure automation directly from VS Code using natural language.

## 🎯 Two Ways to Use

### Option 1: Pure MCP (Industry Standard) ⭐ RECOMMENDED

Use AWX MCP Server directly with GitHub Copilot Chat - **no extension needed**:

```bash
# Install server
pip install awx-mcp-server

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

**Benefits:**
- ✅ Standard MCP implementation (like Postman MCP)
- ✅ Works with Copilot, Claude, Cursor, any MCP client
- ✅ Simple configuration, portable
- ✅ Independent server updates

📖 **[Complete MCP Setup Guide →](MCP_COPILOT_SETUP.md)**

### Option 2: Extension + MCP (Rich UI)

Install this extension for enhanced UI features:

**Features:**
- 🤖 `@awx` chat participant with intelligent tool invocation
- 📊 Sidebar views (instances, jobs, metrics, logs)
- 🌲 Tree view of AWX resources
- 🎨 Configuration webview UI
- ⚡ Automatic MCP setup

**Install:** Search "AWX MCP Extension" in VS Code Extensions

📖 **[Architecture Comparison: MCP vs Extension →](ARCHITECTURE_COMPARISON.md)**

## ✨ Features

- 🤖 **GitHub Copilot Chat Participant**: Use `@awx` to intelligently interact with AWX (auto-invokes tools!)
- 🧠 **Smart Tool Invocation**: Copilot automatically selects and calls AWX tools based on your questions
- 🚀 **One-Click Setup**: Automatic installation and configuration of the MCP server
- 📊 **Job Management**: Launch, monitor, and troubleshoot Ansible jobs
- 🔐 **Secure Authentication**: Credential storage using OS keyring
- 🌍 **Multi-Environment**: Support for multiple AWX/Tower instances
- 📈 **Real-time Monitoring**: View server metrics and logs in the sidebar
- ⚡ **Auto-start**: Server starts automatically when VS Code opens

## 🎯 Two Ways to Use AWX with Copilot

### Method 1: Chat Participant (Recommended) ⭐

Use the `@awx` chat participant for intelligent, automatic tool invocation:

```
@awx List my job templates
@awx Show me recent jobs
@awx What inventories do I have?
```

**How it works:**
- Extension analyzes your question
- Automatically selects appropriate AWX tools
- Invokes tools and formats results
- No manual tool selection needed!

[📖 Full Copilot Chat Guide](./COPILOT_CHAT_GUIDE.md)

### Method 2: Traditional MCP Tools

Use the "Add context" button in Copilot Chat:
1. Click the attachment icon in Copilot Chat
2. Select "Tool" → Choose AWX tools
3. Ask questions about the tool results

## 📋 Requirements

- **VS Code** 1.85.0 or higher
- **Python** 3.10 or higher
- **AWX or Ansible Tower** instance with API access
- **GitHub Copilot** extension (for AI integration)

## 🏗️ Architecture

This extension uses **Python MCP Server via PyPI**:
- ✅ Server: `pip install awx-mcp-server` from PyPI
- ✅ Package size: 11.7 MB (not bundled, smaller download)
- ✅ Independent updates without republishing extension
- ✅ Full AWX API support through official Python SDK

**How it works:**
1. Extension auto-detects Python on your system
2. Installs `awx-mcp-server` via pip (one-time, 15-30 sec)
3. Spawns server: `python -m awx_mcp_server`
4. Communicates via JSON-RPC over STDIO

📖 See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical information.

## 🚀 Quick Start

1. **Install the Extension** from the VS Code Marketplace
2. **Python Setup** (one-time):
   - The extension will automatically install `awx-mcp-server` from PyPI
   - Or manually: `pip install awx-mcp-server`
3. **Configure AWX Connection**:
   - Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
   - Run `AWX MCP: Configure AWX Environment`
   - Enter your AWX URL, username, and token/password
4. **Start Using with Copilot**:
   ```
   Open GitHub Copilot Chat and try:
   "@awx list my job templates"
   "@awx show me recent jobs"  
   "@awx what inventories do I have?"
   ```

The extension will automatically:
- Detect your Python environment
- Install `awx-mcp-server` from PyPI if not present
- Register as `@awx` chat participant
- Configure MCP tools for Copilot

## 💡 Usage Examples

### 📋 Discovery & Listing
```
@awx list all job templates
@awx show me inventories  
@awx what projects are available?
@awx list environments
```

### 🚀 Job Management
```
@awx launch template "Deploy Production"
@awx show recent jobs
@awx show failed jobs
@awx show running jobs
@awx cancel job 123
```

### 📊 Job Monitoring & Status
```
@awx job 123
@awx status of job 456
@awx get output for job 123
@awx get events for job 789
```

### 🔍 Failure Diagnosis
```
@awx why did job 123 fail?
@awx job 456 error
@awx show failed jobs
@awx get logs for job 123
```

### 🔧 Project Management
```
@awx update project "My App"
@awx sync project "Infrastructure"
@awx list projects
```

### 🌍 Environment Management
```
@awx current environment
@awx test connection
@awx list environments
```

**See [FEATURE_COVERAGE.md](./FEATURE_COVERAGE.md) for complete capability reference (16 tools, 100% AWX API coverage)**

## ⚙️ Configuration

Access settings via `File > Preferences > Settings` and search for "AWX MCP":

| Setting | Description | Default |
|---------|-------------|---------|
| `awx-mcp.pythonPath` | Path to Python interpreter | Auto-detect |
| `awx-mcp.autoStart` | Auto-start MCP server | `true` |
| `awx-mcp.logLevel` | Logging verbosity | `info` |
| `awx-mcp.enableMonitoring` | Enable metrics collection | `true` |
| `awx-mcp.serverTimeout` | Server operation timeout | `30` seconds |

## 📚 Commands

Access all commands via Command Palette (`Ctrl+Shift+P`):

- `AWX MCP: Start AWX MCP Server` - Start the MCP server
- `AWX MCP: Stop AWX MCP Server` - Stop the MCP server  
- `AWX MCP: Restart AWX MCP Server` - Restart the server
- `AWX MCP: Show AWX MCP Server Status` - Display current status
- `AWX MCP: Configure AWX Environment` - Setup AWX connection
- `AWX MCP: View AWX MCP Logs` - Open log output
- `AWX MCP: View AWX MCP Metrics` - Display metrics

## 🎛️ Sidebar Views

The extension adds an **AWX MCP** activity bar with three panels:

### AWX Environments
- Manage multiple AWX instances
- Switch between environments  
- View connection status

### Metrics
- Real-time server status
- Request/error counts
- Server uptime
- Performance stats

### Logs
- Recent server activity
- Error tracking
- Debug information

## 🔧 Troubleshooting

### Server Won't Start

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.10 or higher
   ```

2. **View logs** via Command Palette → `AWX MCP: View AWX MCP Logs`

3. **Manual installation** (if auto-install fails):
   ```bash
   pip install awx-mcp-server
   ```

### Copilot Can't Connect

1. Verify server is running (check status bar shows "AWX MCP: Running")
2. Restart VS Code
3. Ensure GitHub Copilot extension is active
4. Try using `@awx-local` prefix in Copilot Chat

### Authentication Errors

1. Run `AWX MCP: Configure AWX Environment` to update credentials
2. Verify AWX URL is accessible
3. Check your AWX token/password is valid

### Python Environment Issues

The extension auto-detects Python from:
- VS Code Python extension settings
- System PATH
- Virtual environments

You can manually specify: `Settings → AWX MCP → Python Path`

## 🏗️ Building from Source

See [BUILD.md](BUILD.md) for detailed build instructions.

```bash
# Clone repository
git clone https://github.com/your-org/awx-mcp-python
cd awx-mcp-python/vscode-extension

# Install dependencies
npm install

# Build extension
.\build.ps1
```

## 📖 Documentation

### Getting Started
- **[MCP Copilot Setup Guide](MCP_COPILOT_SETUP.md)** - Industry standard MCP configuration (no extension needed) ⭐
- **[Configuration Examples](mcp-config-examples.json)** - Copy-paste MCP configurations
- **[Installation Guide](INSTALLATION_GUIDE.md)** - Extension installation and troubleshooting

### Architecture & Design
- **[Architecture Comparison](ARCHITECTURE_COMPARISON.md)** - MCP vs Extension patterns, industry standards ⭐
- **[Architecture Overview](ARCHITECTURE.md)** - Detailed technical architecture (Python/PyPI)
- **[Production Ready Checklist](PRODUCTION_READY.md)** - Deployment readiness

### Testing & Development
- **[Test Guide](TEST_GUIDE.md)** - Manual and automated testing procedures
- **[Final Summary](FINAL_SUMMARY.md)** - Package optimization and current status
- **[Build Instructions](BUILD.md)** - Building from source

## 🏗️ Architecture Patterns

This project demonstrates **two MCP integration approaches**:

### Industry Standard (Pure MCP) ⭐
```
GitHub Copilot Chat
    ↓ (MCP Protocol)
awx-mcp-server (Python)
    ↓ (REST API)
AWX/Ansible Tower
```

**Configuration:** `.vscode/settings.json` or user settings  
**Guide:** [MCP_COPILOT_SETUP.md](MCP_COPILOT_SETUP.md)  
**Pattern:** Same as Postman MCP, Claude MCP, industry standard  
**Works with:** GitHub Copilot, Claude, Cursor, any MCP client  

### Extension Enhanced (Rich UI)
```
VS Code Extension (TypeScript)
    ├─ Spawns → awx-mcp-server (Python)
    ├─ Provides → Sidebar views, tree providers
    └─ Manages → Server lifecycle, configuration UI
```

**Installation:** VS Code Marketplace extension  
**Guide:** [Installation Guide](INSTALLATION_GUIDE.md)  
**Benefits:** Automatic setup, rich UI, one-click experience  
**Comparison:** [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md)  

**Choose based on needs:**
- **MCP Only:** Standard, portable, simple, works everywhere
- **Extension:** Rich UI, automatic setup, AWX-specific features

## 🤝 Contributing

Contributions are welcome! Please see our contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/SurgeX-Labs/awx-mcp-server/issues)
- **MCP Server (PyPI):** `pip install awx-mcp-server`
- **Extension (Marketplace):** `surgexlabs.awx-mcp-extension`
- **Documentation:** See links above

## 🔗 Quick Links

- **Marketplace:** [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=surgexlabs.awx-mcp-extension)
- **GitHub:** [Source Repository](https://github.com/SurgeX-Labs/awx-mcp-server)
- **MCP Spec:** [Model Context Protocol](https://modelcontextprotocol.io)
- **AWX Docs:** [Ansible Automation Platform](https://docs.ansible.com/automation-controller/)

---

**Version:** 1.0.0  
**Architecture:** Python MCP Server (PyPI) + Optional VS Code Extension  
**Industry Standard:** ✅ Compatible with Postman MCP pattern  
**Works With:** GitHub Copilot, Claude, Cursor, any MCP client  

**Enjoy automating with AWX and GitHub Copilot! 🚀**
