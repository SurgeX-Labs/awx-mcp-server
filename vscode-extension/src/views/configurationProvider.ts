/**
 * Configuration Provider
 * Manages AWX instance configurations with connection testing
 */

import * as vscode from 'vscode';
import * as path from 'path';

export interface AWXInstance {
    id: string;
    name: string;
    url: string;
    username?: string;
    verifySSL: boolean;
    isDefault: boolean;
    lastConnected?: string;
    status?: 'connected' | 'disconnected' | 'error' | 'testing';
    version?: string;
}

export class ConfigurationProvider implements vscode.TreeDataProvider<ConfigItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<ConfigItem | undefined | null | void> = new vscode.EventEmitter<ConfigItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ConfigItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private instances: AWXInstance[] = [];
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.loadInstances();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ConfigItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: ConfigItem): Promise<ConfigItem[]> {
        if (!element) {
            // Root level - show instances and actions
            const items: ConfigItem[] = [];

            if (this.instances.length === 0) {
                items.push(new ConfigItem(
                    'No AWX instances configured',
                    'Click + to add an instance',
                    vscode.TreeItemCollapsibleState.None,
                    'info'
                ));
            } else {
                for (const instance of this.instances) {
                    items.push(new ConfigItem(
                        instance.name,
                        instance.url,
                        vscode.TreeItemCollapsibleState.Collapsed,
                        'instance',
                        instance
                    ));
                }
            }

            return items;
        } else if (element.contextValue === 'instance' && element.instance) {
            // Show instance details
            const instance = element.instance;
            return [
                new ConfigItem('URL', instance.url, vscode.TreeItemCollapsibleState.None, 'detail'),
                new ConfigItem('Username', instance.username || 'Not configured', vscode.TreeItemCollapsibleState.None, 'detail'),
                new ConfigItem('SSL Verification', instance.verifySSL ? 'Enabled' : 'Disabled', vscode.TreeItemCollapsibleState.None, 'detail'),
                new ConfigItem('Status', instance.status || 'unknown', vscode.TreeItemCollapsibleState.None, 'status'),
                new ConfigItem('Version', instance.version || 'Unknown', vscode.TreeItemCollapsibleState.None, 'detail'),
                new ConfigItem('Default', instance.isDefault ? 'Yes' : 'No', vscode.TreeItemCollapsibleState.None, 'detail')
            ];
        }

        return [];
    }

    private loadInstances(): void {
        const stored = this.context.globalState.get<AWXInstance[]>('awx.instances', []);
        this.instances = stored;
    }

    async saveInstances(): Promise<void> {
        await this.context.globalState.update('awx.instances', this.instances);
        this.refresh();
    }

    async addInstance(instance: AWXInstance): Promise<void> {
        this.instances.push(instance);
        await this.saveInstances();
    }

    async removeInstance(id: string): Promise<void> {
        this.instances = this.instances.filter(i => i.id !== id);
        await this.saveInstances();
    }

    async updateInstance(id: string, updates: Partial<AWXInstance>): Promise<void> {
        const instance = this.instances.find(i => i.id === id);
        if (instance) {
            Object.assign(instance, updates);
            await this.saveInstances();
        }
    }

    async setDefaultInstance(id: string): Promise<void> {
        this.instances.forEach(i => i.isDefault = (i.id === id));
        await this.saveInstances();
    }

    getInstances(): AWXInstance[] {
        return this.instances;
    }

    getDefaultInstance(): AWXInstance | undefined {
        return this.instances.find(i => i.isDefault);
    }

    getInstanceById(id: string): AWXInstance | undefined {
        return this.instances.find(i => i.id === id);
    }
}

export class ConfigItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly value: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly instance?: AWXInstance
    ) {
        super(label, collapsibleState);
        
        if (contextValue === 'instance') {
            this.description = value;
            this.tooltip = `${label}\n${value}`;
            
            // Set icon based on status
            const status = instance?.status || 'disconnected';
            switch (status) {
                case 'connected':
                    this.iconPath = new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'));
                    break;
                case 'disconnected':
                    this.iconPath = new vscode.ThemeIcon('circle-outline');
                    break;
                case 'error':
                    this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
                    break;
                case 'testing':
                    this.iconPath = new vscode.ThemeIcon('sync~spin');
                    break;
            }

            // Add context menu commands
            this.contextValue = 'awx-instance';
        } else if (contextValue === 'status') {
            this.description = value;
            const statusIcon = value === 'connected' ? 'pass' : 'circle-outline';
            this.iconPath = new vscode.ThemeIcon(statusIcon);
        } else if (contextValue === 'detail') {
            this.description = value;
            this.iconPath = new vscode.ThemeIcon('info');
        } else if (contextValue === 'info') {
            this.description = value;
            this.iconPath = new vscode.ThemeIcon('info', new vscode.ThemeColor('editorInfo.foreground'));
        }
    }
}
