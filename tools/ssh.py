"""SSH tool for executing remote commands."""

import subprocess

from langchain.tools import tool


@tool
def ssh_run(host: str, command: str) -> str:
    """Execute command on remote host using system SSH (with ~/.ssh/config).

    Args:
        host: The Host name from SSH configuration
        command: The command to execute

    Returns:
        The command execution result
    """
    try:
        ssh_cmd = ["ssh", host, command]
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"SSH command execution failed: {e.stderr.strip()}"
