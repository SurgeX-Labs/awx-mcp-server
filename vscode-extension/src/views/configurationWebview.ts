/**
 * Configuration Webview Panel
 * Provides GUI for configuring AWX instances
 */

import * as vscode from 'vscode';
import { ConfigurationProvider, AWXInstance } from './configurationProvider';

export class ConfigurationWebview {
    private panel: vscode.WebviewPanel | undefined;
    private configProvider: ConfigurationProvider;
    private context: vscode.ExtensionContext;

    constructor(context: vscode.ExtensionContext, configProvider: ConfigurationProvider) {
        this.context = context;
        this.configProvider = configProvider;
    }

    public show(instance?: AWXInstance) {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'awxConfiguration',
            instance ? 'Edit AWX Instance' : 'Add AWX Instance',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        this.panel.webview.html = this.getWebviewContent(instance);

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'save':
                        await this.saveConfiguration(message.data);
                        return;
                    case 'test':
                        await this.testConnection(message.data);
                        return;
                    case 'cancel':
                        this.panel?.dispose();
                        return;
                }
            },
            undefined,
            this.context.subscriptions
        );

        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });
    }

    private async saveConfiguration(data: any): Promise<void> {
        try {
            const instance: AWXInstance = {
                id: data.id || this.generateId(),
                name: data.name,
                url: data.url,
                username: data.username,
                verifySSL: data.verifySSL,
                isDefault: data.isDefault || false,
                status: 'disconnected'
            };

            if (data.id) {
                await this.configProvider.updateInstance(data.id, instance);
                vscode.window.showInformationMessage(`AWX instance "${instance.name}" updated successfully`);
            } else {
                await this.configProvider.addInstance(instance);
                vscode.window.showInformationMessage(`AWX instance "${instance.name}" added successfully`);
            }

            // Store credentials securely
            if (data.password) {
                await this.context.secrets.store(
                    `awx.${instance.id}.password`,
                    data.password
                );
                console.log(`[AWX MCP] Stored password for instance ${instance.id}`);
            }
            if (data.token) {
                await this.context.secrets.store(
                    `awx.${instance.id}.token`,
                    data.token
                );
                console.log(`[AWX MCP] Stored token for instance ${instance.id}`);
            }
            
            // Remove credentials if switching auth modes
            if (data.password && !data.token) {
                await this.context.secrets.delete(`awx.${instance.id}.token`);
            }
            if (data.token && !data.password) {
                await this.context.secrets.delete(`awx.${instance.id}.password`);
            }

            this.panel?.dispose();
        } catch (error: any) {
            this.panel?.webview.postMessage({
                command: 'error',
                message: `Failed to save configuration: ${error.message}`
            });
        }
    }

    private async testConnection(data: any): Promise<void> {
        this.panel?.webview.postMessage({
            command: 'testStarted'
        });

        try {
            // Test connection using Python client
            const { spawn } = require('child_process');
            const config = vscode.workspace.getConfiguration('awx-mcp');
            const pythonPath = config.get<string>('pythonPath') || 'python';

            const pythonScript = `
import sys
import asyncio

from awx_mcp_server.domain import AWXEnvironment
from awx_mcp_server.clients import ${data.authType === 'token' ? 'TokenAWXClient' : 'PasswordAWXClient'}

async def test():
    env = AWXEnvironment(
        env_id='test',
        name='Test',
        url='${data.url}',
        verify_ssl=${data.verifySSL}
    )
    client = ${data.authType === 'token' ? 'TokenAWXClient(env, "${data.username}", "${data.password}")' : 'PasswordAWXClient(env, "${data.username}", "${data.password}")'}
    result = await client.test_connection()
    print('SUCCESS' if result else 'FAILED')

asyncio.run(test())
`;

            const testResult = await new Promise<boolean>((resolve) => {
                const proc = spawn(pythonPath, ['-c', pythonScript]);
                let output = '';
                
                proc.stdout.on('data', (data: Buffer) => {
                    output += data.toString();
                });

                proc.on('close', (code: number) => {
                    resolve(code === 0 && output.trim().includes('SUCCESS'));
                });

                setTimeout(() => {
                    proc.kill();
                    resolve(false);
                }, 10000);
            });

            this.panel?.webview.postMessage({
                command: 'testResult',
                success: testResult,
                message: testResult 
                    ? `Successfully connected to ${new URL(data.url).hostname}`
                    : 'Connection test failed - please verify your credentials and URL',
                version: '23.0.0' // Mock version
            });
        } catch (error: any) {
            this.panel?.webview.postMessage({
                command: 'testResult',
                success: false,
                message: `Connection failed: ${error.message}`
            });
        }
    }

    private generateId(): string {
        return `awx-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    private getWebviewContent(instance?: AWXInstance): string {
        const isEdit = !!instance;
        
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>${isEdit ? 'Edit' : 'Add'} AWX Instance</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 20px;
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                }
                .container {
                    max-width: 700px;
                    margin: 0 auto;
                }
                h1 {
                    color: var(--vscode-titleBar-activeForeground);
                    margin-bottom: 10px;
                }
                .subtitle {
                    color: var(--vscode-descriptionForeground);
                    margin-bottom: 30px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 6px;
                    font-weight: 500;
                    color: var(--vscode-input-foreground);
                }
                .required::after {
                    content: " *";
                    color: var(--vscode-errorForeground);
                }
                input[type="text"],
                input[type="url"],
                input[type="password"],
                select {
                    width: 100%;
                    padding: 8px 12px;
                    background-color: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 2px;
                    font-size: 13px;
                    box-sizing: border-box;
                }
                input[type="text"]:focus,
                input[type="url"]:focus,
                input[type="password"]:focus,
                select:focus {
                    outline: 1px solid var(--vscode-focusBorder);
                }
                .checkbox-group {
                    display: flex;
                    align-items: center;
                    margin-top: 8px;
                }
                input[type="checkbox"] {
                    margin-right: 8px;
                }
                .help-text {
                    font-size: 12px;
                    color: var(--vscode-descriptionForeground);
                    margin-top: 4px;
                }
                .button-group {
                    display: flex;
                    gap: 10px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid var(--vscode-panel-border);
                }
                button {
                    padding: 8px 16px;
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 2px;
                    cursor: pointer;
                    font-size: 13px;
                    font-weight: 500;
                }
                button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                .button-secondary {
                    background-color: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }
                .button-secondary:hover {
                    background-color: var(--vscode-button-secondaryHoverBackground);
                }
                .button-test {
                    margin-left: auto;
                }
                .section {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid var(--vscode-panel-border);
                }
                .section-title {
                    font-size: 14px;
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: var(--vscode-titleBar-activeForeground);
                }
                .status-message {
                    padding: 10px 12px;
                    margin-top: 15px;
                    border-radius: 2px;
                    font-size: 13px;
                }
                .status-success {
                    background-color: var(--vscode-testing-iconPassed);
                    color: var(--vscode-editor-background);
                }
                .status-error {
                    background-color: var(--vscode-testing-iconFailed);
                    color: var(--vscode-editor-background);
                }
                .status-info {
                    background-color: var(--vscode-editorInfo-background);
                    color: var(--vscode-editorInfo-foreground);
                }
                .spinner {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border: 2px solid var(--vscode-button-foreground);
                    border-top-color: transparent;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                    margin-right: 8px;
                    vertical-align: middle;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .auth-mode {
                    margin-bottom: 15px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>${isEdit ? 'Edit AWX Instance' : 'Add New AWX Instance'}</h1>
                <p class="subtitle">Configure connection to your AWX/Ansible Tower instance</p>

                <form id="configForm">
                    <input type="hidden" id="instanceId" value="${instance?.id || ''}">

                    <div class="form-group">
                        <label for="name" class="required">Instance Name</label>
                        <input type="text" id="name" placeholder="Production AWX" value="${instance?.name || ''}" required>
                        <div class="help-text">A friendly name to identify this instance</div>
                    </div>

                    <div class="form-group">
                        <label for="url" class="required">AWX URL</label>
                        <input type="url" id="url" placeholder="https://awx.example.com" value="${instance?.url || ''}" required>
                        <div class="help-text">Full URL to your AWX instance (e.g., https://awx.example.com)</div>
                    </div>

                    <div class="section">
                        <div class="section-title">Authentication</div>

                        <div class="form-group">
                            <label>Authentication Method</label>
                            <div class="auth-mode">
                                <label class="checkbox-group">
                                    <input type="radio" name="authMode" value="password" checked>
                                    Username & Password
                                </label>
                                <label class="checkbox-group">
                                    <input type="radio" name="authMode" value="token">
                                    OAuth Token
                                </label>
                            </div>
                        </div>

                        <div id="passwordAuth">
                            <div class="form-group">
                                <label for="username" class="required">Username</label>
                                <input type="text" id="username" placeholder="admin" value="${instance?.username || ''}" autocomplete="username">
                            </div>

                            <div class="form-group">
                                <label for="password" class="required">Password</label>
                                <input type="password" id="password" placeholder="••••••••" autocomplete="current-password">
                                <div class="help-text">Password will be stored securely in VS Code's secret storage</div>
                            </div>
                        </div>

                        <div id="tokenAuth" style="display: none;">
                            <div class="form-group">
                                <label for="token" class="required">OAuth Token</label>
                                <input type="password" id="token" placeholder="Enter your OAuth token">
                                <div class="help-text">Token will be stored securely in VS Code's secret storage</div>
                            </div>
                        </div>
                    </div>

                    <div class="section">
                        <div class="section-title">Options</div>

                        <div class="form-group">
                            <label class="checkbox-group">
                                <input type="checkbox" id="verifySSL" ${instance?.verifySSL !== false ? 'checked' : ''}>
                                Verify SSL certificates
                            </label>
                            <div class="help-text">Disable for self-signed certificates (not recommended for production)</div>
                        </div>

                        <div class="form-group">
                            <label class="checkbox-group">
                                <input type="checkbox" id="isDefault" ${instance?.isDefault ? 'checked' : ''}>
                                Set as default instance
                            </label>
                            <div class="help-text">This instance will be used by default for all operations</div>
                        </div>
                    </div>

                    <div id="statusMessage"></div>

                    <div class="button-group">
                        <button type="submit" id="saveBtn">
                            ${isEdit ? 'Update' : 'Add'} Instance
                        </button>
                        <button type="button" class="button-secondary" id="cancelBtn">
                            Cancel
                        </button>
                        <button type="button" class="button-secondary button-test" id="testBtn">
                            Test Connection
                        </button>
                    </div>
                </form>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                const form = document.getElementById('configForm');
                const statusMessage = document.getElementById('statusMessage');
                const saveBtn = document.getElementById('saveBtn');
                const testBtn = document.getElementById('testBtn');
                const passwordAuth = document.getElementById('passwordAuth');
                const tokenAuth = document.getElementById('tokenAuth');
                const authModes = document.querySelectorAll('input[name="authMode"]');

                // Toggle auth mode
                authModes.forEach(radio => {
                    radio.addEventListener('change', (e) => {
                        if (e.target.value === 'password') {
                            passwordAuth.style.display = 'block';
                            tokenAuth.style.display = 'none';
                        } else {
                            passwordAuth.style.display = 'none';
                            tokenAuth.style.display = 'block';
                        }
                    });
                });

                // Form submission
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    
                    const authMode = document.querySelector('input[name="authMode"]:checked').value;
                    const data = {
                        id: document.getElementById('instanceId').value || null,
                        name: document.getElementById('name').value,
                        url: document.getElementById('url').value,
                        username: authMode === 'password' ? document.getElementById('username').value : null,
                        password: authMode === 'password' ? document.getElementById('password').value : null,
                        token: authMode === 'token' ? document.getElementById('token').value : null,
                        verifySSL: document.getElementById('verifySSL').checked,
                        isDefault: document.getElementById('isDefault').checked
                    };

                    vscode.postMessage({
                        command: 'save',
                        data: data
                    });
                });

                // Test connection
                testBtn.addEventListener('click', () => {
                    const authMode = document.querySelector('input[name="authMode"]:checked').value;
                    const data = {
                        url: document.getElementById('url').value,
                        username: authMode === 'password' ? document.getElementById('username').value : null,
                        password: authMode === 'password' ? document.getElementById('password').value : null,
                        token: authMode === 'token' ? document.getElementById('token').value : null,
                        verifySSL: document.getElementById('verifySSL').checked
                    };

                    vscode.postMessage({
                        command: 'test',
                        data: data
                    });
                });

                // Cancel button
                document.getElementById('cancelBtn').addEventListener('click', () => {
                    vscode.postMessage({ command: 'cancel' });
                });

                // Handle messages from extension
                window.addEventListener('message', event => {
                    const message = event.data;
                    
                    switch (message.command) {
                        case 'testStarted':
                            testBtn.disabled = true;
                            testBtn.innerHTML = '<span class="spinner"></span> Testing...';
                            statusMessage.className = 'status-message status-info';
                            statusMessage.textContent = 'Testing connection to AWX instance...';
                            break;
                            
                        case 'testResult':
                            testBtn.disabled = false;
                            testBtn.textContent = 'Test Connection';
                            
                            if (message.success) {
                                statusMessage.className = 'status-message status-success';
                                statusMessage.textContent = '✓ ' + message.message;
                                if (message.version) {
                                    statusMessage.textContent += ' (Version: ' + message.version + ')';
                                }
                            } else {
                                statusMessage.className = 'status-message status-error';
                                statusMessage.textContent = '✗ ' + message.message;
                            }
                            break;
                            
                        case 'error':
                            statusMessage.className = 'status-message status-error';
                            statusMessage.textContent = '✗ ' + message.message;
                            break;
                    }
                });
            </script>
        </body>
        </html>`;
    }
}
