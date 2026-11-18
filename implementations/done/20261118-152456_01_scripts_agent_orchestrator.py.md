## Goal

Separate the combined `is_partial` signal computed in `Orchestrator._execute_turn`
into two independent booleans, `had_partial_text` and `was_compensated`, and thread both
to `AuditEventEmitter.emit_turn_end`. This lets the turn-end audit event record whether the
LLM stream was cut off (`had_partial_text`) separately from whether the turn's partial DB
rows were rolled back (`was_compensated`), instead of the current `or`-combined value that
mislabels a clean compensation as a partial completion (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `was_compensated` is produced solely by the caller via `boundary.rollback_partial_turn()`
  after `execute_turn` returns, so it cannot be carried in `execute_turn`'s return tuple;
  it stays local to `_execute_turn` and is threaded to the audit emitter directly.
- On the non-raising (success) path, `execute_turn`'s returned `is_partial` equals
  `had_partial_text` only (no compensation occurs without an exception); it is set via
  `result.exception.partial_text` in `_run_execute_stage`
  (`workflow_engine_adapter.py:366-368`), verified against current source. `was_compensated`
  is `False` on that path.
- `rollback_partial_turn` (`turn_persistence.py:234`) returns a `bool` (`True` when
  compensation ran) — the compensation signal.
- `emit_turn_end` has one production caller (`orchestrator.py:200`); the two new parameters
  are contained within the `agent` package and cross no import-linter boundary.

## Design decisions
- Keep `execute_turn`'s return tuple unchanged (`answer, error_kind, is_partial`). Its public
  contract is not touched; `was_compensated` is computable only post-return, so extending the
  tuple is impossible for that signal (a containment win over the issue's tuple-extension
  idea). `had_partial_text` is derived from the returned `is_partial` on the success path.
- Compute both signals as locals initialized to `False` before the `try`, so the success and
  `ConversationPersistenceError` paths carry well-defined values.

## Alternatives considered
- Extend `execute_turn`'s return tuple to carry both signals. Rejected: impossible for
  `was_compensated` (computed post-return) and needlessly widens a public contract.
- Keep a single `is_partial` but widen its meaning to "turn did not complete cleanly."
  Rejected: does not separate the two conditions, so it fails `REQ-001`/`REQ-002`.

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
Rewrite `_execute_turn` (`orchestrator.py:168-204`) to split the combined partial signal.

### Method
1. In the variable-declaration block before the `try` (`orchestrator.py:169-173`), replace
   `is_partial: bool = False` with two locals, both initialized `False`:
   `had_partial_text: bool = False` and `was_compensated: bool = False`.
2. In the `try` body, change the tuple unpacking
   (`orchestrator.py:178`) from
   `answer, error_kind, is_partial = await self._workflow_adapter.execute_turn(...)` to
   `answer, error_kind, returned_is_partial = await self._workflow_adapter.execute_turn(...)`,
   then assign `had_partial_text = returned_is_partial` on the next line (success path; the
   returned value equals `had_partial_text` because no compensation occurs without an
   exception). Leave `was_compensated` as the pre-`try` `False`.
3. In the `except BaseException` handler (`orchestrator.py:192-197`), replace
   `is_partial = bool(getattr(exc, "partial_text", "")) or compensated` with two statements:
   `had_partial_text = bool(getattr(exc, "partial_text", ""))` and
   `was_compensated = bool(compensated)`.
4. In the `except ConversationPersistenceError` handler (`orchestrator.py:183-191`), set
   `had_partial_text = False` and `was_compensated = False` (both already `False` from
   initialization; state them explicitly for clarity).
5. In the `finally` block (`orchestrator.py:198-202`), pass both signals positionally to
   `emit_turn_end`, which now takes two extra parameters:
   `await self._audit_emitter.emit_turn_end(line, answer, turn_started_at, error_kind, had_partial_text, was_compensated)`.

### Details
- `execute_turn`'s return tuple `(answer, error_kind, is_partial)` is unchanged; only the
  local name in `_execute_turn` that captures the third element is renamed to
  `returned_is_partial` before re-assigning `had_partial_text`.
- The `error_kind` assignments per branch are unchanged; only the two signal locals are
  updated.
- `was_compensated` is read from the `compensated` local already bound in the `except`
  handler (`orchestrator.py:195`); guard on `boundary is not None` is preserved.

## Compatibility considerations
- `emit_turn_end` gains two positional parameters (`had_partial_text: bool`,
  `was_compensated: bool`, defaulting to `False` for any external caller). Its sole production
  caller is updated in this document. Existing tests that mock `emit_turn_end` and assert on
  positional index 4 (`call_args[4]`) still observe `False` on the `ConversationPersistenceError`
  path, where `had_partial_text` is `False`.
- `execute_turn`'s public return tuple and the workflow adapter are untouched.

## Security considerations
N/A: metric-only separation; no auth, secret, or input-handling change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `scripts/agent/orchestrator.py`: `uv run ruff format --check` && `uv run ruff check`.
- `scripts/agent/orchestrator.py`: `uv run mypy --no-namespace-packages`.
- `uv run pytest tests/agent/test_orchestrator.py` — new signal assertions plus existing
  partial-completion and turn-end tests pass.

## Completion criteria
- `_execute_turn` has no remaining reference to the combined `is_partial` expression; the two
  locals `had_partial_text` and `was_compensated` are initialized before the `try` and assigned
  on every reachable branch (success, `ConversationPersistenceError`, `BaseException`).
- The `finally` call to `emit_turn_end` passes both signals positionally.
- `ruff format`, `ruff check`, and `mypy` pass on `orchestrator.py`.
- Existing orchestrator tests pass unchanged (except the intended `test_non_persistence_exception_after_commit_records_is_partial`
  update covered by the test-file procedure).

## Out of Scope
- `execute_turn`'s return tuple shape (left unchanged; see Design).
- The persistence/compensation logic (`rollback_partial_turn`).
- The `stat_ns` partial-completion counter and the REPL `/stats` + warning contract
  (`REQ-004`; reads `ctx.stats.stat_ns`, independent of the audit field).
- Session restore/recovery, selection policy, compression.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118 | 20261118 | implemented,2:tests added+passing,3:validation green (4386 passed) |
| 2 | Add or update tests per Validation plan | Completed | 20261118 | 20261118 | Covered by the companion test-file procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118 | 20261118 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118 | 20261118 | N/A: no doc edit required for this file |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261118-141333_ispartial001_partial-flag-metric-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-143411_ispartial001_partial-flag-metric-conflation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-152456
- **Related target files**: scripts/agent/orchestrator.py
