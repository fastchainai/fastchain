"""Static security analysis tests using Bandit."""
import subprocess
import pytest
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

def ensure_src_dir(project_root):
    """Ensure src directory exists, create if not."""
    src_dir = project_root / "src"
    if not src_dir.exists():
        src_dir.mkdir(parents=True)
    return src_dir

def test_bandit_scan(project_root):
    """
    Run Bandit static analysis on the project codebase.
    """
    src_dir = ensure_src_dir(project_root)

    # Run Bandit scan with less strict settings for initial implementation
    process = subprocess.run(
        [
            "bandit",
            "-r",  # Recursive scan
            "-f", "json",  # JSON output format
            "-ll",  # Report only medium and high severity
            "-i",  # Include only issues
            "--exit-zero",  # Don't fail on findings
            "-q",  # Quiet mode - no progress bar
            str(src_dir)
        ],
        capture_output=True,
        text=True
    )

    # Log the command output for debugging
    logger.debug(f"Bandit stdout: {process.stdout}")
    logger.debug(f"Bandit stderr: {process.stderr}")

    try:
        if process.stdout.strip():
            results = json.loads(process.stdout)
        else:
            logger.info("No issues found in Bandit scan")
            return
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bandit output: {e}")
        logger.error(f"Raw output: {process.stdout}")
        pytest.fail("Failed to parse Bandit output")

    # Check only for high severity issues
    high_severity_issues = [
        issue for issue in results.get("results", [])
        if issue.get("issue_severity") == "HIGH"
    ]

    if high_severity_issues:
        issues_str = "\n".join(
            f"- {issue['issue_text']} in {issue['filename']}:{issue['line_number']}"
            for issue in high_severity_issues
        )
        pytest.fail(
            f"Found {len(high_severity_issues)} high severity security issues:\n{issues_str}"
        )

def test_secret_detection(project_root):
    """Test for exposed secrets in the codebase."""
    src_dir = ensure_src_dir(project_root)

    # Run Bandit with focus on secret detection
    process = subprocess.run(
        [
            "bandit",
            "-r",
            "-f", "json",
            "--tests", "B105,B106,B107",  # Focus on hardcoded password tests
            "--exit-zero",  # Don't fail on findings
            "-q",  # Quiet mode - no progress bar
            str(src_dir)
        ],
        capture_output=True,
        text=True
    )

    # Log the command output for debugging
    logger.debug(f"Secret detection stdout: {process.stdout}")
    logger.debug(f"Secret detection stderr: {process.stderr}")

    try:
        if process.stdout.strip():
            results = json.loads(process.stdout)
        else:
            logger.info("No secrets found in scan")
            return
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bandit output: {e}")
        logger.error(f"Raw output: {process.stdout}")
        pytest.fail("Failed to parse Bandit output")

    secret_issues = results.get("results", [])
    if secret_issues:
        issues_str = "\n".join(
            f"- {issue['issue_text']} in {issue['filename']}:{issue['line_number']}"
            for issue in secret_issues
        )
        pytest.fail(
            f"Found {len(secret_issues)} potential secrets in code:\n{issues_str}"
        )