/**
 * Shared types for MCP server management
 */

export interface ServerStatus {
    running: boolean;
    pid?: number;
    uptime?: string;
    requestCount?: number;
    errorCount?: number;
}

export interface ServerMetrics extends ServerStatus {
    avgResponseTime?: string;
}
