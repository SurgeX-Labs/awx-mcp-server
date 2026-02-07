"""Quick test runner for AWX MCP integration tests.

Run individual test scripts to validate AWX MCP functionality.

Usage:
    python run_tests.py                    # Show menu
    python run_tests.py env                # Test environment management
    python run_tests.py templates          # Test list templates
    python run_tests.py projects           # Test list projects
    python run_tests.py all                # Run pytest suite
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run integration tests."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    # Test options
    tests = {
        'env': ('Environment Management', 'test_env_management.py'),
        'templates': ('List Job Templates', 'test_list_templates.py'),
        'projects': ('List Projects', 'test_list_projects.py'),
        'inventories': ('List Inventories', 'test_list_inventories.py'),
        'jobs': ('List Jobs', 'test_list_jobs.py'),
        'launch': ('Launch Job', 'test_job_launch.py'),
        'get': ('Get Job Status', 'test_job_get.py'),
        'cancel': ('Cancel Job', 'test_job_cancel.py'),
        'stdout': ('Get Job Output', 'test_job_stdout.py'),
        'events': ('Get Job Events', 'test_job_events.py'),
        'failure': ('Analyze Job Failure', 'test_job_failure_summary.py'),
        'update': ('Update Project', 'test_project_update.py'),
    }
    
    # Show menu if no arguments
    if len(sys.argv) == 1:
        print("=" * 70)
        print("AWX MCP Integration Test Suite")
        print("=" * 70)
        print()
        print("Available tests:")
        print()
        
        for key, (name, file) in tests.items():
            print(f"  {key:12} - {name}")
        
        print()
        print("Special commands:")
        print(f"  {'all':12} - Run full pytest suite")
        print(f"  {'pytest':12} - Run pytest with custom arguments")
        print()
        print("Usage:")
        print(f"  python run_tests.py <test>")
        print(f"  python run_tests.py env")
        print(f"  python run_tests.py templates")
        print(f"  python run_tests.py all")
        print()
        return 0
    
    test_name = sys.argv[1].lower()
    
    # Run pytest suite
    if test_name == 'all':
        print("=" * 70)
        print("Running Full Pytest Suite")
        print("=" * 70)
        print()
        
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_dir),
            "-v",
            "--tb=short",
            "--color=yes",
        ]
        
        result = subprocess.run(cmd)
        return result.returncode
    
    # Run pytest with custom args
    if test_name == 'pytest':
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_dir),
        ] + sys.argv[2:]
        
        result = subprocess.run(cmd)
        return result.returncode
    
    # Run specific test
    if test_name in tests:
        test_desc, test_file = tests[test_name]
        test_path = tests_dir / test_file
        
        print("=" * 70)
        print(f"AWX MCP Test: {test_desc}")
        print("=" * 70)
        print()
        
        cmd = [sys.executable, str(test_path)] + sys.argv[2:]
        result = subprocess.run(cmd)
        
        return result.returncode
    
    # Unknown test
    print(f"Unknown test: {test_name}")
    print(f"Run 'python run_tests.py' to see available tests.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
