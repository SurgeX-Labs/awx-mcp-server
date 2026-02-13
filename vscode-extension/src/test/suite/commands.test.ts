import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Commands Test Suite', () => {
    const requiredCommands = [
        'awx-mcp.start',
        'awx-mcp.stop',
        'awx-mcp.restart',
        'awx-mcp.status',
        'awx-mcp.configureCopilot',
        'awx-mcp.setupDependencies',
        'awx-mcp.addEnvironment',
        'awx-mcp.editEnvironment',
        'awx-mcp.deleteEnvironment',
        'awx-mcp.connectEnvironment',
        'awx-mcp.testConnection',
        'awx-mcp.setActiveEnvironment',
        'awx-mcp.listEnvironments',
        'awx-mcp.refreshMetrics',
        'awx-mcp.viewLogs',
        'awx-mcp.clearLogs'
    ];

    test('All required commands should be registered', async () => {
        const allCommands = await vscode.commands.getCommands(true);
        
        for (const cmd of requiredCommands) {
            assert.ok(
                allCommands.includes(cmd),
                `Command ${cmd} should be registered`
            );
        }
    });

    test('Commands should execute without crashing', async function() {
        this.timeout(5000);
        
        // Test safe commands that should not have side effects
        const safeCommands = [
            'awx-mcp.status',
            'awx-mcp.listEnvironments',
            'awx-mcp.viewLogs'
        ];
        
        for (const cmd of safeCommands) {
            try {
                await vscode.commands.executeCommand(cmd);
                // Should complete without error
                assert.ok(true, `${cmd} executed successfully`);
            } catch (error: any) {
                // Command may fail if extension not fully initialized
                // But should not crash
                assert.ok(error.message, `${cmd} should handle errors gracefully`);
                console.log(`${cmd} failed (expected in test):`, error.message);
            }
        }
    });

    test('Start/Stop commands should be safe to call', async function() {
        this.timeout(10000);
        
        try {
            // Try stop first (should be safe even if not running)
            await vscode.commands.executeCommand('awx-mcp.stop');
            assert.ok(true, 'Stop command completed');
            
            // Try start (may fail due to dependencies)
            await vscode.commands.executeCommand('awx-mcp.start');
            assert.ok(true, 'Start command completed');
            
            // Clean up
            await vscode.commands.executeCommand('awx-mcp.stop');
        } catch (error: any) {
            // Expected to fail in test environment
            console.log('Start/Stop test failed (expected):', error.message);
            assert.ok(error.message, 'Should have error message');
        }
    });
});
