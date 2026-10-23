## Goal

Verify and, if required, adjust `StartupOrchestrator.run()` so startup failures surface
correctly through its rollback path (REQ-008). The method (`:67`) already calls
`lifecycle.shutdown_all()` on failure (`:79`, `:92`) before surfacing the error at
`:102`; this row confirms that contract and aligns it with the startup-failure return
type described by REQ-006 where it applies.

## Scope

`scripts/agent/startup.py` only: the `run()` method (`:67`), its two rollback branches
(`:77-89`, `:90-102`), and the final guard (`:103-107`). Reference reads: the lifecycle
coordinator (row 3), the repl caller (row 11). No code change unless verification finds a
gap.

## Assumptions

- `run()` returns `(cmds, orchestrator)` on success and raises on failure; the rollback
  always calls `lifecycle.shutdown_all()` before propagating.
- REQ-006 describes `run()` returning `StartupFailure | HttpStartupError | None`; if the
  Plan intends that contract here, the change is to return rather than raise on the
  caught paths (`:90`, `:102`).

## Design decisions

- **Verify, do not modify first.** Read `run()` (`:67-107`) and confirm:
  - Both `except` branches (`:77`, `:90`) call `lifecycle.shutdown_all()` before
    propagating.
  - The `# noqa: BLE001` on the inner `except Exception` (`:80`, `:93`) correctly prevents
    a rollback failure from masking the original error.
  - The final guard (`:103-107`) raises `RuntimeError` only when initialization is
    incomplete.
- **If REQ-006's return-type contract applies**, convert the `raise setup_err` (`:102`)
  and the interrupt path to return the appropriate `StartupFailure`/`HttpStartupError`
  value instead of raising, and update the return annotation (`:67`). Otherwise record
  the confirmation.

## Alternatives considered

- Raising a typed `StartupFailure` instead of re-raising the raw `setup_err` — viable if
  REQ-006 requires it; adopt only after confirming the requirement's intent.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. Read `scripts/agent/startup.py` around `:55-110`.
2. Confirm both rollback branches call `lifecycle.shutdown_all()` before propagating.
3. Decide against REQ-006 whether `run()` should return startup-failure values instead of
   raising; if so, edit `:67`, `:102`, and the caught-path handling.
4. If no change, record the confirmation of the existing contract.

### Method

Read-and-confirm; edit only if verification finds a concrete gap or REQ-006 mandates the
return-type change.

### Details

- The rollback ordering (terminate before propagate) is the part that directly supports
  REQ-008's "subprocesses are not orphaned on startup failure."
- The repl caller (row 11) handles both raise and return paths; any change here must keep
  `:128-130`'s unpacking valid.

## Compatibility considerations

- Behavioral only if REQ-006 mandates returning instead of raising; the repl caller
  (row 11) must be updated in lockstep.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/startup.py` restores HEAD.
  Reversible; touches no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_startup_rollback.py` (row 17) — asserts rollback calls
  `shutdown_all()` and surfaces the startup failure.
- `uv run mypy --no-namespace-packages scripts/agent`.
- `uv run ruff check scripts/agent/startup.py`.

## Completion criteria

`run()` (`:67`) rolls back via `lifecycle.shutdown_all()` before surfacing startup errors
(:102), and — if REQ-006 applies — returns `StartupFailure | HttpStartupError | None`
instead of raising; mypy plus tests pass.

## Out of Scope

- The vocabulary (row 1), the terminator conversion (row 2), the coordinator branch
  (row 3), the repl caller (row 11), the tests (row 17), and the docstring corrections
  (rows 5, 18-21).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify/adjust `run()` startup error handling (:67, :102) | Pending | — | — | REQ-008 |
| 2 | Add/update rollback tests (row 17) | Pending | — | — | REQ-001 |
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
- **Requirement ID**: REQ-008
- **Source issue**: `issues/20261021-093421_shutdown003-subprocess-termination-failures-report-success.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-082349_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-104938
- **Related target files**: `scripts/agent/startup.py`
