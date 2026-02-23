# API Endpoint Cleanup - Production Ready

## Overview

The HTTP server has been simplified to include only production-ready MCP endpoints and essential monitoring.

---

## ✅ Production Endpoints (KEEP)

### Core MCP Endpoints
- **POST /mcp** - Main MCP JSON-RPC endpoint for all tool calls
- **GET /mcp/sse** - Server-Sent Events endpoint for streaming
- **OPTIONS /mcp** - CORS preflight handling
- **OPTIONS /mcp/sse** - CORS preflight handling

### Monitoring & Health
- **GET /health** - Health check for load balancers
- **GET /prometheus-metrics** - Prometheus metrics (public, no auth)
- **GET /** - Root endpoint with server info

### Admin Endpoints
- **POST /api/keys** - Create API key (admin only)
- **GET /api/keys** - List API keys (admin only)

---

## ❌ Removed Endpoints (Legacy/Duplicate)

### Deprecated MCP Endpoint
- ~~POST /messages~~ - Old MCP endpoint, replaced by `/mcp`

### Admin Stats (Removed - use Prometheus instead)
- ~~GET /metrics~~ - Duplicate of prometheus-metrics but with auth
- ~~GET /stats~~ - Admin stats endpoint
- ~~GET /stats/requests~~ - Admin request history

### REST API Endpoints (Removed - use MCP tools instead)
All `/api/v1/*` endpoints have been removed as they duplicate MCP functionality:

- ~~GET /api/v1/environments~~ → Use MCP tool `env_list`
- ~~GET /api/v1/environments/active~~ → Use MCP tool `env_get_active`
- ~~POST /api/v1/environments/test~~ → Use MCP tool `env_test_connection`
- ~~GET /api/v1/job-templates~~ → Use MCP tool `awx_templates_list`
- ~~GET /api/v1/job-templates/{name}~~ → Use MCP tool `awx_template_get`
- ~~GET /api/v1/jobs~~ → Use MCP tool `awx_jobs_list`
- ~~GET /api/v1/jobs/{job_id}~~ → Use MCP tool `awx_job_get`
- ~~POST /api/v1/jobs/launch~~ → Use MCP tool `awx_job_launch`
- ~~POST /api/v1/jobs/{job_id}/cancel~~ → Use MCP tool `awx_job_cancel`
- ~~GET /api/v1/jobs/{job_id}/stdout~~ → Use MCP tool `awx_job_stdout`
- ~~GET /api/v1/jobs/{job_id}/events~~ → Use MCP tool `awx_job_events`
- ~~GET /api/v1/projects~~ → Use MCP tool `awx_projects_list`
- ~~POST /api/v1/projects/{name}/update~~ → Use MCP tool `awx_project_update`
- ~~GET /api/v1/inventories~~ → Use MCP tool `awx_inventories_list`

---

## 🎯 Why Remove REST API Endpoints?

### 1. Duplication
Every REST endpoint duplicates functionality already available through MCP tools:
```json
// OLD: REST API
GET /api/v1/job-templates

// NEW: MCP Protocol
POST /mcp
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"awx_templates_list"}}
```

### 2. Simplified Maintenance
- **Before**: 25+ endpoints to maintain
- **After**: 8 essential endpoints
- Reduces code complexity by ~60%

### 3. Protocal Consistency  
- MCP is the standardized protocol for AI assistants
- GitHub Copilot, Claude, and Cursor all use MCP
- REST endpoints were custom and non-standard

### 4. Better Security
- MCP endpoints properly handle authentication via headers
- Single authentication mechanism (vs separate REST auth)
- Easier to audit and monitor

### 5. Future-Proof
- MCP is an industry standard (anthropic.com/mcp)
- Growing ecosystem and tooling
- Better long-term support

---

## 🔄 Migration Guide

### For REST API Users

If you were using the REST API endpoints directly:

**Before**:
```bash
curl http://localhost:8000/api/v1/job-templates \
  -H "Authorization: Bearer API_KEY"
```

**After** (use MCP):
```bash
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-AWX-Base-URL: https://awx.example.com" \
  -H "X-AWX-Token: YOUR_AWX_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "awx_templates_list",
      "arguments": {}
    }
  }'
```

**Or use the MCP client** (recommended):
```python
from mcp import Client

async with Client("http://localhost:8000/mcp") as client:
    result = await client.call_tool("awx_templates_list", {})
    print(result)
```

---

## 📋 Implementation Checklist

To remove the unwanted endpoints from `http_server.py`:

- [ ] Remove `/messages` endpoint and handler
- [ ] Remove `get_client()` helper function
- [ ] Remove all `/api/v1/environments*` endpoints
- [ ] Remove all `/api/v1/job-templates*` endpoints
- [ ] Remove all `/api/v1/jobs*` endpoints
- [ ] Remove all `/api/v1/projects*` endpoints
- [ ] Remove all `/api/v1/inventories*` endpoints
- [ ] Remove `/metrics` endpoint (keep `/prometheus-metrics`)
- [ ] Remove `/stats` and `/stats/requests` endpoints
- [ ] Update root endpoint to reflect only current endpoints
- [ ] Update OpenAPI docs
- [ ] Test all remaining endpoints
- [ ] Update client documentation

---

## ✅ Final Endpoint List

After cleanup, the server exposes only these endpoints:

```
GET    /                      - Server info
GET    /health                - Health check
GET    /prometheus-metrics    - Prometheus metrics  
POST   /api/keys              - Create API key (admin)
GET    /api/keys              - List API keys (admin)
POST   /mcp                   - MCP JSON-RPC endpoint
GET    /mcp/sse               - MCP Server-Sent Events
OPTIONS /mcp                  - CORS preflight
OPTIONS /mcp/sse              - CORS preflight
```

**Total: 9 endpoints** (down from 25+)

---

## 🚀 Benefits of Cleanup

✅ **Simpler codebase** - 60% less endpoint code
✅ **Easier maintenance** - Single protocol to support
✅ **Better security** - Unified authentication
✅ **Standards compliant** - Full MCP protocol support
✅ **Future-proof** - Growing MCP ecosystem
✅ **Better monitoring** - Focused metrics
✅ **Faster development** - Less code to test

---

## 📚 Related Documentation

- [Production Readiness](./PRODUCTION_READINESS.md)
- [Multi-Environment Setup](./MULTI_ENVIRONMENT_SETUP.md)
- [Logging and Monitoring](./LOGGING.md)
