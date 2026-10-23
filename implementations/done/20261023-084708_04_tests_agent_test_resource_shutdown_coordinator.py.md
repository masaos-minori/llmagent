## Goal

Keep the five existing stubbed `ResourceShutdownCoordinator.close_resources()` tests as
the explicit ordering / error-collection contract (labelled as such in their
docstrings), and add one **unstubbed** test that a real, contended checkpoint step is
bounded by the coordinator's own `asyncio.wait_for` — producing a recorded
`TimeoutError` shutdown error while the following cleanup steps still run (AC-1, AC-6,
REQ-001, REQ-009).

## Scope

Test change to `tests/agent/test_resource_shutdown_coordinator.py` only. Adds one case
to the existing file; relabels the two `TestSettlementBlockRemoved` docstrings to state
they exercise stubs. Reference reads: `scripts/agent/resource_shutdown_coordinator.py`
(the `wait_for` blocks and the `errors` list at `:67`, summary at `:149-151`),
`scripts/agent/wal_checkpoint_manager.py` (the real step body under test, row 1),
`scripts/db/helper.py` (a temp WAL database with a competing reader). Depends on row 1
(production step body) and, for a fast bound, on row 2/3 making the bound a settable
named value.

## Assumptions

- `ResourceShutdownCoordinator(ctx, view, wal)` accepts any object exposing
  `checkpoint_sync()` / `backup_sync()` returning the documented shapes, so a real
  `WalCheckpointManager` can be injected in place of the current `MagicMock`/`AsyncMock`
  `wal` — confirm the constructor signature at `resource_shutdown_coordinator.py` before
  injecting.
- A second connection holding an open read transaction over a temp WAL database makes a
  real `PRAGMA wal_checkpoint(PASSIVE)` copy zero frames and block (measured in the
  plan Background), which is what forces the real step body past the bound.
- The coordinator's checkpoint bound is currently a hardcoded `30.0` (`:74`); a test
  must shorten it (see Design decisions) so it does not wait 30 s.

## Design decisions

- Build the new case around a **real temporary database** (`tmp_path`) and a **real
  `WalCheckpointManager`**, never an `AsyncMock` — that is exactly what REQ-011 forbids
  in the existing five cases (a stub whose `await` yields, which production's blocking
  step never does). The assertion must exercise the production step body (AC-1).
- Shorten the coordinator's bound for the test by monkeypatching the module-level bound
  the coordinator reads (e.g. `resource_shutdown_coordinator._SHUTDOWN_TIMEOUT_S = 0.5`),
  which requires row 2/3 to have introduced a single named bound (REQ-003). Until then,
  patch the current `timeout=` literal path via the same mechanism the implementation
  chooses; do **not** hardcode a `0.5` literal into the test that the production code
  does not expose.
- Assert two things: (1) a `TimeoutError` shutdown-error entry is recorded in the
  coordinator's `errors` list (the abandoned step), and (2) the post-checkpoint cleanup
  steps still run (background-task cancellation, history flush) — i.e. AC-6 holds even
  when the checkpoint is abandoned.
- Relabel the two `TestSettlementBlockRemoved` methods (`test_healthy_shutdown_completes_promptly`,
  `test_no_shutdown_error_entries_after_settlement_block_removal`) to state in their
  docstrings that they exercise stubs and document intent at zero cost, per the plan's
  Tests section.

## Alternatives considered

- Injecting a fake step that blocks via `asyncio.sleep` instead of a real DB — rejected:
  that re-introduces the stub shape REQ-011 forbids and would not prove the *production*
  step body is bounded. Real database required.
- Making the bound a constructor/config parameter — out of scope; the plan keeps the
  single bound in the coordinator (REQ-003), so the test patches the module constant.

## Implementation

### Target file

`tests/agent/test_resource_shutdown_coordinator.py`

### Procedure

1. **Rework the two `TestSettlementBlockRemoved` docstrings.** Add one clause each
   stating the case exercises stubbed `checkpoint_sync`/`backup_sync` (`AsyncMock`) and
   documents the ordering/error-collection contract rather than the real defect
   (REQ-011). Leave the assertions unchanged.
2. **Add one unstubbed class** (e.g. `TestRealContendedStepIsBounded`) with a single
   async test:
   - Open a temp WAL database (`tmp_path`, `PRAGMA journal_mode=WAL`) with committed
     rows; open a **second** connection in a held read transaction over it.
   - Construct a real `WalCheckpointManager` pointed at that database and inject it as
     the coordinator's `wal`; construct the coordinator with a real-ish `view` and a
     minimal `ctx`.
   - Monkeypatch the coordinator's bound to a short value (see Assumptions).
   - Call `await coordinator.close_resources()`.
   - Assert a `TimeoutError`-naming entry is present in the recorded shutdown errors
     (the abandoned checkpoint), and that the post-checkpoint cleanup still ran
     (background tasks cancelled / history written) — AC-1 + AC-6.
   - Tear down the competing connection and temp DB in `finally` to avoid handle leaks
     (Risks).

### Details

- The test is inherently timing-sensitive; assert via `asyncio.Event` / completion
  markers where possible and keep the shortened bound generous enough to be stable
  (REQ-008 forbids `time.sleep` as a fix).
- Because this file is shared with `20261022-082349` (which also targets
  `resource_shutdown_coordinator.py` and this test), apply this edit only after reading
  `20261022-082349` and confirming the new test class is region-disjoint from its edits.
- Do not import or reference any symbol that does not yet exist in row 1 without marking
  it `(new)`.

## Compatibility considerations

- New test class is additive; the five existing stubbed tests are preserved verbatim
  except for docstring relabelling. No existing assertion changes behaviour.

## Security considerations

- N/A: tests operate on throwaway temporary databases under `tmp_path`; no auth, secret,
  or permission change.

## Rollback considerations

- Delete the added class and revert the two docstrings. Single logical commit;
  reversible.

## Validation plan

- `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -q` (all six cases
  pass).
- `uv run pytest tests/agent -q --durations=10` to confirm no slow-test / handle-leak
  regression.
- Mutation: deleting the coordinator's `except TimeoutError` append (`:78-83`) must fail
  the new case (REQ-005 gives that branch a real signal).
- `uv run ruff check`, `uv run mypy --no-namespace-packages` on the test file.

## Completion criteria

The five stubbed tests remain as the labelled ordering/error-collection contract, the
new unstubbed case passes against a real contended step and asserts both the recorded
`TimeoutError` and that subsequent cleanup runs, the mutation check fails as stated, and
no integration-marked case runs in the default suite.

## Out of Scope

- Production step edits — row 1. Coordinator bound collapse — row 2. `test_repl.py` —
  row 5. Docs — rows 6/7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relabel the two `TestSettlementBlockRemoved` docstrings to state they exercise stubs | Completed | 20261023-144455 | 20261023-144455 | REQ-011 implemented; full suite 9836 passed; procedures corrected (counts field names, step methods, TRUNCATE busy handling, single 30s bound, write_warning, mock counts) |
| 2 | Add one unstubbed real-contended-step-is-bounded test (AC-1, AC-6) | Completed | 20261023-144455 | 20261023-144455 | Gated on row 1; bound shortening needs row 2/3 |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-144455 | 20261023-144455 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Shared file with `20261022-082349`; must confirm region-disjoint before applying | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-03 | 2 | Ordering | Open | implementer | after `20261022-082349` verified disjoint |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005, REQ-009, REQ-011
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `tests/agent/test_resource_shutdown_coordinator.py`