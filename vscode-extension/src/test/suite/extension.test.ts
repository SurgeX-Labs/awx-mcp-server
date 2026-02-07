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
        assert.ok(vscode.extensions.getExtension('awx-mcp-team.awx-mcp-extension'));
    });

    test('Extension should activate', async () => {
        const ext = vscode.extensions.getExtension('awx-mcp-team.awx-mcp-extension');
        assert.ok(ext);
        await ext!.activate();
        assert.strictEqual(ext!.isActive, true);
    });

    test('Commands should be registered', async () => {
        const commands = await vscode.commands.getCommands();
        const awxCommands = commands.filter(cmd => cmd.startsWith('awx-mcp.'));
        
        assert.ok(awxCommands.includes('awx-mcp.start'), 'Start command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.stop'), 'Stop command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.restart'), 'Restart command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.addInstance'), 'Add instance command should be registered');
        assert.ok(awxCommands.includes('awx-mcp.testConnection'), 'Test connection command should be registered');
    });

    test('Configuration settings should be available', () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        
        assert.ok(config.has('pythonPath'), 'pythonPath setting should exist');
        assert.ok(config.has('autoStart'), 'autoStart setting should exist');
        assert.ok(config.has('logLevel'), 'logLevel setting should exist');
        assert.ok(config.has('enableMonitoring'), 'enableMonitoring setting should exist');
    });
});

suite('Configuration Provider Tests', () => {
    let context: vscode.ExtensionContext;
    let configProvider: ConfigurationProvider;

    suiteSetup(async () => {
        const ext = vscode.extensions.getExtension('awx-mcp-team.awx-mcp-extension');
        await ext!.activate();
        context = (ext!.exports as any).context;
    });

    test('Should create configuration provider', () => {
        configProvider = new ConfigurationProvider(context);
        assert.ok(configProvider);
    });

    test('Should handle empty instances list', async () => {
        configProvider = new ConfigurationProvider(context);
        const instances = await configProvider.getInstances();
        assert.ok(Array.isArray(instances));
    });
});

suite('Connection Status Provider Tests', () => {
    let context: vscode.ExtensionContext;
    let configProvider: ConfigurationProvider;
    let statusProvider: ConnectionStatusProvider;

    suiteSetup(async () => {
        const ext = vscode.extensions.getExtension('awx-mcp-team.awx-mcp-extension');
        await ext!.activate();
        context = (ext!.exports as any).context;
        configProvider = new ConfigurationProvider(context);
    });

    test('Should create connection status provider', () => {
        statusProvider = new ConnectionStatusProvider(configProvider, context);
        assert.ok(statusProvider);
    });

    test('Should refresh status', () => {
        statusProvider = new ConnectionStatusProvider(configProvider, context);
        assert.doesNotThrow(() => statusProvider.refresh());
    });
});
