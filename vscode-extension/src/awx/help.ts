/**
 * Help messages and documentation for AWX chat participant
 */

import * as vscode from 'vscode';

export function showHelp(stream: vscode.ChatResponseStream): void {
    stream.markdown('I can help you with AWX/Ansible Tower tasks:\n\n');
    stream.markdown('**List Resources:**\n');
    stream.markdown('- List job templates\n');
    stream.markdown('- Show inventories\n');
    stream.markdown('- List projects\n\n');
    stream.markdown('**Job Management:**\n');
    stream.markdown('- Show recent jobs\n');
    stream.markdown('- Get job status with full details\n');
    stream.markdown('- View job output/logs\n');
    stream.markdown('- Analyze failed jobs\n');
    stream.markdown('- View job events and task execution\n');
    stream.markdown('- Launch/cancel jobs\n\n');
    stream.markdown('**Examples:**\n');
    stream.markdown('- `@awx List my job templates`\n');
    stream.markdown('- `@awx Check status of job 123`\n');
    stream.markdown('- `@awx Show output for job 456`\n');
    stream.markdown('- `@awx Why did job 789 fail?`\n');
    stream.markdown('- `@awx Show failed jobs`\n');
    stream.markdown('- `@awx List running jobs`\n');
    stream.markdown('- `@awx Launch template Demo Job Template`\n');
    stream.markdown('- `@awx Run template MyTemplate with vars env=prod tier=web`\n\n');
    stream.markdown('💡 I provide detailed, human-readable output that GitHub Copilot can use to help troubleshoot issues!');
}

export function getDescription(): string {
    return 'AWX/Ansible Tower automation assistant';
}

export function getSampleRequest(): string {
    return 'List my job templates';
}
