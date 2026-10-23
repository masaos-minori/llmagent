## Goal

Relabel `TestCloseResourcesWALCheckpoint.test_checkpoint_timeout_records_error_and_still_runs_backup`
so it reads as a **branch-existence / scenario** test that exercises a stub, not as
coverage of the real defect. Move the real bounded-await assertion into the new
`tests/agent/test_wal_checkpoint_manager.py` (row 3).

## Scope

Test change to `tests/agent/test_repl.py` only. One method's docstring is rewritten; its
assertions are kept. Reference reads: `scripts/agent/resource_shutdown_coordinator.py`
(the `except TimeoutError` branch at `:77-87`), `scripts/agent/wal_checkpoint_manager.py`
(row 1, the real step body). Depends on row 3 for the moved assertion.

## Assumptions

- The method under change is `test_checkpoint_timeout_records_error_and_still_runs_backup`
  inside `class TestCloseResourcesWALCheckpoint` (currently around `:926-953`; cite by
  name, not line number — the file churns). Its current body makes the mocked
  `SQLiteHelper`'s `checkpoint` raise `TimeoutError` directly
  (`mock_db.checkpoint.side_effect = lambda mode: (_ for _ in ()).throw(TimeoutError())`),
  which reaches the coordinator's `except TimeoutError` branch because the stub raises
  immediately — a mechanism production's blocking step never has.

## Design decisions

- Keep the method and its assertions (`elapsed < 0.2`, a "timed out" error logged,
  backup still running) but rewrite its docstring to state explicitly that it drives a
  **stubbed** `checkpoint` that raises `TimeoutError` directly, so it verifies the
  branch exists and the backup fallback runs — **not** that the real step is bounded
  (REQ-011). This stops the next reader from mistaking it for coverage of the actual
  defect.
- Do **not** change the assertions. The real proof that a bound fires on the production
  body lives in row 3's `test_wal_checkpoint_manager.py` (bounded-await case built from
  the real step).
- Confirm the method is region-disjoint from `20261022-071052` (which also targets
  `test_repl.py`) before editing; this Plan touches only this one method's docstring.

## Alternatives considered

- Deleting the method — rejected: it is a valid branch-existence check and the plan
  keeps it, merely relabelled.
- Rewriting it to use a real DB — rejected: that duplicates row 3 and moves a
  scenario test into the real-body suite; the plan's split is branch-existence here,
  real-body elsewhere.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Locate `test_checkpoint_timeout_records_error_and_still_runs_backup` inside
   `TestCloseResourcesWALCheckpoint` by name (do not trust a cached line number).
2. Replace its docstring with one that states: this case stubs `checkpoint` to raise
   `TimeoutError` directly; it verifies the coordinator's timeout branch exists and that
   the backup stage still runs when that branch fires; it does **not** exercise the real
   blocking step body (that belongs to `test_wal_checkpoint_manager.py`).
3. Leave the method body and assertions unchanged.

### Details

- The relabel is documentation-only within the test; no new import, no assertion change.
- If `20261022-071052` edits the same class, coordinate ordering so this docstring edit
  does not conflict (region-disjoint: this is one method's docstring).

## Compatibility considerations
Correction: the TRUNCATE-fallback test's `MagicMock` counts read as busy once `busy` is honoured (`int(MagicMock())` is 1), which made it spend a real 3 s on retry backoff; its `checkpoint` stub now returns `WalCheckpointCounts(0, 0, 0)` for TRUNCATE.


- Purely additive docstring text; the method's runtime behaviour is unchanged.

## Security considerations

- N/A: test-docstring edit only.

## Rollback considerations

- Revert the docstring. Single logical commit; reversible.

## Validation plan

- `uv run pytest tests/agent/test_repl.py -q` (must stay green; behaviour unchanged).
- `uv run ruff check`, `uv run mypy --no-namespace-packages` on the test file.

## Completion criteria

The method's docstring states it exercises a stub and is a branch-existence check, its
assertions are unchanged, the real bounded-await assertion now lives in row 3, and
`test_repl.py` stays green.

## Out of Scope

- Production edits — rows 1/2. Coordinator tests — row 4. Docs — rows 6/7. Moving the
  assertion — row 3.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relabel `test_checkpoint_timeout_records_error_and_still_runs_backup` docstring to state it exercises a stub | Completed | 20261023-144456 | 20261023-144456 | REQ-011 implemented; full suite 9836 passed; procedures corrected (counts field names, step methods, TRUNCATE busy handling, single 30s bound, write_warning, mock counts) |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-144456 | 20261023-144456 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Shared file with `20261022-071052`; confirm region-disjoint before editing | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-04 | 1 | Ordering | Open | implementer | after `20261022-071052` verified disjoint |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `tests/agent/test_repl.py`