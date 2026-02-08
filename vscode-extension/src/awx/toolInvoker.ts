/**
 * Tool invocation logic - handles calling AWX tools via Python subprocess
 * Includes slot-filling validation for missing parameters
 */

import * as vscode from 'vscode';
import { ToolResult } from './types';
import { validateToolArguments, optimizeToolInvocation, resumeToolInvocation } from './slotFilling';

/**
 * Invoke an AWX tool via Python subprocess with slot-filling validation
 */
export async function invokeTool(
    toolName: string,
    args: any,
    extensionPath: string,
    outputChannel: vscode.OutputChannel
): Promise<ToolResult> {
    try {
        // Check if this is a resume call
        if (args.resume_token) {
            return await resumeToolCall(args.resume_token, args.answers || {}, extensionPath, outputChannel);
        }
        
        // Try optimization first (e.g., get latest failed job instead of asking for job_id)
        const optimization = optimizeToolInvocation(toolName, args);
        if (optimization.optimized) {
            outputChannel.appendLine(`[Optimization] ${optimization.explanation}`);
            
            // Execute alternative tool first
            const altResult = await invokeMCPTool(
                optimization.alternativeTool!,
                optimization.alternativeArgs!,
                extensionPath,
                outputChannel
            );
            
            // Extract job_id from result if available
            if (altResult && Array.isArray(altResult) && altResult.length > 0) {
                args.job_id = altResult[0].id;
                outputChannel.appendLine(`[Optimization] Using job_id=${args.job_id}`);
            } else {
                return {
                    success: false,
                    error: 'Could not find any failed jobs. Please provide a specific job ID.'
                };
            }
        }
        
        // Validate required parameters
        const validation = validateToolArguments(toolName, args);
        
        if (validation.status === 'needs_input') {
            outputChannel.appendLine(`[Slot-Filling] Missing fields: ${validation.missing!.map(m => m.name).join(', ')}`);
            return {
                success: false,
                error: 'Missing required information',
                needsInput: true,
                missing: validation.missing,
                resumeToken: validation.resume_token
            };
        }
        
        // All parameters present, execute tool
        const result = await invokeMCPTool(toolName, args, extensionPath, outputChannel);
        return { success: true, data: result };
        
    } catch (error: any) {
        outputChannel.appendLine(`[Tool Invocation Failed] ${toolName}: ${error.message}`);
        return {
            success: false,
            error: error.message,
            type: error.type,
            traceback: error.traceback
        };
    }
}

/**
 * Resume a tool call with provided answers
 */
async function resumeToolCall(
    resume_token: string,
    answers: Record<string, any>,
    extensionPath: string,
    outputChannel: vscode.OutputChannel
): Promise<ToolResult> {
    const resumed = resumeToolInvocation(resume_token, answers);
    
    if (!resumed.success) {
        // Still missing fields or error
        if (resumed.args && resumed.args.missing) {
            return {
                success: false,
                error: resumed.error!,
                needsInput: true,
                missing: resumed.args.missing,
                resumeToken: resumed.args.resume_token
            };
        }
        
        return {
            success: false,
            error: resumed.error!
        };
    }
    
    // Execute with complete arguments
    outputChannel.appendLine(`[Resume] Executing ${resumed.tool} with complete args`);
    const result = await invokeMCPTool(resumed.tool!, resumed.args!, extensionPath, outputChannel);
    return { success: true, data: result };
}

/**
 * Invoke MCP tool via the Python server
 */
async function invokeMCPTool(
    toolName: string,
    args: any,
    extensionPath: string,
    outputChannel: vscode.OutputChannel
): Promise<any> {
    const config = vscode.workspace.getConfiguration('awx-mcp');
    const pythonPath = config.get<string>('pythonPath') || 'python';

    const pythonScript = generatePythonScript(toolName, args, extensionPath);

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
                outputChannel.appendLine(`[Python Error] ${stderr}`);
                reject(new Error(`Tool invocation failed: ${stderr}`));
            } else {
                try {
                    const result = JSON.parse(stdout.trim());
                    if (result.success) {
                        resolve(result.data);
                    } else {
                        outputChannel.appendLine(`[Tool Error] ${result.traceback || result.error}`);
                        const error: any = new Error(result.error);
                        error.type = result.type;
                        error.traceback = result.traceback;
                        reject(error);
                    }
                } catch (e) {
                    outputChannel.appendLine(`[Parse Error] ${stdout}`);
                    reject(new Error(`Failed to parse tool result: ${stdout}`));
                }
            }
        });

        proc.on('error', (error: Error) => {
            outputChannel.appendLine(`[Process Error] ${error.message}`);
            reject(error);
        });
    });
}

/**
 * Generate Python script for tool invocation
 */
function generatePythonScript(toolName: string, args: any, extensionPath: string): string {
    const path = require('path');
    const bundledServerPath = path.join(
        extensionPath,
        'bundled',
        'awx-mcp-server',
        'src'
    ).replace(/\\/g, '\\\\');

    return `
import sys
import json
import asyncio
import os

# Suppress ALL logging before any imports
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['LOG_LEVEL'] = 'CRITICAL'

# Configure logging to stderr and suppress everything
import logging
logging.basicConfig(stream=sys.stderr, level=logging.CRITICAL + 10)
logging.disable(logging.CRITICAL)

# Redirect stdout to stderr during imports and execution to prevent any output contamination
_original_stdout = sys.stdout
sys.stdout = sys.stderr

try:
    sys.path.insert(0, r'${bundledServerPath}')

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
                result = [t.model_dump(mode='json') for t in templates]
            elif tool == "awx_template_get":
                template = await client.get_job_template(args.get("name"))
                result = template.model_dump(mode='json')
                
            # Inventories
            elif tool == "awx_inventories_list":
                inventories = await client.list_inventories(
                    page=args.get("page", 1),
                    page_size=args.get("page_size", 25)
                )
                result = [i.model_dump(mode='json') for i in inventories]
                
            # Projects
            elif tool == "awx_projects_list":
                projects = await client.list_projects(
                    page=args.get("page", 1),
                    page_size=args.get("page_size", 25)
                )
                result = [p.model_dump(mode='json') for p in projects]
            elif tool == "awx_project_update":
                update_result = await client.update_project(args.get("name"))
                result = {"success": True, "message": f"Project update initiated for {args.get('name')}"}
                
            # Jobs - Execution
            elif tool == "awx_job_launch":
                job = await client.launch_job(
                    args.get("template_name"),
                    args.get("extra_vars")
                )
                result = job.model_dump(mode='json')
            elif tool == "awx_job_get":
                job = await client.get_job(args.get("job_id"))
                result = job.model_dump(mode='json')
            elif tool == "awx_jobs_list":
                jobs = await client.list_jobs(
                    status=args.get("status"),
                    page=args.get("page", 1),
                    page_size=args.get("page_size", 10)
                )
                result = [j.model_dump(mode='json') for j in jobs]
            elif tool == "awx_jobs_by_template":
                # Get template first to get its ID
                template = await client.get_job_template(args.get("template_name"))
                # Then get jobs for that template
                jobs = await client.list_jobs(
                    job_template_id=template.id,
                    page=args.get("page", 1),
                    page_size=args.get("page_size", 5)
                )
                result = {
                    "template": template.model_dump(mode='json'),
                    "jobs": [j.model_dump(mode='json') for j in jobs]
                }
            elif tool == "awx_job_cancel":
                cancel_result = await client.cancel_job(args.get("job_id"))
                result = {"success": True, "message": f"Job {args.get('job_id')} canceled"}
                
            # Jobs - Output & Diagnostics
            elif tool == "awx_job_stdout":
                # First check if job exists
                try:
                    job = await client.get_job(args.get("job_id"))
                except Exception as e:
                    result = {
                        "error": True,
                        "message": f"Job {args.get('job_id')} not found. Please verify the job ID exists.",
                        "error_detail": str(e)
                    }
                else:
                    try:
                        stdout = await client.get_job_stdout(args.get("job_id"))
                        if not stdout or stdout.strip() == "":
                            result = {
                                "job_id": args.get("job_id"),
                                "job_name": job.name,
                                "status": job.status.value,
                                "output": "(No output available - job may have produced no console output)",
                                "started": job.started.isoformat() if job.started else None,
                                "finished": job.finished.isoformat() if job.finished else None,
                                "elapsed": job.elapsed
                            }
                        else:
                            result = {
                                "job_id": args.get("job_id"),
                                "job_name": job.name,
                                "status": job.status.value,
                                "output": stdout,
                                "started": job.started.isoformat() if job.started else None,
                                "finished": job.finished.isoformat() if job.finished else None,
                                "elapsed": job.elapsed
                            }
                    except Exception as e:
                        # Extract underlying error from RetryError if present
                        error_msg = str(e)
                        error_type = type(e).__name__
                        
                        # Check if it's a RetryError and extract the real cause
                        if error_type == "RetryError" and hasattr(e, 'last_attempt'):
                            try:
                                actual_error = e.last_attempt.exception()
                                if actual_error:
                                    error_msg = str(actual_error)
                                    error_type = type(actual_error).__name__
                            except Exception:
                                pass
                        
                        result = {
                            "error": True,
                            "job_id": args.get("job_id"),
                            "job_name": job.name,
                            "status": job.status.value,
                            "message": f"Failed to fetch job output. Error: {error_msg}",
                            "error_detail": error_msg,
                            "error_type": error_type
                        }
            elif tool == "awx_job_events":
                events = await client.get_job_events(
                    args.get("job_id"),
                    args.get("page", 1),
                    args.get("page_size", 50)
                )
                result = [e.model_dump(mode='json') for e in events]
            elif tool == "awx_job_failure_summary":
                job = await client.get_job(args.get("job_id"))
                stdout = await client.get_job_stdout(args.get("job_id"))
                events = await client.get_job_events(args.get("job_id"), failed_only=True)
                failed_tasks = [e for e in events if e.failed and e.task]
                result = {
                    "job_id": job.id,
                    "name": job.name,
                    "status": job.status.value,
                    "elapsed": job.elapsed,
                    "playbook": job.playbook,
                    "failed_tasks": [{
                        "task": e.task,
                        "play": e.play,
                        "host": e.host,
                        "stdout": e.stdout
                    } for e in failed_tasks[:5]],
                    "output_excerpt": stdout[-2000:] if len(stdout) > 2000 else stdout
                }
            else:
                raise ValueError(f"Unknown tool: {tool}")
            
            # Restore stdout and return result as JSON
            sys.stdout = _original_stdout
            print(json.dumps({"success": True, "data": result}, default=str))
            
        except Exception as e:
            import traceback
            
            # Extract underlying error from RetryError if present
            error_msg = str(e)
            error_type = type(e).__name__
            tb = traceback.format_exc()
            
            if error_type == "RetryError" and hasattr(e, 'last_attempt'):
                try:
                    actual_error = e.last_attempt.exception()
                    if actual_error:
                        error_msg = str(actual_error)
                        error_type = type(actual_error).__name__
                        # Get traceback from the actual error if available
                        tb = ''.join(traceback.format_exception(type(actual_error), actual_error, actual_error.__traceback__))
                except Exception:
                    pass
            
            # Restore stdout and return error
            sys.stdout = _original_stdout
            print(json.dumps({"success": False, "error": error_msg, "type": error_type, "traceback": tb}))

    asyncio.run(invoke_tool())
finally:
    # Ensure stdout is always restored
    sys.stdout = _original_stdout
`;
}
