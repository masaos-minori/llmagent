# mcp_tool_discovery escalates per-entry WARNING findings to FATAL for required servers, contradicting its own docstring and tests

## Priority
High

## Summary
`scripts/agent/services/mcp_tool_discovery.py`'s `_validate_and_normalize_entry()`
docstring states "Schema errors are per-tool WARNING findings, not FATAL", and its helper
`_warning_entry()` always builds a `StartupCheckStatus.WARNING` finding. But
`_fetch_server_tools()` (the caller) escalates any such finding to
`StartupCheckStatus.FATAL` whenever `cfg.required` is true:

```
normalized, finding = self._validate_and_normalize_entry(key, cfg.url, raw_entry)
if finding is not None and cfg.required:
    finding = StartupCheckOutcome(..., status=StartupCheckStatus.FATAL, ...)
```

`McpServerConfig.required` defaults to `True`. 4 tests in
`tests/agent/services/test_mcp_tool_discovery.py` construct servers via the file's
`_server()` helper (which does not override `required`), expect the resulting finding's
`status` to be `WARNING` per the docstring, and fail because it is actually `FATAL`.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` that this
reproduces identically on that commit alone, unrelated to this session's own (Agent/
EventBus reference-table) work rebased on top of it afterward.

## Problem
It is unclear from the code alone which side is the intended, current design: the
docstring/tests (per-tool schema issues should always be WARNING, never FATAL), or the
escalation logic (a required server's malformed tool entry should be FATAL, blocking
startup). As written, the escalation logic wins at runtime, silently contradicting the
documented contract in `_validate_and_normalize_entry()`'s own docstring. If the
escalation is the correct, intended behavior, a single malformed tool entry from any
`required=True` server (the default for every server unless explicitly overridden) will
FATAL-block agent startup — a much stronger blast radius than "per-tool WARNING findings,
not FATAL" implies to a reader of that docstring.

## Reason for Change
A docstring that contradicts the actual runtime behavior is itself a defect (misleads any
future maintainer reading `_validate_and_normalize_entry()` in isolation), and the current
runtime behavior may be an unintended over-escalation that could FATAL-block agent startup
for a minor, single-tool schema issue on any server that has not explicitly set
`required=False`.

## Implementation Intent
Decide, with evidence (git history of `_fetch_server_tools()`'s escalation block and
`_validate_and_normalize_entry()`'s docstring, and/or the intended operational behavior
this discovery service should have), which behavior is correct:
- If per-entry schema WARNING should never escalate to FATAL even for required servers,
  remove or narrow the escalation block in `_fetch_server_tools()` so it does not apply to
  findings originating from `_validate_and_normalize_entry()` (it may still be intended
  for whole-server unreachability findings — read the surrounding code before removing
  anything).
- If escalation to FATAL for required servers is intentional, correct
  `_validate_and_normalize_entry()`'s docstring to state this explicitly, and update the 4
  failing tests to expect `FATAL` when the server is required (and add/keep a
  `required=False` case expecting `WARNING`, so both branches remain covered).
Do not pick a resolution based only on which change makes the tests pass — the
docstring/test/code triangle must end up mutually consistent with a deliberate, correct
design.

## Target Files or Areas
- `scripts/agent/services/mcp_tool_discovery.py` (`_validate_and_normalize_entry`,
  `_fetch_server_tools`)
- `tests/agent/services/test_mcp_tool_discovery.py` (4 tests using `_server()`'s default
  `required=True`)

## Required Changes
- Investigate which of the two behaviors above is intended (check `git log -p` for when
  the escalation block and the docstring were each last changed, and whether they moved
  together or drifted apart).
- Apply the corresponding fix from Implementation Intent above.

## Constraints
Whatever the resolution, both `required=True` and `required=False` server configurations
must have explicit, tested coverage for this escalation behavior afterward — do not leave
only one branch covered.

## Acceptance Criteria
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` reports 0 failures.
- `_validate_and_normalize_entry()`'s docstring accurately describes the actual runtime
  severity behavior for both `required=True` and `required=False` servers.

## Testing Expectations
Run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q`; also run the full
`uv run pytest tests/ -q` to confirm no new failures are introduced elsewhere.

## Documentation Impact
If the resolution changes `_validate_and_normalize_entry()`'s docstring, check whether any
`docs/*.md` file describing MCP tool discovery startup-check severity needs the same
correction (per `routing.md`'s Documentation row) — not investigated as part of this
issue.

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/test_orchestrator.py`, `tests/agent/services/test_config_reload.py`,
`tests/eventbus/test_eventbus_auth.py`,
`tests/mcp_servers/git/test_git_security_compliance.py`) — each is tracked as its own
issue.

## Dependencies
N/A: none.

## Unresolved Questions
Which behavior (always-WARNING vs. escalate-to-FATAL-when-required) is the intended
design is not resolved by this issue — left as the implementer's first investigation step.

## AI Implementation Instruction
Do not fix this by simply changing the 4 tests' expected status to `FATAL` without first
determining whether that is the correct intended behavior — that would silently accept a
possibly-unintended startup-blocking escalation. Investigate first, then apply exactly one
of the two resolutions in Implementation Intent, keeping both `required=True`/`False`
branches tested. Keep the diff minimal and scoped to this file pair.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164314
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py, tests/agent/services/test_mcp_tool_discovery.py
