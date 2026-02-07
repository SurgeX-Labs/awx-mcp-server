/**
 * Logs Provider
 * Displays recent logs in the sidebar
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';

export class LogsProvider implements vscode.TreeDataProvider<LogItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<LogItem | undefined | null | void> = new vscode.EventEmitter<LogItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<LogItem | undefined | null | void> = this._onDidChangeTreeData.event;
    private logs: LogItem[] = [];

    constructor(private serverManager: MCPServerManager) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    addLog(level: string, message: string): void {
        const timestamp = new Date().toLocaleTimeString();
        this.logs.unshift(new LogItem(`[${timestamp}] ${level}`, message));
        if (this.logs.length > 50) {
            this.logs.pop();
        }
        this.refresh();
    }

    getTreeItem(element: LogItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: LogItem): Promise<LogItem[]> {
        if (!element) {
            return this.logs;
        }
        return [];
    }
}

class LogItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private message: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = message;
        this.description = message.substring(0, 50);
    }
}
