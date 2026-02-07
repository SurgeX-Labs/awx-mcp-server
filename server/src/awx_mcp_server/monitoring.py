"""Monitoring and metrics collection for AWX MCP Server."""

import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import structlog

logger = structlog.get_logger(__name__)


# Prometheus metrics
REQUEST_COUNT = Counter(
    'awx_mcp_requests_total',
    'Total number of requests',
    ['tenant_id', 'endpoint', 'method', 'status']
)

REQUEST_DURATION = Histogram(
    'awx_mcp_request_duration_seconds',
    'Request duration in seconds',
    ['tenant_id', 'endpoint', 'method']
)

ACTIVE_CONNECTIONS = Gauge(
    'awx_mcp_active_connections',
    'Number of active connections',
    ['tenant_id']
)

MCP_TOOL_CALLS = Counter(
    'awx_mcp_tool_calls_total',
    'Total number of MCP tool calls',
    ['tenant_id', 'tool_name', 'status']
)

CHAT_INTERACTIONS = Counter(
    'awx_mcp_chat_interactions_total',
    'Total number of chat interactions',
    ['tenant_id', 'source']
)

AWX_API_CALLS = Counter(
    'awx_mcp_awx_api_calls_total',
    'Total number of AWX API calls',
    ['tenant_id', 'endpoint', 'status']
)

ERROR_COUNT = Counter(
    'awx_mcp_errors_total',
    'Total number of errors',
    ['tenant_id', 'error_type']
)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    tenant_id: str
    endpoint: str
    method: str
    status_code: int
    duration: float
    timestamp: datetime
    tool_name: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TenantStats:
    """Statistics for a tenant."""
    tenant_id: str
    total_requests: int = 0
    total_tool_calls: int = 0
    total_chat_interactions: int = 0
    total_errors: int = 0
    active_connections: int = 0
    avg_response_time: float = 0.0
    last_activity: Optional[datetime] = None
    tool_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class MonitoringService:
    """Service for collecting and managing metrics."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self.tenant_stats: Dict[str, TenantStats] = defaultdict(
            lambda: TenantStats(tenant_id="")
        )
        self.request_history: List[RequestMetrics] = []
        self.max_history = 1000  # Keep last 1000 requests
    
    def record_request(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        tool_name: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Record a request metric."""
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
            status=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method
        ).observe(duration)
        
        if error:
            ERROR_COUNT.labels(
                tenant_id=tenant_id,
                error_type=type(error).__name__ if isinstance(error, Exception) else "unknown"
            ).inc()
        
        # Update internal stats
        metrics = RequestMetrics(
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration,
            timestamp=datetime.utcnow(),
            tool_name=tool_name,
            error=error,
        )
        
        self.request_history.append(metrics)
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
        
        # Update tenant stats
        stats = self.tenant_stats[tenant_id]
        stats.tenant_id = tenant_id
        stats.total_requests += 1
        stats.last_activity = datetime.utcnow()
        
        if error:
            stats.total_errors += 1
        
        # Update average response time
        stats.avg_response_time = (
            (stats.avg_response_time * (stats.total_requests - 1) + duration)
            / stats.total_requests
        )
        
        logger.info(
            "request_recorded",
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration,
            tool_name=tool_name,
        )
    
    def record_tool_call(
        self,
        tenant_id: str,
        tool_name: str,
        success: bool = True,
    ):
        """Record an MCP tool call."""
        MCP_TOOL_CALLS.labels(
            tenant_id=tenant_id,
            tool_name=tool_name,
            status="success" if success else "error"
        ).inc()
        
        stats = self.tenant_stats[tenant_id]
        stats.tenant_id = tenant_id
        stats.total_tool_calls += 1
        stats.tool_usage[tool_name] += 1
        
        logger.info(
            "tool_call_recorded",
            tenant_id=tenant_id,
            tool_name=tool_name,
            success=success,
        )
    
    def record_chat_interaction(
        self,
        tenant_id: str,
        source: str = "unknown",
    ):
        """Record a chat interaction."""
        CHAT_INTERACTIONS.labels(
            tenant_id=tenant_id,
            source=source
        ).inc()
        
        stats = self.tenant_stats[tenant_id]
        stats.tenant_id = tenant_id
        stats.total_chat_interactions += 1
        
        logger.info(
            "chat_interaction_recorded",
            tenant_id=tenant_id,
            source=source,
        )
    
    def record_awx_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        status_code: int,
    ):
        """Record an AWX API call."""
        AWX_API_CALLS.labels(
            tenant_id=tenant_id,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
    
    def update_active_connections(self, tenant_id: str, delta: int):
        """Update active connection count."""
        stats = self.tenant_stats[tenant_id]
        stats.tenant_id = tenant_id
        stats.active_connections += delta
        
        ACTIVE_CONNECTIONS.labels(tenant_id=tenant_id).set(stats.active_connections)
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for a tenant."""
        stats = self.tenant_stats.get(tenant_id)
        if not stats:
            return {}
        
        return {
            "tenant_id": stats.tenant_id,
            "total_requests": stats.total_requests,
            "total_tool_calls": stats.total_tool_calls,
            "total_chat_interactions": stats.total_chat_interactions,
            "total_errors": stats.total_errors,
            "active_connections": stats.active_connections,
            "avg_response_time": round(stats.avg_response_time, 3),
            "last_activity": stats.last_activity.isoformat() if stats.last_activity else None,
            "tool_usage": dict(stats.tool_usage),
        }
    
    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all tenants."""
        return [
            self.get_tenant_stats(tenant_id)
            for tenant_id in self.tenant_stats.keys()
        ]
    
    def get_recent_requests(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recent requests."""
        requests = self.request_history
        
        if tenant_id:
            requests = [r for r in requests if r.tenant_id == tenant_id]
        
        requests = requests[-limit:]
        
        return [
            {
                "tenant_id": r.tenant_id,
                "endpoint": r.endpoint,
                "method": r.method,
                "status_code": r.status_code,
                "duration": round(r.duration, 3),
                "timestamp": r.timestamp.isoformat(),
                "tool_name": r.tool_name,
                "error": r.error,
            }
            for r in requests
        ]
    
    def get_prometheus_metrics(self) -> bytes:
        """Get Prometheus metrics in text format."""
        return generate_latest()


# Global monitoring service instance
monitoring_service = MonitoringService()


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        tool_name: Optional[str] = None,
    ):
        """Initialize request timer."""
        self.tenant_id = tenant_id
        self.endpoint = endpoint
        self.method = method
        self.tool_name = tool_name
        self.start_time = None
        self.status_code = 200
        self.error = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        monitoring_service.update_active_connections(self.tenant_id, 1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metrics."""
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.status_code = 500
            self.error = str(exc_val)
        
        monitoring_service.record_request(
            tenant_id=self.tenant_id,
            endpoint=self.endpoint,
            method=self.method,
            status_code=self.status_code,
            duration=duration,
            tool_name=self.tool_name,
            error=self.error,
        )
        
        monitoring_service.update_active_connections(self.tenant_id, -1)
        
        return False  # Don't suppress exceptions
