# Extension Module Structure

This directory contains modularized components of the AWX MCP VS Code extension, breaking down the original 1000+ line extension.ts into focused, maintainable modules.

## Architecture

```
extension/
├── dependencies.ts         - Dependency checking and setup
├── mcpConfiguration.ts     - MCP server configuration for GitHub Copilot
├── htmlGenerators.ts       - Webview HTML generation  
├── pythonExecutor.ts       - Python command execution utilities
├── commands.ts             - Command registration and handlers
└── README.md              - This file
```

## Modules

### dependencies.ts
Handles Python environment setup and verification.

**Functions:**
- `execCommand(command, args)` - Execute system commands
- `checkDependencies(outputChannel)` - Verify Python and packages
- `setupDependencies(extensionPath, outputChannel)` - Install AWX MCP Server

**Usage:**
```typescript
import { checkDependencies, setupDependencies } from './extension/dependencies';

const success = await checkDependencies(outputChannel);
if (!success) {
    await setupDependencies(context.extensionPath, outputChannel);
}
```

### mcpConfiguration.ts
Configures AWX MCP server for GitHub Copilot Chat integration.

**Functions:**
- `configureMcpServer(outputChannel)` - Register MCP server in VS Code settings
- `showManualConfigurationInstructions(outputChannel)` - Display manual setup guide

**Behavior:**
- Adds `awx-mcp` to `github.copilot.chat.mcpServers` setting
- Configures Python command and environment variables
- Documents slot-filling capabilities for users
- Shows follow-up actions (Open Chat, Add Instance, View Settings)

**Usage:**
```typescript
import { configureMcpServer } from './extension/mcpConfiguration';

await configureMcpServer(outputChannel);
```

### htmlGenerators.ts
Generates HTML for webview panels.

**Functions:**
- `getMetricsHtml(metrics)` - Server metrics dashboard HTML
- `getJobTemplatesHtml(templates)` - Job templates list HTML
- `escapeHtml(text)` - Sanitize HTML strings

**Usage:**
```typescript
import { getMetricsHtml, getJobTemplatesHtml } from './extension/htmlGenerators';

const panel = vscode.window.createWebviewPanel('metrics', 'Metrics', vscode.ViewColumn.One, {});
panel.webview.html = getMetricsHtml(metrics);
```

### pythonExecutor.ts
Handles Python subprocess execution for AWX operations.

**Functions:**
- `executePythonCommand(extensionPath, script, outputChannel, streamOutput)` - Run Python scripts
- `generatePythonScript(tool, args)` - Create Python AWX MCP tool invocation
- `executeAwxTool(extensionPath, tool, args, outputChannel)` - Call AWX tools via Python

**Usage:**
```typescript
import { executeAwxTool } from './extension/pythonExecutor';

const result = await executeAwxTool(
    context.extensionPath,
    'awx.list_job_templates',
    { profile: 'production' },
    outputChannel
);
```

### commands.ts
Centralized command registration for all VS Code commands.

**Functions:**
- `registerCommands(context, serverManager, configProvider, ...)` - Register all extension commands

**Commands Registered:**
- Server management: `start`, `stop`, `restart`, `status`
- MCP configuration: `configureCopilot`
- Instance management: `addInstance`, `editInstance`, `removeInstance`, `testConnection`
- Utilities: `listJobTemplates`, `viewMetrics`, `setupDependencies`

**Usage:**
```typescript
import { registerCommands } from './extension/commands';

registerCommands(
    context,
    serverManager,
    configProvider,
    configWebview,
    connectionStatusProvider,
    outputChannel
);
```

## Integration with Main Extension

The main [extension.ts](../extension.ts) orchestrates these modules:

```typescript
import { registerCommands } from './extension/commands';
import { checkDependencies, setupDependencies } from './extension/dependencies';
import { configureMcpServer } from './extension/mcpConfiguration';

export function activate(context: vscode.ExtensionContext) {
    // Check dependencies
    checkDependencies(outputChannel).then(success => {
        if (success) {
            configureMcpServer(outputChannel);
        } else {
            // Show setup prompt
        }
    });
    
    // Initialize providers
    // ...
    
    // Register all commands
    registerCommands(context, serverManager, configProvider, ...);
}
```

## Benefits of Modularization

1. **Maintainability**: Each module has a single, clear responsibility
2. **Testability**: Modules can be unit tested in isolation
3. **Readability**: 130-line orchestrator vs. 1000+ line monolith
4. **Reusability**: Functions can be imported where needed
5. **Collaboration**: Multiple developers can work on different modules

## Related Modules

- **[mcp/](../mcp/)**: MCP server lifecycle management (Python resolution, server start/stop, uptime)
- **[awx/](../awx/)**: AWX Copilot Chat participant (tool selection, invocation, formatting)

## Migration Notes

- **Original files backed up**: `extension.ts.backup`, `mcpServerManager.ts.backup`
- **Line count reduction**:
  - extension.ts: 995 lines → 136 lines (86% reduction)
  - mcpServerManager.ts: 289 lines → 145 lines (50% reduction)
- **No breaking changes**: All public APIs maintained
- **TypeScript compilation**: ✓ Successful with no errors

## Future Enhancements

1. **Slot-filling behavior**: Implement MCP resume flow for interactive prompts
2. **Error handling**: Add retry logic and user-friendly error messages
3. **Testing**: Add unit tests for each module
4. **Logging**: Structured logging with log levels
5. **Configuration validation**: Validate AWX instance configs before saving
