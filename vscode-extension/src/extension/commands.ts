/**
 * Command registration and handlers
 */

import * as vscode from 'vscode';
import { MCPServerManager } from '../mcpServerManager';
import { ConfigurationProvider } from '../views/configurationProvider';
import { ConfigurationWebview } from '../views/configurationWebview';
import { ConnectionStatusProvider } from '../views/connectionStatusProvider';
import { configureMcpServer } from './mcpConfiguration';
import { setupDependencies } from './dependencies';
import { executePythonCommand } from './pythonExecutor';
import { getJobTemplatesHtml, getMetricsHtml } from './htmlGenerators';

export function registerCommands(
    context: vscode.ExtensionContext,
    serverManager: MCPServerManager,
    configProvider: ConfigurationProvider,
    configWebview: ConfigurationWebview,
    connectionStatusProvider: ConnectionStatusProvider,
    outputChannel: vscode.OutputChannel
): void {
    
    // Server Management Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.start', async () => {
            try {
                outputChannel.show();
                await serverManager.start();
            } catch (error: any) {
                outputChannel.appendLine(`Error starting server: ${error.message}`);
                vscode.window.showErrorMessage(`Failed to start AWX MCP Server: ${error.message}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.stop', async () => {
            try {
                await serverManager.stop();
                vscode.window.showInformationMessage('AWX MCP Server stopped');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to stop AWX MCP Server: ${error.message}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.restart', async () => {
            try {
                outputChannel.show();
                await serverManager.restart();
                vscode.window.showInformationMessage('AWX MCP Server restarted');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to restart AWX MCP Server: ${error.message}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.status', async () => {
            const config = vscode.workspace.getConfiguration();
            const mcpServers = config.get<{[key: string]: any}>('github.copilot.chat.mcpServers') || {};
            const isConfigured = !!mcpServers['awx-mcp'];
            const instances = configProvider.getInstances();
            const awxConfig = vscode.workspace.getConfiguration('awx-mcp');
            
            const message = `AWX MCP Extension Status:

GitHub Copilot Integration: ${isConfigured ? '\u2713 Configured' : '\u2717 Not Configured'}
AWX Instances: ${instances.length}
Default Instance: ${configProvider.getDefaultInstance()?.name || 'None'}

Configuration:
Python: ${awxConfig.get('pythonPath') || 'python'}
Log Level: ${awxConfig.get('logLevel') || 'info'}

${!isConfigured ? '\n\u26a0 Run \"AWX MCP: Configure for Copilot Chat\" to enable' : ''}`;

            const buttons = isConfigured 
                ? ['View Settings', 'Reconfigure', 'Open Chat']
                : ['Configure Now', 'View Documentation'];
                
            vscode.window.showInformationMessage(message, { modal: true }, ...buttons)
                .then(selection => {
                    if (selection === 'Configure Now' || selection === 'Reconfigure') {
                        vscode.commands.executeCommand('awx-mcp.configureCopilot');
                    } else if (selection === 'View Settings') {
                        vscode.commands.executeCommand('workbench.action.openSettings', 'github.copilot.chat.mcpServers');
                    } else if (selection === 'Open Chat') {
                        vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
                    } else if (selection === 'View Documentation') {
                        outputChannel.show();
                    }
                });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.configureCopilot', async () => {
            await configureMcpServer(outputChannel);
        })
    );

    // Instance Management Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.addInstance', async () => {
            configWebview.show();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.editInstance', async (item) => {
            if (item && item.instance) {
                configWebview.show(item.instance);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.removeInstance', async (item) => {
            if (item && item.instance) {
                const confirm = await vscode.window.showWarningMessage(
                    `Remove AWX instance "${item.instance.name}"?`,
                    { modal: true },
                    'Remove'
                );
                if (confirm === 'Remove') {
                    await configProvider.removeInstance(item.instance.id);
                    vscode.window.showInformationMessage(`Instance "${item.instance.name}" removed`);
                }
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.testConnection', async (item) => {
            const instance = item?.instance || item;
            if (instance && instance.id) {
                await configProvider.updateInstance(instance.id, { status: 'testing' });
                
                try {
                    const authStatus = await connectionStatusProvider.testAuthentication(instance);
                    
                    if (authStatus.valid) {
                        await configProvider.updateInstance(instance.id, {
                            status: 'connected',
                            lastConnected: new Date().toISOString(),
                            version: '23.0.0'
                        });
                        
                        connectionStatusProvider.refresh();
                        vscode.window.showInformationMessage(`Connected to ${instance.name} successfully - Authentication valid`);
                    } else {
                        await configProvider.updateInstance(instance.id, { status: 'error' });
                        connectionStatusProvider.refresh();
                        vscode.window.showErrorMessage(`Authentication failed for ${instance.name}: ${authStatus.message}`);
                    }
                } catch (error: any) {
                    await configProvider.updateInstance(instance.id, { status: 'error' });
                    connectionStatusProvider.refresh();
                    vscode.window.showErrorMessage(`Failed to connect to ${instance.name}: ${error.message}`);
                }
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.testAuthentication', async (item) => {
            const instance = item?.instance || item;
            if (instance && instance.name) {
                const progressOptions = {
                    location: vscode.ProgressLocation.Notification,
                    title: `Testing authentication for ${instance.name}...`,
                    cancellable: false
                };

                await vscode.window.withProgress(progressOptions, async () => {
                    try {
                        const authStatus = await connectionStatusProvider.testAuthentication(instance);
                        
                        if (authStatus.valid) {
                            vscode.window.showInformationMessage(
                                `✓ Authentication successful for ${instance.name}`,
                                'View Details'
                            ).then(selection => {
                                if (selection === 'View Details') {
                                    outputChannel.show();
                                }
                            });
                        } else {
                            vscode.window.showErrorMessage(
                                `✗ Authentication failed for ${instance.name}: ${authStatus.message}`,
                                'View Logs'
                            ).then(selection => {
                                if (selection === 'View Logs') {
                                    outputChannel.show();
                                }
                            });
                        }
                        
                        connectionStatusProvider.refresh();
                    } catch (error: any) {
                        vscode.window.showErrorMessage(`Error testing authentication: ${error.message}`);
                    }
                });
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.setDefaultInstance', async (item) => {
            if (item && item.instance) {
                await configProvider.setDefaultInstance(item.instance.id);
                vscode.window.showInformationMessage(`"${item.instance.name}" set as default instance`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.refreshInstances', async () => {
            configProvider.refresh();
            connectionStatusProvider.refresh();
        })
    );

    // Tools and Utilities Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.viewLogs', () => {
            outputChannel.show();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.listJobTemplates', async (item) => {
            const instance = item?.instance || configProvider.getDefaultInstance();
            
            if (!instance) {
                vscode.window.showErrorMessage('No AWX instance configured. Please add an instance first.');
                return;
            }

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Fetching job templates from ${instance.name}...`,
                cancellable: false
            }, async () => {
                try {
                    const password = await context.secrets.get(`awx.${instance.id}.password`);
                    const token = await context.secrets.get(`awx.${instance.id}.token`);
                    
                    if (!password && !token) {
                        vscode.window.showErrorMessage(`No credentials found for ${instance.name}. Please configure credentials first.`);
                        return;
                    }

                    const result = await executePythonCommand(
                        context.extensionPath,
                        `list_templates`,
                        outputChannel,
                        true
                    );

                    const parsed = JSON.parse(result);
                    if (parsed.success && parsed.templates) {
                        const panel = vscode.window.createWebviewPanel(
                            'awxJobTemplates',
                            `Job Templates - ${instance.name}`,
                            vscode.ViewColumn.One,
                            { enableScripts: true }
                        );
                        panel.webview.html = getJobTemplatesHtml(parsed.templates);
                    } else {
                        vscode.window.showErrorMessage(`Failed to fetch job templates: ${parsed.error || 'Unknown error'}`);
                    }
                } catch (error: any) {
                    outputChannel.appendLine(`Error listing job templates: ${error.message}`);
                    vscode.window.showErrorMessage(`Error: ${error.message}`);
                }
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.viewMetrics', async () => {
            const metrics = await serverManager.getMetrics();
            const panel = vscode.window.createWebviewPanel(
                'awxMcpMetrics',
                'AWX MCP Metrics',
                vscode.ViewColumn.One,
                {}
            );
            panel.webview.html = getMetricsHtml(metrics);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('awx-mcp.setupDependencies', async () => {
            await setupDependencies(context.extensionPath, outputChannel);
        })
    );
}
