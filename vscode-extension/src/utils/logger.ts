/**
 * Structured logging utilities for AWX MCP Extension
 * Based on Postman MCP Server logging patterns
 */

import * as vscode from 'vscode';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogContext {
    [key: string]: unknown;
}

export class StructuredLogger {
    private outputChannel: vscode.OutputChannel;
    private logLevel: LogLevel;

    constructor(outputChannel: vscode.OutputChannel, logLevel: LogLevel = 'info') {
        this.outputChannel = outputChannel;
        this.logLevel = logLevel;
    }

    /**
     * Log a message with structured context
     */
    log(level: LogLevel, message: string, context?: LogContext): void {
        if (!this.shouldLog(level)) {
            return;
        }

        const timestamp = new Date().toISOString();
        const contextStr = context ? ` ${JSON.stringify(context)}` : '';
        const logLine = `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`;

        this.outputChannel.appendLine(logLine);

        // Also log to console for debugging
        if (level === 'error') {
            console.error(logLine);
        } else if (level === 'warn') {
            console.warn(logLine);
        } else {
            console.log(logLine);
        }
    }

    debug(message: string, context?: LogContext): void {
        this.log('debug', message, context);
    }

    info(message: string, context?: LogContext): void {
        this.log('info', message, context);
    }

    warn(message: string, context?: LogContext): void {
        this.log('warn', message, context);
    }

    error(message: string, context?: LogContext): void {
        this.log('error', message, context);
    }

    /**
     * Log an error with stack trace
     */
    logError(error: Error, context?: LogContext): void {
        this.error(error.message, {
            ...context,
            stack: error.stack,
            name: error.name,
        });
    }

    /**
     * Set the current log level
     */
    setLogLevel(level: LogLevel): void {
        this.logLevel = level;
        this.info('Log level changed', { newLevel: level });
    }

    /**
     * Check if we should log at this level
     */
    private shouldLog(level: LogLevel): boolean {
        const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
        const currentLevelIndex = levels.indexOf(this.logLevel);
        const messageLevelIndex = levels.indexOf(level);
        return messageLevelIndex >= currentLevelIndex;
    }

    /**
     * Log a function call with timing
     */
    async logAsyncCall<T>(
        functionName: string,
        context: LogContext,
        fn: () => Promise<T>
    ): Promise<T> {
        const startTime = Date.now();
        this.debug(`Starting ${functionName}`, context);

        try {
            const result = await fn();
            const duration = Date.now() - startTime;
            this.debug(`Completed ${functionName}`, { ...context, duration });
            return result;
        } catch (error: any) {
            const duration = Date.now() - startTime;
            this.error(`Failed ${functionName}`, {
                ...context,
                duration,
                error: error.message,
            });
            throw error;
        }
    }
}

/**
 * Format error for user display
 */
export function formatErrorForUser(error: Error, action: string): string {
    const errorType = error.name || 'Error';
    const errorMessage = error.message || 'Unknown error occurred';

    if (errorMessage.includes('ECONNREFUSED')) {
        return `❌ **Connection Failed**\n\nCannot connect to AWX server. Please check:\n- AWX server is running\n- URL is correct\n- Firewall allows connection`;
    }

    if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
        return `❌ **Authentication Failed**\n\nYour credentials are invalid. Please run:\n\`AWX MCP: Configure AWX Environment\``;
    }

    if (errorMessage.includes('404') || errorMessage.includes('Not Found')) {
        return `❌ **Resource Not Found**\n\nThe requested resource doesn't exist on your AWX server.`;
    }

    if (errorMessage.includes('timeout') || errorMessage.includes('ETIMEDOUT')) {
        return `❌ **Request Timeout**\n\nAWX server took too long to respond. Try again or increase timeout in settings.`;
    }

    // Generic error format
    return `❌ **${errorType}**\n\nFailed to ${action}:\n\`\`\`\n${errorMessage}\n\`\`\``;
}

/**
 * Sanitize context for logging (remove sensitive data)
 */
export function sanitizeContext(context: LogContext): LogContext {
    const sanitized: LogContext = {};
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'credential'];

    for (const [key, value] of Object.entries(context)) {
        if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
            sanitized[key] = '***REDACTED***';
        } else if (typeof value === 'object' && value !== null) {
            sanitized[key] = sanitizeContext(value as LogContext);
        } else {
            sanitized[key] = value;
        }
    }

    return sanitized;
}

/**
 * Create a logger instance from VS Code configuration
 */
export function createLoggerFromConfig(
    outputChannel: vscode.OutputChannel
): StructuredLogger {
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const logLevel = config.get<LogLevel>('logLevel', 'info');
    return new StructuredLogger(outputChannel, logLevel);
}
