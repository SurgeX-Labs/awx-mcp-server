# Operating System Compatibility Guide

## ✅ Supported Operating Systems

The **AWX MCP Server** is a cross-platform Python package that works on all major operating systems:

| Operating System | Status | Python Version | Notes |
|-----------------|--------|----------------|-------|
| **Windows 10/11** | ✅ Fully Supported | 3.10+ | Primary test platform |
| **macOS 12+** | ✅ Fully Supported | 3.10+ | Intel & Apple Silicon |
| **Linux (Ubuntu/Debian)** | ✅ Fully Supported | 3.10+ | Tested on Ubuntu 20.04+ |
| **Linux (RHEL/CentOS/Fedora)** | ✅ Fully Supported | 3.10+ | Enterprise distributions |
| **Linux (Other)** | ✅ Likely Compatible | 3.10+ | Any distribution with Python 3.10+ |

## 📦 Installation Instructions by OS

### Windows

```powershell
# Install Python 3.10+ from python.org or Microsoft Store
# Verify installation
python --version

# Install AWX MCP Server
pip install awx-mcp-server

# Test installation
python -m awx_mcp_server --version
```

**VS Code Configuration** (Windows):
```json
{
  "mcpServers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://your-awx-server.com"
      }
    }
  }
}
```

### macOS

```bash
# Install Python 3.10+ via Homebrew
brew install python@3.12

# Or use system Python (macOS 12.3+ includes Python 3.8+)
python3 --version

# Install AWX MCP Server
pip3 install awx-mcp-server

# Test installation
python3 -m awx_mcp_server --version
```

**VS Code Configuration** (macOS):
```json
{
  "mcpServers": {
    "awx": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://your-awx-server.com"
      }
    }
  }
}
```

**Finding Python Path on macOS**:
```bash
which python3
# Common locations:
# /usr/local/bin/python3 (Homebrew)
# /opt/homebrew/bin/python3 (Apple Silicon Homebrew)
# /Library/Frameworks/Python.framework/Versions/3.X/bin/python3 (python.org)
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version

# Install AWX MCP Server
pip3 install awx-mcp-server

# Test installation
python3 -m awx_mcp_server --version
```

**VS Code Configuration** (Linux):
```json
{
  "mcpServers": {
    "awx": {
      "command": "/usr/bin/python3",
      "args": ["-m", "awx_mcp_server"],
      "env": {
        "AWX_BASE_URL": "https://your-awx-server.com"
      }
    }
  }
}
```

**Finding Python Path on Linux**:
```bash
which python3
# Common locations:
# /usr/bin/python3 (System Python)
# /usr/local/bin/python3 (Custom installation)
# ~/.local/bin/python3 (User installation)
```

### Linux (RHEL/CentOS/Fedora)

```bash
# RHEL 8/9, CentOS 8/9, Fedora
sudo dnf install python3 python3-pip

# RHEL 7, CentOS 7
sudo yum install python3 python3-pip

# Verify installation
python3 --version

# Install AWX MCP Server
pip3 install awx-mcp-server

# Test installation
python3 -m awx_mcp_server --version
```

## 🔐 Credential Storage by OS

The AWX MCP Server uses the `keyring` library for secure credential storage. Each OS has a different backend:

| OS | Backend | Location | Security |
|----|---------|----------|----------|
| **Windows** | Windows Credential Manager | `Control Panel → Credential Manager` | Encrypted by Windows |
| **macOS** | macOS Keychain | Keychain Access app | Encrypted by macOS |
| **Linux (GNOME)** | GNOME Keyring / Secret Service | `~/.local/share/keyrings/` | Encrypted with login password |
| **Linux (KDE)** | KWallet | KWallet Manager | Encrypted with KWallet password |
| **Linux (headless)** | Encrypted file backend | `~/.local/share/python_keyring/` | Encrypted with master password |

### Setting Up Keyring on Linux

**GNOME (Ubuntu default)**:
```bash
# Install GNOME Keyring (usually pre-installed)
sudo apt install gnome-keyring

# The keyring daemon should start automatically with your session
```

**Headless Linux Servers**:
```bash
# For servers without GUI, keyring will use encrypted file backend
# You'll be prompted to set a master password on first use
python3 -m keyring --help
```

**Alternative for Headless**: Use environment variables instead:
```bash
export AWX_TOKEN="your-token-here"
python -m awx_mcp_server
```

## 🐳 Docker (Platform-Independent)

For consistent behavior across all platforms, use Docker:

```bash
# Works on Windows, macOS, and Linux
docker run -it --rm \
  -e AWX_BASE_URL=https://your-awx.com \
  -e AWX_TOKEN=your-token \
  -p 8000:8000 \
  surgexlabs/awx-mcp-server:latest
```

## 📋 Platform-Specific Notes

### Windows

**Path Separators**:
- Use forward slashes `/` or escaped backslashes `\\` in JSON configuration
- ✅ Good: `"C:/Python312/python.exe"` or `"C:\\Python312\\python.exe"`
- ❌ Bad: `"C:\Python312\python.exe"` (JSON parsing error)

**PowerShell vs CMD**:
- Use PowerShell (recommended) for better UTF-8 support
- Some commands differ: `where` vs `which`, `$env:VAR` vs `%VAR%`

**Credential Manager Access**:
```powershell
# View stored credentials
cmdkey /list
# Credentials stored as: "awx_mcp_server:{env_name}"
```

### macOS

**Apple Silicon (M1/M2/M3)**:
- Fully supported - all Python packages have ARM64 builds
- Use Homebrew ARM64 version: `/opt/homebrew/bin/python3`

**Keychain Access**:
- Credentials stored in "Login" keychain
- Search for "awx_mcp_server" to find stored credentials
- May prompt for keychain password on first access

**Permissions**:
- VS Code may need "Full Disk Access" permission for keychain access
- `System Settings → Privacy & Security → Full Disk Access`

### Linux

**Distribution Differences**:
- Package managers: `apt` (Debian/Ubuntu), `dnf` (Fedora/RHEL 8+), `yum` (RHEL 7)
- Python command: usually `python3` (not `python`)
- pip location: `/usr/bin/pip3` or `python3 -m pip`

**Headless Servers**:
- Use environment variables instead of keyring
- Or configure encrypted file backend with master password
- Consider using remote server mode with centralized credentials

**SELinux (RHEL/CentOS)**:
- May need to allow network connections: `setsebool -P httpd_can_network_connect 1`
- Or run in permissive mode for testing: `sudo setenforce 0`

## 🧪 Testing OS Compatibility

### Verify Installation

**All Platforms**:
```bash
# Check Python version (should be 3.10+)
python --version    # or python3 --version

# Check pip installation
pip --version       # or pip3 --version

# Install and test
pip install awx-mcp-server
python -m awx_mcp_server --version
```

### Test Remote Server Mode

**Start HTTP Server**:
```bash
# Works on all platforms
python -m awx_mcp_server.cli start --host localhost --port 8000
```

**Test from Browser**:
```
http://localhost:8000/health
http://localhost:8000/docs
```

**Test from Command Line**:
```bash
# macOS/Linux
curl http://localhost:8000/health

# Windows (PowerShell)
Invoke-WebRequest http://localhost:8000/health
```

### Test VS Code Integration

1. **Configure VS Code** (see platform-specific examples above)
2. **Open VS Code Settings**: `Ctrl+,` (Windows/Linux) or `Cmd+,` (macOS)
3. **Search for**: "chat.mcp"
4. **Edit settings.json**: Add MCP server configuration
5. **Restart VS Code**
6. **Test in Copilot Chat**: Ask "@workspace What AWX environments are configured?"

## 🔧 Troubleshooting by OS

### Windows

**Issue**: `python: command not found`
```powershell
# Add Python to PATH
# Install from python.org with "Add to PATH" checked
# Or use Python from Microsoft Store (auto-adds to PATH)
```

**Issue**: SSL verification errors
```powershell
# Update certificates
pip install --upgrade certifi
```

**Issue**: Permission errors on `pip install`
```powershell
# Install for current user only
pip install --user awx-mcp-server
```

### macOS

**Issue**: `certificate verify failed`
```bash
# Install certificates (for python.org installations)
/Applications/Python\ 3.X/Install\ Certificates.command

# Or upgrade certifi
pip3 install --upgrade certifi
```

**Issue**: `command not found: python`
```bash
# Use python3 instead
python3 --version

# Or create alias in ~/.zshrc or ~/.bash_profile
echo 'alias python=python3' >> ~/.zshrc
```

**Issue**: Keychain access denied
```bash
# Grant VS Code full disk access
# System Settings → Privacy & Security → Full Disk Access → Add VS Code
```

### Linux

**Issue**: `ModuleNotFoundError` after install
```bash
# Ensure proper Python path
python3 -m site  # Check installation paths

# Install in user directory
pip3 install --user awx-mcp-server

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install awx-mcp-server
```

**Issue**: Keyring backend not available
```bash
# Install keyring backend
sudo apt install gnome-keyring  # Debian/Ubuntu
sudo dnf install gnome-keyring  # Fedora/RHEL

# Or use environment variables
export AWX_TOKEN="your-token"
```

**Issue**: Permission denied on port 8000
```bash
# Use port >1024 (no root needed)
python3 -m awx_mcp_server.cli start --port 8080

# Or use sudo for port <1024
sudo python3 -m awx_mcp_server.cli start --port 80
```

## 📊 Platform Comparison

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Python Installation | ✅ python.org / Microsoft Store | ✅ Homebrew / python.org | ✅ Package manager |
| Credential Storage | ✅ Credential Manager | ✅ Keychain | ✅ GNOME Keyring / KWallet |
| VS Code Integration | ✅ Full support | ✅ Full support | ✅ Full support |
| Remote Server Mode | ✅ Full support | ✅ Full support | ✅ Full support |
| Docker Support | ✅ Docker Desktop | ✅ Docker Desktop | ✅ Native Docker |
| Performance | Good | Excellent | Excellent |
| Recommended for | Development/Enterprise | Development | Production/Containers |

## 🎯 Recommendations

### For Development
- **Windows**: Good for development if using Windows as primary OS
- **macOS**: Excellent for development, best performance on Apple Silicon
- **Linux**: Excellent for development, closest to production environment

### For Production (Remote Server Mode)
- **Linux**: Best choice for production (Docker/Kubernetes/VM)
- **Docker**: Recommended for consistent deployment across all platforms
- **Windows Server**: Supported but less common in cloud environments

### For Team Use
- Deploy remote server on Linux/Docker (enterprise mode)
- Clients use any OS (Windows/macOS/Linux) with VS Code
- Centralized credential management on server

## 📚 Additional Resources

- **Python Downloads**: https://www.python.org/downloads/
- **Homebrew (macOS)**: https://brew.sh/
- **Docker**: https://www.docker.com/get-started
- **VS Code**: https://code.visualstudio.com/download
- **Keyring Documentation**: https://github.com/jaraco/keyring

## ✅ Summary

**Yes, VS Code installation works on all operating systems!**

The AWX MCP Server is fully cross-platform because:
1. ✅ Pure Python package (no platform-specific code)
2. ✅ All dependencies support Windows/macOS/Linux
3. ✅ Automatic credential storage backend selection per OS
4. ✅ VS Code runs on all platforms with identical MCP support
5. ✅ Same API and functionality regardless of OS

**Installation is equally easy on all platforms:**
```bash
pip install awx-mcp-server  # Works everywhere!
```
