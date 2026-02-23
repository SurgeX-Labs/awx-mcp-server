# Changelog

All notable changes to the AWX MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-02-22

### Added
- **Production Readiness**: Comprehensive production deployment documentation
  - Production readiness checklist and feature assessment
  - Performance characteristics and benchmarks
  - High availability setup with Kubernetes examples
  - Security guidelines by environment type
  
- **Multi-Environment Support**: Complete guide for managing multiple AWX/AAP environments
  - Configuration examples for Local, Dev, Staging, and Production environments
  - Environment switching via Copilot Chat dropdown
  - Environment-specific security best practices
  - Transaction logging with environment context
  
- **Comprehensive Documentation Structure**:
  - New `/docs` folder with organized documentation
  - `MULTI_ENVIRONMENT_SETUP.md` - Multi-environment configuration guide
  - `PRODUCTION_READINESS.md` - Production deployment checklist
  - `LOGGING.md` - Logging and monitoring architecture
  - `ENDPOINT_CLEANUP.md` - API cleanup strategy and rationale
  - `docs/README.md` - Documentation index and navigation
  - `PRODUCTION_READY_SUMMARY.md` - Quick reference summary
  
- **Logging & Monitoring Enhancements**:
  - Documented structured JSON logging with all transaction details
  - Prometheus metrics integration guide
  - ELK Stack and Splunk integration examples
  - Alerting rules for production monitoring
  - Log retention policies
  
- **API Cleanup Documentation**:
  - Clear separation between production and legacy endpoints
  - Migration guide from REST API to MCP protocol
  - Rationale for endpoint consolidation (60% code reduction)

### Changed
- Enhanced README with proper documentation organization
- Improved HTTP server with cleaner endpoint structure
- Better authentication handling for multi-environment scenarios

### Documentation
- Complete restructure of documentation for production use
- Added 2500+ lines of comprehensive guides
- Professional documentation index with use-case navigation
- Quick reference guides for common scenarios

### Security
- Documented security best practices per environment type
- Token-based authentication recommendations for production
- SSL/TLS configuration guidelines
- Credential management improvements

## [1.1.6] - Previous Release

### Features
- HTTP server mode for remote MCP access
- MCP-over-HTTP with SSE support
- 49 AWX automation tools
- API key management
- Health and metrics endpoints
- Structured logging with structlog
- Prometheus metrics integration

---

For more details, see the [GitHub repository](https://github.com/SurgeX-Labs/awx-mcp-server).
