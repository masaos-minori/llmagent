"""scripts/agent/__main__.py

Entry point for `python -m agent` invocation.

Runs the interactive REPL agent. sys.path manipulation is not needed because
python -m resolves packages relative to the working directory (scripts/).
"""

from agent.repl import main

if __name__ == "__main__":
    main()
