"""agent/repl_tool_exec.py
Backward-compatible re-export layer for tool execution helpers.

Implementation split into:
  tool_policy.py          — risk classification & pre-flight checks
  tool_audit.py           — structured audit-log writers
  tool_result_formatter.py — preview builders & mask_args
  tool_approval.py        — interactive approval flow
  tool_runner.py          — execution orchestration (public entry point)

External callers (tests, orchestrator) import from here unchanged.
"""

from agent.tool_runner import (
    execute_all_tool_calls,
    execute_one_tool_call,
)

__all__ = [
    # Public API used by orchestrator.py and tests
    "execute_all_tool_calls",
    "execute_one_tool_call",
]
