/**
 * Metrics Provider
 * Displays server metrics in the sidebar
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';

export class MetricsProvider implements vscode.TreeDataProvider<MetricItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<MetricItem | undefined | null | void> = new vscode.EventEmitter<MetricItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<MetricItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private serverManager: MCPServerManager) {
        // Refresh metrics every 5 seconds
        setInterval(() => this.refresh(), 5000);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MetricItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: MetricItem): Promise<MetricItem[]> {
        if (!element) {
            const status = this.serverManager.getStatus();
            return [
                new MetricItem('Status', status.running ? 'Running' : 'Stopped'),
                new MetricItem('Uptime', status.uptime || 'N/A'),
                new MetricItem('Requests', status.requestCount?.toString() || '0'),
                new MetricItem('Errors', status.errorCount?.toString() || '0')
            ];
        }
        return [];
    }
}

class MetricItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private value: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = value;
    }
}
