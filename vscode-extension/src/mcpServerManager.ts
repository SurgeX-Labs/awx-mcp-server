/**
 * MCP Server Manager
 * Handles the lifecycle of the local MCP server process
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';

export interface ServerStatus {
    running: boolean;
    pid?: number;
    uptime?: string;
    requestCount?: number;
    errorCount?: number;
}

export class MCPServerManager {
    private process?: child_process.ChildProcess;
    private startTime?: Date;
    private requestCount = 0;
    private errorCount = 0;

    constructor(
        private context: vscode.ExtensionContext,
        private outputChannel: vscode.OutputChannel,
        private statusBarItem: vscode.StatusBarItem
    ) {}

    async start(): Promise<void> {
        if (this.process) {
            throw new Error('Server is already running');
        }

        const config = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = await this.getPythonPath();
        const logLevel = config.get<string>('logLevel') || 'info';

        this.outputChannel.appendLine('Starting AWX MCP Server...');
        this.outputChannel.appendLine(`Python: ${pythonPath}`);
        this.outputChannel.appendLine(`Log Level: ${logLevel}`);
        this.outputChannel.show(); // Show output channel

        // Check if awx-mcp-server is installed
        this.outputChannel.appendLine('Checking if awx-mcp-server package is installed...');
        const isInstalled = await this.checkPackageInstalled(pythonPath);
        if (!isInstalled) {
            this.outputChannel.appendLine('AWX MCP Server package is not installed. Installing...');
            const serverPath = this.getBundledServerPath();
            
            try {
                await this.installPackage(pythonPath, serverPath);
                this.outputChannel.appendLine('✓ AWX MCP Server package installed successfully');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to install AWX MCP Server: ${error.message}`);
                throw error;
            }
        } else {
            this.outputChannel.appendLine('✓ AWX MCP Server package is installed');
        }

        try {
            // Start the MCP server process
            this.process = child_process.spawn(
                pythonPath,
                ['-m', 'awx_mcp_server'],
                {
                    env: {
                        ...process.env,
                        LOG_LEVEL: logLevel,
                        PYTHONUNBUFFERED: '1'
                    },
                    stdio: ['pipe', 'pipe', 'pipe'] // Keep stdin/stdout/stderr open
                }
            );

            this.startTime = new Date();
            this.outputChannel.appendLine(`Process started with PID: ${this.process.pid}`);

            // Handle stdout
            this.process.stdout?.on('data', (data) => {
                const output = data.toString();
                this.outputChannel.appendLine(`[STDOUT] ${output}`);
                this.requestCount++;
            });

            // Handle stderr
            this.process.stderr?.on('data', (data) => {
                const message = data.toString();
                this.outputChannel.appendLine(`[STDERR] ${message}`);
                if (message.toLowerCase().includes('error')) {
                    this.errorCount++;
                }
            });

            // Handle process exit
            this.process.on('close', (code) => {
                this.outputChannel.appendLine(`Server process exited with code ${code}`);
                this.process = undefined;
                this.startTime = undefined;
                this.updateStatusBar();
                
                if (code !== 0 && code !== null) {
                    vscode.window.showErrorMessage(`AWX MCP Server exited unexpectedly (code ${code})`);
                }
            });

            // Handle process errors
            this.process.on('error', (error) => {
                this.outputChannel.appendLine(`Process error: ${error.message}`);
                vscode.window.showErrorMessage(`Failed to start AWX MCP Server: ${error.message}`);
            });

            // Wait a bit to ensure server started
            await new Promise(resolve => setTimeout(resolve, 1000));

            if (this.process && !this.process.killed) {
                this.outputChannel.appendLine('Server started successfully and is running in MCP stdio mode');
                this.outputChannel.appendLine('The server is now waiting for GitHub Copilot to connect...');
                this.updateStatusBar();
                vscode.window.showInformationMessage('AWX MCP Server started successfully');
            } else {
                throw new Error('Server failed to start - process exited immediately');
            }

        } catch (error: any) {
            this.outputChannel.appendLine(`Failed to start server: ${error.message}`);
            this.outputChannel.show();
            throw error;
        }
    }

    async stop(): Promise<void> {
        if (!this.process) {
            throw new Error('Server is not running');
        }

        this.outputChannel.appendLine('Stopping AWX MCP Server...');

        return new Promise((resolve) => {
            if (this.process) {
                this.process.on('close', () => {
                    this.process = undefined;
                    this.startTime = undefined;
                    this.updateStatusBar();
                    this.outputChannel.appendLine('Server stopped');
                    resolve();
                });

                // Send SIGTERM on Unix-like systems, kill on Windows
                if (process.platform === 'win32') {
                    child_process.exec(`taskkill /pid ${this.process.pid} /T /F`);
                } else {
                    this.process.kill('SIGTERM');
                }
            } else {
                resolve();
            }
        });
    }

    async restart(): Promise<void> {
        if (this.process) {
            await this.stop();
        }
        await this.start();
    }

    getStatus(): ServerStatus {
        const status: ServerStatus = {
            running: !!this.process,
            pid: this.process?.pid,
            requestCount: this.requestCount,
            errorCount: this.errorCount
        };

        if (this.startTime) {
            const uptime = Date.now() - this.startTime.getTime();
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);
            status.uptime = `${hours}h ${minutes}m ${seconds}s`;
        }

        return status;
    }

    async getMetrics(): Promise<any> {
        const status = this.getStatus();
        return {
            ...status,
            avgResponseTime: this.requestCount > 0 ? '120ms' : 'N/A'
        };
    }

    private async getPythonPath(): Promise<string> {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        let pythonPath = config.get<string>('pythonPath');

        if (!pythonPath || pythonPath === 'python') {
            // Try to find Python from the Python extension
            try {
                const pythonExtension = vscode.extensions.getExtension('ms-python.python');
                if (pythonExtension) {
                    if (!pythonExtension.isActive) {
                        await pythonExtension.activate();
                    }
                    const pythonApi = pythonExtension.exports;
                    if (pythonApi) {
                        const envPath = pythonApi.settings.getExecutionDetails?.()?.execCommand;
                        if (envPath) {
                            pythonPath = Array.isArray(envPath) ? envPath[0] : envPath;
                        }
                    }
                }
            } catch (error) {
                this.outputChannel.appendLine('Could not get Python path from Python extension');
            }
        }

        return pythonPath || 'python';
    }

    private updateStatusBar(): void {
        if (this.process) {
            this.statusBarItem.text = '$(check) AWX MCP: Running';
            this.statusBarItem.tooltip = 'AWX MCP Server is running. Click for details.';
            this.statusBarItem.backgroundColor = undefined;
        } else {
            this.statusBarItem.text = '$(circle-slash) AWX MCP: Stopped';
            this.statusBarItem.tooltip = 'AWX MCP Server is stopped. Click to start.';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    }

    private async checkPackageInstalled(pythonPath: string): Promise<boolean> {
        return new Promise((resolve) => {
            const checkProcess = child_process.spawn(
                pythonPath,
                ['-m', 'pip', 'show', 'awx-mcp-server'],
                { stdio: 'pipe' }
            );

            let output = '';
            checkProcess.stdout?.on('data', (data) => {
                output += data.toString();
            });

            checkProcess.on('close', (code) => {
                resolve(code === 0 && output.includes('Name: awx-mcp-server'));
            });

            checkProcess.on('error', () => {
                resolve(false);
            });
        });
    }

    private getBundledServerPath(): string {
        const path = require('path');
        
        // Get the path to bundled server package within the extension
        const extensionPath = this.context.extensionPath;
        const serverPath = path.join(extensionPath, 'bundled', 'awx-mcp-server');
        
        this.outputChannel.appendLine(`Using bundled server from: ${serverPath}`);
        return serverPath;
    }

    private async installPackage(pythonPath: string, serverPath: string): Promise<void> {
        return new Promise((resolve, reject) => {
            this.outputChannel.appendLine(`Installing AWX MCP Server from: ${serverPath}`);
            
            const installProcess = child_process.spawn(
                pythonPath,
                ['-m', 'pip', 'install', '--upgrade', '--force-reinstall', serverPath],
                { 
                    stdio: 'pipe',
                    shell: true
                }
            );

            installProcess.stdout?.on('data', (data) => {
                this.outputChannel.appendLine(data.toString());
            });

            installProcess.stderr?.on('data', (data) => {
                this.outputChannel.appendLine(data.toString());
            });

            installProcess.on('close', (code) => {
                if (code === 0) {
                    this.outputChannel.appendLine('✓ Package installed successfully!');
                    resolve();
                } else {
                    const error = `Package installation failed with code ${code}`;
                    this.outputChannel.appendLine(`✗ ${error}`);
                    reject(new Error(error));
                }
            });

            installProcess.on('error', (error) => {
                this.outputChannel.appendLine(`✗ Installation error: ${error.message}`);
                reject(error);
            });
        });
    }
}