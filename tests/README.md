# AWX MCP Tests

Comprehensive test suite for AWX MCP Server functionality.

## Quick Start

```bash
# Run test menu
python tests/run_tests.py

# Run specific test
python tests/run_tests.py env
python tests/run_tests.py templates
python tests/run_tests.py launch

# Run pytest suite
python tests/run_tests.py all
pytest
```

## Test Files

### Environment Management
- **test_env_management.py** - List, set, and test environments

### Discovery Operations
- **test_list_templates.py** - List job templates
- **test_list_projects.py** - List projects
- **test_list_inventories.py** - List inventories
- **test_project_update.py** - Update project from SCM

### Job Execution
- **test_job_launch.py** - Launch jobs from templates (interactive)
- **test_job_get.py** - Get job status and details
- **test_list_jobs.py** - List all jobs and running jobs
- **test_job_cancel.py** - Cancel running jobs (interactive)

### Diagnostics & Analysis
- **test_job_stdout.py** - View job output/logs
- **test_job_events.py** - View job events (with --failed-only option)
- **test_job_failure_summary.py** - Analyze failures with AI suggestions

### Integration Tests
- **test_mcp_integration.py** - Pytest-based MCP integration tests
- **test_connection.py** - Basic connection tests
- **conftest.py** - Pytest fixtures and configuration

## Running Individual Tests

Each test can be run independently:

```bash
# Environment management
python tests/test_env_management.py

# List resources
python tests/test_list_templates.py
python tests/test_list_projects.py
python tests/test_list_inventories.py
python tests/test_list_jobs.py

# Job operations
python tests/test_job_launch.py
python tests/test_job_get.py 123
python tests/test_job_cancel.py 123
python tests/test_job_stdout.py 123
python tests/test_job_events.py 123
python tests/test_job_events.py 123 --failed-only
python tests/test_job_failure_summary.py 123

# Project operations
python tests/test_project_update.py
python tests/test_project_update.py 5 --wait
```

## Running with Pytest

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=awx_mcp --cov-report=html

# Run specific test file
pytest tests/test_mcp_integration.py

# Run specific test function
pytest tests/test_mcp_integration.py::test_list_templates

# Run with verbose output
pytest -v

# Run with debug output
pytest -v --log-cli-level=DEBUG
```

## Test Requirements

1. **AWX Server** - Running and accessible
2. **Environment Configured** - At least one environment set up
   ```bash
   python -m awx_mcp.cli env add --name local --url http://localhost:30080 --token TOKEN
   ```

3. **Credentials** - Stored in keyring
4. **Active Environment** - Default environment set
   ```bash
   python -m awx_mcp.cli env set-default local
   ```

## Test Output Examples

### Environment Management
```bash
$ python tests/test_env_management.py
======================================================================
AWX MCP Server - Environment Management Tests
======================================================================

[Test 1] List Environments
----------------------------------------------------------------------
Found 1 environment(s):

  [local-123] local ✓ ACTIVE
      URL: http://localhost:30080
      Verify SSL: False

[Test 2] Get Active Environment
----------------------------------------------------------------------
✓ Active environment: local
  Environment ID: local-123
  Base URL: http://localhost:30080
...
```

### List Templates
```bash
$ python tests/test_list_templates.py
Loading AWX configuration...
✓ Active environment: local (http://localhost:30080)
✓ Using token authentication

Testing connection...
✓ Connection successful

Listing job templates...

Found 3 job template(s):

  [7] Deploy Web App
      Description: Deploy web application to production
      Project: Web App Project
      Playbook: deploy.yml
  ...
```

### Launch Job
```bash
$ python tests/test_job_launch.py
...
Enter template ID to launch: 7
Optional: Enter extra variables as JSON (or press Enter to skip)
Example: {"version": "1.2.3", "environment": "production"}
Extra vars: {"version": "2.0.0"}

Launching job from template 7...

✓ Job launched successfully!
  Job ID: 123
  Job Name: Deploy Web App
  Status: pending
  URL: http://localhost:30080/#/jobs/playbook/123
```

## Interactive Tests

Some tests are interactive and prompt for input:
- `test_job_launch.py` - Prompts for template ID and variables
- `test_job_cancel.py` - Prompts for job ID and confirmation
- `test_project_update.py` - Prompts for project ID

You can also pass arguments:
```bash
python tests/test_job_get.py 123
python tests/test_job_cancel.py 123
python tests/test_project_update.py 5 --wait
```

## Troubleshooting Tests

### No Active Environment
```bash
✗ No active environment set!

# Fix:
python -m awx_mcp.cli env set-default local
```

### Connection Failed
```bash
✗ Connection failed!

# Check:
1. AWX server is running
2. URL is correct
3. Credentials are valid
4. Network connectivity

# Test manually:
curl http://localhost:30080/api/v2/ping/
```

### No Resources Found
```bash
No job templates found.

# Create resources in AWX UI first:
http://localhost:30080
```

## Continuous Integration

Add to CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  env:
    AWX_URL: ${{ secrets.AWX_URL }}
    AWX_TOKEN: ${{ secrets.AWX_TOKEN }}
  run: |
    python -m awx_mcp.cli env add --name ci --url $AWX_URL --token $AWX_TOKEN
    pytest --cov=awx_mcp --cov-report=xml
```

## Writing New Tests

Follow the pattern from existing tests:

```python
"""Test AWX MCP functionality - description."""
import asyncio
from awx_mcp.storage import ConfigManager, CredentialStore
from awx_mcp.clients import CompositeAWXClient
from awx_mcp.domain import CredentialType

async def test_your_feature():
    """Test description."""
    # Setup
    config_manager = ConfigManager()
    credential_store = CredentialStore()
    env = config_manager.get_active()
    
    # Get credentials
    try:
        username, secret = credential_store.get_credential(
            env.env_id, CredentialType.PASSWORD
        )
        is_token = False
    except Exception:
        username, secret = credential_store.get_credential(
            env.env_id, CredentialType.TOKEN
        )
        is_token = True
    
    # Test
    client = CompositeAWXClient(env, username, secret, is_token)
    async with client:
        # Your test code here
        pass

if __name__ == "__main__":
    asyncio.run(test_your_feature())
```

## Resources

- [Getting Started](../docs/GETTING_STARTED.md) - Initial setup
- [Server Guide](../docs/SERVER_GUIDE.md) - Server management
- [Development Guide](../docs/DEVELOPMENT.md) - Development workflow
