/**
 * Shared types for AWX extension
 */

export interface AWXTool {
    name: string;
    description: string;
    inputSchema: any;
}

export interface ToolInvocation {
    name: string;
    args: any;
    displayName: string;
}

export interface ToolResult {
    success: boolean;
    data?: any;
    error?: string;
    type?: string;
    traceback?: string;
    needsInput?: boolean;
    missing?: Array<{
        name: string;
        prompt: string;
        choices?: string[];
        required: boolean;
    }>;
    resumeToken?: string;
}
