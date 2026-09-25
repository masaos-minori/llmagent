# Fix timeout-hierarchy inversion: shell MCP server's max_timeout_sec (300s) exceeds Workflow execute stage's timeout_sec (120s)

## Priority
High

## Summary
The Workflow, Agent, and MCP Server layers each enforce their own timeout independently, with no guarantee that an inner layer's timeout is shorter than an enclosing outer layer's. A concrete inversion exists today: `config/shell_mcp_server.toml`'s `max_timeout_sec = 300` allows the LLM to request a shell command timeout of up to 300 seconds, while `config/workflows/default.json`'s execute stage `timeout_sec` is 120 seconds. If the LLM requests a long-running shell command, `WorkflowEngine` can raise `WorkflowTimeoutError` and fail the stage at 120s while the underlying shell subprocess is still running for up to 300s, with no evidence in `subprocess_runner.py` that this orphaned process is cancelled when the enclosing Workflow stage times out.

## Background
This issue follows a design review requested in this session covering six Agent/Workflow design questions (memo2.md), one of which was "Workflow、Agent、MCPのタイムアウト階層" (a Workflow/Agent/MCP timeout hierarchy, implying inner timeouts should be strictly shorter than outer ones so a layer never has to explain away an inconsistent partial state from a layer it doesn't control). The investigating fork found this specific inversion and confirmed no existing ADR, Known Issue, or Needs Confirmation entry documents it.

## Problem
Confirmed by direct reading:
- **Workflow layer** (outermost): `scripts/agent/workflow/workflow_engine.py` line ~304, `timeout = stage_def.timeout_sec if stage_def else 60`, enforced via `asyncio.wait_for` (line ~321) → raises `WorkflowTimeoutError` on expiry. `config/workflows/default.json` sets stage `timeout_sec` values of 30/120/10 (plan/execute/verify, per file order).
- **Agent layer** (middle): no turn-wide or Tool-Call-wide time budget was found in `llm_turn_runner.py`. The only related value, `scripts/shared/llm_sse_stream.py` line ~35 `sse_heartbeat_timeout` (`config/agent.toml`, default 60.0s), detects inter-chunk silence — it is not an upper bound on total turn or tool-call duration.
- **MCP Server layer** (innermost): `config/shell_mcp_server.toml` line ~7 sets `max_timeout_sec = 300` — the ceiling the LLM's own per-request `timeout_sec` (default 30, range 1-3600 per `shell_models.py` line ~139) is clamped to (`shell_service.py` line ~265, `min(req.timeout_sec, self._max_timeout_sec)`). Other MCP servers have their own independent values (`web_search`: 10-15s, `mdq`: 30s, `rag_pipeline`: 120.0s hardcoded).
- **The inversion**: shell's `max_timeout_sec=300` > Workflow execute stage's `timeout_sec=120`. If the LLM requests (or the clamp allows) a shell command timeout close to 300s, the enclosing Workflow execute stage times out first at 120s. `subprocess_runner.py`'s own kill/timeout handling operates independently of the Workflow-level timeout signal — there is no code path connecting a `WorkflowTimeoutError` to cancelling an in-flight shell subprocess, so the process may continue running orphaned after the Workflow layer has already reported the stage as failed.

## Reason for Change
A layer that has already reported failure (Workflow stage timeout) while an inner operation (shell subprocess) is still running creates an observability gap (the audit trail says "failed" while a side-effecting process is still executing) and a potential resource leak (the orphaned process is never explicitly cancelled by the outer timeout). This is exactly the kind of cross-layer inconsistency ADR-014's responsibility-boundary work aims to prevent, even though ADR-014 itself does not cover numeric timeout values (Out of Scope there).

## Implementation Intent
Establish and enforce the invariant that each layer's maximum allowed duration is strictly less than the enclosing layer's timeout, either by lowering `shell_mcp_server.toml`'s `max_timeout_sec` to fit within the Workflow execute stage's `timeout_sec` (with margin for Agent-layer overhead), or by making the Workflow execute stage's `timeout_sec` configurable per-stage-type to accommodate long-running shell operations deliberately, and by ensuring an in-flight subprocess is actually cancelled when the enclosing Workflow stage times out (closing the orphaned-process gap in `subprocess_runner.py`).

## Target Files or Areas
- `config/shell_mcp_server.toml`
- `config/workflows/default.json`
- `scripts/mcp_servers/shell/subprocess_runner.py`
- `scripts/agent/workflow/workflow_engine.py`

## Required Changes
- Decide (as a design/product judgment, not purely mechanical) whether shell's `max_timeout_sec` should be lowered to fit within the Workflow execute stage's `timeout_sec` with margin, or whether the Workflow execute stage's `timeout_sec` should be raised/made stage-type-aware to legitimately accommodate long shell operations — this issue does not prescribe which; either resolves the inversion but they have different operational consequences (Constraints below).
- Whichever direction is chosen, verify and, if needed, wire the actual process cancellation: confirm `subprocess_runner.py`'s termination handling (`kill_process_group` per its `SIGTERM`/`SIGKILL` docstring) is invoked when `WorkflowEngine`'s `asyncio.wait_for` raises `TimeoutError` for a stage that had an in-flight shell subprocess, closing the orphaned-process gap.
- Audit the other MCP servers' timeout values (`web_search`: 10-15s, `mdq`: 30s, `rag_pipeline`: 120.0s hardcoded) against all Workflow stage `timeout_sec` values in `config/workflows/default.json` for the same inversion pattern, not just shell — this issue's investigation only confirmed the shell case in detail.

## Constraints
- Lowering `shell_mcp_server.toml`'s `max_timeout_sec` has an operational cost: it caps how long a legitimately long-running shell command (e.g. a large test suite) can run before being killed regardless of Workflow settings — do not lower it below what current legitimate use cases require without checking actual shell command usage patterns first.
- Raising the Workflow execute stage's `timeout_sec` affects every execute stage, not just ones that happen to invoke shell — evaluate whether a per-stage-type or per-tool timeout budget is more appropriate than a single global raise.

## Acceptance Criteria
- No MCP server's maximum allowed operation duration exceeds the Workflow stage `timeout_sec` that encloses it, across all servers checked in Required Changes' audit step.
- An in-flight shell subprocess is confirmed to be terminated when the enclosing Workflow stage times out (verified by a new test, not just code inspection).
- The chosen resolution and its rationale are recorded (ADR Known Deviation, Review Trigger, or a new operational doc section) so a future timeout-value change can be checked against this invariant.

## Testing Expectations
Add an integration test that starts a shell command with a duration between the (post-fix) MCP-layer max and the Workflow-layer stage timeout is no longer possible to construct if the fix eliminates the inversion — construct instead a test that intentionally exceeds the Workflow stage timeout with an in-flight shell subprocess and confirms the subprocess is actually terminated (not orphaned). Run `tests/agent/workflow/` and `tests/mcp_servers/shell/` after the change.

## Documentation Impact
Document the intended timeout hierarchy (Workflow > Agent > MCP Server, with the specific invariant "inner max ≤ outer timeout with margin") in `docs/agent_10_04_operations-and-observability-validation-and-troubleshooting.md` or the nearest equivalent operational doc, and cite the resolved values so future config changes can be checked against it.

## Out of Scope
- Establishing an Agent/turn-level time budget distinct from `sse_heartbeat_timeout` — this issue only addresses the confirmed Workflow-vs-MCP inversion; whether an intermediate Agent-layer timeout is needed at all is a separate design question.
- The Tool Call-level idempotency/execution-ID gap and the retry-ownership documentation gap — tracked separately (see related issues from the same design review).

## Dependencies
N/A: none — can be implemented independently, though it shares source context with the Tool Call idempotency and retry-ownership issues filed from the same review.

## Unresolved Questions
Which direction to resolve the inversion (lower MCP ceiling vs. raise/restructure Workflow stage timeout) is a product/operational judgment this issue does not make — resolve during implementation by checking actual historical shell command durations in audit logs, if available, before choosing.

## AI Implementation Instruction
Do not silently pick a resolution direction without first checking actual usage data (or explicitly flagging that no such data was available) — this is a case where a wrong default (e.g. arbitrarily lowering the MCP ceiling) could break legitimate long-running shell use cases. If no usage data is available, present the tradeoff rather than deciding unilaterally.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-123737
- **Related target files**: config/shell_mcp_server.toml, config/workflows/default.json, scripts/mcp_servers/shell/subprocess_runner.py, scripts/agent/workflow/workflow_engine.py
