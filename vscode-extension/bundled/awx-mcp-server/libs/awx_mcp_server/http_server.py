"""HTTP server implementation for remote MCP access with SSE transport."""

import asyncio
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel

from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.utils import configure_logging, get_logger

logger = get_logger(__name__)

# API Key storage (in production, use database)
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
    """Create FastAPI application with MCP server."""
    app = FastAPI(
        title="AWX MCP Server",
        description="Industrial-grade MCP server for AWX automation",
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

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "AWX MCP Server",
            "version": "1.0.0",
            "status": "running",
            "transport": "http",
            "endpoints": {
                "messages": "/messages",
                "health": "/health",
                "metrics": "/metrics",
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
        }

    @app.get("/metrics")
    async def metrics(tenant_info: dict = Depends(verify_api_key)):
        """Metrics endpoint (requires authentication)."""
        config_manager = ConfigManager(tenant_id=tenant_info["tenant_id"])
        envs = config_manager.list_environments()
        
        return {
            "tenant_id": tenant_info["tenant_id"],
            "environments_count": len(envs),
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
        # Simple admin check (replace with proper auth in production)
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
        """
        Handle MCP messages via POST.
        This is a simpler alternative to SSE for MCP communication.
        """
        logger.info("message_received", tenant_id=tenant_info["tenant_id"])
        
        try:
            # Get the message from the request body
            message = await request.json()
            
            # Here you would process the MCP message through your server
            # For now, return a simple response
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "status": "received",
                    "tenant_id": tenant_info["tenant_id"]
                }
            }
        except Exception as e:
            logger.error("message_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )

    return app


async def start_http_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
):
    """Start the HTTP server."""
    configure_logging(debug=debug)
    
    # Import server here to avoid circular import
    from awx_mcp_server.server import create_mcp_server
    
    mcp_server = create_mcp_server()
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
