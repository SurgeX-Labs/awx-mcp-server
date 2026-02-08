/**
 * Server lifecycle management - start, stop, restart
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';

/**
 * Start MCP server process
 */
export async function startServer(
    pythonPath: string,
    logLevel: string,
    outputChannel: vscode.OutputChannel,
    onStdout: (data: string) => void,
    onStderr: (data: string) => void,
    onClose: (code: number | null) => void,
    onError: (error: Error) => void
): Promise<child_process.ChildProcess> {
    outputChannel.appendLine('Starting AWX MCP Server...');
    outputChannel.appendLine(`Python: ${pythonPath}`);
    outputChannel.appendLine(`Log Level: ${logLevel}`);
    outputChannel.show();

    const serverProcess = child_process.spawn(
        pythonPath,
        ['-m', 'awx_mcp_server'],
        {
            env: {
                ...process.env,
                LOG_LEVEL: logLevel,
                PYTHONUNBUFFERED: '1'
            },
            stdio: ['pipe', 'pipe', 'pipe']
        }
    );

    outputChannel.appendLine(`Process started with PID: ${serverProcess.pid}`);

    // Handle stdout
    serverProcess.stdout?.on('data', (data: Buffer) => {
        const output = data.toString();
        outputChannel.appendLine(`[STDOUT] ${output}`);
        onStdout(output);
    });

    // Handle stderr
    serverProcess.stderr?.on('data', (data: Buffer) => {
        const message = data.toString();
        outputChannel.appendLine(`[STDERR] ${message}`);
        onStderr(message);
    });

    // Handle process exit
    serverProcess.on('close', (code: number | null) => {
        outputChannel.appendLine(`Server process exited with code ${code}`);
        onClose(code);
        
        if (code !== 0 && code !== null) {
            vscode.window.showErrorMessage(`AWX MCP Server exited unexpectedly (code ${code})`);
        }
    });

    // Handle process errors
    serverProcess.on('error', (error: Error) => {
        outputChannel.appendLine(`Process error: ${error.message}`);
        onError(error);
        vscode.window.showErrorMessage(`Failed to start AWX MCP Server: ${error.message}`);
    });

    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (serverProcess && !serverProcess.killed) {
        outputChannel.appendLine('Server started successfully and is running in MCP stdio mode');
        outputChannel.appendLine('The server is now waiting for GitHub Copilot to connect...');
        vscode.window.showInformationMessage('AWX MCP Server started successfully');
        return serverProcess;
    } else {
        throw new Error('Server failed to start - process exited immediately');
    }
}

/**
 * Stop MCP server process
 */
export async function stopServer(
    serverProcess: child_process.ChildProcess | undefined,
    outputChannel: vscode.OutputChannel
): Promise<void> {
    if (!serverProcess) {
        throw new Error('Server is not running');
    }

    outputChannel.appendLine('Stopping AWX MCP Server...');

    return new Promise((resolve) => {
        if (serverProcess) {
            serverProcess.on('close', () => {
                outputChannel.appendLine('Server stopped');
                resolve();
            });

            // Send SIGTERM on Unix-like systems, kill on Windows
            if (process.platform === 'win32') {
                child_process.exec(`taskkill /pid ${serverProcess.pid} /T /F`);
            } else {
                serverProcess.kill('SIGTERM');
            }
        } else {
            resolve();
        }
    });
}

/**
 * Calculate server uptime
 */
export function calculateUptime(startTime: Date): string {
    const uptime = Date.now() - startTime.getTime();
    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);
    return `${hours}h ${minutes}m ${seconds}s`;
}
