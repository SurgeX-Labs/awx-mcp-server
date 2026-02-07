/**
 * AWX Copilot Chat Participant
 * Enables intelligent tool invocation through GitHub Copilot Chat
 */

import * as vscode from 'vscode';

export interface AWXTool {
    name: string;
    description: string;
    inputSchema: any;
}

export class AWXCopilotChatParticipant {
    private participant?: vscode.ChatParticipant;
    private tools: Map<string, AWXTool> = new Map();
    private mcpClient?: any; // Connection to MCP server

    constructor(
        private context: vscode.ExtensionContext,
        private outputChannel: vscode.OutputChannel
    ) {}

    /**
     * Register the AWX chat participant with Copilot
     */
    register(): vscode.Disposable | undefined {
        try {
            // Create chat participant
            this.participant = vscode.chat.createChatParticipant('awx-mcp.awx', this.handleChatRequest.bind(this));
            
            this.participant.iconPath = vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'awx-mcp.svg');
            
            // Set metadata
            if (this.participant) {
                // Description shown in chat participant picker
                (this.participant as any).description = 'AWX/Ansible Tower automation assistant';
                
                // Sample prompts to help users get started
                (this.participant as any).sampleRequest = 'List my job templates';
            }

            this.outputChannel.appendLine('✓ AWX Chat Participant registered');
            return this.participant;

        } catch (error: any) {
            this.outputChannel.appendLine(`⚠ Failed to register chat participant: ${error.message}`);
            this.outputChannel.appendLine('Note: Chat participant requires GitHub Copilot Chat extension');
            return undefined;
        }
    }

    /**
     * Handle incoming chat requests from Copilot
     */
    private async handleChatRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<vscode.ChatResult> {
        try {
            const userMessage = request.prompt;
            this.outputChannel.appendLine(`[Chat Request] ${userMessage}`);

            // Determine which AWX tool(s) to invoke based on the request
            const toolsToInvoke = await this.selectToolsForRequest(userMessage);

            if (toolsToInvoke.length === 0) {
                this.showHelp(stream);
                return { metadata: { command: 'help' } };
            }

            // Invoke the selected tools
            stream.progress('Connecting to AWX...');
            
            for (const tool of toolsToInvoke) {
                if (token.isCancellationRequested) {
                    break;
                }

                stream.progress(`Calling ${tool.displayName}...`);
                
                try {
                    const result = await this.invokeTool(tool.name, tool.args);
                    stream.markdown(`\n## ${tool.displayName}\n\n`);
                    stream.markdown(this.formatToolResult(tool.name, result));
                } catch (toolError: any) {
                    stream.markdown(`\n⚠️ Error: ${toolError.message}\n`);
                    this.outputChannel.appendLine(`[Tool Error] ${tool.name}: ${toolError.message}`);
                }
            }

            return { 
                metadata: { 
                    command: toolsToInvoke.map(t => t.name).join(','),
                    toolCount: toolsToInvoke.length
                } 
            };

        } catch (error: any) {
            stream.markdown(`\n❌ Error: ${error.message}\n`);
            this.outputChannel.appendLine(`[Chat Error] ${error.message}`);
            return { errorDetails: { message: error.message } };
        }
    }

    /**
     * Show help message
     */
    private showHelp(stream: vscode.ChatResponseStream): void {
        stream.markdown('I can help you with AWX/Ansible Tower tasks:\n\n');
        stream.markdown('**List Resources:**\n');
        stream.markdown('- List job templates\n');
        stream.markdown('- Show inventories\n');
        stream.markdown('- List projects\n\n');
        stream.markdown('**Job Management:**\n');
        stream.markdown('- Show recent jobs\n');
        stream.markdown('- Get job status\n');
        stream.markdown('- View job output/logs\n');
        stream.markdown('- Check failed job details\n');
        stream.markdown('- Launch/cancel jobs\n\n');
        stream.markdown('**Examples:**\n');
        stream.markdown('- `@awx List my job templates`\n');
        stream.markdown('- `@awx Show failed jobs`\n');
        stream.markdown('- `@awx Get output for job 123`\n');
        stream.markdown('- `@awx Why did job 456 fail?`\n\n');
        stream.markdown('What would you like to do?');
    }

    /**
     * Intelligently select which tools to invoke based on the user's request
     */
    private async selectToolsForRequest(userMessage: string): Promise<Array<{name: string, args: any, displayName: string}>> {
        const message = userMessage.toLowerCase();
        const tools: Array<{name: string, args: any, displayName: string}> = [];

        // Extract job ID from message if present (e.g., "job 123", "job #456", "job id 789")
        const jobIdMatch = message.match(/job\s*(?:#|id)?\s*(\d+)/);
        const jobId = jobIdMatch ? parseInt(jobIdMatch[1]) : null;

        // Environment management
        if (message.includes('environment') || message.includes('switch env') || message.includes('set env')) {
            if (message.includes('list') || message.includes('show')) {
                tools.push({
                    name: 'env_list',
                    args: {},
                    displayName: 'AWX Environments'
                });
            } else if (message.includes('active') || message.includes('current')) {
                tools.push({
                    name: 'env_get_active',
                    args: {},
                    displayName: 'Active Environment'
                });
            } else if (message.includes('test') || message.includes('check connection')) {
                tools.push({
                    name: 'env_test_connection',
                    args: {},
                    displayName: 'Connection Test'
                });
            }
        }

        // Job output/logs - HIGHEST PRIORITY for specific job queries
        if (jobId && (message.includes('output') || message.includes('log') || message.includes('stdout') || message.includes('console'))) {
            tools.push({
                name: 'awx_job_stdout',
                args: { job_id: jobId },
                displayName: `Job ${jobId} Output`
            });
        }

        // Job failure analysis
        if (jobId && (message.includes('fail') || message.includes('error') || message.includes('why') || message.includes('wrong'))) {
            tools.push({
                name: 'awx_job_failure_summary',
                args: { job_id: jobId },
                displayName: `Job ${jobId} Failure Analysis`
            });
        }

        // Job events
        if (jobId && (message.includes('event') || message.includes('detail') || message.includes('step'))) {
            tools.push({
                name: 'awx_job_events',
                args: { job_id: jobId, page: 1, page_size: 50 },
                displayName: `Job ${jobId} Events`
            });
        }

        // Specific job status
        if (jobId && !tools.length) {
            tools.push({
                name: 'awx_job_get',
                args: { job_id: jobId },
                displayName: `Job ${jobId} Status`
            });
        }

        // Job cancellation
        if (message.includes('cancel') && message.includes('job')) {
            if (jobId) {
                tools.push({
                    name: 'awx_job_cancel',
                    args: { job_id: jobId },
                    displayName: `Cancel Job ${jobId}`
                });
            }
        }

        // Job launch
        if (message.includes('launch') || message.includes('run') || message.includes('start') || message.includes('execute')) {
            const templateNameMatch = message.match(/template\s+["']?([^"']+)["']?/);
            if (templateNameMatch) {
                tools.push({
                    name: 'awx_job_launch',
                    args: { template_name: templateNameMatch[1].trim() },
                    displayName: `Launch Job Template`
                });
            }
        }

        // List jobs - failed jobs specifically
        if (message.includes('failed') && message.includes('job')) {
            tools.push({
                name: 'awx_jobs_list',
                args: { status: 'failed', page: 1, page_size: 10 },
                displayName: 'Failed Jobs'
            });
        }
        // List jobs - running jobs
        else if (message.includes('running') && message.includes('job')) {
            tools.push({
                name: 'awx_jobs_list',
                args: { status: 'running', page: 1, page_size: 10 },
                displayName: 'Running Jobs'
            });
        }
        // List jobs - recent/all jobs
        else if (message.includes('job') && (message.includes('list') || message.includes('recent') || message.includes('show all'))) {
            tools.push({
                name: 'awx_jobs_list',
                args: { page: 1, page_size: 10 },
                displayName: 'Recent Jobs'
            });
        }

        // Job Template queries
        if (message.includes('job template') || message.includes('template')) {
            if (!message.includes('launch') && !message.includes('run')) {
                const templateNameMatch = message.match(/template\s+["']?([^"']+)["']?/);
                if (templateNameMatch && (message.includes('get') || message.includes('show') || message.includes('detail'))) {
                    tools.push({
                        name: 'awx_template_get',
                        args: { name: templateNameMatch[1].trim() },
                        displayName: `Template Details`
                    });
                } else {
                    tools.push({
                        name: 'awx_templates_list',
                        args: { page: 1, page_size: 25 },
                        displayName: 'Job Templates'
                    });
                }
            }
        }

        // Inventory queries
        if (message.includes('inventor') || message.includes('host')) {
            tools.push({
                name: 'awx_inventories_list',
                args: { page: 1, page_size: 25 },
                displayName: 'Inventories'
            });
        }

        // Project queries
        if (message.includes('project')) {
            if (message.includes('update') || message.includes('sync') || message.includes('refresh')) {
                const projectNameMatch = message.match(/project\s+["']?([^"']+)["']?/);
                if (projectNameMatch) {
                    tools.push({
                        name: 'awx_project_update',
                        args: { name: projectNameMatch[1].trim() },
                        displayName: `Update Project`
                    });
                }
            } else {
                tools.push({
                    name: 'awx_projects_list',
                    args: { page: 1, page_size: 25 },
                    displayName: 'Projects'
                });
            }
        }

        return tools;
    }

    /**
     * Invoke an MCP tool
     */
    private async invokeTool(toolName: string, args: any): Promise<any> {
        // First, try to invoke via the MCP server using stdio
        try {
            const result = await this.invokeMCPTool(toolName, args);
            return result;
        } catch (error: any) {
            this.outputChannel.appendLine(`[Tool Invocation Failed] ${toolName}: ${error.message}`);
            throw new Error(`Failed to invoke ${toolName}: ${error.message}`);
        }
    }

    /**
     * Invoke MCP tool via the Python server
     */
    private async invokeMCPTool(toolName: string, args: any): Promise<any> {
        const config = vscode.workspace.getConfiguration('awx-mcp');
        const pythonPath = config.get<string>('pythonPath') || 'python';

        // Create Python script to invoke the tool directly using the AWX client
        const pythonScript = `
import sys
import json
import asyncio
sys.path.insert(0, r'${this.getBundledServerPath()}')

from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import CredentialType

async def invoke_tool():
    try:
        config_manager = ConfigManager()
        credential_store = CredentialStore()
        
        # Get active environment
        env = config_manager.get_active()
        
        # Get credentials
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
            is_token = False
        except:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        
        # Create client
        client = CompositeAWXClient(env, username, secret, is_token)
        
        # Invoke the appropriate method based on tool name
        tool = "${toolName}"
        args = ${JSON.stringify(args)}
        
        result = None
        
        # Environment Management
        if tool == "env_list":
            envs = config_manager.list()
            result = [{"id": e.env_id, "name": e.name, "url": e.url} for e in envs]
        elif tool == "env_get_active":
            env = config_manager.get_active()
            result = {"id": env.env_id, "name": env.name, "url": env.url}
        elif tool == "env_test_connection":
            result = await client.test_connection()
            
        # Job Templates
        elif tool == "awx_templates_list":
            templates = await client.list_job_templates(
                name_filter=args.get("name_filter"),
                page=args.get("page", 1),
                page_size=args.get("page_size", 25)
            )
            result = [{"id": t.id, "name": t.name, "description": t.description} for t in templates]
        elif tool == "awx_template_get":
            template = await client.get_job_template(args.get("name"))
            result = {"id": template.id, "name": template.name, "description": template.description}
            
        # Inventories
        elif tool == "awx_inventories_list":
            inventories = await client.list_inventories(
                page=args.get("page", 1),
                page_size=args.get("page_size", 25)
            )
            result = [{"id": i.id, "name": i.name, "description": i.description} for i in inventories]
            
        # Projects
        elif tool == "awx_projects_list":
            projects = await client.list_projects(
                page=args.get("page", 1),
                page_size=args.get("page_size", 25)
            )
            result = [{"id": p.id, "name": p.name, "description": p.description, "scm_type": p.scm_type, "scm_url": p.scm_url} for p in projects]
        elif tool == "awx_project_update":
            update_result = await client.update_project(args.get("name"))
            result = {"success": True, "message": f"Project update initiated for {args.get('name')}"}
            
        # Jobs - Execution
        elif tool == "awx_job_launch":
            job = await client.launch_job(
                args.get("template_name"),
                args.get("extra_vars")
            )
            result = {"id": job.id, "name": job.name, "status": job.status}
        elif tool == "awx_job_get":
            job = await client.get_job(args.get("job_id"))
            result = {
                "id": job.id,
                "name": job.name,
                "status": job.status,
                "started": str(job.started) if job.started else None,
                "finished": str(job.finished) if job.finished else None,
                "elapsed": job.elapsed
            }
        elif tool == "awx_jobs_list":
            jobs = await client.list_jobs(
                status_filter=args.get("status"),
                page=args.get("page", 1),
                page_size=args.get("page_size", 10)
            )
            result = [{"id": j.id, "name": j.name, "status": j.status, "started": str(j.started) if j.started else None} for j in jobs]
        elif tool == "awx_job_cancel":
            cancel_result = await client.cancel_job(args.get("job_id"))
            result = {"success": True, "message": f"Job {args.get('job_id')} canceled"}
            
        # Jobs - Output & Diagnostics
        elif tool == "awx_job_stdout":
            stdout = await client.get_job_stdout(args.get("job_id"))
            result = {"job_id": args.get("job_id"), "output": stdout}
        elif tool == "awx_job_events":
            events = await client.get_job_events(
                args.get("job_id"),
                args.get("page", 1),
                args.get("page_size", 50)
            )
            result = [{"event": e.event, "task": e.task, "role": e.role, "stdout": e.stdout} for e in events]
        elif tool == "awx_job_failure_summary":
            job = await client.get_job(args.get("job_id"))
            stdout = await client.get_job_stdout(args.get("job_id"))
            result = {
                "job_id": job.id,
                "name": job.name,
                "status": job.status,
                "elapsed": job.elapsed,
                "output_excerpt": stdout[-2000:] if len(stdout) > 2000 else stdout
            }
        else:
            raise ValueError(f"Unknown tool: {tool}")
        
        # Return result as JSON
        print(json.dumps({"success": True, "data": result}, default=str))
        
    except Exception as e:
        import traceback
        print(json.dumps({"success": False, "error": str(e), "type": type(e).__name__, "traceback": traceback.format_exc()}))

asyncio.run(invoke_tool())
`;

        // Invoke via Python subprocess
        return new Promise((resolve, reject) => {
            const { spawn } = require('child_process');
            
            const proc = spawn(pythonPath, ['-c', pythonScript]);

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data: Buffer) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data: Buffer) => {
                stderr += data.toString();
            });

            proc.on('close', (code: number) => {
                if (code !== 0) {
                    this.outputChannel.appendLine(`[Python Error] ${stderr}`);
                    reject(new Error(`Tool invocation failed: ${stderr}`));
                } else {
                    try {
                        const result = JSON.parse(stdout.trim());
                        if (result.success) {
                            resolve(result.data);
                        } else {
                            this.outputChannel.appendLine(`[Tool Error] ${result.traceback || result.error}`);
                            reject(new Error(`${result.type}: ${result.error}`));
                        }
                    } catch (e) {
                        this.outputChannel.appendLine(`[Parse Error] ${stdout}`);
                        reject(new Error(`Failed to parse tool result: ${stdout}`));
                    }
                }
            });

            proc.on('error', (error: Error) => {
                this.outputChannel.appendLine(`[Process Error] ${error.message}`);
                reject(error);
            });
        });
    }

    /**
     * Get path to bundled MCP server
     */
    private getBundledServerPath(): string {
        const path = require('path');
        return path.join(
            this.context.extensionPath,
            'bundled',
            'awx-mcp-server',
            'src'
        ).replace(/\\/g, '\\\\'); // Escape backslashes for Python string
    }

    /**
     * Format tool results for display in chat
     */
    private formatToolResult(toolName: string, result: any): string {
        if (!result) {
            return '_No results_';
        }

        // Job stdout - format as code block
        if (toolName === 'awx_job_stdout') {
            if (result.output) {
                return '```\n' + result.output + '\n```';
            }
        }

        // Job failure summary - format with highlights
        if (toolName === 'awx_job_failure_summary') {
            let output = `**Job ID:** ${result.job_id}\n`;
            output += `**Name:** ${result.name}\n`;
            output += `**Status:** ${result.status}\n`;
            output += `**Elapsed:** ${result.elapsed}s\n\n`;
            output += '**Output (last 2000 chars):**\n';
            output += '```\n' + result.output_excerpt + '\n```';
            return output;
        }

        // Job events - format as list
        if (toolName === 'awx_job_events') {
            if (Array.isArray(result) && result.length > 0) {
                let output = '';
                for (const event of result.slice(0, 20)) {
                    output += `- **${event.event}**`;
                    if (event.task) output += ` - ${event.task}`;
                    if (event.role) output += ` (${event.role})`;
                    if (event.stdout) output += `\n  \`${event.stdout.substring(0, 100)}\``;
                    output += '\n';
                }
                if (result.length > 20) {
                    output += `\n_... and ${result.length - 20} more events_`;
                }
                return output;
            }
        }

        // Single job details
        if (toolName === 'awx_job_get' && result.id) {
            let output = `**Job ID:** ${result.id}\n`;
            output += `**Name:** ${result.name}\n`;
            output += `**Status:** ${result.status}\n`;
            if (result.started) output += `**Started:** ${result.started}\n`;
            if (result.finished) output += `**Finished:** ${result.finished}\n`;
            if (result.elapsed) output += `**Elapsed:** ${result.elapsed}s\n`;
            return output;
        }

        // Environment list/active
        if (toolName === 'env_list' || toolName === 'env_get_active') {
            if (Array.isArray(result)) {
                let output = '';
                for (const env of result) {
                    output += `- **${env.name}** (${env.id})\n`;
                    output += `  URL: ${env.url}\n`;
                }
                return output;
            } else if (result.id) {
                return `**${result.name}** (${result.id})\nURL: ${result.url}`;
            }
        }

        // Connection test
        if (toolName === 'env_test_connection') {
            if (result.success || result === true) {
                return '✓ Connection successful';
            } else {
                return `✗ Connection failed: ${result.error || 'Unknown error'}`;
            }
        }

        // Job launch/cancel - show success message
        if (toolName === 'awx_job_launch' && result.id) {
            return `✓ Job launched successfully\n**Job ID:** ${result.id}\n**Name:** ${result.name}\n**Status:** ${result.status}`;
        }

        if (toolName === 'awx_job_cancel') {
            return result.message || '✓ Job canceled successfully';
        }

        if (toolName === 'awx_project_update') {
            return result.message || '✓ Project update initiated';
        }

        // Default: format as markdown
        return this.formatDataAsMarkdown(result);
    }

    /**
     * Format data structures as readable markdown
     */
    private formatDataAsMarkdown(data: any): string {
        if (!data) {
            return '_No data_';
        }

        // Handle arrays of items (common for list operations)
        if (Array.isArray(data)) {
            return this.formatListAsMarkdown(data);
        }

        // Handle object with results array
        if (data.results && Array.isArray(data.results)) {
            let output = '';
            if (data.count) {
                output += `**Total:** ${data.count}\n\n`;
            }
            output += this.formatListAsMarkdown(data.results);
            return output;
        }

        // Fallback to JSON
        return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
    }

    /**
     * Format an array of items as a markdown table or list
     */
    private formatListAsMarkdown(items: any[]): string {
        if (items.length === 0) {
            return '_No items found_';
        }

        // For small lists, use a simple list format
        if (items.length <= 3) {
            let output = '';
            for (const item of items) {
                output += `- **${item.name || item.id}**`;
                if (item.description) {
                    output += `: ${item.description}`;
                }
                output += '\n';
            }
            return output;
        }

        // For larger lists, create a table
        const keys = Object.keys(items[0]).slice(0, 4); // Limit to first 4 columns
        let table = '| ' + keys.join(' | ') + ' |\n';
        table += '| ' + keys.map(() => '---').join(' | ') + ' |\n';

        for (const item of items.slice(0, 10)) { // Limit to first 10 rows
            table += '| ' + keys.map(k => String(item[k] || '').substring(0, 50)).join(' | ') + ' |\n';
        }

        if (items.length > 10) {
            table += `\n_... and ${items.length - 10} more items_`;
        }

        return table;
    }

    /**
     * Update available tools from MCP server
     */
    async updateTools(): Promise<void> {
        try {
            // In a real implementation, query the MCP server for available tools
            // For now, we'll define them statically based on the AWX MCP server capabilities
            
            const defaultTools: AWXTool[] = [
                {
                    name: 'awx_list_job_templates',
                    description: 'List all job templates in AWX',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            page: { type: 'number' },
                            page_size: { type: 'number' }
                        }
                    }
                },
                {
                    name: 'awx_list_inventories',
                    description: 'List all inventories in AWX',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            page: { type: 'number' },
                            page_size: { type: 'number' }
                        }
                    }
                },
                {
                    name: 'awx_list_projects',
                    description: 'List all projects in AWX',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            page: { type: 'number' },
                            page_size: { type: 'number' }
                        }
                    }
                },
                {
                    name: 'awx_list_jobs',
                    description: 'List recent jobs in AWX',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            page: { type: 'number' },
                            page_size: { type: 'number' }
                        }
                    }
                }
            ];

            for (const tool of defaultTools) {
                this.tools.set(tool.name, tool);
            }

            this.outputChannel.appendLine(`✓ Loaded ${this.tools.size} AWX tools`);

        } catch (error: any) {
            this.outputChannel.appendLine(`⚠ Failed to update tools: ${error.message}`);
        }
    }

    dispose() {
        // Cleanup
        this.participant?.dispose();
    }
}
