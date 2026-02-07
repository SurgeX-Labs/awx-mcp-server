"""Tests for failure analysis."""

from awx_mcp.domain import JobEvent, FailureCategory
from awx_mcp.utils import analyze_job_failure


def test_analyze_auth_failure():
    """Test authentication failure detection."""
    events = [
        JobEvent(
            id=1,
            event="runner_on_failed",
            event_level=3,
            failed=True,
            changed=False,
            task="Gather Facts",
            host="web01",
            stdout="",
            stderr="Permission denied (publickey,password)",
            event_data={"res": {"stderr": "Permission denied (publickey,password)"}},
        )
    ]
    
    analysis = analyze_job_failure(123, events, "")
    
    assert analysis.category == FailureCategory.AUTH_FAILURE
    assert analysis.host == "web01"
    assert len(analysis.suggested_fixes) > 0
    assert any("SSH" in fix or "credential" in fix for fix in analysis.suggested_fixes)


def test_analyze_missing_variable():
    """Test missing variable detection."""
    events = [
        JobEvent(
            id=1,
            event="runner_on_failed",
            event_level=3,
            failed=True,
            changed=False,
            task="Deploy application",
            host="web01",
            stdout="",
            stderr="",
            event_data={
                "res": {
                    "msg": "The task includes an option with an undefined variable. "
                    "The error was: 'app_version' is undefined"
                }
            },
        )
    ]
    
    analysis = analyze_job_failure(123, events, "")
    
    assert analysis.category == FailureCategory.MISSING_VARIABLE
    assert len(analysis.suggested_fixes) > 0
    assert any("variable" in fix.lower() for fix in analysis.suggested_fixes)


def test_analyze_syntax_error():
    """Test syntax error detection."""
    events = [
        JobEvent(
            id=1,
            event="runner_on_failed",
            event_level=3,
            failed=True,
            changed=False,
            task="Parse config",
            host="web01",
            stdout="",
            stderr="Syntax Error while loading YAML",
            event_data={"res": {"stderr": "Syntax Error while loading YAML"}},
        )
    ]
    
    analysis = analyze_job_failure(123, events, "")
    
    assert analysis.category == FailureCategory.SYNTAX_ERROR
    assert len(analysis.suggested_fixes) > 0
    assert any("syntax" in fix.lower() or "yaml" in fix.lower() for fix in analysis.suggested_fixes)


def test_analyze_connection_timeout():
    """Test connection timeout detection."""
    events = [
        JobEvent(
            id=1,
            event="runner_on_unreachable",
            event_level=3,
            failed=True,
            changed=False,
            task="Setup",
            host="web01",
            stdout="",
            stderr="Connection timed out",
            event_data={"res": {"msg": "Connection timed out"}},
        )
    ]
    
    analysis = analyze_job_failure(123, events, "")
    
    assert analysis.category == FailureCategory.CONNECTION_TIMEOUT
    assert len(analysis.suggested_fixes) > 0
    assert any("timeout" in fix.lower() or "network" in fix.lower() for fix in analysis.suggested_fixes)


def test_analyze_no_failed_events():
    """Test analysis with no failed events."""
    events = [
        JobEvent(
            id=1,
            event="runner_on_ok",
            event_level=3,
            failed=False,
            changed=True,
            task="Deploy app",
            host="web01",
        )
    ]
    
    analysis = analyze_job_failure(123, events, "")
    
    assert analysis.category == FailureCategory.UNKNOWN
    assert len(analysis.suggested_fixes) > 0
