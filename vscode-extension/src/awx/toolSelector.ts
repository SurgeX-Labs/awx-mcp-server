/**
 * Tool selection logic - determines which AWX tools to invoke based on user message
 */

import { ToolInvocation } from './types';

/**
 * Intelligently select which tools to invoke based on the user's request
 */
export async function selectToolsForRequest(userMessage: string): Promise<ToolInvocation[]> {
    const message = userMessage.toLowerCase();
    const tools: ToolInvocation[] = [];

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
    if (jobId && (message.includes('status') || message.includes('check') || message.includes('info') || message.includes('details')) && !tools.length) {
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
            const extraVars = extractExtraVars(message);
            
            tools.push({
                name: 'awx_job_launch',
                args: { 
                    template_name: templateNameMatch[1].trim(),
                    extra_vars: Object.keys(extraVars).length > 0 ? extraVars : undefined
                },
                displayName: `Launch Job Template`
            });
        }
    }

    // List jobs by status
    if (message.includes('failed') && message.includes('job')) {
        tools.push({
            name: 'awx_jobs_list',
            args: { status: 'failed', page: 1, page_size: 10 },
            displayName: 'Failed Jobs'
        });
    }
    else if (message.includes('successful') && message.includes('job')) {
        tools.push({
            name: 'awx_jobs_list',
            args: { status: 'successful', page: 1, page_size: 10 },
            displayName: 'Successful Jobs'
        });
    }
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
            
            // Check if asking for jobs related to a template
            if (templateNameMatch && (message.includes('job') && (message.includes('status') || message.includes('last') || message.includes('recent') || message.includes('ran')))) {
                tools.push({
                    name: 'awx_jobs_by_template',
                    args: { template_name: templateNameMatch[1].trim(), page: 1, page_size: 5 },
                    displayName: `Jobs for Template: ${templateNameMatch[1].trim()}`
                });
            }
            else if (templateNameMatch && (message.includes('get') || message.includes('show') || message.includes('detail'))) {
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
 * Extract extra_vars from user message
 * Examples: "with vars x=1 y=2", "extra_vars={\"x\":1}"
 */
function extractExtraVars(message: string): Record<string, any> {
    const extraVars: Record<string, any> = {};
    const varsMatch = message.match(/(?:with (?:vars?|extra[_\s]?vars?)|extra[_\s]?vars?[=:]\s*)(\{[^}]+\}|[\w=,\s]+)/i);
    
    if (varsMatch) {
        const varsStr = varsMatch[1].trim();
        if (varsStr.startsWith('{')) {
            // JSON format
            try {
                Object.assign(extraVars, JSON.parse(varsStr));
            } catch (e) {
                // Ignore parse errors
            }
        } else {
            // Key=value format: "x=1 y=2" or "x=1,y=2"
            const pairs = varsStr.split(/[,\s]+/);
            for (const pair of pairs) {
                const [key, value] = pair.split('=');
                if (key && value) {
                    extraVars[key.trim()] = value.trim();
                }
            }
        }
    }
    
    return extraVars;
}
