"""HTTP server implementation for remote MCP access with monitoring."""

import asyncio
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from mcp.server import Server
from pydantic import BaseModel
import structlog

from awx_mcp_server.monitoring import (
    monitoring_service,
    RequestTimer,
    CONTENT_TYPE_LATEST,
)

# Import local components
from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.utils import configure_logging, get_logger

logger = get_logger(__name__)

# API Key storage (in production, use database or Redis)
API_KEYS: dict[str, dict[str, Any]] = {}


class APIKeyCreate(BaseModel):
    """API key creation request."""
    name: str
    tenant_id: str
    expires_days: Optional[int] = 90


class APIKeyResponse(BaseModel):
    """API key response."""
    api_key: str
    name: str
    tenant_id: str
    created_at: str
    expires_at: Optional[str]


def verify_api_key(x_api_key: str = Header(...)) -> dict[str, Any]:
    """Verify API key and return tenant info."""
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_info = API_KEYS[x_api_key]
    
    # Check expiration
    if key_info.get("expires_at"):
        expires_at = datetime.fromisoformat(key_info["expires_at"])
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=401, detail="API key expired")
    
    return key_info


def create_app(mcp_server: Server) -> FastAPI:
    """Create FastAPI application with MCP server and monitoring."""
    app = FastAPI(
        title="AWX MCP Server",
        description="Production-ready MCP server for AWX automation with monitoring",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        """Middleware to track all requests."""
        # Extract tenant ID from header if available
        tenant_id = request.headers.get("X-API-Key", "anonymous")
        if tenant_id in API_KEYS:
            tenant_id = API_KEYS[tenant_id].get("tenant_id", tenant_id)
        
        with RequestTimer(
            tenant_id=tenant_id,
            endpoint=request.url.path,
            method=request.method,
        ) as timer:
            try:
                response = await call_next(request)
                timer.status_code = response.status_code
                return response
            except Exception as e:
                timer.status_code = 500
                timer.error = str(e)
                raise

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "AWX MCP Server",
            "version": "1.0.0",
            "status": "running",
            "transport": "http",
            "features": ["monitoring", "multi-tenant", "authentication"],
            "endpoints": {
                "messages": "/messages",
                "health": "/health",
                "metrics": "/metrics",
                "prometheus": "/prometheus-metrics",
                "stats": "/stats",
                "docs": "/docs",
            }
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "awx-mcp-server",
            "version": "1.0.0",
        }

    @app.get("/metrics")
    async def metrics(tenant_info: dict = Depends(verify_api_key)):
        """Get metrics for authenticated tenant."""
        tenant_id = tenant_info["tenant_id"]
        config_manager = ConfigManager(tenant_id=tenant_id)
        envs = config_manager.list_environments()
        
        # Get tenant-specific stats
        stats = monitoring_service.get_tenant_stats(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "environments_count": len(envs),
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
        }

    @app.get("/prometheus-metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint (public)."""
        metrics_data = monitoring_service.get_prometheus_metrics()
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)

    @app.get("/stats")
    async def get_stats(
        tenant_id: Optional[str] = None,
        authorization: str = Header(...),
    ):
        """Get statistics (admin only)."""
        if authorization != "Bearer admin-secret-token":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if tenant_id:
            return monitoring_service.get_tenant_stats(tenant_id)
        else:
            return {
                "tenants": monitoring_service.get_all_stats(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    @app.get("/stats/requests")
    async def get_requests(
        tenant_id: Optional[str] = None,
        limit: int = 100,
        authorization: str = Header(...),
    ):
        """Get recent requests (admin only)."""
        if authorization != "Bearer admin-secret-token":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return {
            "requests": monitoring_service.get_recent_requests(tenant_id, limit),
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.post("/api/keys", response_model=APIKeyResponse)
    async def create_api_key(
        key_request: APIKeyCreate,
        authorization: str = Header(...),
    ):
        """
        Create a new API key (requires admin authorization).
        In production, implement proper admin authentication.
        """
        if authorization != "Bearer admin-secret-token":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Generate secure API key
        api_key = f"awx_mcp_{secrets.token_urlsafe(32)}"
        created_at = datetime.utcnow()
        expires_at = (
            created_at + timedelta(days=key_request.expires_days)
            if key_request.expires_days
            else None
        )
        
        # Store API key
        API_KEYS[api_key] = {
            "name": key_request.name,
            "tenant_id": key_request.tenant_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        
        logger.info(
            "api_key_created",
            tenant_id=key_request.tenant_id,
            name=key_request.name,
        )
        
        return APIKeyResponse(
            api_key=api_key,
            name=key_request.name,
            tenant_id=key_request.tenant_id,
            created_at=created_at.isoformat(),
            expires_at=expires_at.isoformat() if expires_at else None,
        )

    @app.get("/api/keys")
    async def list_api_keys(authorization: str = Header(...)):
        """List all API keys (admin only)."""
        if authorization != "Bearer admin-secret-token":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return {
            "keys": [
                {
                    "api_key_preview": f"{key[:12]}...{key[-8:]}",
                    **info,
                }
                for key, info in API_KEYS.items()
            ]
        }

    @app.post("/messages")
    async def handle_messages(
        request: Request,
        tenant_info: dict = Depends(verify_api_key),
    ):
        """Handle MCP messages via POST with monitoring."""
        tenant_id = tenant_info["tenant_id"]
        
        logger.info("message_received", tenant_id=tenant_id)
        monitoring_service.record_chat_interaction(tenant_id, source="api")
        
        try:
            message = await request.json()
            
            # Extract tool name if it's a tool call
            tool_name = None
            if message.get("method") == "tools/call":
                tool_name = message.get("params", {}).get("name")
                monitoring_service.record_tool_call(tenant_id, tool_name, success=True)
            
            # Process MCP message through your server
            # For now, return a simple response
            result = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "status": "received",
                    "tenant_id": tenant_id,
                    "tool_name": tool_name,
                }
            }
            
            return result
            
        except Exception as e:
            logger.error("message_error", error=str(e), tenant_id=tenant_id)
            if tool_name:
                monitoring_service.record_tool_call(tenant_id, tool_name, success=False)
            raise HTTPException(status_code=500, detail=str(e))

    # Helper function to get AWX client
    async def get_client(tenant_id: str):
        """Get AWX client for tenant."""
        from awx_mcp_server.storage import ConfigManager, CredentialStore
        from awx_mcp_server.clients import CompositeAWXClient
        from awx_mcp_server.domain import CredentialType
        
        config_manager = ConfigManager(tenant_id=tenant_id)
        credential_store = CredentialStore(tenant_id=tenant_id)
        
        env = config_manager.get_active()
        
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
            is_token = False
        except:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        
        return CompositeAWXClient(env, username, secret, is_token)

    # AWX REST API Endpoints

    # Environment Management
    @app.get("/api/v1/environments")
    async def list_environments(tenant_info: dict = Depends(verify_api_key)):
        """List all AWX environments."""
        tenant_id = tenant_info["tenant_id"]
        from awx_mcp_server.storage import ConfigManager
        
        config_manager = ConfigManager(tenant_id=tenant_id)
        envs = config_manager.list()
        
        return {
            "environments": [
                {"id": e.env_id, "name": e.name, "url": e.url}
                for e in envs
            ]
        }

    @app.get("/api/v1/environments/active")
    async def get_active_environment(tenant_info: dict = Depends(verify_api_key)):
        """Get active AWX environment."""
        tenant_id = tenant_info["tenant_id"]
        from awx_mcp_server.storage import ConfigManager
        
        config_manager = ConfigManager(tenant_id=tenant_id)
        env = config_manager.get_active()
        
        return {
            "environment": {
                "id": env.env_id,
                "name": env.name,
                "url": env.url
            }
        }

    @app.post("/api/v1/environments/test")
    async def test_environment(tenant_info: dict = Depends(verify_api_key)):
        """Test connection to AWX environment."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        result = await client.test_connection()
        
        return {"success": result, "message": "Connection successful" if result else "Connection failed"}

    # Job Templates
    @app.get("/api/v1/job-templates")
    async def list_job_templates(
        filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """List job templates."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        templates = await client.list_job_templates(name_filter=filter, page=page, page_size=page_size)
        
        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "job_type": t.job_type,
                    "inventory": t.inventory,
                    "project": t.project,
                    "playbook": t.playbook
                }
                for t in templates
            ]
        }

    @app.get("/api/v1/job-templates/{name}")
    async def get_job_template(name: str, tenant_info: dict = Depends(verify_api_key)):
        """Get job template details."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        template = await client.get_job_template(name)
        
        return {
            "template": {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "job_type": template.job_type,
                "inventory": template.inventory,
                "project": template.project,
                "playbook": template.playbook,
                "extra_vars": template.extra_vars
            }
        }

    # Jobs
    @app.get("/api/v1/jobs")
    async def list_jobs(
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """List jobs."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        jobs = await client.list_jobs(status_filter=status, page=page, page_size=page_size)
        
        return {
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "status": j.status,
                    "started": str(j.started) if j.started else None,
                    "finished": str(j.finished) if j.finished else None,
                    "elapsed": j.elapsed
                }
                for j in jobs
            ]
        }

    @app.get("/api/v1/jobs/{job_id}")
    async def get_job(job_id: int, tenant_info: dict = Depends(verify_api_key)):
        """Get job details."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        job = await client.get_job(job_id)
        
        return {
            "job": {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "started": str(job.started) if job.started else None,
                "finished": str(job.finished) if job.finished else None,
                "elapsed": job.elapsed
            }
        }

    @app.post("/api/v1/jobs/launch")
    async def launch_job(
        request: Request,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """Launch a job."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        
        data = await request.json()
        template_name = data.get("template_name")
        extra_vars = data.get("extra_vars")
        
        job = await client.launch_job(template_name, extra_vars)
        
        return {
            "job": {
                "id": job.id,
                "name": job.name,
                "status": job.status
            }
        }

    @app.post("/api/v1/jobs/{job_id}/cancel")
    async def cancel_job(job_id: int, tenant_info: dict = Depends(verify_api_key)):
        """Cancel a job."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        await client.cancel_job(job_id)
        
        return {"success": True, "message": f"Job {job_id} canceled"}

    @app.get("/api/v1/jobs/{job_id}/stdout")
    async def get_job_stdout(job_id: int, tenant_info: dict = Depends(verify_api_key)):
        """Get job output."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        output = await client.get_job_stdout(job_id)
        
        return {"job_id": job_id, "output": output}

    @app.get("/api/v1/jobs/{job_id}/events")
    async def get_job_events(
        job_id: int,
        page: int = 1,
        page_size: int = 50,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """Get job events."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        events = await client.get_job_events(job_id, page, page_size)
        
        return {
            "events": [
                {
                    "event": e.event,
                    "task": e.task,
                    "role": e.role,
                    "stdout": e.stdout
                }
                for e in events
            ]
        }

    # Projects
    @app.get("/api/v1/projects")
    async def list_projects(
        page: int = 1,
        page_size: int = 25,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """List projects."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        projects = await client.list_projects(page=page, page_size=page_size)
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "scm_type": p.scm_type,
                    "scm_url": p.scm_url
                }
                for p in projects
            ]
        }

    @app.post("/api/v1/projects/{name}/update")
    async def update_project(name: str, tenant_info: dict = Depends(verify_api_key)):
        """Update project from SCM."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        await client.update_project(name)
        
        return {"success": True, "message": f"Project '{name}' update initiated"}

    # Inventories
    @app.get("/api/v1/inventories")
    async def list_inventories(
        page: int = 1,
        page_size: int = 25,
        tenant_info: dict = Depends(verify_api_key)
    ):
        """List inventories."""
        tenant_id = tenant_info["tenant_id"]
        client = await get_client(tenant_id)
        inventories = await client.list_inventories(page=page, page_size=page_size)
        
        return {
            "inventories": [
                {
                    "id": i.id,
                    "name": i.name,
                    "description": i.description
                }
                for i in inventories
            ]
        }

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    return app


async def start_http_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
):
    """Start the HTTP server with monitoring."""
    configure_logging(debug=debug)
    
    # Import MCP server
    try:
        from awx_mcp_server.mcp_server import create_mcp_server
        mcp_server = create_mcp_server()
    except ImportError:
        logger.warning("Could not import MCP server, using basic server")
        from mcp.server import Server
        mcp_server = Server("awx-mcp-server")
    
    app = create_app(mcp_server)
    
    logger.info("starting_http_server", host=host, port=port)
    
    # Use uvicorn
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
        access_log=True,
    )
    
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    """Entry point for running as a module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AWX MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    asyncio.run(start_http_server(host=args.host, port=args.port, debug=args.debug))
