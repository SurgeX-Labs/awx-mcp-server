/**
 * Extension tests
 */

import * as assert from 'assert';
import * as vscode from 'vscode';
import { ConfigurationProvider } from '../../views/configurationProvider';
import { ConnectionStatusProvider } from '../../views/connectionStatusProvider';

suite('AWX MCP Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('Extension should be present', () => {
        assert.ok(vscode.extensions.getExtension('SurgeXlabs.awx-mcp-extension'));
    });

    test('Extension should activate', async () => {
        const ext = vscode.extensions.getExtension('SurgeXlabs.awx-mcp-extension');
        assert.ok(ext);
        if (ext) {
            await ext.activate();
            assert.strictEqual(ext.isActive, true);
        }
    });

    test('Commands should be registered', async () => {
        const commands = await vscode.commands.getCommands();
        const awxCommands = commands.filter(cmd => cmd.startsWith('awx-mcp.'));
        
        assert.ok(awxCommands.includes('awx-mcp.start'), 'Start command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.stop'), 'Stop command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.restart'), 'Restart command should be registered');
        // Note: Some commands may not be registered in test environment
        assert.ok(awxCommands.length > 0, 'Some AWX commands should be registered');
    });

    test('Configuration settings should be available', () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        
        assert.ok(config.has('pythonPath'), 'pythonPath setting should exist');
        assert.ok(config.has('autoStart'), 'autoStart setting should exist');
        assert.ok(config.has('logLevel'), 'logLevel setting should exist');
        assert.ok(config.has('enableMonitoring'), 'enableMonitoring setting should exist');
    });
});

// Provider tests moved to views.test.ts for better organization
