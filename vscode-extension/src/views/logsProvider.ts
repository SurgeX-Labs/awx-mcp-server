/**
 * Logs Provider
 * Displays recent logs and request traces in the sidebar
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';

type LogLevel = 'info' | 'warn' | 'error' | 'debug' | 'request' | 'response';

interface LogEntry {
    timestamp: Date;
    level: LogLevel;
    message: string;
    details?: any;
}

export class LogsProvider implements vscode.TreeDataProvider<LogItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<LogItem | undefined | null | void> = new vscode.EventEmitter<LogItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<LogItem | undefined | null | void> = this._onDidChangeTreeData.event;
    private logs: LogEntry[] = [];
    private maxLogs = 100;

    constructor(private serverManager: MCPServerManager) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    /**
     * Add a log entry
     */
    addLog(level: LogLevel, message: string, details?: any): void {
        const entry: LogEntry = {
            timestamp: new Date(),
            level,
            message,
            details
        };
        
        this.logs.unshift(entry);
        
        // Keep only last N logs
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(0, this.maxLogs);
        }
        
        this.refresh();
    }
    
    /**
     * Log an MCP request
     */
    logRequest(tool: string, args: any): void {
        this.addLog('request', `MCP Request: ${tool}`, args);
    }
    
    /**
     * Log an MCP response
     */
    logResponse(tool: string, success: boolean, duration: number): void {
        const message = `MCP Response: ${tool} (${duration}ms) - ${success ? 'Success' : 'Failed'}`;
        this.addLog('response', message, { tool, success, duration });
    }
    
    /**
     * Clear all logs
     */
    clearLogs(): void {
        this.logs = [];
        this.refresh();
    }

    getTreeItem(element: LogItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: LogItem): Promise<LogItem[]> {
        if (!element) {
            if (this.logs.length === 0) {
                return [new LogItem({
                    timestamp: new Date(),
                    level: 'info',
                    message: 'No logs yet. Logs will appear here when the server starts.'
                })];
            }
            return this.logs.map(log => new LogItem(log));
        }
        return [];
    }
}

class LogItem extends vscode.TreeItem {
    constructor(private logEntry: LogEntry) {
        super(LogItem.formatLabel(logEntry), vscode.TreeItemCollapsibleState.None);
        
        // Set icon based on log level
        switch (logEntry.level) {
            case 'error':
                this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'));
                break;
            case 'warn':
                this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('notificationsWarningIcon.foreground'));
                break;
            case 'request':
                this.iconPath = new vscode.ThemeIcon('arrow-right', new vscode.ThemeColor('charts.blue'));
                break;
            case 'response':
                this.iconPath = new vscode.ThemeIcon('arrow-left', new vscode.ThemeColor('charts.green'));
                break;
            case 'debug':
                this.iconPath = new vscode.ThemeIcon('bug');
                break;
            default:
                this.iconPath = new vscode.ThemeIcon('info');
        }
        
        // Set description (truncated message)
        this.description = logEntry.message.substring(0, 60);
        if (logEntry.message.length > 60) {
            this.description += '...';
        }
        
        // Set tooltip with full details
        this.tooltip = this.buildTooltip(logEntry);
    }
    
    private static formatLabel(entry: LogEntry): string {
        const time = entry.timestamp.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const levelEmoji = {
            'info': 'ℹ️',
            'warn': '⚠️',
            'error': '❌',
            'debug': '🔍',
            'request': '➡️',
            'response': '⬅️'
        };
        
        return `${time} ${levelEmoji[entry.level] || ''}`;
    }
    
    private buildTooltip(entry: LogEntry): string {
        let tooltip = `[${entry.timestamp.toLocaleString()}] ${entry.level.toUpperCase()}\n`;
        tooltip += `${entry.message}\n`;
        
        if (entry.details) {
            tooltip += `\nDetails:\n${JSON.stringify(entry.details, null, 2)}`;
        }
        
        return tooltip;
    }
}
