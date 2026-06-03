"""RAG pipeline debug data builder and context utility functions.

Pure module-level helpers with no AgentContext dependency.
Extracted from agent/repl.py to reduce per-task load cost.

Debug output goes through CLIView.write_debug_rag(); these helpers build
structured dicts so the data can be serialised, logged, or rendered by
any presenter.
"""

# This file has been split into:
# - scripts/agent/rag_debug.py (RAG debug data builder)
# - scripts/agent/context_detection.py (Two-stage context detection)
