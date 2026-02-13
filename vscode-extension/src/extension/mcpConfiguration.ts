/**
 * MCP server configuration for GitHub Copilot Chat
 * 
 * Note: This is OPTIONAL. Users can configure AWX MCP server directly in their VS Code settings
 * following the industry standard pattern (like Postman MCP, Claude MCP).
 * 
 * This extension provides UI enhancements (sidebar, views) but MCP configuration can work independently.
 */

import * as vscode from 'vscode';

/**
 * Configure AWX MCP server for GitHub Copilot Chat
 * Detects if user has already configured MCP manually and respects their configuration.
 * Only auto-configures if no existing MCP configuration found.
 */
export async function configureMcpServer(outputChannel: vscode.OutputChannel): Promise<void> {
    try {
        const config = vscode.workspace.getConfiguration();
        
        // Check if GitHub Copilot supports MCP configuration
        const inspect = config.inspect('github.copilot.chat.mcpServers');
        if (!inspect) {
            outputChannel.appendLine('ℹ️  Industry Standard MCP Configuration Available:');
            outputChannel.appendLine('   You can configure AWX MCP server directly in VS Code settings');
            outputChannel.appendLine('   See: MCP_COPILOT_SETUP.md for instructions');
            outputChannel.appendLine('   This extension provides optional UI enhancements only');
            outputChannel.appendLine('');
            return;
        }
        
        const mcpServers = config.get<{[key: string]: any}>('github.copilot.chat.mcpServers') || {};
        
        // Check if user has already configured AWX MCP manually (any variation)
        const existingAwxConfig = Object.keys(mcpServers).find(key => 
            key.toLowerCase().includes('awx') || 
            (mcpServers[key].command && 
             mcpServers[key].args && 
             mcpServers[key].args.some((arg: string) => arg.includes('awx_mcp_server')))
        );
        
        if (existingAwxConfig) {
            outputChannel.appendLine(`✓ AWX MCP Server already configured as "${existingAwxConfig}"`);
            outputChannel.appendLine('  Using your manual configuration (Industry Standard pattern)');
            outputChannel.appendLine('  Extension providing UI enhancements only');
            outputChannel.appendLine('');
            return;
        }
        
        // Get Python path and extension details
        const awxConfig = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = awxConfig.get<string>('pythonPath') || 'python';
        const logLevel = awxConfig.get<string>('logLevel') || 'info';
        
        // Auto-configure for convenience (extension mode)
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
        
        outputChannel.appendLine('✓ AWX MCP Server auto-configured (Extension Mode)');
        outputChannel.appendLine('  Alternative: Configure manually for Industry Standard pattern');
        outputChannel.appendLine('  See: MCP_COPILOT_SETUP.md');
        outputChannel.appendLine('');
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
        outputChannel.appendLine(`ℹ️  Could not configure MCP server automatically: ${error.message}`);
        outputChannel.appendLine('   The @awx chat participant will work without this configuration');
        outputChannel.appendLine('');
        
        // Only show manual config if user wants to see it
        const isConfigError = error.message.includes('not a registered configuration');
        if (!isConfigError) {
            showManualConfigurationInstructions(outputChannel);
        }
        
        // Don't show error UI for missing MCP support
        if (!isConfigError) {
            vscode.window.showInformationMessage(
                'AWX MCP chat participant is ready. MCP tools require GitHub Copilot with MCP support.',
                'View Output'
            ).then(selection => {
                if (selection === 'View Output') {
                    outputChannel.show();
                }
            });
        }
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
