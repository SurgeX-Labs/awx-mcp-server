"""Utility functions for parsing and analysis."""

import re
from typing import Optional

from awx_mcp_server.domain import FailureAnalysis, FailureCategory, JobEvent


def analyze_job_failure(job_id: int, events: list[JobEvent], stdout: str) -> FailureAnalysis:
    """
    Analyze job failure and provide actionable suggestions.

    Args:
        job_id: Job ID
        events: List of job events
        stdout: Job stdout
    
    Returns:
        Failure analysis with categorization and suggestions
    """
    failed_events = [e for e in events if e.failed]
    
    if not failed_events:
        return FailureAnalysis(
            job_id=job_id,
            category=FailureCategory.UNKNOWN,
            suggested_fixes=["No failed events found. Check job status for details."],
        )
    
    # Analyze the first failed event
    event = failed_events[0]
    
    # Extract error details
    error_message = event.stdout or ""
    stderr = event.stderr or ""
    event_data = event.event_data
    
    # Try to get more detailed error info
    if "res" in event_data:
        res = event_data["res"]
        if "msg" in res:
            error_message = res["msg"]
        if "stderr" in res:
            stderr = res["stderr"]
    
    # Classify failure category
    category = _classify_failure(error_message, stderr, event)
    
    # Generate suggestions
    suggestions = _generate_suggestions(category, error_message, stderr, event)
    
    return FailureAnalysis(
        job_id=job_id,
        category=category,
        task_name=event.task,
        play_name=event.play,
        role_name=event.role,
        file_path=None,  # Would need to parse from stdout
        host=event.host,
        error_message=error_message,
        stderr=stderr,
        suggested_fixes=suggestions,
        failed_events_count=len(failed_events),
    )


def _classify_failure(error_msg: str, stderr: str, event: JobEvent) -> FailureCategory:
    """Classify failure category based on error patterns."""
    combined = f"{error_msg} {stderr}".lower()
    
    # Check for common patterns
    if any(
        pattern in combined
        for pattern in ["unreachable", "could not resolve hostname", "connection refused"]
    ):
        return FailureCategory.INVENTORY_ISSUE
    
    if any(
        pattern in combined
        for pattern in [
            "permission denied",
            "authentication failed",
            "invalid credentials",
            "unauthorized",
        ]
    ):
        return FailureCategory.AUTH_FAILURE
    
    if any(pattern in combined for pattern in ["undefined variable", "variable is not defined"]):
        return FailureCategory.MISSING_VARIABLE
    
    if any(
        pattern in combined
        for pattern in ["syntax error", "yaml syntax", "unexpected token", "invalid syntax"]
    ):
        return FailureCategory.SYNTAX_ERROR
    
    if "timeout" in combined or "timed out" in combined:
        return FailureCategory.CONNECTION_TIMEOUT
    
    if "permission" in combined and "denied" in combined:
        return FailureCategory.PERMISSION_DENIED
    
    # Check for module-specific failures
    if event.task and any(mod in event.task.lower() for mod in ["yum", "apt", "dnf", "package"]):
        if "no package" in combined or "not found" in combined:
            return FailureCategory.MODULE_FAILURE
    
    return FailureCategory.UNKNOWN


def _generate_suggestions(
    category: FailureCategory, error_msg: str, stderr: str, event: JobEvent
) -> list[str]:
    """Generate actionable suggestions based on failure category."""
    suggestions = []
    
    if category == FailureCategory.INVENTORY_ISSUE:
        suggestions.extend(
            [
                "Verify the host exists in the inventory",
                "Check network connectivity to the target host",
                "Ensure the hostname resolves correctly (check DNS or /etc/hosts)",
                "Verify firewall rules allow SSH connections",
            ]
        )
    
    elif category == FailureCategory.AUTH_FAILURE:
        suggestions.extend(
            [
                "Verify SSH credentials or keys are correct",
                "Check that the user has access to the target host",
                "Ensure SSH key is in the authorized_keys file",
                "Verify sudo/become password if required",
            ]
        )
    
    elif category == FailureCategory.MISSING_VARIABLE:
        # Try to extract variable name
        var_match = re.search(r"['\"]([\w_]+)['\"].*undefined", error_msg + stderr)
        if var_match:
            var_name = var_match.group(1)
            suggestions.append(f"Define the variable '{var_name}' in extra_vars or playbook")
        suggestions.extend(
            [
                "Check the playbook for required variables",
                "Add missing variables to extra_vars in the job template",
                "Verify variable names are spelled correctly",
            ]
        )
    
    elif category == FailureCategory.SYNTAX_ERROR:
        suggestions.extend(
            [
                "Check YAML syntax in the playbook",
                "Verify proper indentation (use spaces, not tabs)",
                "Run ansible-playbook --syntax-check locally",
                "Check for missing quotes or special characters",
            ]
        )
    
    elif category == FailureCategory.CONNECTION_TIMEOUT:
        suggestions.extend(
            [
                "Increase timeout values in ansible.cfg",
                "Check network latency to target hosts",
                "Verify no firewall is blocking connections",
                "Check if target host is overloaded",
            ]
        )
    
    elif category == FailureCategory.PERMISSION_DENIED:
        suggestions.extend(
            [
                "Check file/directory permissions on target host",
                "Verify the user has necessary privileges",
                "Use 'become: yes' if elevated privileges are needed",
                "Check SELinux/AppArmor policies if applicable",
            ]
        )
    
    elif category == FailureCategory.MODULE_FAILURE:
        suggestions.extend(
            [
                f"Check module '{event.task}' documentation for required parameters",
                "Verify the module is available on the target system",
                "Check module prerequisites are installed",
                "Review module error message for specific issues",
            ]
        )
    
    else:
        suggestions.extend(
            [
                "Review the full job output for more context",
                "Check Ansible module documentation",
                "Verify all task parameters are correct",
                "Try running the task manually on the target host",
            ]
        )
    
    return suggestions


def sanitize_secret(text: str, secrets: list[str]) -> str:
    """
    Sanitize secrets from text.

    Args:
        text: Text that may contain secrets
        secrets: List of secret strings to redact
    
    Returns:
        Text with secrets replaced by [REDACTED]
    """
    result = text
    for secret in secrets:
        if secret and len(secret) > 0:
            result = result.replace(secret, "[REDACTED]")
    return result
