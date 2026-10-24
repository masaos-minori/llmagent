## Goal

Make `Orchestrator._execute_turn` (`scripts/agent/orchestrator.py`) the single owner of the
turn bracket so exactly one `turn_end` audit event is emitted on every exit path (success,
soft LLM error, workflow halt, an escaping exception, cancellation) and `turn_end.elapsed_ms`
measures the turn instead of process uptime (`REQ-001`, `REQ-002`).

## Scope

- **In-Scope**: `_execute_turn` (`:165-172`) rewritten as a `try` / `except BaseException` /
  `finally` bracket; adding `import time` to the stdlib import group (`:22-24`).
- **Out-of-Scope**: `handle_turn` (`:158-163`), `workflow_status()` (`:174-183`), the adapter
  wiring (`:144-154`), and every other method in the file. The adapter's own turn-end work,
  the emitter, and `TurnState` are covered by sibling documents.

## Assumptions

- `execute_turn` returns the `(answer, error_kind, is_partial)` tuple on every normal return,
  and raises (does not swallow on non-halt paths) so the `except` observes the real cause.
- `emit_turn_start` / `emit_turn_end` are idempotent-enough to be called from the bracket even
  when the adapter also ran its own path today; the adapter sibling removes the adapter copy.
- `ctx.services_required.audit_logger` may be `None` (the test harness sets it `None` at
  `tests/agent/test_orchestrator.py:79`); `emit_turn_end` already guards on `None`.

## Design decisions

- Measure `turn_started_at = time.perf_counter()` once, before `emit_turn_start()`, and thread
  it into `execute_turn` and `emit_turn_end` so `elapsed_ms` is turn-relative (`REQ-001`).
- Derive `error_kind` from the escaped exception's class name (`exc.__class__.__name__`) with no
  new event type (`DR-004`); keep it in the existing `turn_end` event only.

## Alternatives considered

`N/A: the Plan fixes the ownership model (Orchestrator owns the bracket) as a frozen decision
(`DR-001`); re-locating the bracket back into the adapter is out of scope.`

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Add `import time` to the stdlib import group near `:22-24` (keep isort order; `logger`
   already exists at `:52`).
2. Rewrite `_execute_turn` (`:165-172`) into a bracket:
   - Initialize the three locals before the `try`: `answer: str = ""`,
     `error_kind: str | None = None`, `is_partial: bool = False` (so the `finally` can always
     read them even if `emit_turn_start` raises first).
   - Set `turn_started_at = time.perf_counter()` as the first statement.
   - `try`: `await self._audit_emitter.emit_turn_start()` then
     `answer, error_kind, is_partial = await self._workflow_adapter.execute_turn(line, turn_started_at, "")`
     (pass the real timestamp instead of the `0.0` literal at the old `:168`).
   - `except BaseException as exc:` assign `error_kind = exc.__class__.__name__` and
     `is_partial = <partial flag from exc if applicable>`, then `raise`.
   - `finally:` open an inner `try` that awaits
     `self._audit_emitter.emit_turn_end(line, answer, turn_started_at, error_kind, is_partial)`
     (`REQ-004`: the emit is behind its own `try`), and in a nested `finally` call
     `self._workflow_adapter.deactivate_workflow(self._ctx)` as the very last statement.
3. Leave `handle_turn`, `workflow_status()`, and the adapter wiring untouched.

### Method

Edit the two regions inline; no new symbols, no new imports beyond `time`. Keep the body within
the measured complexity budget (complexity grade `A`; `radon cc -s -n C` stays empty; ~7540 B
against the 16384 B gate, so no baseline entry is needed).

### Details

- The current code passes `0.0` as `turn_started_at` at both `:168` and `:171`, which makes
  `elapsed_ms` equal to process uptime (~56 million ms in the measured run). Replace both with
  the single `turn_started_at` captured before the bracket.
- The `except` must re-raise so the engine's caller sees the original failure; the `finally`
  still emits `turn_end` with the derived `error_kind`.
- `deactivate_workflow` stays behind its own nesting so a raise inside `emit_turn_end` cannot
  skip the teardown (`REQ-004`, risk row: a stale active workflow would otherwise hang
  `workflow_status()` reporting `running`).

## Compatibility considerations

`execute_turn`'s signature is unchanged (the adapter sibling keeps it); only the argument passed
for `turn_started_at` changes from `0.0` to a real timestamp. No other caller of `_execute_turn`
exists outside `handle_turn`.

## Security considerations

`N/A: no auth, secret, or input-handling change. The turn ID already comes from
`emit_turn_start`; this change only re-times and re-owns the `turn_end` emission.`

## Rollback considerations

`N/A: revert the single commit.`

## Validation plan

- Add `TestTurnEndBracket` (new) in `tests/agent/test_orchestrator.py` (sibling document) covering
  cases A (success), C (soft LLM error), halt, an escaping non-retryable exception (G),
  cancellation (E), and a failure raised before `_activate_workflow`; assert the event count is
  exactly one `turn_end` per path, the fields (`task_id`, `workflow_id`, turn-relative
  `elapsed_ms`, `error_kind`), the teardown (`deactivate_workflow` called, workflow state reset),
  and the preserved soft-error fields.
- Confirm `test_orchestrator.py:537-560`, `:564-590`, `:1249-1273` and the integration suite
  (`tests/integration/test_orchestrator_integration.py`, out of scope) still pass.
- `radon cc -s -n C` reports no cycles for this file.

## Completion criteria

`_execute_turn` is a `try`/`except BaseException`/`finally` bracket that captures one
`turn_started_at`, passes it to `execute_turn` and `emit_turn_end`, derives `error_kind` from the
escaped exception, emits exactly one `turn_end` on every exit path, and calls
`deactivate_workflow` last; the four unchanged regions (`:158-163`, `:174-183`, `:144-154`,
stdlib imports aside) are byte-for-byte as before except the added `import time`.

## Out of Scope

The adapter's turn-end builders, the emitter's `task_id` parameter, the `TurnState` dead fields,
and the four doc passages are handled by sibling documents. Passing a real `session_id` at the
old `:168` stays out of scope (`turn001` frozen `REQ-009`, `UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `_execute_turn` as the turn bracket (`Implementation > Procedure`) | Pending | — | — | witness for `AC-1`-`AC-4`, `AC-8`, `AC-9` |
| 2 | Add `TestTurnEndBracket` (new) per Validation plan | Pending | — | — | asserts one `turn_end` per exit path |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `radon`, full agent test suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: no doc edit in this file | | | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 2 | turn002 (`plans/20261023-102728_plan.md`) and turn003 (`plans/20261023-125756_plan.md`) rewrite the adapter region but not this file; this file's anchors are stable | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|--------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (turn-relative `elapsed_ms`), `REQ-002`/`REQ-007` (one `turn_end`
  on every exit path), `REQ-004` (teardown never skipped), `DR-004` (derive `error_kind`, no new
  event type)
- **Source issue**: `issues/20261021-093421_turn004_turn-end-events-duplicated-or-missing.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-140855_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-092307
- **Related target files**: `scripts/agent/orchestrator.py`
