# AWX MCP Server - Quick Reference

## Installation

```bash
# Install
cd awx-mcp-python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pip install awxkit

# Configure
awx-mcp env add --name prod --url https://awx.example.com --username admin

# Test
awx-mcp env test prod

# Start server
awx-mcp serve
```

## CLI Commands

### Environment Management

```bash
# Add environment
awx-mcp env add --name PROD_NAME --url URL --username USER
awx-mcp env add --name DEV --url URL --token TOKEN --no-verify-ssl

# List environments
awx-mcp env list

# Set active
awx-mcp env set-default PROD

# Remove environment
awx-mcp env remove PROD --yes

# Test connection
awx-mcp env test PROD
```

## MCP Tools Reference

### Environment Management

| Tool | Description | Arguments |
|------|-------------|-----------|
| `env_list` | List all environments | None |
| `env_set_active` | Set active environment | `env_name` |
| `env_get_active` | Get active environment | None |
| `env_test_connection` | Test connection | `env_name?` |

### Discovery

| Tool | Description | Arguments |
|------|-------------|-----------|
| `awx_templates_list` | List job templates | `filter?`, `page?`, `page_size?` |
| `awx_projects_list` | List projects | `filter?`, `page?`, `page_size?` |
| `awx_inventories_list` | List inventories | `filter?`, `page?`, `page_size?` |
| `awx_project_update` | Update project from SCM | `project_id`, `wait?` |

### Execution

| Tool | Description | Arguments |
|------|-------------|-----------|
| `awx_job_launch` | Launch job | `template_id`, `extra_vars?`, `limit?`, `tags?`, `skip_tags?` |
| `awx_job_get` | Get job status | `job_id` |
| `awx_jobs_list` | List jobs | `status?`, `created_after?`, `page?`, `page_size?` |
| `awx_job_cancel` | Cancel job | `job_id` |

### Diagnostics

| Tool | Description | Arguments |
|------|-------------|-----------|
| `awx_job_stdout` | Get job output | `job_id`, `format?`, `tail_lines?` |
| `awx_job_events` | Get job events | `job_id`, `failed_only?`, `page?`, `page_size?` |
| `awx_job_failure_summary` | Analyze failure | `job_id` |

## Chat Command Examples

```
# Environment
awx env list
awx use production
awx env test

# Discovery
awx templates
awx templates filter:deploy
awx projects
awx inventories

# Execution
run template 15
launch deploy-web-app with vars version=1.2.3
launch template deploy-api with vars {"version": "2.0.0", "env": "prod"}

# Monitoring
show job 12345
check status of job 12345
get logs for job 12345
show last 100 lines of job 12345

# Diagnostics
analyze job 12345
why did job 12345 fail?
show failed events for job 12345

# Operations
update project 5
cancel job 12345
sync project Web-App
```

## Python API Examples

### Basic Usage

```python
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

# Setup
config_mgr = ConfigManager()
cred_store = CredentialStore()

env = config_mgr.get_active()
username, secret = cred_store.get_credential(env.env_id, CredentialType.PASSWORD)

# Create client
async with CompositeAWXClient(env, username, secret) as client:
    # List templates
    templates = await client.list_job_templates()
    
    # Launch job
    job = await client.launch_job(
        template_id=15,
        extra_vars={"version": "1.2.3"}
    )
    
    # Get status
    job = await client.get_job(job.id)
    
    # Get logs
    stdout = await client.get_job_stdout(job.id)
```

### Failure Analysis

```python
from awx_mcp.utils import analyze_job_failure

async with CompositeAWXClient(env, username, secret) as client:
    events = await client.get_job_events(job_id, failed_only=True)
    stdout = await client.get_job_stdout(job_id, "txt", 500)
    
    analysis = analyze_job_failure(job_id, events, stdout)
    
    print(f"Category: {analysis.category.value}")
    print(f"Error: {analysis.error_message}")
    for fix in analysis.suggested_fixes:
        print(f"  - {fix}")
```

## Failure Categories

| Category | Description | Common Causes |
|----------|-------------|---------------|
| `auth_failure` | Authentication failed | SSH keys, passwords, sudo |
| `missing_variable` | Undefined variable | Missing extra_vars |
| `syntax_error` | YAML/syntax error | Playbook errors |
| `module_failure` | Module execution failed | Missing dependencies |
| `connection_timeout` | Connection timeout | Network issues |
| `inventory_issue` | Host unreachable | DNS, firewall |
| `permission_denied` | Permission error | File permissions, sudo |
| `unknown` | Unknown failure | Other issues |

## Configuration Files

| Path | Content | Format |
|------|---------|--------|
| `~/.awx-mcp/config.json` | Environment configs | JSON |
| OS Keyring | Credentials | Encrypted |

## VSCode Integration

**.vscode/settings.json:**

```json
{
  "mcp.servers": {
    "awx": {
      "command": "python",
      "args": ["-m", "awx_mcp_server"],
      "cwd": "/path/to/awx-mcp-python"
    }
  }
}
```

## Environment Variables

```bash
# Optional config path
export AWX_MCP_CONFIG_PATH=/custom/path/config.json

# Debug mode
export AWX_MCP_DEBUG=true

# Prefer CLI over REST
export AWX_MCP_PREFER_CLI=true
```

## Common Workflows

### Deploy Application

```
1. awx use production
2. update project Web-App
3. run template deploy-web-app with vars version=1.2.3
4. check status of job XXXX
5. show logs for job XXXX
```

### Debug Failed Job

```
1. show recent failed jobs
2. analyze job 12345
3. show failed events for job 12345
4. get last 200 lines of job 12345
```

### Multi-Environment Deploy

```
1. awx use dev
2. run template deploy-api with vars version=2.0.0-rc1
3. awx use staging  
4. run template deploy-api with vars version=2.0.0-rc1
5. awx use production
6. run template deploy-api with vars version=2.0.0
```

## Security Best Practices

✅ **DO:**
- Use token auth for CI/CD
- Set allowlists for production
- Verify SSL in production
- Use descriptive environment names
- Review audit logs regularly

❌ **DON'T:**
- Store credentials in code
- Disable SSL verification in production
- Share credentials between environments
- Run with debug logging in production
- Skip allowlist configuration

## Troubleshooting

### Connection Failed

```bash
# Test connection
awx-mcp env test prod

# Check with debug
awx-mcp --debug env test prod

# Verify AWX is accessible
curl -k https://awx.example.com/api/v2/ping/
```

### SSL Errors

```bash
# For development only
awx-mcp env add --name dev --url ... --no-verify-ssl
```

### Credential Errors

```bash
# Remove and re-add
awx-mcp env remove prod --yes
awx-mcp env add --name prod --url ... --username admin
```

### awxkit Not Found

```bash
pip install awxkit
awx --version
```

## Support & Resources

- **Documentation**: `docs/`
- **Examples**: `examples/`
- **Tests**: `tests/`
- **Issues**: Check logs with `--debug` flag

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src

# Linting
ruff check src
black src

# Run with coverage
pytest --cov=awx_mcp --cov-report=html
```

## Project Structure

```
awx-mcp-python/
├── src/awx_mcp/
│   ├── domain/          # Core models & exceptions
│   ├── storage/         # Config & credential storage
│   ├── clients/         # AWX clients (CLI & REST)
│   ├── utils/           # Logging & parsing
│   ├── server.py        # MCP server
│   └── cli.py           # CLI interface
├── tests/               # Unit tests
├── docs/                # Documentation
├── examples/            # Usage examples
└── pyproject.toml       # Dependencies & config
```
