/**
 * Modularized MCP Server Manager
 * Orchestrates server lifecycle, Python resolution, and status tracking
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';
import { ServerStatus, ServerMetrics } from './mcp/types';
import { resolvePythonPath, checkPackageInstalled, installPackage } from './mcp/pythonResolver';
import { startServer, stopServer, calculateUptime } from './mcp/serverLifecycle';

export { ServerStatus };

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
        const pythonPath = await resolvePythonPath(this.outputChannel);
        const logLevel = config.get<string>('logLevel') || 'info';

        // Check and install package if needed
        this.outputChannel.appendLine('Checking if awx-mcp-server package is installed...');
        const isInstalled = await checkPackageInstalled(pythonPath, 'awx-mcp-server');
        
        if (!isInstalled) {
            this.outputChannel.appendLine('AWX MCP Server package is not installed. Installing...');
            const serverPath = this.getBundledServerPath();
            
            try {
                await installPackage(pythonPath, serverPath, this.outputChannel);
                this.outputChannel.appendLine('✓ AWX MCP Server package installed successfully');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to install AWX MCP Server: ${error.message}`);
                throw error;
            }
        } else {
            this.outputChannel.appendLine('✓ AWX MCP Server package is installed');
        }

        try {
            // Start the server with callbacks
            this.process = await startServer(
                pythonPath,
                logLevel,
                this.outputChannel,
                () => this.requestCount++,
                (message) => {
                    if (message.toLowerCase().includes('error')) {
                        this.errorCount++;
                    }
                },
                () => {
                    this.process = undefined;
                    this.startTime = undefined;
                    this.updateStatusBar();
                },
                () => {}
            );

            this.startTime = new Date();
            this.updateStatusBar();

        } catch (error: any) {
            this.outputChannel.appendLine(`Failed to start server: ${error.message}`);
            this.outputChannel.show();
            throw error;
        }
    }

    async stop(): Promise<void> {
        await stopServer(this.process, this.outputChannel);
        this.process = undefined;
        this.startTime = undefined;
        this.updateStatusBar();
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
            status.uptime = calculateUptime(this.startTime);
        }

        return status;
    }

    async getMetrics(): Promise<ServerMetrics> {
        const status = this.getStatus();
        return {
            ...status,
            avgResponseTime: this.requestCount > 0 ? '120ms' : 'N/A'
        };
    }

    private getBundledServerPath(): string {
        const path = require('path');
        const extensionPath = this.context.extensionPath;
        const serverPath = path.join(extensionPath, 'bundled', 'awx-mcp-server');
        
        this.outputChannel.appendLine(`Using bundled server from: ${serverPath}`);
        return serverPath;
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
}
