# Publishing AWX MCP Server to GitHub and MCP Registry

**Complete guide for publishing your MCP server and making it discoverable**

This guide shows you how to publish your AWX MCP server to GitHub, register it with the official MCP Registry, and automate the process with GitHub Actions.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Part 1: Publish to GitHub](#part-1-publish-to-github)
3. [Part 2: Register with MCP Registry](#part-2-register-with-mcp-registry)
4. [Part 3: Automate with GitHub Actions](#part-3-automate-with-github-actions)
5. [Part 4: Verify Publication](#part-4-verify-publication)
6. [Part 5: Update and Maintain](#part-5-update-and-maintain)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- ✅ Functional AWX MCP server (tested locally)
- ✅ GitHub account
- ✅ Git installed locally
- ✅ Python 3.10+
- ✅ All tests passing (`pytest tests/ -v`)

### Optional (for PyPI)

- PyPI account (if publishing to PyPI)
- `twine` installed (`pip install twine`)

---

## Part 1: Publish to GitHub

### Step 1: Prepare Your Repository

**Check your code is ready:**

```powershell
# Run tests
cd awx-mcp-python/server
pytest tests/ -v

# Verify package metadata
cat pyproject.toml

# Check for sensitive data
git status
```

**⚠️ Security Check:**
- Remove any hardcoded tokens, passwords, or credentials
- Verify `.gitignore` includes `.env`, `*.token`, `venv/`
- Review all configuration files

### Step 2: Initialize Git Repository

```powershell
cd awx-mcp-python/server

# Initialize repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: AWX MCP Server v1.0.0"
```

### Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Fill in details:
   - **Repository name**: `awx-mcp-server`
   - **Description**: "Industry-standard MCP server for AWX/Ansible Tower automation"
   - **Visibility**: Public (required for MCP Registry)
   - **Don't** initialize with README, .gitignore, or license (you have these)

3. Click **Create repository**

### Step 4: Push to GitHub

```powershell
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/awx-mcp-server.git

# Rename branch to main (if needed)
git branch -M main

# Push code
git push -u origin main
```

**Verify on GitHub:**
- All files are present
- README.md displays correctly
- No sensitive data committed

### Step 5: Add Repository Topics

On GitHub repository page:

1. Click "⚙️ Manage topics" (near description)
2. Add these topics:
   - `mcp`
   - `model-context-protocol`
   - `awx`
   - `ansible-tower`
   - `github-copilot`
   - `claude`
   - `cursor`
   - `python`
   - `automation`
   - `mcp-server`

3. Click **Done**

### Step 6: Create First Release

```powershell
# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0: Industry Standard MCP Server"

# Push tag
git push origin v1.0.0
```

**Create GitHub Release:**

1. Go to: `https://github.com/YOUR_USERNAME/awx-mcp-server/releases`
2. Click **Draft a new release**
3. Fill in:
   - **Tag**: v1.0.0
   - **Title**: "AWX MCP Server v1.0.0 - Initial Release"
   - **Description**:
     ```markdown
     ## 🎉 Initial Release
     
     Industry-standard MCP server for AWX/Ansible Tower automation.
     
     ### Features
     - ✅ 18+ AWX operations (jobs, templates, projects, inventories)
     - ✅ Support for 7+ MCP clients (VS Code, Claude, Cursor, etc.)
     - ✅ Token and OAuth2 authentication
     - ✅ STDIO transport (industry standard)
     - ✅ Comprehensive error handling
     - ✅ Full test coverage
     
     ### Installation
     
     ```bash
     pip install git+https://github.com/YOUR_USERNAME/awx-mcp-server.git
     ```
     
     ### Quick Start
     
     See [README.md](README.md) for complete setup instructions.
     
     ### Documentation
     - [Client Installation Guide](CLIENT_INSTALLATION.md)
     - [Developer Testing Guide](DEVELOPER_TESTING.md)
     - [Quick Start](QUICK_START.md)
     ```

4. Click **Publish release**

---

## Part 2: Register with MCP Registry

### Step 1: Install MCP Publisher CLI

**macOS/Linux (Homebrew):**
```bash
brew install mcp-publisher
```

**Windows (Pre-built Binary):**
1. Download from: https://github.com/modelcontextprotocol/mcp-publisher/releases
2. Extract to a directory in PATH
3. Verify: `mcp-publisher --version`

**Alternative (Build from Source):**
```bash
git clone https://github.com/modelcontextprotocol/mcp-publisher.git
cd mcp-publisher
go build
./mcp-publisher --version
```

**Verify Installation:**
```powershell
mcp-publisher --version
mcp-publisher help
```

### Step 2: Initialize server.json

Navigate to your server directory and run:

```powershell
cd awx-mcp-python/server
mcp-publisher init
```

**This creates `server.json` with auto-detected values.**

### Step 3: Configure server.json

Edit the generated `server.json`:

```json
{
  "name": "io.github.YOUR_USERNAME/awx-mcp-server",
  "displayName": "AWX MCP Server",
  "description": "Industry-standard MCP server for AWX/Ansible Tower automation. Control AWX through natural language in VS Code, Claude, Cursor, and other MCP clients.",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com",
    "url": "https://github.com/YOUR_USERNAME"
  },
  "license": "MIT",
  "homepage": "https://github.com/YOUR_USERNAME/awx-mcp-server",
  "repository": {
    "type": "git",
    "url": "https://github.com/YOUR_USERNAME/awx-mcp-server.git"
  },
  "keywords": [
    "mcp",
    "model-context-protocol",
    "awx",
    "ansible-tower",
    "automation",
    "github-copilot",
    "claude",
    "cursor",
    "python"
  ],
  "capabilities": [
    "tools"
  ],
  "transport": [
    "stdio"
  ],
  "deployment": {
    "type": "github",
    "owner": "YOUR_USERNAME",
    "repo": "awx-mcp-server"
  },
  "installation": {
    "pip": "git+https://github.com/YOUR_USERNAME/awx-mcp-server.git",
    "command": "python -m awx_mcp_server.mcp_server"
  },
  "configuration": {
    "required": [
      "AWX_BASE_URL",
      "AWX_TOKEN"
    ],
    "optional": [
      "AWX_USERNAME",
      "AWX_PASSWORD",
      "AWX_VERIFY_SSL"
    ]
  },
  "clients": [
    "vscode",
    "claude-desktop",
    "cursor",
    "windsurf",
    "claude-code",
    "github-copilot-cli",
    "antigravity"
  ],
  "tools": [
    {
      "name": "awx_list_job_templates",
      "description": "List all job templates in AWX"
    },
    {
      "name": "awx_job_launch",
      "description": "Launch a job from a template"
    },
    {
      "name": "awx_list_jobs",
      "description": "List all jobs with status filtering"
    },
    {
      "name": "awx_get_job",
      "description": "Get details of a specific job"
    },
    {
      "name": "awx_job_stdout",
      "description": "Get job output/logs"
    },
    {
      "name": "awx_job_cancel",
      "description": "Cancel a running job"
    },
    {
      "name": "awx_list_projects",
      "description": "List all projects"
    },
    {
      "name": "awx_project_update",
      "description": "Update project from SCM"
    },
    {
      "name": "awx_list_inventories",
      "description": "List all inventories"
    },
    {
      "name": "awx_get_inventory",
      "description": "Get inventory details"
    },
    {
      "name": "awx_list_hosts",
      "description": "List all hosts"
    },
    {
      "name": "awx_list_credentials",
      "description": "List all credentials"
    },
    {
      "name": "awx_env_list",
      "description": "List configured AWX environments"
    },
    {
      "name": "awx_env_test",
      "description": "Test AWX connection"
    }
  ]
}
```

**Key Fields:**
- `name`: MUST follow `io.github.YOUR_USERNAME/repo-name` format
- `deployment.type`: Use `"github"` for GitHub-based deployment
- `installation.pip`: Full pip install command
- `installation.command`: How to run the MCP server
- `clients`: List of supported MCP clients
- `tools`: List of available tools (helps discovery)

### Step 4: Update pyproject.toml (Optional but Recommended)

If you plan to publish to PyPI later, add `mcpName` to `pyproject.toml`:

```toml
[project]
name = "awx-mcp-server"
version = "1.0.0"
# ... existing fields ...

[tool.mcp]
name = "io.github.YOUR_USERNAME/awx-mcp-server"
```

**Or create a separate MCP section:**

```toml
[tool.mcp-registry]
name = "io.github.YOUR_USERNAME/awx-mcp-server"
displayName = "AWX MCP Server"
transport = ["stdio"]
capabilities = ["tools"]
```

### Step 5: Authenticate with MCP Registry

**Authenticate using GitHub:**

```powershell
mcp-publisher login github
```

**What happens:**
1. Opens browser window for GitHub OAuth
2. You authorize MCP Publisher to access your GitHub
3. Creates two token files:
   - `.mcpregistry_github_token`
   - `.mcpregistry_registry_token`

**⚠️ Security:**

Add these to `.gitignore`:

```gitignore
# MCP Registry tokens
.mcpregistry_github_token
.mcpregistry_registry_token
```

**Verify authentication:**

```powershell
mcp-publisher whoami
```

Expected output:
```
Authenticated as: YOUR_USERNAME
Registry: https://registry.modelcontextprotocol.io
```

### Step 6: Publish to MCP Registry

**Publish your server:**

```powershell
mcp-publisher publish
```

**What happens:**
1. Validates `server.json` format
2. Verifies GitHub repository exists and is public
3. Checks you have write access to the repository
4. Registers server metadata with MCP Registry
5. Server becomes discoverable

**Expected Output:**

```
✅ Validating server.json...
✅ Verifying GitHub repository: YOUR_USERNAME/awx-mcp-server
✅ Publishing to MCP Registry...
✅ Successfully published: io.github.YOUR_USERNAME/awx-mcp-server@1.0.0

Your server is now available at:
https://registry.modelcontextprotocol.io/servers/io.github.YOUR_USERNAME/awx-mcp-server
```

### Step 7: Commit server.json

**Add server.json to repository:**

```powershell
git add server.json
git commit -m "Add MCP Registry metadata (server.json)"
git push origin main
```

---

## Part 3: Automate with GitHub Actions

Automate publishing to MCP Registry on every release.

### Step 1: Create GitHub Actions Workflow

Create `.github/workflows/publish-mcp.yml`:

```yaml
name: Publish to MCP Registry

on:
  release:
    types: [published]
  workflow_dispatch:  # Allow manual trigger

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
      
      - name: Run tests
        run: |
          pip install pytest pytest-cov
          pytest tests/ -v
      
      - name: Install MCP Publisher
        run: |
          # Download latest release
          curl -L -o mcp-publisher https://github.com/modelcontextprotocol/mcp-publisher/releases/latest/download/mcp-publisher-linux-amd64
          chmod +x mcp-publisher
          sudo mv mcp-publisher /usr/local/bin/
      
      - name: Verify server.json
        run: |
          if [ ! -f server.json ]; then
            echo "❌ server.json not found"
            exit 1
          fi
          echo "✅ server.json found"
      
      - name: Update version in server.json
        run: |
          # Extract version from release tag (remove 'v' prefix)
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "Publishing version: $VERSION"
          
          # Update version in server.json using jq
          sudo apt-get install -y jq
          jq --arg version "$VERSION" '.version = $version' server.json > server.json.tmp
          mv server.json.tmp server.json
      
      - name: Publish to MCP Registry
        env:
          MCP_GITHUB_TOKEN: ${{ secrets.MCP_GITHUB_TOKEN }}
          MCP_REGISTRY_TOKEN: ${{ secrets.MCP_REGISTRY_TOKEN }}
        run: |
          # Create token files
          echo "$MCP_GITHUB_TOKEN" > .mcpregistry_github_token
          echo "$MCP_REGISTRY_TOKEN" > .mcpregistry_registry_token
          
          # Publish
          mcp-publisher publish
      
      - name: Create publication summary
        run: |
          echo "## ✅ Published to MCP Registry" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Server**: io.github.${{ github.repository_owner }}/awx-mcp-server" >> $GITHUB_STEP_SUMMARY
          echo "**Version**: ${GITHUB_REF#refs/tags/v}" >> $GITHUB_STEP_SUMMARY
          echo "**Registry**: https://registry.modelcontextprotocol.io" >> $GITHUB_STEP_SUMMARY
```

### Step 2: Add GitHub Secrets

**Get your tokens (from Step 2.5):**

```powershell
# On your local machine
cat .mcpregistry_github_token
cat .mcpregistry_registry_token
```

**Add to GitHub:**

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add two secrets:
   - Name: `MCP_GITHUB_TOKEN`
     Value: [content of .mcpregistry_github_token]
   - Name: `MCP_REGISTRY_TOKEN`
     Value: [content of .mcpregistry_registry_token]

### Step 3: Commit Workflow

```powershell
git add .github/workflows/publish-mcp.yml
git commit -m "Add automated MCP Registry publishing workflow"
git push origin main
```

### Step 4: Test Automation

**Create a new release:**

```powershell
# Tag new version
git tag -a v1.0.1 -m "Release v1.0.1: Test automation"
git push origin v1.0.1
```

**Create GitHub Release:**
1. Go to repository → Releases → Draft new release
2. Tag: v1.0.1
3. Title: "v1.0.1 - Test automation"
4. Click **Publish release**

**Verify workflow:**
1. Go to **Actions** tab
2. Watch "Publish to MCP Registry" workflow
3. Check for green checkmark ✅

---

## Part 4: Verify Publication

### Method 1: Search MCP Registry API

```powershell
# Search for your server
curl "https://registry.modelcontextprotocol.io/api/search?q=awx"

# Get specific server
curl "https://registry.modelcontextprotocol.io/api/servers/io.github.YOUR_USERNAME/awx-mcp-server"
```

**Expected Response:**

```json
{
  "name": "io.github.YOUR_USERNAME/awx-mcp-server",
  "displayName": "AWX MCP Server",
  "description": "Industry-standard MCP server for AWX/Ansible Tower automation...",
  "version": "1.0.0",
  "author": {...},
  "repository": "https://github.com/YOUR_USERNAME/awx-mcp-server",
  "installation": {
    "pip": "git+https://github.com/YOUR_USERNAME/awx-mcp-server.git"
  },
  "clients": ["vscode", "claude-desktop", ...],
  "tools": [...]
}
```

### Method 2: Check MCP Registry Website

Visit: https://registry.modelcontextprotocol.io

1. Search for "AWX" or your username
2. Your server should appear in results
3. Click to see details

### Method 3: Test Installation as User

**Fresh environment test:**

```powershell
# Create new directory
mkdir test-awx-mcp
cd test-awx-mcp

# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install from GitHub
pip install git+https://github.com/YOUR_USERNAME/awx-mcp-server.git

# Verify
python -c "import awx_mcp_server; print('✅ OK')"
```

### Method 4: Test in VS Code

**Create test workspace:**

1. Create `.vscode/mcp.json`:
   ```json
   {
     "mcpServers": {
       "awx": {
         "command": "python",
         "args": ["-m", "awx_mcp_server.mcp_server"],
         "env": {
           "AWX_BASE_URL": "https://your-awx.com",
           "AWX_TOKEN": "test_token"
         }
       }
     }
   }
   ```

2. Restart VS Code
3. Test in Copilot Chat: `@workspace list AWX job templates`

---

## Part 5: Update and Maintain

### Updating Your Server

**1. Make changes to code:**

```powershell
# Edit your code
# Run tests
pytest tests/ -v

# Commit changes
git add .
git commit -m "feat: Add new feature"
git push origin main
```

**2. Create new release:**

```powershell
# Bump version in pyproject.toml
# Update CHANGELOG.md

# Tag new version
git tag -a v1.1.0 -m "Release v1.1.0: New features"
git push origin v1.1.0
```

**3. Create GitHub Release:**

Automated workflow will:
- Run tests
- Update version in server.json
- Publish to MCP Registry automatically

**4. Verify publication:**

```powershell
curl "https://registry.modelcontextprotocol.io/api/servers/io.github.YOUR_USERNAME/awx-mcp-server"
# Check version is updated
```

### Version Management

**Semantic Versioning:**
- `v1.0.0` → `v1.0.1`: Bug fixes
- `v1.0.0` → `v1.1.0`: New features (backward compatible)
- `v1.0.0` → `v2.0.0`: Breaking changes

**Update checklist:**
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Run all tests
- [ ] Update documentation if needed
- [ ] Create git tag
- [ ] Create GitHub release
- [ ] Verify MCP Registry update

### Deprecation Process

If deprecating features:

1. **Announce in release notes**
2. **Add deprecation warnings** in code
3. **Update documentation**
4. **Give users time** (at least 2-3 releases)
5. **Remove in major version** (e.g., v2.0.0)

---

## Troubleshooting

### Problem 1: MCP Publisher Not Found

**Error:**
```
mcp-publisher: command not found
```

**Solutions:**
- **macOS/Linux**: `brew install mcp-publisher`
- **Windows**: Download from releases, add to PATH
- **Alternative**: Build from source

### Problem 2: Authentication Failed

**Error:**
```
❌ Authentication failed: Invalid token
```

**Solutions:**
```powershell
# Re-authenticate
mcp-publisher logout
mcp-publisher login github

# Verify
mcp-publisher whoami

# Check token files exist
ls -la | grep mcpregistry
```

### Problem 3: Repository Not Found

**Error:**
```
❌ Repository not found: YOUR_USERNAME/awx-mcp-server
```

**Checks:**
- Repository is public (not private)
- Repository name matches `server.json`
- You have write access
- Repository exists on GitHub

### Problem 4: server.json Invalid

**Error:**
```
❌ Invalid server.json: missing required field "name"
```

**Solution:**
```powershell
# Validate JSON syntax
cat server.json | python -m json.tool

# Check required fields
# - name (must be io.github.USERNAME/repo)
# - version
# - description
# - deployment.type
```

### Problem 5: Token Expired

**Error:**
```
❌ Token expired or invalid
```

**Solution:**
```powershell
# Re-authenticate
mcp-publisher login github

# Update GitHub secrets (for Actions)
# 1. Get new tokens
cat .mcpregistry_github_token
cat .mcpregistry_registry_token

# 2. Update in GitHub repository Settings → Secrets
```

### Problem 6: GitHub Actions Failing

**Check workflow logs:**

1. Go to **Actions** tab
2. Click failed workflow
3. Expand failed step
4. Check error message

**Common issues:**
- Missing GitHub secrets
- Invalid server.json
- Tests failing
- MCP Publisher version mismatch

**Debug locally:**
```powershell
# Simulate GitHub Actions
act -j publish  # Using 'act' tool

# Or run steps manually
pytest tests/ -v
mcp-publisher publish --dry-run
```

---

## Best Practices

### 1. Version Your server.json

Keep `server.json` version in sync with git tags:

```json
{
  "version": "1.0.0"  // Match git tag v1.0.0
}
```

### 2. Comprehensive Tool Descriptions

Make tools discoverable with good descriptions:

```json
{
  "tools": [
    {
      "name": "awx_list_job_templates",
      "description": "List all job templates in AWX. Returns template name, ID, type, and last run time. Useful for discovering available automation jobs.",
      "parameters": {
        "name_filter": "Optional search filter for template names"
      }
    }
  ]
}
```

### 3. Document Configuration

List all required and optional environment variables:

```json
{
  "configuration": {
    "required": ["AWX_BASE_URL", "AWX_TOKEN"],
    "optional": ["AWX_VERIFY_SSL", "AWX_TIMEOUT"],
    "description": "See README.md for detailed configuration guide"
  }
}
```

### 4. Test Before Publishing

Always test locally before publishing:

```powershell
# Run full test suite
pytest tests/ -v --cov

# Test installation
pip install -e .

# Test MCP server
python -m awx_mcp_server.mcp_server

# Dry run publish
mcp-publisher publish --dry-run
```

### 5. Keep Documentation Updated

Update these on every release:
- README.md
- CHANGELOG.md
- server.json
- Example configurations

### 6. Communicate with Users

**Use GitHub Releases:**
- Clear release notes
- Migration guides for breaking changes
- Links to documentation

**Use GitHub Discussions:**
- Answer questions
- Share tips
- Gather feedback

---

## Checklist: Publishing Your MCP Server

### Pre-Publication

- [ ] All tests passing
- [ ] Documentation complete
- [ ] No sensitive data in code
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated
- [ ] README.md has clear installation instructions

### GitHub Publication

- [ ] Repository created on GitHub (public)
- [ ] Code pushed to main branch
- [ ] Topics added to repository
- [ ] Release created with tag (v1.0.0)
- [ ] Release notes written

### MCP Registry

- [ ] MCP Publisher CLI installed
- [ ] server.json created and configured
- [ ] Authenticated with GitHub
- [ ] Published to MCP Registry
- [ ] Verified in registry API
- [ ] server.json committed to repository

### Automation

- [ ] GitHub Actions workflow created
- [ ] GitHub secrets added (tokens)
- [ ] Workflow tested with new release
- [ ] Automation verified working

### Post-Publication

- [ ] Tested installation as user
- [ ] Tested in VS Code/Copilot
- [ ] Announced in relevant communities
- [ ] Monitoring for issues

---

## Resources

### Official Documentation
- **MCP Registry**: https://registry.modelcontextprotocol.io
- **MCP Publisher**: https://github.com/modelcontextprotocol/mcp-publisher
- **Model Context Protocol**: https://modelcontextprotocol.io

### Related Guides
- [DEVELOPER_TESTING.md](DEVELOPER_TESTING.md) - Local development
- [CLIENT_INSTALLATION.md](CLIENT_INSTALLATION.md) - User installation
- [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) - GitHub publishing
- [README.md](README.md) - Project overview

### Community
- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **Discord/Slack**: Real-time chat (if available)

---

## Summary

**Publishing workflow:**

1. ✅ **Develop** → Test locally
2. ✅ **GitHub** → Push code, create release
3. ✅ **MCP Registry** → Register with mcp-publisher
4. ✅ **Automate** → GitHub Actions for updates
5. ✅ **Maintain** → Regular updates and support

**Your server is now:**
- 🌍 Publicly accessible on GitHub
- 🔍 Discoverable in MCP Registry
- 🤖 Usable by any MCP client
- 🔄 Automatically updated on releases

**Next steps:**
1. Publish your first release
2. Register with MCP Registry
3. Share with the community
4. Monitor for issues and feedback

---

**Happy Publishing!** 🚀

Your AWX MCP server is now ready for the world!
