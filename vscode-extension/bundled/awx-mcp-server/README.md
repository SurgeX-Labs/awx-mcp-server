# AWX MCP Server

Model Context Protocol (MCP) server for AWX/Ansible Tower integration with AI assistants like GitHub Copilot.

## Features

- List and manage AWX inventories, projects, and job templates
- Launch and monitor jobs
- Retrieve job outputs and events
- Secure credential management with keyring
- Multi-environment support

## Installation

This package is typically installed automatically by the AWX MCP VS Code extension. For standalone use:

```bash
pip install awx-mcp-server
```

## Usage

### With VS Code Extension

Install the AWX MCP Extension from the VS Code marketplace. The extension will automatically install and manage this package.

### Standalone

```bash
# Configure environment
export AWX_HOST=https://your-awx-instance.com
export AWX_USERNAME=your-username
export AWX_TOKEN=your-token  # or use AWX_PASSWORD

# Start server
awx-mcp-server
```

## Configuration

The server can be configured via environment variables:

- `AWX_HOST` - AWX instance URL
- `AWX_USERNAME` - Username for authentication
- `AWX_TOKEN` - Authentication token (preferred)
- `AWX_PASSWORD` - Password (alternative to token)
- `AWX_VERIFY_SSL` - Verify SSL certificates (default: true)
- `LOG_LEVEL` - Logging level (debug, info, warning, error)

## License

MIT License - see LICENSE file for details.
