/**
 * Environment Tree Provider
 * Displays AWX environments in the sidebar
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';

export class EnvironmentTreeProvider implements vscode.TreeDataProvider<EnvironmentItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<EnvironmentItem | undefined | null | void> = new vscode.EventEmitter<EnvironmentItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<EnvironmentItem | undefined | null | void> = this._onDidChangeTreeData.event;

    constructor(private serverManager: MCPServerManager) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: EnvironmentItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: EnvironmentItem): Promise<EnvironmentItem[]> {
        if (!element) {
            // Root level - return environments
            return [
                new EnvironmentItem('Production', 'https://awx.example.com', true),
                new EnvironmentItem('Staging', 'https://awx-staging.example.com', false),
                new EnvironmentItem('Development', 'http://localhost:30080', false)
            ];
        }
        return [];
    }
}

class EnvironmentItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private url: string,
        private isActive: boolean
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = url;
        this.description = isActive ? '(active)' : '';
        this.iconPath = isActive 
            ? new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('terminal.ansiGreen'))
            : new vscode.ThemeIcon('circle-outline');
    }
}
