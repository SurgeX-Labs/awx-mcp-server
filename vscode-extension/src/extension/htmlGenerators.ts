/**
 * HTML generators for webviews
 */

import { ServerMetrics } from '../mcp/types';

/**
 * Generate HTML for server metrics webview
 */
export function getMetricsHtml(metrics: ServerMetrics): string {
    const statusIcon = metrics.running ? '🟢' : '🔴';
    const statusText = metrics.running ? 'Running' : 'Stopped';
    const statusColor = metrics.running ? '#4CAF50' : '#f44336';
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWX MCP Server Metrics</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .header {
            border-bottom: 2px solid var(--vscode-panel-border);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 600;
            margin-left: 10px;
        }
        .metric-card {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid var(--vscode-activityBar-foreground);
        }
        .metric-label {
            font-size: 12px;
            text-transform: uppercase;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: 600;
        }
        .metric-unit {
            font-size: 14px;
            opacity: 0.7;
            margin-left: 5px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${statusIcon} AWX MCP Server</h1>
        <span class="status-badge" style="background-color: ${statusColor}20; color: ${statusColor};">
            ${statusText}
        </span>
    </div>
    
    ${metrics.running ? `
    <div class="grid">
        <div class="metric-card">
            <div class="metric-label">Process ID</div>
            <div class="metric-value">${metrics.pid}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Uptime</div>
            <div class="metric-value">${metrics.uptime}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Total Requests</div>
            <div class="metric-value">${metrics.requestCount.toLocaleString()}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Errors</div>
            <div class="metric-value">${metrics.errorCount.toLocaleString()}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value">
                ${(() => {
                    const avgTime = metrics.avgResponseTime;
                    if (avgTime != null && !isNaN(Number(avgTime))) {
                        return Number(avgTime).toFixed(0);
                    }
                    return avgTime || '0';
                })()}
                <span class="metric-unit">ms</span>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value">
                ${metrics.requestCount > 0 
                    ? ((1 - metrics.errorCount / metrics.requestCount) * 100).toFixed(1)
                    : 0
                }
                <span class="metric-unit">%</span>
            </div>
        </div>
    </div>
    ` : `
    <p style="text-align: center; padding: 40px; opacity: 0.7;">
        Server is not running. Click "Start AWX MCP Server" to launch it.
    </p>
    `}
</body>
</html>`;
}

/**
 * Generate HTML for job templates webview
 */
export function getJobTemplatesHtml(templates: any[]): string {
    const templateRows = templates.map(template => `
        <tr>
            <td>${template.id}</td>
            <td><strong>${escapeHtml(template.name)}</strong></td>
            <td>${escapeHtml(template.description || 'N/A')}</td>
            <td><span class="type-badge">${template.type || 'job'}</span></td>
            <td>
                <button onclick="launchTemplate(${template.id}, '${escapeHtml(template.name)}')">
                    🚀 Launch
                </button>
            </td>
        </tr>
    `).join('');

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWX Job Templates</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .header {
            border-bottom: 2px solid var(--vscode-panel-border);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        th {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
        }
        tr:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        .type-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
        }
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 AWX Job Templates</h1>
        <p>Found ${templates.length} template(s)</p>
    </div>
    
    ${templates.length > 0 ? `
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Type</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            ${templateRows}
        </tbody>
    </table>
    ` : `
    <div class="empty-state">
        <h2>No templates found</h2>
        <p>Configure an AWX instance to see job templates</p>
    </div>
    `}
    
    <script>
        const vscode = acquireVsCodeApi();
        
        function launchTemplate(id, name) {
            vscode.postMessage({
                command: 'launchTemplate',
                templateId: id,
                templateName: name
            });
        }
    </script>
</body>
</html>`;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
