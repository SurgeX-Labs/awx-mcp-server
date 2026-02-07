# AWX MCP Extension for VS Code

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://marketplace.visualstudio.com/items?itemName=awx-mcp-team.awx-mcp-extension)
[![VS Code](https://img.shields.io/badge/VS%20Code-1.85.0+-007ACC.svg)](https://code.visualstudio.com/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

Integrate AWX/Ansible Tower with GitHub Copilot through the Model Context Protocol (MCP). Manage your infrastructure automation directly from VS Code using natural language.

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

## 🚀 Quick Start

1. **Install the Extension** from the VS Code Marketplace
2. **Configure AWX Connection**:
   - Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
   - Run `AWX MCP: Configure AWX Environment`
   - Enter your AWX URL, username, and token/password
3. **Start Using with Copilot**:
   ```
   Open GitHub Copilot Chat and try:
   "@awx list my job templates"
   "@awx show me recent jobs"  
   "@awx what inventories do I have?"
   ```

The extension will automatically:
- Install the required MCP server on first use
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

- [Getting Started Guide](../docs/GETTING_STARTED.md)
- [Extension Installation](../docs/EXTENSION_INSTALL_REBUILD.md)
- [Troubleshooting](../docs/EXTENSION_TROUBLESHOOTING.md)
- [FAQ](../docs/FAQ.md)

## 🤝 Contributing

Contributions are welcome! Please see our contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- [Marketplace](https://marketplace.visualstudio.com/items?itemName=awx-mcp-team.awx-mcp-extension)
- [GitHub Repository](https://github.com/your-org/awx-mcp-python)
- [Report Issues](https://github.com/your-org/awx-mcp-python/issues)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

**Enjoy automating with AWX and GitHub Copilot! 🚀**
