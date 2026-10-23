## Goal

Confirm `test_startup_rollback.py` covers REQ-008: on startup failure, `run()` rolls back by
calling `lifecycle.shutdown_all()` before surfacing the error, and subprocesses are not
orphaned. Verify existing rollback tests still pass against any change in row 10.

## Scope

`tests/agent/test_startup_rollback.py` only. Reference: the startup orchestrator (row 10),
the lifecycle coordinator (row 3). No change unless a gap is found.

## Assumptions

- The existing test asserts `run()` returns `(cmds, orchestrator)` on success (`:238-239`)
  and exercises the rollback path on failure.

## Design decisions

- **Verify, then fill the gap.** Confirm there is a test asserting that when a startup step
  fails, `lifecycle.shutdown_all()` is called before the error propagates (or is returned,
  if row 10 adopts REQ-006's return-type contract). If absent, add a test that forces a
  startup-step failure and asserts the rollback call.
- **Reconcile the success assertion** (`:238-239`) with row 10: if `run()` starts returning
  a `StartupFailure` value instead of raising on some path, ensure the success path still
  returns the `(cmds, orchestrator)` tuple asserted here.

## Alternatives considered

- Rewriting the rollback test from scratch — rejected: verify-only, add minimally.

## Implementation

### Target file

`tests/agent/test_startup_rollback.py`

### Procedure

1. Read `tests/agent/test_startup_rollback.py`, focusing on the rollback and success cases.
2. Confirm a rollback test asserts `lifecycle.shutdown_all()` is invoked on failure.
3. If absent, add one. Reconcile the success-tuple assertion (`:238-239`) with row 10.
4. Otherwise record the confirmation.

### Method

Add one test method if a gap exists; reconcile the success assertion; otherwise no edit.

### Details

- REQ-008's "no orphaned subprocesses on startup failure" is proven by asserting the
  rollback call; the test must force a failure mid-sequence (e.g., in `_verify_mcp_health`
  or `_check_services`).

## Compatibility considerations

- N/A unless a test is added or the success assertion is reconciled; tied to row 10.

## Security considerations

- N/A.

## Rollback considerations

- Single logical commit; `git checkout -- tests/agent/test_startup_rollback.py` restores
  HEAD. Reversible.

## Validation plan

- `uv run pytest tests/agent/test_startup_rollback.py`.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check tests/agent/test_startup_rollback.py`.

## Completion criteria

`test_startup_rollback.py` asserts the rollback `shutdown_all()` call on startup failure
(REQ-008) and the success-tuple assertion matches row 10; a case is added only if missing,
and the suite passes.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the repl caller (row 11), the tests (rows 12-16), and the docstring corrections
  (rows 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/strengthen rollback test (REQ-008) | Pending | — | — | Verify-only |
| 2 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | AC-9 |

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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `tests/agent/test_startup_rollback.py`
