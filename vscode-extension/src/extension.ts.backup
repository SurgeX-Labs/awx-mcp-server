/**
 * AWX MCP VS Code Extension
 * 
 * This extension integrates AWX with GitHub Copilot through the Model Context Protocol (MCP).
 * It runs a local MCP server and registers it with GitHub Copilot Chat.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as child_process from 'child_process';
import { MCPServerManager } from './mcpServerManager';
import { ConfigurationProvider } from './views/configurationProvider';
import { ConfigurationWebview } from './views/configurationWebview';
import { ConnectionStatusProvider } from './views/connectionStatusProvider';
import { MetricsProvider } from './views/metricsProvider';
import { LogsProvider } from './views/logsProvider';
import { AWXCopilotChatParticipant } from './copilotChatParticipant';

let serverManager: MCPServerManager;
let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;
let configProvider: ConfigurationProvider;
let configWebview: ConfigurationWebview;
let connectionStatusProvider: ConnectionStatusProvider;
let chatParticipant: AWXCopilotChatParticipant;

export function activate(context: vscode.ExtensionContext) {
    console.log('AWX MCP extension is now active');

    // Create output channel
    outputChannel = vscode.window.createOutputChannel('AWX MCP');
    context.subscriptions.push(outputChannel);

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'awx-mcp.status';
    statusBarItem.text = '$(plug) AWX MCP';
    statusBarItem.tooltip = 'AWX MCP Server for GitHub Copilot';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Check dependencies before configuring MCP
    checkAndSetupDependencies(context).then(success => {
        if (success) {
            // Configure MCP server for Copilot Chat only if dependencies are ready
            configureMcpServer(context).catch(err => {
                outputChannel.appendLine(`Warning: Could not configure MCP server: ${err.message}`);
            });
        } else {
            statusBarItem.text = '$(warning) AWX MCP: Setup Required';
            statusBarItem.tooltip = 'Click to setup AWX MCP dependencies';
            vscode.window.showWarningMessage(
                'AWX MCP requires Python dependencies. Click "Setup Now" to install.',
                'Setup Now',
                'View Requirements',
                'Dismiss'
            ).then(selection => {
                if (selection === 'Setup Now') {
                    vscode.commands.executeCommand('awx-mcp.setupDependencies');
                } else if (selection === 'View Requirements') {
                    outputChannel.show();
                }
            });
        }
    });

    // Initialize server manager (for manual control)
    serverManager = new MCPServerManager(context, outputChannel, statusBarItem);

    // Initialize configuration provider
    configProvider = new ConfigurationProvider(context);
    vscode.window.registerTreeDataProvider('awx-mcp-instances', configProvider);

    // Initialize configuration webview
    configWebview = new ConfigurationWebview(context, configProvider);

    // Initialize connection status provider
    connectionStatusProvider = new ConnectionStatusProvider(configProvider, context, outputChannel);
    vscode.window.registerTreeDataProvider('awx-mcp-connection-status', connectionStatusProvider);

    // Register metrics and logs providers
    const metricsProvider = new MetricsProvider(serverManager);
    vscode.window.registerTreeDataProvider('awx-mcp-metrics', metricsProvider);

    const logsProvider = new LogsProvider(serverManager);
    vscode.window.registerTreeDataProvider('awx-mcp-logs', logsProvider);

    // Register Copilot Chat Participant for intelligent tool invocation
    try {
        chatParticipant = new AWXCopilotChatParticipant(context, outputChannel);
        const participantDisposable = chatParticipant.register();
        
        if (participantDisposable) {
            context.subscriptions.push(participantDisposable);
            
            // Load available tools
            chatParticipant.updateTools().catch(err => {
                outputChannel.appendLine(`Note: Could not load tools metadata: ${err.message}`);
            });
            
            outputChannel.appendLine('✓ AWX Copilot Chat Participant initialized');
            outputChannel.appendLine('  You can now use @awx in Copilot Chat to interact with AWX');
        }
    } catch (error: any) {
        outputChannel.appendLine(`Note: Copilot Chat Participant not available: ${error.message}`);
        outputChannel.appendLine('  This feature requires GitHub Copilot Chat extension');
    }

    // Register commands
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
            // Show MCP configuration status
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
            await configureMcpServer(context);
        })
    );

    // AWX Instance Management Commands
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
            // Extract instance from tree item (StatusItem or ConfigItem)
            const instance = item?.instance || item;
            if (instance && instance.id) {
                await configProvider.updateInstance(instance.id, { status: 'testing' });
                
                try {
                    // Test authentication first
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
            // Extract instance from tree item (StatusItem or ConfigItem)
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
                    // Get credentials
                    const password = await context.secrets.get(`awx.${instance.id}.password`);
                    const token = await context.secrets.get(`awx.${instance.id}.token`);
                    
                    if (!password && !token) {
                        vscode.window.showErrorMessage(`No credentials found for ${instance.name}. Please configure credentials first.`);
                        return;
                    }

                    // Execute Python script to fetch templates
                    const result = await executePythonCommand('list_templates', {
                        url: instance.url,
                        username: instance.username || 'admin',
                        password: password,
                        token: token,
                        verify_ssl: instance.verifySSL
                    });

                    if (result.success && result.templates) {
                        // Create webview to display templates
                        const panel = vscode.window.createWebviewPanel(
                            'awxJobTemplates',
                            `Job Templates - ${instance.name}`,
                            vscode.ViewColumn.One,
                            { enableScripts: true }
                        );
                        panel.webview.html = getJobTemplatesHtml(result.templates, instance.name);
                    } else {
                        vscode.window.showErrorMessage(`Failed to fetch job templates: ${result.error || 'Unknown error'}`);
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
            await setupPythonDependencies(context);
        })
    );

    // Note: Auto-start is not needed when using VS Code's MCP system
    // VS Code will manage the MCP server lifecycle automatically
}

/**
 * Check if Python dependencies are installed
 */
async function checkAndSetupDependencies(context: vscode.ExtensionContext): Promise<boolean> {
    try {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = config.get<string>('pythonPath') || 'python';
        
        outputChannel.appendLine('Checking Python dependencies...');
        
        // Check if Python is available
        try {
            const pythonVersion = await execCommand(pythonPath, ['--version']);
            outputChannel.appendLine(`✓ Python found: ${pythonVersion.trim()}`);
        } catch (error) {
            outputChannel.appendLine('✗ Python not found in PATH');
            outputChannel.appendLine('Please install Python 3.10 or later from https://python.org');
            return false;
        }
        
        // Check if awx-mcp-server package is installed
        try {
            await execCommand(pythonPath, ['-m', 'awx_mcp_server', '--version']);
            outputChannel.appendLine('✓ AWX MCP Server package is installed');
            return true;
        } catch (error) {
            outputChannel.appendLine('✗ AWX MCP Server package not installed');
            outputChannel.appendLine('');
            outputChannel.appendLine('Required Python packages:');
            outputChannel.appendLine('  • awx-mcp-server (bundled with extension)');
            outputChannel.appendLine('  • mcp >= 0.9.0');
            outputChannel.appendLine('  • httpx >= 0.27.0');
            outputChannel.appendLine('  • pydantic >= 2.0.0');
            outputChannel.appendLine('  • keyring >= 25.0.0');
            outputChannel.appendLine('  • and more...');
            return false;
        }
    } catch (error: any) {
        outputChannel.appendLine(`Error checking dependencies: ${error.message}`);
        return false;
    }
}

/**
 * Setup Python dependencies including awx-mcp-server
 */
async function setupPythonDependencies(context: vscode.ExtensionContext): Promise<void> {
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    const bundledServerPath = context.extensionPath + '\\\\bundled\\\\awx-mcp-server';
    
    outputChannel.show();
    outputChannel.appendLine('');
    outputChannel.appendLine('='.repeat(60));
    outputChannel.appendLine('Installing AWX MCP Server Dependencies');
    outputChannel.appendLine('='.repeat(60));
    outputChannel.appendLine('');
    
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Installing AWX MCP Server dependencies...',
        cancellable: false
    }, async (progress) => {
        try {
            // Step 1: Install the bundled awx-mcp-server package
            progress.report({ message: 'Installing AWX MCP Server package...' });
            outputChannel.appendLine('Step 1: Installing AWX MCP Server package...');
            outputChannel.appendLine(`From: ${bundledServerPath}`);
            outputChannel.appendLine('');
            
            const installOutput = await execCommand(pythonPath, [
                '-m', 'pip', 'install', '-e', bundledServerPath
            ]);
            outputChannel.appendLine(installOutput);
            outputChannel.appendLine('✓ AWX MCP Server package installed');
            outputChannel.appendLine('');
            
            // Step 2: Verify installation
            progress.report({ message: 'Verifying installation...' });
            outputChannel.appendLine('Step 2: Verifying installation...');
            
            try {
                const versionOutput = await execCommand(pythonPath, ['-m', 'awx_mcp_server', '--version']);
                outputChannel.appendLine(`✓ Verification successful: ${versionOutput.trim()}`);
                outputChannel.appendLine('');
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('✓ Setup Complete!');
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('');
                outputChannel.appendLine('Next steps:');
                outputChannel.appendLine('  1. Add an AWX instance (click + in AWX MCP view)');
                outputChannel.appendLine('  2. Configure Copilot (run \"AWX MCP: Configure for Copilot Chat\")');
                outputChannel.appendLine('  3. Use with GitHub Copilot Chat');
                
                // Now configure MCP server
                await configureMcpServer(context);
                
                vscode.window.showInformationMessage(
                    'AWX MCP dependencies installed successfully!',
                    'Add AWX Instance',
                    'Open Chat'
                ).then(selection => {
                    if (selection === 'Add AWX Instance') {
                        vscode.commands.executeCommand('awx-mcp.addInstance');
                    } else if (selection === 'Open Chat') {
                        vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
                    }
                });
                
                statusBarItem.text = '$(check) AWX MCP';
                statusBarItem.tooltip = 'AWX MCP Server ready';
                
            } catch (verifyError: any) {
                throw new Error(`Installation verification failed: ${verifyError.message}`);
            }
            
        } catch (error: any) {
            outputChannel.appendLine('');
            outputChannel.appendLine('✗ Installation failed');
            outputChannel.appendLine(`Error: ${error.message}`);
            outputChannel.appendLine('');
            outputChannel.appendLine('Manual installation:');
            outputChannel.appendLine(`  1. Open terminal in: ${bundledServerPath}`);
            outputChannel.appendLine(`  2. Run: ${pythonPath} -m pip install -e .`);
            
            vscode.window.showErrorMessage(
                `Failed to install AWX MCP dependencies: ${error.message}`,
                'View Output',
                'Retry'
            ).then(selection => {
                if (selection === 'View Output') {
                    outputChannel.show();
                } else if (selection === 'Retry') {
                    vscode.commands.executeCommand('awx-mcp.setupDependencies');
                }
            });
            
            throw error;
        }
    });
}

async function configureEnvironment() {
    const name = await vscode.window.showInputBox({
        prompt: 'Environment name',
        placeHolder: 'production'
    });
    if (!name) return;

    const url = await vscode.window.showInputBox({
        prompt: 'AWX URL',
        placeHolder: 'https://awx.example.com'
    });
    if (!url) return;

    const authMethod = await vscode.window.showQuickPick(
        ['Token', 'Username/Password'],
        { placeHolder: 'Select authentication method' }
    );
    if (!authMethod) return;

    let username: string | undefined;
    let password: string | undefined;
    let token: string | undefined;

    if (authMethod === 'Token') {
        token = await vscode.window.showInputBox({
            prompt: 'AWX Token',
            password: true
        });
        if (!token) return;
    } else {
        username = await vscode.window.showInputBox({
            prompt: 'Username'
        });
        if (!username) return;

        password = await vscode.window.showInputBox({
            prompt: 'Password',
            password: true
        });
        if (!password) return;
    }

    const setAsDefault = await vscode.window.showQuickPick(
        ['Yes', 'No'],
        { placeHolder: 'Set as default environment?' }
    );

    // Call CLI to add environment
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const pythonPath = config.get<string>('pythonPath') || 'python';

    try {
        const args = [
            '-m', 'awx_mcp.cli', 'env', 'add',
            '--name', name,
            '--url', url
        ];

        if (token) {
            args.push('--token', token);
        } else {
            args.push('--username', username!, '--password', password!);
        }

        if (setAsDefault === 'Yes') {
            args.push('--set-default');
        }

        await execCommand(pythonPath, args);
        vscode.window.showInformationMessage(`Environment '${name}' configured successfully`);
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to configure environment: ${error.message}`);
    }
}

/**
 * Configure AWX MCP server for GitHub Copilot Chat
 * This configures the server in VS Code settings so Copilot can discover it
 */
async function configureMcpServer(context: vscode.ExtensionContext): Promise<void> {
    try {
        const config = vscode.workspace.getConfiguration();
        const mcpServers = config.get<{[key: string]: any}>('github.copilot.chat.mcpServers') || {};
        
        // Get Python path and extension details
        const awxConfig = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = awxConfig.get<string>('pythonPath') || 'python';
        const logLevel = awxConfig.get<string>('logLevel') || 'info';
        
        // Check if AWX MCP server is already configured
        if (mcpServers['awx-mcp']) {
            outputChannel.appendLine('✓ AWX MCP Server already configured in settings');
            return;
        }
        
        // Configure AWX MCP server
        mcpServers['awx-mcp'] = {
            command: pythonPath,
            args: ['-m', 'awx_mcp_server'],
            env: {
                LOG_LEVEL: logLevel,
                PYTHONUNBUFFERED: '1'
            }
        };
        
        // Update settings (ConfigurationTarget.Global for user settings)
        await config.update('github.copilot.chat.mcpServers', mcpServers, vscode.ConfigurationTarget.Global);
        
        outputChannel.appendLine('✓ AWX MCP Server configured for GitHub Copilot Chat');
        outputChannel.appendLine(`  Command: ${pythonPath} -m awx_mcp_server`);
        outputChannel.appendLine(`  Log Level: ${logLevel}`);
        outputChannel.appendLine('');
        outputChannel.appendLine('🎉 Setup Complete!');
        outputChannel.appendLine('');
        outputChannel.appendLine('GitHub Copilot Chat can now use AWX MCP tools.');
        outputChannel.appendLine('');
        outputChannel.appendLine('To use AWX MCP with Copilot Chat:');
        outputChannel.appendLine('  1. Open Copilot Chat (Ctrl+Alt+I or Cmd+Alt+I)');
        outputChannel.appendLine('  2. Click the "@" button to select an agent');
        outputChannel.appendLine('  3. Start asking questions about your AWX instance:');
        outputChannel.appendLine('     • "List my AWX job templates"');
        outputChannel.appendLine('     • "Show me the status of my AWX projects"');
        outputChannel.appendLine('     • "What inventory groups do I have?"');
        outputChannel.appendLine('');
        outputChannel.appendLine('Note: Make sure you have configured at least one AWX instance');
        outputChannel.appendLine('in the extension (use "AWX MCP: Add Instance")');
        
        // Show success notification
        const result = await vscode.window.showInformationMessage(
            'AWX MCP Server is now available in GitHub Copilot Chat!',
            'Open Chat',
            'Configure AWX',
            'View Settings'
        );
        
        if (result === 'Open Chat') {
            vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
        } else if (result === 'Configure AWX') {
            vscode.commands.executeCommand('awx-mcp.addInstance');
        } else if (result === 'View Settings') {
            vscode.commands.executeCommand('workbench.action.openSettings', 'github.copilot.chat.mcpServers');
        }
        
    } catch (error: any) {
        outputChannel.appendLine(`⚠ Failed to configure MCP server: ${error.message}`);
        outputChannel.appendLine('You may need to configure the MCP server manually in VS Code settings.');
        outputChannel.appendLine('Add the following to your settings.json:');
        outputChannel.appendLine('');
        outputChannel.appendLine('{');
        outputChannel.appendLine('  "github.copilot.chat.mcpServers": {');
        outputChannel.appendLine('    "awx-mcp": {');
        outputChannel.appendLine('      "command": "python",');
        outputChannel.appendLine('      "args": ["-m", "awx_mcp_server"],');
        outputChannel.appendLine('      "env": {');
        outputChannel.appendLine('        "LOG_LEVEL": "info",');
        outputChannel.appendLine('        "PYTHONUNBUFFERED": "1"');
        outputChannel.appendLine('      }');
        outputChannel.appendLine('    }');
        outputChannel.appendLine('  }');
        outputChannel.appendLine('}');
        
        vscode.window.showWarningMessage(
            'Could not auto-configure AWX MCP. Check output channel for manual setup instructions.',
            'View Output'
        ).then(selection => {
            if (selection === 'View Output') {
                outputChannel.show();
            }
        });
    }
}

function getMetricsHtml(metrics: any): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWX MCP Metrics</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .metric {
            margin: 10px 0;
            padding: 15px;
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 5px;
        }
        .metric-label {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
        .metric-value {
            font-size: 24px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>AWX MCP Metrics</h1>
    <div class="metric">
        <div class="metric-label">Total Requests</div>
        <div class="metric-value">${metrics.requestCount || 0}</div>
    </div>
    <div class="metric">
        <div class="metric-label">Total Errors</div>
        <div class="metric-value">${metrics.errorCount || 0}</div>
    </div>
    <div class="metric">
        <div class="metric-label">Uptime</div>
        <div class="metric-value">${metrics.uptime || 'N/A'}</div>
    </div>
    <div class="metric">
        <div class="metric-label">Average Response Time</div>
        <div class="metric-value">${metrics.avgResponseTime || 'N/A'}</div>
    </div>
</body>
</html>`;
}

function execCommand(command: string, args: string[]): Promise<string> {
    return new Promise((resolve, reject) => {
        const proc = child_process.spawn(command, args);
        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        proc.on('close', (code) => {
            if (code === 0) {
                resolve(stdout);
            } else {
                reject(new Error(stderr || `Process exited with code ${code}`));
            }
        });
    });
}

async function executePythonCommand(command: string, args: any): Promise<any> {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = config.get<string>('pythonPath') || 'python';
        
        const scriptContent = `
import sys
import json
from uuid import uuid4
sys.path.insert(0, r'${vscode.extensions.getExtension('awx-mcp-team.awx-mcp-extension')?.extensionPath}\\bundled\\awx-mcp-server\\src')

from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import EnvironmentConfig
import asyncio

async def list_templates(url, username, password, token, verify_ssl):
    try:
        # Create environment config
        env = EnvironmentConfig(
            env_id=uuid4(),
            name="temp-query",
            base_url=url,
            verify_ssl=verify_ssl
        )
        
        # Create client with credentials
        if token:
            client = CompositeAWXClient(env, "token", token, is_token=True)
        elif password:
            client = CompositeAWXClient(env, username, password, is_token=False)
        else:
            return {"success": False, "error": "No credentials provided"}
        
        # Fetch templates
        async with client:
            templates = await client.list_job_templates()
            
            # Convert to dict
            templates_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description or "No description",
                    "job_type": t.job_type,
                    "playbook": t.playbook
                }
                for t in templates
            ]
            
        return {
            "success": True,
            "templates": templates_data,
            "count": len(templates_data)
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"{str(e)}\\n{traceback.format_exc()}"}

args = json.loads(r'''${JSON.stringify(args)}''')
result = asyncio.run(list_templates(
    args.get('url'),
    args.get('username'),
    args.get('password'),
    args.get('token'),
    args.get('verify_ssl', True)
))
print(json.dumps(result))
`;

        const tempFile = require('os').tmpdir() + '\\awx_query_' + Date.now() + '.py';
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

function getJobTemplatesHtml(templates: any[], instanceName: string): string {
    const templateRows = templates.map(t => `
        <tr>
            <td>${t.id}</td>
            <td><strong>${t.name}</strong></td>
            <td>${t.description}</td>
            <td>${t.job_type}</td>
            <td><code>${t.playbook}</code></td>
        </tr>
    `).join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Templates - ${instanceName}</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        h1 {
            color: var(--vscode-titleBar-activeForeground);
            margin-bottom: 5px;
        }
        .subtitle {
            color: var(--vscode-descriptionForeground);
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        th {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            font-weight: 600;
            color: var(--vscode-textLink-foreground);
        }
        tr:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }
        .count {
            color: var(--vscode-descriptionForeground);
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>📋 Job Templates</h1>
    <div class="subtitle">${instanceName}</div>
    <div class="count">Found ${templates.length} job template(s)</div>
    
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Type</th>
                <th>Playbook</th>
            </tr>
        </thead>
        <tbody>
            ${templateRows}
        </tbody>
    </table>
</body>
</html>`;
}

export function deactivate() {
    if (serverManager) {
        serverManager.stop();
    }
    if (connectionStatusProvider) {
        connectionStatusProvider.dispose();
    }
}
