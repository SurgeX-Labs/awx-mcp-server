/**
 * Python environment resolution utilities
 */

import * as vscode from 'vscode';

/**
 * Get Python executable path, trying VS Code Python extension first
 */
export async function resolvePythonPath(outputChannel: vscode.OutputChannel): Promise<string> {
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
            outputChannel.appendLine('Could not get Python path from Python extension');
        }
    }

    return pythonPath || 'python';
}

/**
 * Check if a Python package is installed
 */
export async function checkPackageInstalled(pythonPath: string, packageName: string): Promise<boolean> {
    const { spawn } = require('child_process');
    
    return new Promise((resolve) => {
        const checkProcess = spawn(
            pythonPath,
            ['-m', 'pip', 'show', packageName],
            { stdio: 'pipe' }
        );

        let output = '';
        checkProcess.stdout?.on('data', (data: Buffer) => {
            output += data.toString();
        });

        checkProcess.on('close', (code: number) => {
            resolve(code === 0 && output.includes(`Name: ${packageName}`));
        });

        checkProcess.on('error', () => {
            resolve(false);
        });
    });
}

/**
 * Install Python package from local path
 */
export async function installPackage(
    pythonPath: string,
    serverPath: string,
    outputChannel: vscode.OutputChannel
): Promise<void> {
    const { spawn } = require('child_process');
    
    return new Promise((resolve, reject) => {
        outputChannel.appendLine(`Installing AWX MCP Server from: ${serverPath}`);
        
        const installProcess = spawn(
            pythonPath,
            ['-m', 'pip', 'install', '--upgrade', '--force-reinstall', serverPath],
            { 
                stdio: 'pipe',
                shell: true
            }
        );

        installProcess.stdout?.on('data', (data: Buffer) => {
            outputChannel.appendLine(data.toString());
        });

        installProcess.stderr?.on('data', (data: Buffer) => {
            outputChannel.appendLine(data.toString());
        });

        installProcess.on('close', (code: number) => {
            if (code === 0) {
                outputChannel.appendLine('✓ Package installed successfully!');
                resolve();
            } else {
                const error = `Package installation failed with code ${code}`;
                outputChannel.appendLine(`✗ ${error}`);
                reject(new Error(error));
            }
        });

        installProcess.on('error', (error: Error) => {
            outputChannel.appendLine(`✗ Installation error: ${error.message}`);
            reject(error);
        });
    });
}
