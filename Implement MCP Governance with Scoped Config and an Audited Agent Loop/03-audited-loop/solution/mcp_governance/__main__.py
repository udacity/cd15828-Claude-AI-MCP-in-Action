"""``python -m mcp_governance`` / ``mcp-governance`` entry point."""

from __future__ import annotations

import sys

from mcp_governance.cli import main

if __name__ == "__main__":
    sys.exit(main())
