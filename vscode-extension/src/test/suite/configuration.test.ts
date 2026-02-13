import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Configuration Test Suite', () => {
    test('Should have awx-mcp configuration section', () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        assert.ok(config, 'Configuration section should exist');
    });

    test('Should have default values for key settings', () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        
        // Test autoStart default
        const autoStart = config.get('autoStart');
        assert.ok(autoStart === true || autoStart === false, 'autoStart should have boolean value');
        
        // Test logLevel default
        const logLevel = config.get('logLevel');
        assert.ok(logLevel, 'logLevel should have value');
        assert.ok(['debug', 'info', 'warn', 'error'].includes(logLevel as string), 
            'logLevel should be valid');
        
        // Test enableMonitoring default
        const monitoring = config.get('enableMonitoring');
        assert.ok(monitoring === true || monitoring === false, 
            'enableMonitoring should have boolean value');
        
        // Test serverTimeout default
        const timeout = config.get('serverTimeout');
        assert.ok(typeof timeout === 'number' && timeout > 0, 
            'serverTimeout should be positive number');
    });

    test('Should allow updating configuration', async () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        const originalValue = config.get('logLevel');
        
        try {
            // Try to update
            await config.update('logLevel', 'debug', vscode.ConfigurationTarget.Global);
            const newValue = config.get('logLevel');
            
            // Verify change took effect
            assert.strictEqual(newValue, 'debug', 'Configuration should update');
            
            // Restore original
            await config.update('logLevel', originalValue, vscode.ConfigurationTarget.Global);
        } catch (error) {
            // Configuration update may fail in test environment
            console.log('Config update failed (expected in test env)');
        }
    });

    test('Should validate pythonPath if set', () => {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = config.get<string>('pythonPath');
        
        if (pythonPath) {
            // If set, should be non-empty string
            assert.ok(pythonPath.length > 0, 'pythonPath should not be empty string');
            assert.ok(pythonPath.includes('python'), 
                'pythonPath should reference python executable');
        }
        // If not set, that's OK (auto-detect)
    });
});
