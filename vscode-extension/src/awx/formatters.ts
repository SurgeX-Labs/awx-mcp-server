/**
 * Formatting utilities for AWX tool results and errors
 */

/**
 * Format job status with appropriate styling
 */
export function formatJobStatus(status: string): string {
    const statusMap: { [key: string]: string } = {
        'successful': '✅ Successful',
        'failed': '❌ Failed',
        'error': '⛔ Error',
        'running': '⏳ Running',
        'pending': '⏸️ Pending',
        'waiting': '⏳ Waiting',
        'canceled': '🚫 Canceled'
    };
    return statusMap[status.toLowerCase()] || status;
}

/**
 * Get status icon for job lists
 */
export function getStatusIcon(status: string): string {
    const iconMap: { [key: string]: string } = {
        'successful': '✅',
        'failed': '❌',
        'error': '⛔',
        'running': '⏳',
        'pending': '⏸️',
        'waiting': '⏳',
        'canceled': '🚫'
    };
    return iconMap[status.toLowerCase()] || '•';
}

/**
 * Format duration in a human-readable way
 */
export function formatDuration(seconds: number): string {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

/**
 * Format error messages in a user-friendly way
 */
export function formatErrorMessage(error: any, toolName: string): string {
    let message = '⚠️ **Error**\n\n';
    
    if (error.type === 'ValidationError') {
        message += '**Type:** Data Validation Error\n\n';
        message += 'There was an issue with the data format returned from AWX. This usually happens when:\n';
        message += '- AWX returns data in an unexpected format\n';
        message += '- Required fields are missing\n';
        message += '- Data types don\'t match expectations\n\n';
        message += `**Details:** ${error.message}\n\n`;
        message += '💡 **Suggestion:** Check the AWX server configuration and ensure the API is responding correctly.';
    } else if (error.type === 'NoActiveEnvironmentError') {
        message += '**Type:** No Active Environment\n\n';
        message += 'No AWX environment is currently configured or active.\n\n';
        message += '💡 **Next Steps:**\n';
        message += '1. Run the command: **AWX: Configure Environment**\n';
        message += '2. Add your AWX server details\n';
        message += '3. Try your request again';
    } else if (error.message.includes('connection') || error.message.includes('timeout') || error.message.includes('RetryError')) {
        message += '**Type:** Connection Error\n\n';
        message += `Unable to connect to AWX server or request timed out.\n\n`;
        message += `**Details:** ${error.message}\n\n`;
        message += '💡 **Troubleshooting:**\n';
        message += '- Verify the AWX server URL is correct and accessible\n';
        message += '- Check your network connection\n';
        message += '- Ensure the AWX server is running and responsive\n';
        message += '- Verify authentication credentials are valid\n';
        message += '- Check if the AWX API endpoint exists (e.g., /api/v2/jobs/{id}/stdout/)\n';
        message += '- Some AWX endpoints may not be available depending on job status';
    } else if (error.message.includes('401') || error.message.includes('authentication')) {
        message += '**Type:** Authentication Error\n\n';
        message += 'Failed to authenticate with AWX server.\n\n';
        message += '💡 **Next Steps:**\n';
        message += '1. Verify your AWX credentials\n';
        message += '2. Update credentials using: **AWX: Configure Environment**';
    } else if (error.message.includes('404') || error.message.includes('not found')) {
        message += '**Type:** Resource Not Found\n\n';
        message += `The requested resource was not found on the AWX server.\n\n`;
        message += `**Details:** ${error.message}\n\n`;
        message += '💡 **Tip:** Double-check the resource name or ID.';
    } else {
        message += `**Operation:** ${toolName}\n\n`;
        message += `**Details:** ${error.message}\n\n`;
        if (error.type) {
            message += `**Type:** ${error.type}\n\n`;
        }
        message += '💡 Check the Output panel (AWX MCP) for more details.';
    }
    
    return message;
}

/**
 * Format tool results for display in chat
 */
export function formatToolResult(toolName: string, result: any): string {
    if (!result) {
        return '_No results_';
    }

    // Handle error results from tools
    if (result.error) {
        let errorMsg = '⚠️ ';
        if (result.message) {
            errorMsg += result.message;
        }
        if (result.job_name) {
            errorMsg += `\n\n**Job:** ${result.job_name}\n`;
        }
        if (result.status) {
            errorMsg += `**Status:** ${formatJobStatus(result.status)}\n`;
        }
        if (result.error_detail) {
            errorMsg += `\n**Technical Details:** \`${result.error_detail}\`\n`;
        }
        if (result.error_type) {
            errorMsg += `**Error Type:** ${result.error_type}\n`;
        }
        return errorMsg;
    }

    // Job stdout
    if (toolName === 'awx_job_stdout') {
        if (result.output) {
            let output = `**Job:** ${result.job_name || result.job_id}\n`;
            output += `**Status:** ${formatJobStatus(result.status)}\n`;
            if (result.started) {
                output += `**Started:** ${new Date(result.started).toLocaleString()}\n`;
            }
            if (result.finished) {
                output += `**Finished:** ${new Date(result.finished).toLocaleString()}\n`;
            }
            if (result.elapsed) {
                output += `**Duration:** ${formatDuration(result.elapsed)}\n`;
            }
            output += '\n**Output:**\n';
            output += '```\n' + result.output + '\n```';
            return output;
        }
    }

    // Job failure summary
    if (toolName === 'awx_job_failure_summary') {
        let output = `**Job ID:** ${result.job_id}\n`;
        output += `**Name:** ${result.name}\n`;
        output += `**Status:** ${formatJobStatus(result.status)}\n`;
        output += `**Playbook:** ${result.playbook}\n`;
        if (result.elapsed) {
            output += `**Duration:** ${formatDuration(result.elapsed)}\n`;
        }
        
        if (result.failed_tasks && result.failed_tasks.length > 0) {
            output += '\n**Failed Tasks:**\n';
            for (const task of result.failed_tasks) {
                output += `\n- **Task:** ${task.task}\n`;
                if (task.play) output += `  **Play:** ${task.play}\n`;
                if (task.host) output += `  **Host:** ${task.host}\n`;
                if (task.stdout) {
                    const excerpt = task.stdout.substring(0, 200);
                    output += `  **Error:** \`${excerpt}${task.stdout.length > 200 ? '...' : ''}\`\n`;
                }
            }
        }
        
        output += '\n**Output (excerpt):**\n';
        output += '```\n' + result.output_excerpt + '\n```';
        return output;
    }

    // Jobs by template
    if (toolName === 'awx_jobs_by_template' && result.template) {
        let output = `**Template:** ${result.template.name}\n`;
        output += `**Description:** ${result.template.description || 'N/A'}\n`;
        output += `**Playbook:** ${result.template.playbook}\n`;
        output += `**Job Type:** ${result.template.job_type}\n\n`;
        
        if (result.jobs && result.jobs.length > 0) {
            output += `**Recent Jobs (${result.jobs.length}):**\n\n`;
            for (const job of result.jobs) {
                const statusIcon = getStatusIcon(job.status);
                output += `${statusIcon} **Job #${job.id}:** ${job.name}\n`;
                output += `  Status: ${formatJobStatus(job.status)}`;
                if (job.started) {
                    output += ` | Started: ${new Date(job.started).toLocaleString()}`;
                }
                if (job.elapsed) {
                    output += ` | Duration: ${formatDuration(job.elapsed)}`;
                }
                output += '\n\n';
            }
        } else {
            output += '\n_No jobs found for this template_';
        }
        return output;
    }

    // Job events
    if (toolName === 'awx_job_events') {
        if (Array.isArray(result) && result.length > 0) {
            let output = '';
            for (const event of result.slice(0, 20)) {
                const failedIcon = event.failed ? '❌' : event.changed ? '🔄' : '✓';
                output += `${failedIcon} **${event.event}**`;
                if (event.task) output += ` - ${event.task}`;
                if (event.role) output += ` (${event.role})`;
                if (event.host) output += ` @ ${event.host}`;
                if (event.stdout && event.stdout.trim()) {
                    const excerpt = event.stdout.substring(0, 150);
                    output += `\n  \`${excerpt}${event.stdout.length > 150 ? '...' : ''}\``;
                }
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
        output += `**Status:** ${formatJobStatus(result.status)}\n`;
        output += `**Playbook:** ${result.playbook || 'N/A'}\n`;
        if (result.started) {
            output += `**Started:** ${new Date(result.started).toLocaleString()}\n`;
        }
        if (result.finished) {
            output += `**Finished:** ${new Date(result.finished).toLocaleString()}\n`;
        }
        if (result.elapsed) {
            output += `**Duration:** ${formatDuration(result.elapsed)}\n`;
        }
        if (result.extra_vars && Object.keys(result.extra_vars).length > 0) {
            output += `**Extra Vars:** \`${JSON.stringify(result.extra_vars)}\`\n`;
        }
        return output;
    }

    // List jobs
    if (toolName === 'awx_jobs_list' &&Array.isArray(result)) {
        if (result.length === 0) {
            return '_No jobs found_';
        }
        let output = '';
        for (const job of result.slice(0, 15)) {
            const statusIcon = getStatusIcon(job.status);
            output += `${statusIcon} **${job.name}** (ID: ${job.id})\n`;
            output += `  Status: ${formatJobStatus(job.status)} | Playbook: ${job.playbook || 'N/A'}`;
            if (job.started) {
                output += ` | Started: ${new Date(job.started).toLocaleString()}`;
            }
            output += '\n\n';
        }
        if (result.length > 15) {
            output += `_... and ${result.length - 15} more jobs_\n`;
        }
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

    // Job launch/cancel
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
    return formatDataAsMarkdown(result);
}

/**
 * Format data structures as readable markdown
 */
function formatDataAsMarkdown(data: any): string {
    if (!data) {
        return '_No data_';
    }

    if (Array.isArray(data)) {
        return formatListAsMarkdown(data);
    }

    if (data.results && Array.isArray(data.results)) {
        let output = '';
        if (data.count) {
            output += `**Total:** ${data.count}\n\n`;
        }
        output += formatListAsMarkdown(data.results);
        return output;
    }

    return '```json\n' + JSON.stringify(data, null, 2) + '\n```';
}

/**
 * Format an array of items as a markdown table or list
 */
function formatListAsMarkdown(items: any[]): string {
    if (items.length === 0) {
        return '_No items found_';
    }

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

    const keys = Object.keys(items[0]).slice(0, 4);
    let table = '| ' + keys.join(' | ') + ' |\n';
    table += '| ' + keys.map(() => '---').join(' | ') + ' |\n';

    for (const item of items.slice(0, 10)) {
        table += '| ' + keys.map(k => String(item[k] || '').substring(0, 50)).join(' | ') + ' |\n';
    }

    if (items.length > 10) {
        table += `\n_... and ${items.length - 10} more items_`;
    }

    return table;
}
