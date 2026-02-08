/**
 * Parse answers from user message
 * Simple extraction of key-value pairs from natural language
 */
export function parseAnswersFromMessage(message: string): Record<string, any> {
    const answers: Record<string, any> = {};
    
    // Try to extract common patterns
    
    // Profile: "production", "staging", etc.
    const profileMatch = message.match(/profile[:\s]+([a-zA-Z0-9_-]+)/i) || 
                         message.match(/use\s+([a-zA-Z0-9_-]+)\s+profile/i) ||
                         message.match(/^([a-zA-Z0-9_-]+)$/); // Single word response
    
    if (profileMatch) {
        answers.profile = profileMatch[1];
    }
    
    // Job ID: numbers
    const jobIdMatch = message.match(/job[:\s]+(\d+)/i) || 
                       message.match(/id[:\s]+(\d+)/i) ||
                       message.match(/\b(\d+)\b/);
    
    if (jobIdMatch) {
        answers.job_id = parseInt(jobIdMatch[1], 10);
    }
    
    // Template ID or name
    const templateMatch = message.match(/template[:\s]+(.+?)(?:\s|$)/i) ||
                          message.match(/^(.+)$/); // Fallback to full message
    
    if (templateMatch && !answers.profile && !answers.job_id) {
        answers.template_id = templateMatch[1].trim();
    }
    
    // Format
    const formatMatch = message.match(/format[:\s]+(txt|ansi|json|html)/i);
    if (formatMatch) {
        answers.format = formatMatch[1].toLowerCase();
    }
    
    // Status
    const statusMatch = message.match(/status[:\s]+(successful|failed|error|canceled|running|pending)/i);
    if (statusMatch) {
        answers.status = statusMatch[1].toLowerCase();
    }
    
    // Extra vars (JSON)
    const jsonMatch = message.match(/\{[^}]+\}/);
    if (jsonMatch) {
        try {
            answers.extra_vars = JSON.parse(jsonMatch[0]);
        } catch {
            // Invalid JSON, skip
        }
    }
    
    // If we couldn't extract anything specific, try single-word responses
    if (Object.keys(answers).length === 0) {
        const singleWord = message.trim();
        if (singleWord && !singleWord.includes(' ')) {
            // Could be profile, format, or status
            const lowerWord = singleWord.toLowerCase();
            
            if (['txt', 'ansi', 'json', 'html'].includes(lowerWord)) {
                answers.format = lowerWord;
            } else if (['successful', 'failed', 'error', 'canceled', 'running', 'pending'].includes(lowerWord)) {
                answers.status = lowerWord;
            } else if (/^\d+$/.test(singleWord)) {
                answers.job_id = parseInt(singleWord, 10);
            } else {
                answers.profile = singleWord;
            }
        }
    }
    
    return answers;
}
