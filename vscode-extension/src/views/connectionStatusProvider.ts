/**
 * Connection Status Provider
 * Shows real-time connection status and authentication for AWX instances
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';
import { ConfigurationProvider, AWXInstance } from './configurationProvider';

interface AuthenticationStatus {
    valid: boolean;
    message: string;
    tokenExpiry?: string;
    username?: string;
}

export class ConnectionStatusProvider implements vscode.TreeDataProvider<StatusItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<StatusItem | undefined | null | void> = new vscode.EventEmitter<StatusItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<StatusItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private configProvider: ConfigurationProvider;
    private refreshTimer?: NodeJS.Timeout;
    private authStatusCache: Map<string, AuthenticationStatus> = new Map();
    private outputChannel: vscode.OutputChannel;
    private context: vscode.ExtensionContext;

    constructor(
        configProvider: ConfigurationProvider,
        context: vscode.ExtensionContext,
        outputChannel?: vscode.OutputChannel
    ) {
        this.configProvider = configProvider;
        this.context = context;
        this.outputChannel = outputChannel || vscode.window.createOutputChannel('AWX MCP Connection Status');
        
        // Auto-refresh status every 30 seconds if enabled
        const config = vscode.workspace.getConfiguration('awx-mcp');
        if (config.get('autoRefreshStatus', true)) {
            this.startAutoRefresh();
        }
    }

    async testAuthentication(instance: AWXInstance): Promise<AuthenticationStatus> {
        this.outputChannel.appendLine(`Testing authentication for ${instance.name}...`);
        
        try {
            // Get credentials from VS Code's secret storage
            const secrets = this.context.secrets;
            let password = await secrets.get(`awx.${instance.id}.password`);
            let token = await secrets.get(`awx.${instance.id}.token`);
            
            // Check old format for backward compatibility
            if (!password && !token) {
                password = await secrets.get(`awx.password.${instance.id}`);
                token = await secrets.get(`awx.token.${instance.id}`);
                
                // If found in old format, migrate to new format
                if (password) {
                    await secrets.store(`awx.${instance.id}.password`, password);
                    await secrets.delete(`awx.password.${instance.id}`);
                }
                if (token) {
                    await secrets.store(`awx.${instance.id}.token`, token);
                    await secrets.delete(`awx.token.${instance.id}`);
                }
            }
            
            if (!password && !token) {
                const authStatus: AuthenticationStatus = {
                    valid: false,
                    message: 'No credentials found. Please configure credentials for this instance.'
                };
                this.authStatusCache.set(instance.id, authStatus);
                this.outputChannel.appendLine(`✗ No credentials for ${instance.name} (ID: ${instance.id})`);
                return authStatus;
            }

            this.outputChannel.appendLine(`Found credentials for ${instance.name}: ${password ? 'password' : token ? 'token' : 'none'}`);

            // Test connection with credentials
            const result = await this.executeMcpCommand('test_connection', {
                url: instance.url,
                username: instance.username || 'admin',
                password: password,
                token: token,
                verify_ssl: instance.verifySSL
            });

            if (result.success) {
                const authStatus: AuthenticationStatus = {
                    valid: true,
                    message: 'Authentication successful',
                    username: result.username || instance.username
                };
                
                this.authStatusCache.set(instance.id, authStatus);
                this.outputChannel.appendLine(`✓ Authentication successful for ${instance.name}`);
                
                return authStatus;
            } else {
                const authStatus: AuthenticationStatus = {
                    valid: false,
                    message: result.error || 'Authentication failed'
                };
                
                this.authStatusCache.set(instance.id, authStatus);
                this.outputChannel.appendLine(`✗ Authentication failed for ${instance.name}: ${authStatus.message}`);
                
                return authStatus;
            }
        } catch (error: any) {
            this.outputChannel.appendLine(`Error testing authentication: ${error.message}`);
            
            const authStatus: AuthenticationStatus = {
                valid: false,
                message: error.message || 'Connection error'
            };
            
            this.authStatusCache.set(instance.id, authStatus);
            return authStatus;
        }
    }

    private async executeMcpCommand(command: string, args: any): Promise<any> {
        return new Promise((resolve, reject) => {
            const config = vscode.workspace.getConfiguration('awx-mcp');
            const pythonPath = config.get<string>('pythonPath') || 'python';
            
            const scriptContent = `
import sys
import json
from uuid import uuid4

from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import EnvironmentConfig
import asyncio

async def test_connection(url, username, password, token, verify_ssl):
    try:
        # Create a temporary environment object
        env = EnvironmentConfig(
            env_id=uuid4(),
            name="temp-test",
            base_url=url,
            verify_ssl=verify_ssl
        )
        
        # Determine credential type and create client
        if token:
            client = CompositeAWXClient(env, "token", token, is_token=True)
            username_display = "token"
        elif password:
            client = CompositeAWXClient(env, username, password, is_token=False)
            username_display = username
        else:
            return {"success": False, "error": "No credentials provided"}
        
        # Test connection
        async with client:
            result = await client.test_connection()
        
        return {
            "success": True,
            "username": username_display,
            "version": "connected"
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)}\\n{traceback.format_exc()}"}

args = json.loads(r'''${JSON.stringify(args)}''')
result = asyncio.run(test_connection(
    args.get('url'),
    args.get('username'),
    args.get('password'),
    args.get('token'),
    args.get('verify_ssl', True)
))
print(json.dumps(result))
`;

            const tempFile = require('os').tmpdir() + '\\awx_test_' + Date.now() + '.py';
            require('fs').writeFileSync(tempFile, scriptContent);

            const proc = child_process.spawn(pythonPath, [tempFile], {
                timeout: 30000
            });

            let output = '';
            let errorOutput = '';

            proc.stdout?.on('data', (data) => {
                output += data.toString();
            });

            proc.stderr?.on('data', (data) => {
                errorOutput += data.toString();
            });

            proc.on('close', (code) => {
                require('fs').unlinkSync(tempFile);
                
                if (code === 0) {
                    try {
                        const result = JSON.parse(output);
                        resolve(result);
                    } catch (e) {
                        reject(new Error(`Failed to parse output: ${output}`));
                    }
                } else {
                    reject(new Error(errorOutput || 'Process exited with error'));
                }
            });

            proc.on('error', (error) => {
                try {
                    require('fs').unlinkSync(tempFile);
                } catch (e) {
                    // Ignore cleanup errors
                }
                reject(error);
            });
        });
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    startAutoRefresh(): void {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        this.refreshTimer = setInterval(() => this.refresh(), 30000); // 30 seconds
    }

    stopAutoRefresh(): void {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = undefined;
        }
    }

    getTreeItem(element: StatusItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: StatusItem): Promise<StatusItem[]> {
        if (!element) {
            const instances = this.configProvider.getInstances();
            
            if (instances.length === 0) {
                return [
                    new StatusItem(
                        'No instances configured',
                        'Add an AWX instance to get started',
                        'none',
                        'empty'
                    )
                ];
            }

            const items: StatusItem[] = [];

            // Overall status summary
            const connectedCount = instances.filter(i => i.status === 'connected').length;
            const authenticatedCount = Array.from(this.authStatusCache.values()).filter(s => s.valid).length;
            const totalCount = instances.length;
            
            items.push(new StatusItem(
                'Overall Status',
                `${connectedCount}/${totalCount} connected, ${authenticatedCount}/${totalCount} authenticated`,
                connectedCount === totalCount && authenticatedCount === totalCount ? 'connected' : 'partial',
                'summary'
            ));

            // Individual instance statuses
            for (const instance of instances) {
                const authStatus = this.authStatusCache.get(instance.id);
                const statusDesc = this.getStatusDescription(instance, authStatus);
                
                items.push(new StatusItem(
                    instance.name,
                    statusDesc,
                    this.getOverallStatus(instance, authStatus),
                    'instance-status',
                    instance,
                    authStatus
                ));
            }

            return items;
        } else if (element.instance) {
            // Show instance details
            const instance = element.instance;
            const authStatus = element.authStatus;
            
            const details: StatusItem[] = [
                new StatusItem('URL', instance.url, 'info', 'detail'),
                new StatusItem('Connection Status', instance.status || 'unknown', instance.status || 'disconnected', 'detail'),
            ];

            if (authStatus) {
                details.push(new StatusItem(
                    'Authentication',
                    authStatus.valid ? '✓ Valid' : '✗ Invalid',
                    authStatus.valid ? 'connected' : 'error',
                    'detail'
                ));
                
                if (!authStatus.valid) {
                    details.push(new StatusItem(
                        'Auth Error',
                        authStatus.message,
                        'error',
                        'detail'
                    ));
                }
                
                if (authStatus.username) {
                    details.push(new StatusItem(
                        'User',
                        authStatus.username,
                        'info',
                        'detail'
                    ));
                }
            } else {
                details.push(new StatusItem(
                    'Authentication',
                    'Not tested',
                    'testing',
                    'detail'
                ));
            }

            details.push(
                new StatusItem('Version', instance.version || 'Unknown', 'info', 'detail'),
                new StatusItem('Last Connected', instance.lastConnected || 'Never', 'info', 'detail'),
                new StatusItem('SSL Verification', instance.verifySSL ? 'Enabled' : 'Disabled', 'info', 'detail')
            );

            return details;
        }

        return [];
    }

    private getOverallStatus(instance: AWXInstance, authStatus?: AuthenticationStatus): string {
        if (authStatus && !authStatus.valid) {
            return 'error';
        }
        return instance.status || 'disconnected';
    }

    private getStatusDescription(instance: AWXInstance, authStatus?: AuthenticationStatus): string {
        if (authStatus === undefined) {
            return '⟳ Checking...';
        }
        
        if (!authStatus.valid) {
            return '✗ Authentication Failed';
        }
        
        switch (instance.status) {
            case 'connected':
                return '● Connected & Authenticated';
            case 'disconnected':
                return '○ Disconnected';
            case 'error':
                return '✗ Connection Error';
            case 'testing':
                return '⟳ Testing...';
            default:
                return '? Unknown';
        }
    }

    dispose(): void {
        this.stopAutoRefresh();
    }
}

class StatusItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly value: string,
        private status: string,
        public readonly contextValue: string,
        public readonly instance?: AWXInstance,
        public readonly authStatus?: AuthenticationStatus
    ) {
        super(
            label,
            contextValue === 'instance-status' || contextValue === 'summary'
                ? vscode.TreeItemCollapsibleState.Collapsed
                : vscode.TreeItemCollapsibleState.None
        );

        this.description = value;
        this.tooltip = `${label}: ${value}`;

        // Set icon based on status
        switch (status) {
            case 'connected':
                this.iconPath = new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'));
                break;
            case 'disconnected':
                this.iconPath = new vscode.ThemeIcon('circle-outline', new vscode.ThemeColor('descriptionForeground'));
                break;
            case 'error':
                this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
                break;
            case 'testing':
                this.iconPath = new vscode.ThemeIcon('sync~spin');
                break;
            case 'partial':
                this.iconPath = new vscode.ThemeIcon('warning', new vscode.ThemeColor('editorWarning.foreground'));
                break;
            case 'info':
                this.iconPath = new vscode.ThemeIcon('info');
                break;
            default:
                this.iconPath = new vscode.ThemeIcon('circle-outline');
        }

        // Add command to test authentication for instance items
        if (contextValue === 'instance-status' && instance) {
            this.command = {
                command: 'awx-mcp.testAuthentication',
                title: 'Test Authentication',
                arguments: [instance]
            };
        }
    }
}
