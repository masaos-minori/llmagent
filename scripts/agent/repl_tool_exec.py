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

from agent.tool_approval import (
    check_approval,
)
from agent.tool_approval import (
    run_approval_checks as _run_approval_checks,
)
from agent.tool_audit import audit_approval as _audit_approval
from agent.tool_audit import audit_tool_exec as _audit_tool_exec
from agent.tool_policy import (
    check_allowed_repo as _check_allowed_repo,
)
from agent.tool_policy import (
    check_allowed_root as _check_allowed_root,
)
from agent.tool_policy import (
    classify_operation_type as _classify_operation_type,
)
from agent.tool_policy import (
    classify_risk as _classify_risk,
)
from agent.tool_policy import (
    preflight_deny_reason as _preflight_deny_reason,
)
from agent.tool_result_formatter import (
    TOOL_RESULT_MAX_CHARS as _TOOL_RESULT_MAX_CHARS,
)
from agent.tool_result_formatter import (
    TURN_LIMIT_HINT as _TURN_LIMIT_HINT,
)
from agent.tool_result_formatter import (
    build_preview as _build_preview,
)
from agent.tool_result_formatter import (
    is_summarized as _is_summarized,
)
from agent.tool_result_formatter import (
    mask_args,
)
from agent.tool_runner import (
    execute_all_tool_calls,
    execute_one_tool_call,
)

__all__ = [
    # Public API used by orchestrator.py and tests
    "check_approval",
    "execute_all_tool_calls",
    "execute_one_tool_call",
    # Private names kept as aliases for existing test imports
    "_audit_approval",
    "_audit_tool_exec",
    "_build_preview",
    "_classify_risk",
    "_classify_operation_type",
    "_check_allowed_root",
    "_check_allowed_repo",
    "_is_summarized",
    "_preflight_deny_reason",
    "_run_approval_checks",
    "_TOOL_RESULT_MAX_CHARS",
    "_TURN_LIMIT_HINT",
    "mask_args",
]
