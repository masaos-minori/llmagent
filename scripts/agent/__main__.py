"""agent/__main__.py
Entry point for `python -m agent` invocation.

Runs the interactive REPL agent. Compared to the legacy agent.py entry point,
sys.path manipulation is not needed because python -m resolves packages
relative to the working directory (scripts/).
"""

import asyncio

from agent.repl import AgentREPL

if __name__ == "__main__":
    asyncio.run(AgentREPL().run())
