/**
 * Slot-filling behavior for MCP resume flow
 * Validates required fields and generates interactive prompts for missing values
 */

import { AWXTool } from './types';

export interface MissingField {
    name: string;
    prompt: string;
    choices?: string[];
    required: boolean;
}

export interface SlotFillingResult {
    status: 'ready' | 'needs_input';
    missing?: MissingField[];
    resume_token?: string;
}

export interface ResumeState {
    tool: string;
    args: any;
    missing: MissingField[];
    timestamp: number;
}

// Store resume states (in-memory, could be persisted)
const resumeStates = new Map<string, ResumeState>();
const RESUME_TOKEN_EXPIRY = 5 * 60 * 1000; // 5 minutes

/**
 * Tool parameter definitions with required fields
 */
const TOOL_PARAMETERS: Record<string, { required: string[], optional: string[], defaults?: Record<string, any> }> = {
    // System & Auth
    'awx.system_info': {
        required: ['profile', 'info_type'],
        optional: []
    },
    // Organizations
    'awx.list_organizations': {
        required: ['profile'],
        optional: ['filter', 'page', 'page_size'],
        defaults: { page: 1, page_size: 25 }
    },
    'awx.get_organization': {
        required: ['profile', 'org_id'],
        optional: []
    },
    // Credentials
    'awx.list_credential_types': {
        required: ['profile'],
        optional: ['page', 'page_size'],
        defaults: { page: 1, page_size: 25 }
    },
    'awx.list_credentials': {
        required: ['profile'],
        optional: ['filter', 'page', 'page_size'],
        defaults: { page: 1, page_size: 25 }
    },
    'awx.create_credential': {
        required: ['profile', 'name', 'credential_type', 'organization', 'inputs'],
        optional: ['description']
    },
    'awx.delete_credential': {
        required: ['profile', 'credential_id'],
        optional: []
    },
    // Job Templates
    'awx.list_job_templates': {
        required: ['profile'],
        optional: ['page', 'page_size'],
        defaults: { page: 1, page_size: 20 }
    },
    'awx.create_job_template': {
        required: ['profile', 'name', 'inventory', 'project', 'playbook'],
        optional: ['job_type', 'description', 'extra_vars', 'limit']
    },
    'awx.delete_job_template': {
        required: ['profile', 'template_id'],
        optional: []
    },
    'awx.launch_job_template': {
        required: ['profile', 'template_id'],
        optional: ['extra_vars', 'limit', 'inventory']
    },
    // Projects
    'awx.list_projects': {
        required: ['profile'],
        optional: ['page', 'page_size']
    },
    'awx.create_project': {
        required: ['profile', 'name', 'organization'],
        optional: ['scm_type', 'scm_url', 'scm_branch', 'description']
    },
    'awx.delete_project': {
        required: ['profile', 'project_id'],
        optional: []
    },
    // Inventories
    'awx.list_inventories': {
        required: ['profile'],
        optional: ['page', 'page_size']
    },
    'awx.create_inventory': {
        required: ['profile', 'name', 'organization'],
        optional: ['description', 'variables']
    },
    'awx.delete_inventory': {
        required: ['profile', 'inventory_id'],
        optional: []
    },
    // Inventory Groups
    'awx.list_inventory_groups': {
        required: ['profile', 'inventory_id'],
        optional: ['page', 'page_size'],
        defaults: { page: 1, page_size: 25 }
    },
    'awx.create_inventory_group': {
        required: ['profile', 'inventory_id', 'name'],
        optional: ['description', 'variables']
    },
    'awx.delete_inventory_group': {
        required: ['profile', 'group_id'],
        optional: []
    },
    // Inventory Hosts
    'awx.list_inventory_hosts': {
        required: ['profile', 'inventory_id'],
        optional: ['page', 'page_size'],
        defaults: { page: 1, page_size: 25 }
    },
    'awx.create_inventory_host': {
        required: ['profile', 'inventory_id', 'name'],
        optional: ['description', 'variables']
    },
    'awx.delete_inventory_host': {
        required: ['profile', 'host_id'],
        optional: []
    },
    // Jobs
    'awx.get_job_status': {
        required: ['profile', 'job_id'],
        optional: []
    },
    'awx.list_jobs': {
        required: ['profile'],
        optional: ['status', 'job_template_id', 'page', 'page_size']
    },
    'awx.get_job_output': {
        required: ['profile', 'job_id'],
        optional: ['format']
    },
    'awx.get_job_events': {
        required: ['profile', 'job_id'],
        optional: ['event_type', 'task', 'host']
    },
    'awx.cancel_job': {
        required: ['profile', 'job_id'],
        optional: []
    },
    'awx.delete_job': {
        required: ['profile', 'job_id'],
        optional: []
    }
};

/**
 * Validate tool arguments and identify missing required fields
 */
export function validateToolArguments(tool: string, args: any): SlotFillingResult {
    const params = TOOL_PARAMETERS[tool];
    
    if (!params) {
        // Unknown tool, assume ready
        return { status: 'ready' };
    }
    
    const missing: MissingField[] = [];
    
    // Check required fields
    for (const field of params.required) {
        if (args[field] === undefined || args[field] === null || args[field] === '') {
            missing.push(createMissingFieldPrompt(tool, field));
        }
    }
    
    // Apply defaults for optional fields
    if (params.defaults) {
        for (const [key, value] of Object.entries(params.defaults)) {
            if (args[key] === undefined) {
                args[key] = value;
            }
        }
    }
    
    if (missing.length === 0) {
        return { status: 'ready' };
    }
    
    // Generate resume token
    const resume_token = generateResumeToken();
    
    // Store state
    resumeStates.set(resume_token, {
        tool,
        args,
        missing,
        timestamp: Date.now()
    });
    
    return { status: 'needs_input', missing, resume_token };
}

/**
 * Create a user-friendly prompt for a missing field
 */
function createMissingFieldPrompt(tool: string, field: string): MissingField {
    // Field-specific prompts
    const prompts: Record<string, Omit<MissingField, 'name'>> = {
        'profile': {
            prompt: 'Which AWX profile do you want to use? (e.g., "production", "staging")',
            required: true
        },
        'job_id': {
            prompt: 'What is the job ID? (Or I can fetch the latest failed job for you)',
            required: true
        },
        'template_id': {
            prompt: 'What is the job template ID or name?',
            required: true
        },
        'extra_vars': {
            prompt: 'Do you want to provide any extra variables? (JSON format or skip)',
            required: false
        },
        'limit': {
            prompt: 'Do you want to limit execution to specific hosts? (Or skip for all hosts)',
            required: false
        },
        'inventory': {
            prompt: 'Which inventory should be used? (Or skip for template default)',
            required: false
        },
        'format': {
            prompt: 'Which output format do you prefer?',
            choices: ['txt', 'ansi', 'json', 'html'],
            required: false
        },
        'status': {
            prompt: 'Filter by job status?',
            choices: ['successful', 'failed', 'error', 'canceled', 'running', 'pending'],
            required: false
        }
    };
    
    const fieldPrompt = prompts[field] || {
        prompt: `Please provide a value for: ${field}`,
        required: true
    };
    
    return {
        name: field,
        ...fieldPrompt
    };
}

/**
 * Generate a unique resume token
 */
function generateResumeToken(): string {
    return `resume_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Resume a tool invocation with provided answers
 */
export function resumeToolInvocation(resume_token: string, answers: Record<string, any>): {
    success: boolean;
    tool?: string;
    args?: any;
    error?: string;
} {
    const state = resumeStates.get(resume_token);
    
    if (!state) {
        return { success: false, error: 'Resume token not found or expired. Please start over.' };
    }
    
    // Check if token expired
    if (Date.now() - state.timestamp > RESUME_TOKEN_EXPIRY) {
        resumeStates.delete(resume_token);
        return { success: false, error: 'Resume token expired (5 minutes). Please start over.' };
    }
    
    // Merge answers into args
    const updatedArgs = { ...state.args, ...answers };
    
    // Validate again to check if all required fields are now present
    const validation = validateToolArguments(state.tool, updatedArgs);
    
    if (validation.status === 'needs_input') {
        // Still missing some fields, update the state
        const new_resume_token = generateResumeToken();
        resumeStates.set(new_resume_token, {
            tool: state.tool,
            args: updatedArgs,
            missing: validation.missing!,
            timestamp: Date.now()
        });
        resumeStates.delete(resume_token); // Remove old token
        
        return {
            success: false,
            error: `Still need more information. Missing: ${validation.missing!.map(m => m.name).join(', ')}`,
            tool: state.tool,
            args: { resume_token: new_resume_token, missing: validation.missing }
        };
    }
    
    // All fields present, ready to execute
    resumeStates.delete(resume_token);
    return { success: true, tool: state.tool, args: updatedArgs };
}

/**
 * Check if a tool invocation can be optimized (e.g., get latest failed job instead of asking for job_id)
 */
export function optimizeToolInvocation(tool: string, args: any): {
    optimized: boolean;
    alternativeTool?: string;
    alternativeArgs?: any;
    explanation?: string;
} {
    // If job_id is missing and tool needs it, try to get latest failed job
    if ((tool === 'awx.get_job_output' || tool === 'awx.get_job_status' || tool === 'awx.get_job_events') 
        && !args.job_id && args.profile) {
        
        return {
            optimized: true,
            alternativeTool: 'awx.list_jobs',
            alternativeArgs: {
                profile: args.profile,
                status: 'failed',
                page: 1,
                page_size: 1
            },
            explanation: 'I\'ll fetch the latest failed job instead of asking for a job ID'
        };
    }
    
    return { optimized: false };
}

/**
 * Clean up expired resume tokens periodically
 */
export function cleanupExpiredTokens(): void {
    const now = Date.now();
    for (const [token, state] of resumeStates.entries()) {
        if (now - state.timestamp > RESUME_TOKEN_EXPIRY) {
            resumeStates.delete(token);
        }
    }
}

// Cleanup expired tokens every minute
setInterval(cleanupExpiredTokens, 60000);
