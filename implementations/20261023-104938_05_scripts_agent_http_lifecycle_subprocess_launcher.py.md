## Goal

Verify that `SubprocessLauncher` spawns each MCP server subprocess in its own session
(`start_new_session=True`) so the terminator's `os.killpg` path (row 2) has a real
process group to signal. REQ-010 requires the launcher to track spawned subprocesses;
this row confirms that contract holds against current source. No code change unless the
verification finds a gap.

## Scope

`scripts/agent/http_lifecycle_subprocess_launcher.py` only. Reference read: the
terminator (row 2), which consumes the launched process. Dependent test:
`tests/agent/test_http_lifecycle.py` (row 14).

## Assumptions

- The terminator's graceful shutdown (row 2) depends on each process being a group
  leader via `start_new_session=True`; the launcher is the sole construction site.

## Design decisions

- **Verify, do not modify.** Confirm the `Popen` call (`:105`) passes
  `"start_new_session": True` (`:99`) and that the returned process is recorded in the
  launcher's tracking structure (REQ-010).
- **If a gap exists** (e.g., a second launch path without the flag), fix only that path
  and add a regression test; otherwise leave the file untouched.

## Alternatives considered

- Refactoring the launcher to expose a `spawned_processes` accessor — rejected: verify-only
  per the Plan; introduce only if tracking is provably broken.

## Implementation

### Target file

`scripts/agent/http_lifecycle_subprocess_launcher.py`

### Procedure

1. Read `scripts/agent/http_lifecycle_subprocess_launcher.py` around `:95-110`.
2. Confirm `Popen` (`:105`) is called with `"start_new_session": True` (`:99`).
3. Confirm every launched process is recorded for later termination (REQ-010).
4. If both hold, make no change; record the confirmation. If either fails, edit the
   specific path and add a test.

### Method

Read-and-confirm. Edit only if verification finds a concrete gap.

### Details

- REQ-010 ties here because the coordinator (row 3) and terminator (row 2) assume the
  launcher produced group-leader processes.
- If a gap is found, mypy/pytest (row 14) is the guard.

## Compatibility considerations

- N/A unless a gap is found; this row is verification-first.

## Security considerations

- N/A: no auth, secret, or permission change. The `# nosec B603` on the `Popen` line
  (`:105`) is unchanged.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/http_lifecycle_subprocess_launcher.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_http_lifecycle.py` (row 14) — asserts the launcher
  starts each process in a new session.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check scripts/agent/http_lifecycle_subprocess_launcher.py`.

## Completion criteria

The launcher constructs every subprocess with `start_new_session=True` and tracks it for
termination (REQ-010); if unmodified, the confirmation is recorded and mypy/pytest pass.

## Out of Scope

- The terminator conversion (row 2), the coordinator branch (row 3), the tests (row 14),
  and the docstring corrections (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify `start_new_session=True` + spawn tracking (REQ-010) | Pending | — | — | Verify-only |
| 2 | Add/update lifecycle tests (row 14) if a gap is found | Pending | — | — | REQ-001 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-010
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/http_lifecycle_subprocess_launcher.py`
