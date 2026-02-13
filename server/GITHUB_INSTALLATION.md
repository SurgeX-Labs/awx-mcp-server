# Installing AWX MCP Server from GitHub

## 🎯 Overview

Users can install AWX MCP Server directly from GitHub without needing PyPI. This is useful for:
- Testing development versions
- Contributing to the project
- Using the latest unreleased features

---

## 📦 Publishing to GitHub

### 1. Create GitHub Repository

```bash
# Initialize git (if not already)
cd awx-mcp-python/server
git init

# Create repository on GitHub: https://github.com/new
# Repository name: awx-mcp-server
# Description: "MCP server for AWX/Ansible Tower automation"
# Public or Private: Public (recommended for MCP)

# Add remote
git remote add origin https://github.com/YOUR-USERNAME/awx-mcp-server.git

# Initial commit
git add .
git commit -m "Initial commit: AWX MCP Server (Industry Standard)"
git branch -M main
git push -u origin main
```

### 2. Add GitHub Topics (Recommended)

Go to your repository settings and add topics:
- `mcp`
- `model-context-protocol`
- `awx`
- `ansible-tower`
- `github-copilot`
- `claude`
- `cursor`

This helps users discover your MCP server.

### 3. Create Release (Optional)

```bash
# Tag a version
git tag -a v1.0.0 -m "Release v1.0.0: Industry Standard MCP"
git push origin v1.0.0
```

Create release on GitHub: https://github.com/YOUR-USERNAME/awx-mcp-server/releases/new

---

## 🚀 Installation Methods

### Method 1: Install from GitHub (Recommended)

Users can install directly from GitHub using pip:

```bash
# Install from main branch
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git

# Install specific version/tag
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git@v1.0.0

# Install from specific branch
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git@develop
```

### Method 2: Clone and Install (Development)

For contributors or testing:

```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server

# Install in editable mode
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

---

## ⚙️ VS Code MCP Configuration

### Option 1: Install from GitHub (Recommended)

**Step 1: Install the package**
```bash
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git
```

**Step 2: Configure in VS Code**

Open User Settings (JSON): `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

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

**Step 3: Store secret**
```
Ctrl+Shift+P → "GitHub: Store Secret"
Name: awx-token
Value: your-awx-token
```

**Step 4: Reload**
```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

### Option 2: Run from Cloned Repository

If you've cloned the repository for development:

**Step 1: Clone**
```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server
pip install -e .
```

**Step 2: Configure in VS Code**

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": [
        "-m",
        "awx_mcp_server"
      ],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

---

### Option 3: Direct Python Execution (Development)

For testing without installation:

**Step 1: Clone and setup**
```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server
pip install -r requirements.txt
```

**Step 2: Configure in VS Code**

```json
{
  "github.copilot.chat.mcpServers": {
    "awx": {
      "command": "python",
      "args": [
        "C:/path/to/awx-mcp-server/src/awx_mcp_server/__main__.py"
      ],
      "env": {
        "AWX_BASE_URL": "https://awx.example.com",
        "AWX_TOKEN": "${secret:awx-token}",
        "PYTHONPATH": "C:/path/to/awx-mcp-server/src"
      }
    }
  }
}
```

---

## 📝 README Installation Instructions

Update your GitHub README.md with these installation options:

````markdown
## Installation

### From GitHub (Latest)

```bash
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git
```

### From PyPI (Stable)

```bash
pip install awx-mcp-server
```

### For Development

```bash
git clone https://github.com/YOUR-USERNAME/awx-mcp-server.git
cd awx-mcp-server
pip install -e .
```

## Configuration

See [QUICK_START.md](QUICK_START.md) for complete MCP client configuration.
````

---

## 🔧 GitHub-Specific Features

### 1. GitHub Actions (CI/CD)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: pip install pytest
      - run: pytest tests/
```

### 2. Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md` for user bug reports.

### 3. Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md` for contributors.

---

## 🌐 Other MCP Clients (Claude, Cursor)

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
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

### Cursor

Edit `~/.cursor/mcp_settings.json`:

```json
{
  "mcpServers": {
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

---

## 🔄 Upgrading

### From GitHub

```bash
# Upgrade to latest
pip install --upgrade git+https://github.com/YOUR-USERNAME/awx-mcp-server.git

# Upgrade to specific version
pip install --upgrade git+https://github.com/YOUR-USERNAME/awx-mcp-server.git@v1.1.0
```

### Reload VS Code

After upgrading, reload VS Code:
```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

## 🐛 Troubleshooting

### "Module not found"

```bash
# Check installation
pip show awx-mcp-server

# Reinstall
pip uninstall awx-mcp-server
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git
```

### "Permission denied"

```bash
# Use --user flag
pip install --user git+https://github.com/YOUR-USERNAME/awx-mcp-server.git
```

### Check Python environment

```bash
# Verify Python version
python --version  # Should be 3.10+

# Verify pip installation path
pip show awx-mcp-server | grep Location
```

---

## 📊 GitHub Repository Structure

```
awx-mcp-server/
├── .github/
│   ├── workflows/
│   │   └── test.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── src/
│   └── awx_mcp_server/
│       ├── __init__.py
│       ├── __main__.py
│       └── ...
├── tests/
├── deployment/
├── manifest.json
├── QUICK_START.md
├── GITHUB_INSTALLATION.md
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

---

## 🎯 Quick Start for Users

**One-line installation:**
```bash
pip install git+https://github.com/YOUR-USERNAME/awx-mcp-server.git && echo '{"github.copilot.chat.mcpServers":{"awx":{"command":"python","args":["-m","awx_mcp_server"],"env":{"AWX_BASE_URL":"https://awx.example.com","AWX_TOKEN":"${secret:awx-token}"}}}}' > mcp-config.json
```

Then:
1. Copy `mcp-config.json` contents to VS Code User Settings
2. Store AWX token as secret
3. Reload VS Code
4. Test: `@workspace list AWX job templates`

---

## 📚 Additional Resources

- **Main Docs:** [QUICK_START.md](QUICK_START.md)
- **MCP Protocol:** https://modelcontextprotocol.io
- **VS Code MCP:** https://code.visualstudio.com/docs/copilot/copilot-extensibility-overview
- **GitHub Topics:** Add `mcp` topic to your repo for discoverability

---

**GitHub Repository:** https://github.com/YOUR-USERNAME/awx-mcp-server  
**Issues:** https://github.com/YOUR-USERNAME/awx-mcp-server/issues  
**Contributions:** PRs welcome!
