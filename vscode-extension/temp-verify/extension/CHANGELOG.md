# Changelog

All notable changes to the AWX MCP Extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-07

### Added
- Initial release of AWX MCP Extension
- Integration with GitHub Copilot via Model Context Protocol
- AWX/Ansible Tower management through MCP
- List and manage inventories, projects, and job templates
- Launch and monitor jobs with real-time status updates
- Retrieve job outputs and events
- Secure credential management using system keyring
- Multi-environment support
- Auto-installation of bundled MCP server
- Status bar integration showing server status
- Activity bar with AWX environments, metrics, and logs views
- Configuration commands for AWX connection setup
- Python environment auto-detection

### Features
- **MCP Server Management**: Start, stop, and restart the MCP server directly from VS Code
- **AWX Integration**: Full AWX/Ansible Tower API integration
- **Job Management**: Launch jobs, monitor progress, and view outputs
- **Secure Auth**: Credential storage using OS keyring
- **Multiple Environments**: Support for multiple AWX instances
- **Logging**: Comprehensive logging with configurable levels
- **Monitoring**: Real-time metrics and performance monitoring

### Requirements
- VS Code 1.85.0 or higher
- Python 3.10 or higher
- AWX or Ansible Tower instance

## [Unreleased]

### Planned
- Enhanced job filtering and search
- Job template favorites
- Workflow visualization
- Inventory sync status
- Notification support
- Custom MCP tool configuration
