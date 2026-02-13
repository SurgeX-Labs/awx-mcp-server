import * as assert from 'assert';
import { MetricsProvider } from '../../views/metricsProvider';
import { LogsProvider } from '../../views/logsProvider';
import { EnvironmentTreeProvider } from '../../views/environmentTreeProvider';
import { MCPServerManager } from '../../mcpServerManager';

suite('Views Test Suite', () => {
    // Create mock dependencies for testing
    const mockContext = {} as any;
    const mockOutputChannel = {
        appendLine: () => {},
        append: () => {},
        show: () => {}
    } as any;
    const mockStatusBar = {
        text: '',
        show: () => {},
        hide: () => {}
    } as any;

    test('MetricsProvider should initialize', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new MetricsProvider(serverManager);
        assert.ok(provider, 'MetricsProvider should be created');
        
        const children = await provider.getChildren();
        assert.ok(Array.isArray(children), 'Should return children array');
    });

    test('MetricsProvider should track requests', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new MetricsProvider(serverManager);
        
        // Track successful request
        provider.trackRequest(true, 100);
        
        const children = await provider.getChildren();
        assert.ok(children.length > 0, 'Should have metrics items');
        
        // Verify totalRequests increased
        const totalItem = children.find(item => 
            item.label && item.label.toString().includes('Total Requests')
        );
        assert.ok(totalItem, 'Should have Total Requests item');
    });

    test('MetricsProvider should calculate success rate', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new MetricsProvider(serverManager);
        
        // Track some requests
        provider.trackRequest(true, 100);
        provider.trackRequest(true, 150);
        provider.trackRequest(false, 200);
        
        const children = await provider.getChildren();
        const successRateItem = children.find(item => 
            item.label && item.label.toString().includes('Success Rate')
        );
        
        assert.ok(successRateItem, 'Should have Success Rate item');
        // 2 successful out of 3 total = 66.67%
        assert.ok(successRateItem.label?.toString().includes('66.67%'), 
            'Should show correct success rate');
    });

    test('LogsProvider should initialize', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new LogsProvider(serverManager);
        assert.ok(provider, 'LogsProvider should be created');
        
        const children = await provider.getChildren();
        assert.ok(Array.isArray(children), 'Should return children array');
    });

    test('LogsProvider should log requests', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new LogsProvider(serverManager);
        
        provider.logRequest('list_job_templates', { limit: 10 });
        
        const children = await provider.getChildren();
        assert.ok(children.length > 0, 'Should have log entries');
        
        const requestLog = children.find(item => 
            item.label && item.label.toString().includes('list_job_templates')
        );
        assert.ok(requestLog, 'Should have request log entry');
    });

    test('LogsProvider should log responses', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new LogsProvider(serverManager);
        
        provider.logResponse('list_job_templates', true, 250);
        
        const children = await provider.getChildren();
        assert.ok(children.length > 0, 'Should have log entries');
        
        const responseLog = children.find(item => 
            item.label && item.label.toString().includes('list_job_templates')
        );
        assert.ok(responseLog, 'Should have response log entry');
    });

    test('LogsProvider should respect max log limit', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new LogsProvider(serverManager);
        
        // Add more than 100 logs
        for (let i = 0; i < 150; i++) {
            provider.logRequest(`test_tool_${i}`, {});
        }
        
        const children = await provider.getChildren();
        assert.ok(children.length <= 100, 'Should not exceed 100 logs');
    });

    test('EnvironmentTreeProvider should initialize', async () => {
        const serverManager = new MCPServerManager(mockContext, mockOutputChannel, mockStatusBar);
        const provider = new EnvironmentTreeProvider(serverManager);
        assert.ok(provider, 'EnvironmentTreeProvider should be created');
        
        const children = await provider.getChildren();
        assert.ok(Array.isArray(children), 'Should return children array');
    });
});
