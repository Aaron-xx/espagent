#!/usr/bin/env python3
"""ESP-IDF MCP Server - Python module entry point.

Usage:
    cd /path/to/esp32_project
    python -m espagent
"""

import asyncio

from espagent.cli import cli_main


def main() -> None:
    """Python module execution main entry point."""
    asyncio.run(cli_main())


if __name__ == "__main__":
    main()
