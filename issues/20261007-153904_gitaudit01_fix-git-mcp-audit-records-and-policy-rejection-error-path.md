# Fix git-mcp audit records and policy-rejection error path

## Priority
High

## Summary
Guarantee that every write-tool call in git-mcp leaves exactly one audit record (success, rejection, or failure), return policy rejections as normal `is_error` responses instead of HTTP 500, and use only the configuration loaded at startup.

## Background
Source: local investigation notes (memo1.md, ISSUE-03), consolidating MCP-001 (raised from Medium to High) and two earlier findings. ADR-012 requires an audit trail for write operations; ADR-002 requires configuration to be loaded once at startup.

## Problem
- `git_server.py` passes `requested_target=` and `canonical_target=` to `_audit_log()`, but the `audit.py` function does not accept them; the resulting TypeError is swallowed by `_audit_log_safe()`, so no record is written (Explicit in code — `scripts/mcp_servers/git/git_server.py` passes both arguments; `scripts/mcp_servers/audit.py` does not define them). Only the path-containment rejection route still records.
- `outcome` is passed as `"success"`, while `audit.py` defines `ok` / `error` / `rejected`.
- `dispatch_tool()` treats only `ValueError` as a result-level error. Remote rejection, "nothing to commit", and postcondition failure raise `GitServiceError` and become HTTP 500, bypassing auditing (per investigation notes, not re-verified).
- A failed checkout postcondition is reported as a plain failure although the branch switch already happened.
- `format_pull()` / `format_push()` call `GitConfig.load()` on every call, which can diverge from the startup `_cfg`.
- The push postcondition inspects stdout for `[rejected]`, but git reports push results on stderr; real failures surface via exit-code exceptions, so the check is ineffective. Some `[DENIED]...` string returns in `_checkout_op`, `_pull_op`, `_push_op` are unreachable.

## Reason for Change
- The highest-risk write operations (push, pull, checkout) currently leave almost no audit trail, so who did what in which state cannot be reconstructed.
- Tests mocked `_audit_log`, hiding the signature mismatch; auditing is the one feature that must not fail silently.
- A policy rejection surfacing as 500 is seen by the Agent as a transport error, indistinguishable from a tool rejection, and increments health-check failures, which can mark the server unavailable.
- Reporting a plain failure after the state already changed invites a retry that repeats the operation.
- Re-reading configuration per call lets a config-file edit change the effective allow-list at runtime.
- Ineffective checks and dead branches create a false sense of protection.

## Implementation Intent
- Every write-tool call produces one audit record in all outcomes.
- Separate "rejected by policy" from "failed during execution"; rejections are ordinary `is_error=True` responses, and 500 is reserved for unexpected internal faults.
- Use only the startup configuration.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/audit.py`, `format_output.py`, `repository_state.py`, `git_service.py`
- Audit-related tests under `tests/mcp_servers/`
- ADR-012 and MCP git/audit documentation

## Required Changes
- Add `requested_target` and `canonical_target` to `_audit_log()`, `_build_audit_record()`, and `AuditRecord`.
- Unify `outcome` values to `ok` / `error` / `rejected`.
- Wrap the `dispatch_tool` call in `call_tool()` with try/finally so an exception still records `outcome="error"`.
- On audit write failure, log at ERROR, count failures, and expose the count in `/health` details.
- Split `GitServiceError` into rejection (remote not allowed, nothing to commit; handled as `ValueError`-like, returned as `is_error`) and execution failure.
- When reporting a postcondition failure, state that the state already changed and include the resulting state.
- Pass the startup `_cfg` to `format_pull()` / `format_push()`; stop calling `GitConfig.load()` there.
- Remove the stdout-based push postcondition (use exit code) and the unreachable `[DENIED]` returns.
- Add tests that exercise the real audit function without mocking it.

## Constraints
- Do not log secrets in audit records.
- Existing audit record consumers must keep working with the new fields (additive change).
- Fail closed: an audit failure must be visible, not silent.

## Acceptance Criteria
- Success, path rejection, remote rejection, protected-branch rejection, and postcondition failure each produce exactly one audit record, verified through the real audit function.
- A remote rejection returns HTTP 200 with `is_error=True`.
- The audit-failure counter appears in `/health` details.
- No `GitConfig.load()` call remains in the format functions.

## Testing Expectations
- Unit and integration tests as above (no mocking of `_audit_log`); ruff, mypy, targeted pytest.

## Documentation Impact
Update ADR-012 Known Deviations (MCP-001 until fixed), MCP git/audit docs (outcome values, record fields, rejection semantics), and the health-endpoint documentation for the audit-failure counter.

## Out of Scope
- Ref validation and protected-branch logic (separate issue).
- Event-loop blocking (separate issue).

## Dependencies
- After the MCP idempotency issue; may be worked together with the git-mcp ref-validation issue (overlapping files).

## Unresolved Questions
- Whether `audit_log_path` is actually configured in production and whether log rotation is operated.

## AI Implementation Instruction
Do not mock the audit function in new tests. Keep the audit schema change additive. Do not change rejection decisions, only how they are reported and recorded. Stop and report if the HTTP 500 path cannot be reproduced.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-153904
- **Related target files**: `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/git/format_output.py`, `scripts/mcp_servers/git/repository_state.py`, `scripts/mcp_servers/git/git_service.py`
