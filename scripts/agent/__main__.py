"""agent/__main__.py
Entry point for `python -m agent` invocation.

Runs the interactive REPL agent. Compared to the legacy agent.py entry point,
sys.path manipulation is not needed because python -m resolves packages
relative to the working directory (scripts/).
"""

import asyncio
import signal

from agent.repl import AgentREPL


def _request_shutdown(_signum: int, _frame: object) -> None:
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _request_shutdown)

if __name__ == "__main__":
    asyncio.run(AgentREPL().run())
