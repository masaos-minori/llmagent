#!/usr/bin/env python3
"""agent.py — Legacy entry point (backward compat stub).

Use `python -m agent` (from the scripts/ directory) instead.
This file is kept so that existing deploy/init scripts that reference
`python agent.py` continue to work during the migration period.

Migrated to: scripts/agent/__main__.py
"""

import asyncio
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.repl import AgentREPL


def _request_shutdown(_signum: int, _frame: object) -> None:
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _request_shutdown)

if __name__ == "__main__":
    asyncio.run(AgentREPL().run())
