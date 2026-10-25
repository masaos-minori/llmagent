# Implementation Procedure — scripts/agent/commands/db_session_ops.py

## Goal

Make `DbSessionOps.purge` (43-63) forward the current session id
(`self._ctx.session.session_id`) to the service and state the exemption in the
success line (REQ-003, REQ-005, AC-003).

## Scope

- Modify only the `purge` method of `scripts/agent/commands/db_session_ops.py`.
- `purge(rest)` signature seen by `cmd_session.py` (dispatch at `cmd_session.py:229`)
  is unchanged; option parsing and `CommandValidationError` flows are unchanged.

## Assumptions

- `self._ctx` is already held by `DbSessionOps.__init__` (17) and `_make_cmd` in the
  command tests wires a real `DbSessionOps` over a `SimpleNamespace` ctx whose
  `session.session_id` is a plain int (test file 29-60) — no ctx plumbing needed
  (issue verification "no cmd_session.py edit needed").
- `session.session_id` is `None` for an unsaved session; passing `None` means "no
  guard" end to end (procedure 01 branch selection), matching the `_session_delete`
  guard's authoritative value (`cmd_session.py:65-77`).

## Design decisions

- Success-line wording (U-002 decision):
  `Purged: N session(s) removed (kept active session <id>) [Session]` when the
  exemption fired; the existing line verbatim otherwise — the `Purged` prefix and
  `[Session]` suffix stay stable for existing output assertions.
- Forward as keyword `current_session_id (new)=...` (procedure 02 signature).

## Alternatives considered

- Always append the guard state (`kept active session None`): rejected — noisy for
  the common no-exemption case and breaks the "existing line verbatim" default.
- Reading ctx inside the service: rejected — violates the layering constraint.

## Implementation
### Target file
`scripts/agent/commands/db_session_ops.py`

### Procedure

Replace lines 60-63 of `purge` with:

```python
result = DbMaintenanceService().purge(
    max_sessions, max_age_days, current_session_id=self._ctx.session.session_id
)
if result.kept_active_session is not None:
    self._out.write_success(
        f"Purged: {result.sessions_removed} session(s) removed "
        f"(kept active session {result.kept_active_session}) [Session]"
    )
else:
    self._out.write_success(
        f"Purged: {result.sessions_removed} session(s) removed [Session]"
    )
```

### Method
Changed body of the existing `purge` method; no new symbols. The success string is
built from `result.kept_active_session`, the new `DbPurgeResult` field (procedure 03).

### Details
- Lines 43-59 (docstring, `parse_command_args`, `parse_int_arg`,
  `CommandValidationError` handling) stay byte-identical.
- The `except CommandValidationError` path returns before the service call, so an
  invalid flag never triggers a purge (existing test at 573-577 keeps passing).

## Compatibility considerations

- `cmd_session.py` call site unchanged; the offloaded `db_dispatch` path
  (`asyncio.to_thread`) is untouched.
- `test_purge_success` asserts only `"Purged" in out` (526-530) — still green with
  the mock's `kept_active_session=None` default.

## Security considerations

N/A: no SQL in this layer.

## Rollback considerations

`git checkout -- scripts/agent/commands/db_session_ops.py`.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -x -q` (procedures 06
  updates the mock-arg assertions alongside this change).
- ruff + mypy on this file.

## Completion criteria

- AC-003: guarded purge prints the `(kept active session <id>)` note (spy/output
  capture in procedure 06).
- AC-005: unguarded purge output line is the pre-change string verbatim.

## Out of Scope

- Service forwarding (procedure 02) and the result field (procedure 03).
- `/session delete` guard semantics (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the purge body change | Pending | — | — | After procedures 02-03 |
| 2 | Run targeted validation | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (output), REQ-005
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: tests/agent/commands/test_agent_cmd_session.py (procedure 06)
