/**
 * Dependency checking and setup utilities
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';

/**
 * Execute a command and return output
 */
export function execCommand(command: string, args: string[]): Promise<string> {
    return new Promise((resolve, reject) => {
        const proc = child_process.spawn(command, args);
        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data: Buffer) => {
            stdout += data.toString();
        });

        proc.stderr.on('data', (data: Buffer) => {
            stderr += data.toString();
        });

        proc.on('close', (code: number) => {
            if (code === 0) {
                resolve(stdout);
            } else {
                reject(new Error(stderr || `Command exited with code ${code}`));
            }
        });
    });
}

/**
 * Check if Python dependencies are installed
 */
export async function checkDependencies(outputChannel: vscode.OutputChannel): Promise<boolean> {
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
export async function setupDependencies(
    extensionPath: string,
    outputChannel: vscode.OutputChannel
): Promise<void> {
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    const bundledServerPath = extensionPath + '\\bundled\\awx-mcp-server';
    
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
            // Install the bundled awx-mcp-server package
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
            
            // Verify installation
            progress.report({ message: 'Verifying installation...' });
            outputChannel.appendLine('Step 2: Verifying installation...');
            
            try {
                const version = await execCommand(pythonPath, ['-m', 'awx_mcp_server', '--version']);
                outputChannel.appendLine(`✓ Verification successful: ${version.trim()}`);
                outputChannel.appendLine('');
                outputChannel.appendLine('='.repeat(60));
                outputChannel.appendLine('✓ Installation Complete');
                outputChannel.appendLine('='.repeat(60));
                
                vscode.window.showInformationMessage(
                    'AWX MCP Server dependencies installed successfully!',
                    'Configure AWX',
                    'Reload Window'
                ).then(selection => {
                    if (selection === 'Configure AWX') {
                        vscode.commands.executeCommand('awx-mcp.addInstance');
                    } else if (selection === 'Reload Window') {
                        vscode.commands.executeCommand('workbench.action.reloadWindow');
                    }
                });
            } catch (verifyError: any) {
                outputChannel.appendLine(`✗ Verification failed: ${verifyError.message}`);
                throw verifyError;
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
                    setupDependencies(extensionPath, outputChannel);
                }
            });
            
            throw error;
        }
    });
}
