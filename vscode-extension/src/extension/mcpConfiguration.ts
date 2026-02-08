/**
 * MCP server configuration for GitHub Copilot Chat
 */

import * as vscode from 'vscode';

/**
 * Configure AWX MCP server for GitHub Copilot Chat
 * This configures the server in VS Code settings so Copilot can discover it
 */
export async function configureMcpServer(outputChannel: vscode.OutputChannel): Promise<void> {
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
        
        // Configure AWX MCP server with slot-filling behavior
        mcpServers['awx-mcp'] = {
            command: pythonPath,
            args: ['-m', 'awx_mcp_server'],
            env: {
                LOG_LEVEL: logLevel,
                PYTHONUNBUFFERED: '1'
            }
        };
        
        // Update settings
        await config.update('github.copilot.chat.mcpServers', mcpServers, vscode.ConfigurationTarget.Global);
        
        outputChannel.appendLine('✓ AWX MCP Server configured for GitHub Copilot Chat');
        outputChannel.appendLine(`  Command: ${pythonPath} -m awx_mcp_server`);
        outputChannel.appendLine(`  Log Level: ${logLevel}`);
        outputChannel.appendLine('');
        outputChannel.appendLine('🎉 Setup Complete!');
        outputChannel.appendLine('');
        outputChannel.appendLine('GitHub Copilot Chat can now use AWX MCP tools with intelligent slot-filling:');
        outputChannel.appendLine('');
        outputChannel.appendLine('✅ Validates required fields before AWX calls');
        outputChannel.appendLine('✅ Asks follow-up questions for missing values');
        outputChannel.appendLine('✅ Uses resume flow to continue after answers');
        outputChannel.appendLine('✅ Prefers fewer questions (e.g., gets latest failed job automatically)');
        outputChannel.appendLine('✅ Summarizes logs with actionable fix suggestions');
        outputChannel.appendLine('');
        outputChannel.appendLine('To use AWX MCP with Copilot Chat:');
        outputChannel.appendLine('  1. Open Copilot Chat (Ctrl+Alt+I or Cmd+Alt+I)');
        outputChannel.appendLine('  2. Use @awx to interact:');
        outputChannel.appendLine('     • "@awx show output for job 123"');
        outputChannel.appendLine('     • "@awx get logs for the failed job"');
        outputChannel.appendLine('     • "@awx list failed jobs"');
        outputChannel.appendLine('     • "@awx launch template MyTemplate"');
        outputChannel.appendLine('');
        outputChannel.appendLine('💡 If values are missing, Copilot will ask you in chat!');
        outputChannel.appendLine('   (No need to remember exact job IDs or parameter names)');
        
        // Show success notification
        const result = await vscode.window.showInformationMessage(
            'AWX MCP Server configured with intelligent slot-filling for Copilot Chat!',
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
        showManualConfigurationInstructions(outputChannel);
        
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

/**
 * Show manual configuration instructions
 */
function showManualConfigurationInstructions(outputChannel: vscode.OutputChannel): void {
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
}
