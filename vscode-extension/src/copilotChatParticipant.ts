/**
 * AWX Copilot Chat Participant  
 * Enables intelligent tool invocation through GitHub Copilot Chat
 * 
 * This module serves as the orchestrator, delegating to specialized modules:
 * - awx/help.ts: Help messages and documentation
 * - awx/toolSelector.ts: NLP logic for selecting tools
 * - awx/toolInvoker.ts: Tool execution via Python subprocess
 * - awx/formatters.ts: Result and error formatting
 */

import * as vscode from 'vscode';
import { AWXTool } from './awx/types';
import { showHelp, getDescription, getSampleRequest } from './awx/help';
import { selectToolsForRequest } from './awx/toolSelector';
import { invokeTool } from './awx/toolInvoker';
import { formatToolResult, formatErrorMessage } from './awx/formatters';
import { parseAnswersFromMessage } from './awx/answerParser';

export { AWXTool };

export class AWXCopilotChatParticipant {
    private participant?: vscode.ChatParticipant;
    private tools: Map<string, AWXTool> = new Map();

    constructor(
        private context: vscode.ExtensionContext,
        private outputChannel: vscode.OutputChannel
    ) {}

    /**
     * Register the AWX chat participant with Copilot
     */
    register(): vscode.Disposable | undefined {
        try {
            this.participant = vscode.chat.createChatParticipant('awx-mcp.awx', this.handleChatRequest.bind(this));
            
            this.participant.iconPath = vscode.Uri.joinPath(this.context.extensionUri, 'resources', 'awx-mcp.svg');
            
            if (this.participant) {
                (this.participant as any).description = getDescription();
                (this.participant as any).sampleRequest = getSampleRequest();
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
     * Implements slot-filling behavior for interactive parameter collection
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
            
            // Check if this is a resume flow (user providing answers to previous questions)
            const contextResumeToken = (context.history as any)?.resumeToken;
            if (contextResumeToken && !userMessage.toLowerCase().startsWith('help')) {
                // User is providing answers, resume the tool call
                stream.markdown('📝 Resuming with your input...\n\n');
                
                // Parse user's answer
                const answers = parseAnswersFromMessage(userMessage);
                this.outputChannel.appendLine(`[Parsed Answers] ${JSON.stringify(answers)}`);
                
                // Invoke tool with resume token
                const result = await invokeTool(
                    'resume',
                    { resume_token: contextResumeToken, answers },
                    this.context.extensionPath,
                    this.outputChannel
                );
                
                // Handle result
                if (result.needsInput) {
                    // Still need more info
                    stream.markdown('❓ **I still need more information:**\n\n');
                    for (const field of result.missing!) {
                        stream.markdown(`• **${field.name}**: ${field.prompt}\n`);
                        if (field.choices) {
                            stream.markdown(`  Choices: ${field.choices.map(c => `\`${c}\``).join(', ')}\n`);
                        }
                    }
                    return { 
                        metadata: { 
                            command: 'resume_partial',
                            resumeToken: result.resumeToken 
                        } 
                    };
                } else if (result.success) {
                    stream.markdown('✅ **Operation completed!**\n\n');
                    stream.markdown(formatToolResult('resumed', result.data));
                    return { metadata: { command: 'resume_complete' } };
                } else {
                    stream.markdown(formatErrorMessage(new Error(result.error!), 'resumed'));
                    return { metadata: { command: 'resume_error' } };
                }
            }

            // Use toolSelector module for NLP
            const toolsToInvoke = await selectToolsForRequest(userMessage);

            if (toolsToInvoke.length === 0) {
                showHelp(stream);
                return { metadata: { command: 'help' } };
            }

            stream.progress('Connecting to AWX...');
            
            for (const tool of toolsToInvoke) {
                if (token.isCancellationRequested) {
                    break;
                }

                stream.progress(`Calling ${tool.displayName}...`);
                
                try {
                    // Use toolInvoker module for execution (with slot-filling)
                    const result = await invokeTool(
                        tool.name, 
                        tool.args, 
                        this.context.extensionPath,
                        this.outputChannel
                    );
                    
                    // Handle slot-filling: missing required parameters
                    if (result.needsInput && result.missing) {
                        stream.markdown('❓ **I need more information to continue:**\n\n');
                        
                        for (const field of result.missing) {
                            stream.markdown(`• **${field.name}**: ${field.prompt}\n`);
                            
                            if (field.choices && field.choices.length > 0) {
                                stream.markdown(`  Choices: ${field.choices.map(c => `\`${c}\``).join(', ')}\n`);
                            }
                        }
                        
                        stream.markdown('\n💡 **Just reply with the missing information, and I\'ll continue automatically!**\n');
                        
                        return { 
                            metadata: { 
                                command: tool.name,
                                needsInput: true,
                                resumeToken: result.resumeToken
                            } 
                        };
                    }
                    
                    // Use formatters module for display
                    if (result.success) {
                        stream.markdown(`\n## ${tool.displayName}\n\n`);
                        stream.markdown(formatToolResult(tool.name, result.data));
                    } else {
                        stream.markdown(`\n❌ **${tool.displayName} failed:**\n\n`);
                        stream.markdown(result.error || 'Unknown error');
                    }
                } catch (toolError: any) {
                    // Use formatters module for errors
                    const errorMessage = formatErrorMessage(toolError, tool.name);
                    stream.markdown(`\n❌ **Error in ${tool.displayName}:**\n\n${errorMessage}\n`);
                    this.outputChannel.appendLine(`[Tool Error] ${tool.name}: ${toolError.message}`);
                    
                    if (toolError.traceback) {
                        this.outputChannel.appendLine(`[Traceback]\n${toolError.traceback}`);
                    }
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
     * Update available tools from MCP server
     */
    async updateTools(): Promise<void> {
        // Tool discovery logic can be added here if needed
        this.outputChannel.appendLine('Tools updated');
    }

    dispose() {
        this.participant?.dispose();
    }
}
