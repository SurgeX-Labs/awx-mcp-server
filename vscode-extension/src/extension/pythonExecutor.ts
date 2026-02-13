/**
 * Python command execution utilities
 */

import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';

/**
 * Execute Python command with AWX MCP server
 */
export async function executePythonCommand(
    extensionPath: string,
    script: string,
    outputChannel: vscode.OutputChannel,
    streamOutput: boolean = false
): Promise<string> {
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    
    // Set environment variables for Python subprocess
    const env = {
        ...process.env,
        PYTHONUNBUFFERED: '1'
    };
    
    return new Promise((resolve, reject) => {
        const proc = child_process.spawn(pythonPath, ['-c', script], { env });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data: Buffer) => {
            const text = data.toString();
            stdout += text;
            if (streamOutput) {
                outputChannel.append(text);
            }
        });
        
        proc.stderr.on('data', (data: Buffer) => {
            const text = data.toString();
            stderr += text;
            if (streamOutput) {
                outputChannel.append(text);
            }
        });
        
        proc.on('close', (code: number) => {
            if (code === 0) {
                resolve(stdout);
            } else {
                reject(new Error(stderr || `Process exited with code ${code}`));
            }
        });
        
        proc.on('error', (error: Error) => {
            reject(error);
        });
    });
}

/**
 * Generate Python script to call AWX MCP tools
 */
export function generatePythonScript(tool: string, args: any): string {
    const argsJson = JSON.stringify(args);
    
    return `
import asyncio
import json
import sys

# Import MCP server components
from awx_mcp_server.mcp_server import create_mcp_server
from awx_mcp_server.storage import ConfigManager, CredentialStore
from awx_mcp_server.clients import CompositeAWXClient
from awx_mcp_server.domain import CredentialType

async def main():
    """Execute MCP tool directly."""
    try:
        # Parse arguments
        args_dict = ${argsJson}
        
        # Create server instance
        server = create_mcp_server()
        
        # Get the tool handler directly
        # Since we can't easily call the MCP protocol handlers,
        # we'll reconstruct the logic here
        config_manager = ConfigManager()
        credential_store = CredentialStore()
        
        # Get active environment
        env = config_manager.get_active()
        
        # Get credentials
        try:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.PASSWORD)
            is_token = False
        except Exception:
            username, secret = credential_store.get_credential(env.env_id, CredentialType.TOKEN)
            is_token = True
        
        # Create client
        client = CompositeAWXClient(env, username, secret, is_token)
        
        # Execute the requested tool
        result = None
        
        if "${tool}" == "awx_templates_list":
            templates = await client.list_templates(
                filter=args_dict.get("filter"),
                page=args_dict.get("page", 1),
                page_size=args_dict.get("page_size", 25)
            )
            result = {"templates": [t.dict() for t in templates]}
            
        elif "${tool}" == "awx_jobs_list":
            jobs = await client.list_jobs(
                filter=args_dict.get("filter"),
                status=args_dict.get("status"),
                page=args_dict.get("page", 1),
                page_size=args_dict.get("page_size", 25)
            )
            result = {"jobs": [j.dict() for j in jobs]}
            
        elif "${tool}" == "awx_job_get":
            job_id = args_dict.get("job_id")
            if not job_id:
                raise ValueError("job_id is required")
            job = await client.get_job(job_id)
            result = {"job": job.dict()}
            
        elif "${tool}" == "awx_job_output":
            job_id = args_dict.get("job_id")
            if not job_id:
                raise ValueError("job_id is required")
            output = await client.get_job_output(job_id)
            result = {"output": output}
            
        else:
            raise ValueError(f"Unknown tool: ${tool}")
        
        # Print result as JSON
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        import traceback
        error_data = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_data), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
`;
}

/**
 * Execute AWX tool via Python MCP server
 */
export async function executeAwxTool(
    extensionPath: string,
    tool: string,
    args: any,
    outputChannel: vscode.OutputChannel
): Promise<any> {
    const script = generatePythonScript(tool, args);
    
    try {
        const output = await executePythonCommand(extensionPath, script, outputChannel, true);
        return JSON.parse(output);
    } catch (error: any) {
        // Try to parse JSON error from stderr
        try {
            const errorObj = JSON.parse(error.message);
            throw new Error(`${errorObj.type}: ${errorObj.error}`);
        } catch {
            throw error;
        }
    }
}
