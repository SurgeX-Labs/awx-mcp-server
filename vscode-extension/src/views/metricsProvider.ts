/**
 * Metrics Provider
 * Displays server metrics and request statistics in the sidebar
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';

interface RequestStats {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    averageResponseTime: number;
    lastRequestTime?: Date;
}

export class MetricsProvider implements vscode.TreeDataProvider<MetricItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MetricItem | undefined | null | void> = new vscode.EventEmitter<MetricItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MetricItem | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private requestStats: RequestStats = {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTime: 0
    };

    constructor(private serverManager: MCPServerManager) {
        // Refresh metrics every 5 seconds
        setInterval(() => this.refresh(), 5000);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
    
    /**
     * Track a new request
     */
    trackRequest(success: boolean, responseTime: number): void {
        this.requestStats.totalRequests++;
        if (success) {
            this.requestStats.successfulRequests++;
        } else {
            this.requestStats.failedRequests++;
        }
        
        // Update running average
        const prevTotal = this.requestStats.averageResponseTime * (this.requestStats.totalRequests - 1);
        this.requestStats.averageResponseTime = (prevTotal + responseTime) / this.requestStats.totalRequests;
        
        this.requestStats.lastRequestTime = new Date();
        this.refresh();
    }

    getTreeItem(element: MetricItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: MetricItem): Promise<MetricItem[]> {
        if (!element) {
            const status = this.serverManager.getStatus();
            
            const statusIcon = status.running ? '$(check)' : '$(x)';
            const uptimeIcon = '$(clock)';
            const requestIcon = '$(symbol-event)';
            const errorIcon = '$(error)';
            const timeIcon = '$(dashboard)';
            
            return [
                new MetricItem(
                    `${statusIcon} Server Status`,
                    status.running ? 'Running' : 'Stopped',
                    'Server process status'
                ),
                new MetricItem(
                    `${uptimeIcon} Uptime`,
                    status.uptime || 'N/A',
                    'Server uptime'
                ),
                new MetricItem(
                    `${requestIcon} Total Requests`,
                    this.requestStats.totalRequests.toString(),
                    'Total MCP requests processed'
                ),
                new MetricItem(
                    `$(pass) Successful Requests`,
                    this.requestStats.successfulRequests.toString(),
                    'Successfully completed requests'
                ),
                new MetricItem(
                    `${errorIcon} Failed Requests`,
                    this.requestStats.failedRequests.toString(),
                    'Failed or errored requests'
                ),
                new MetricItem(
                    `${timeIcon} Avg Response Time`,
                    this.requestStats.averageResponseTime > 0 
                        ? `${Math.round(this.requestStats.averageResponseTime)}ms`
                        : 'N/A',
                    'Average request response time'
                ),
                new MetricItem(
                    '$(history) Last Request',
                    this.requestStats.lastRequestTime 
                        ? this.formatTimestamp(this.requestStats.lastRequestTime)
                        : 'N/A',
                    'Time of last request'
                )
            ];
        }
        return [];
    }
    
    private formatTimestamp(date: Date): string {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        
        if (diffSec < 60) {
            return `${diffSec}s ago`;
        } else if (diffMin < 60) {
            return `${diffMin}m ago`;
        } else if (diffHour < 24) {
            return `${diffHour}h ago`;
        } else {
            return date.toLocaleString();
        }
    }
}

class MetricItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private value: string,
        tooltip?: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = value;
        if (tooltip) {
            this.tooltip = tooltip;
        }
    }
}
