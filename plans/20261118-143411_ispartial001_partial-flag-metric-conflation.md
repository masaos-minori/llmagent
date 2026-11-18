## Goal
Split the two distinct conditions joined into the turn-end audit field
`partial_completion` so a compensated turn that produced no partial LLM text no longer
reports `partial_completion=true`. The two signals (`had_partial_text`,
`was_compensated`) are computed separately and recorded independently in the audit event.

## Priority
Low

## Scope
- **In-Scope**: Compute `had_partial_text` and `was_compensated` as separate booleans in
  `Orchestrator._execute_turn`; thread both to `AuditEventEmitter.emit_turn_end` /
  `build_turn_end_event`; record them independently in the turn-end audit event; add unit
  tests covering the compensated-no-partial and partial-text branches.
- **Out-of-Scope**: The persistence/compensation logic itself (`rollback_partial_turn`),
  the `stat_ns` partial-completion counter, session restore/recovery, selection policy,
  compression, and how `execute_turn`'s return tuple is shaped (see Design).
- **Dependencies**: The Issue names constraints, not sequencing dependencies.
  - **Depends on**: `issues/done/20261104-115736_partialcount001_partial-completion-counter-dead.md` | phase all | constrains this area (single `stat_ns` owner, runner path); already closed, no ordering required.

## Background
`orchestrator.py::_execute_turn` computes, in the `except BaseException` branch,
`is_partial = bool(getattr(exc, "partial_text", "")) or compensated`, where
`compensated = await boundary.rollback_partial_turn()` (`turn_persistence.py:234`, called
only at `orchestrator.py:195`). The combined value is passed to `emit_turn_end` in the
`finally` block (`orchestrator.py:201`) and recorded as the `partial_completion` field of
the turn-end audit event (`audit_event_emitter.py:116`).

## Problem
`is_partial` is True when either the exception carried partial text OR the turn's partial
DB rows were rolled back. These are unrelated conditions joined by `or`. A turn that was
compensated (rows deleted) without any partial LLM text therefore reports
`partial_completion=true`, mislabeling a clean rollback as a partial completion.

## Reason for Change
The metric currently feeds only an audit field, so no downstream behavior depends on it,
but a misleading `partial_completion=true` can corrupt analytics/dashboards built on the
audit stream and hides the distinction between "generation cut off" and "turn rolled back
cleanly." Non-blocking; fixable without a behavior change elsewhere.

## Implementation Intent
Compute the two signals as separate locals in the `except BaseException` handler:
`had_partial_text` from `exc.partial_text` and `was_compensated` from
`rollback_partial_turn()`. Initialize both to `False` before the `try` so the success and
`ConversationPersistenceError` paths carry well-defined values. Thread both to
`emit_turn_end`, which gains the two parameters, and record them independently in the audit
event. Preserve the `ConversationPersistenceError` branch (`is_partial` stays False) and the
rest of the turn contract. `execute_turn`'s return tuple is left unchanged because
`was_compensated` is produced by the caller after `execute_turn` returns (see Design).

## Requirements
- `REQ-001`: A compensated turn whose exception carried no partial text reports
  `partial_completion=false` and `was_compensated=true` in the turn-end audit event.
- `REQ-002`: A turn whose exception carried partial text reports `had_partial_text=true`
  (and `was_compensated` reflects whether its rows were rolled back).
- `REQ-003`: The `ConversationPersistenceError` branch still records no partial completion
  (`had_partial_text=false`, `was_compensated=false`).
- `REQ-004`: The REPL `/stats` + partial-completion warning contract is unaffected: it
  reads `ctx.stats.stat_ns`, which is independent of the audit `partial_completion` field.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/orchestrator.py` | Modify | In `_execute_turn`, replace the combined `is_partial = bool(getattr(exc, "partial_text", "")) or compensated` (`except BaseException` branch, line 196) with two separate locals `had_partial_text` and `was_compensated`; initialize both to `False` before the `try`; pass both to `emit_turn_end` in the `finally` block (line 201). Leave `execute_turn`'s return tuple unchanged (Design). | REQ-001, REQ-002, REQ-003 | Observed: `is_partial` combined via `or` at line 196; `was_compensated` = `await boundary.rollback_partial_turn()` at line 195; `emit_turn_end` single caller at line 200 (`checked in Step 5`) | `tests/agent/test_orchestrator.py` | Verified |
| `scripts/agent/audit_event_emitter.py` | Modify | `emit_turn_end` (line 120) gains `had_partial_text: bool` and `was_compensated: bool`; `build_turn_end_event` (line 101) threads them and records both as separate keys in the turn-end event dict alongside the existing fields. Single internal caller at line 132. | REQ-001, REQ-002, REQ-003 | `emit_turn_end` has one caller (`orchestrator.py:200`); `build_turn_end_event` has one caller (`audit_event_emitter.py:132`); `partial_completion` built only at line 116 (`checked in Step 5`) | `tests/agent/test_orchestrator.py` | Verified |
| `tests/agent/test_orchestrator.py` | Modify | Add/extend assertions: compensated-no-partial exception → `was_compensated=true`, `had_partial_text=false`; partial-text exception → `had_partial_text=true`; `ConversationPersistenceError` → both false. Existing partial tests at lines 1117-1163 exercise these paths. | REQ-001, REQ-002, REQ-003 | Existing `test_partial_completion_*` and `test_turn_end_*_n_*` tests at lines 1117+ drive the except and ConversationPersistenceError paths (`checked in Step 5`) | `tests/agent/test_orchestrator.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/turn_persistence.py` | Defines `rollback_partial_turn` (line 234) whose boolean return becomes `was_compensated`; must confirm its success/return semantics before treating it as the compensation signal. | `scripts/agent/orchestrator.py` / REQ-001 |
| `scripts/agent/workflow_engine_adapter.py` | Confirm `execute_turn`'s returned `is_partial` on the non-raising path equals `had_partial_text` (set only via `result.exception.partial_text` in `_run_execute_stage`, line 366-368), so the success-path value can feed `had_partial_text`. | `scripts/agent/orchestrator.py` / REQ-002 |
| `tests/agent/test_audit_log_format.py` | May assert the exact set of keys in the turn-end event dict; must be checked before adding/removing fields so the audit-event shape change does not break it. | `scripts/agent/audit_event_emitter.py` / REQ-001 |
| `scripts/agent/llm_turn_runner.py` | Writer of `ctx.stats.stat_ns`; confirm it is independent of the audit `partial_completion` field to satisfy REQ-004 (REPL contract decoupling). | REQ-004 |

## Acceptance Criteria
- A compensated turn with no partial text reports `partial_completion=false` and
  `was_compensated=true` in the turn-end audit event (`REQ-001`).
- A turn whose exception carried partial text reports `had_partial_text=true` (`REQ-002`).
- The `ConversationPersistenceError` branch reports `had_partial_text=false` and
  `was_compensated=false` (`REQ-003`).
- The REPL `/stats` + partial-completion warning still read `ctx.stats.stat_ns` and are
  unaffected by the audit-field change (`REQ-004`).

## Tests
- Unit (`REQ-001`, `REQ-002`, `REQ-003`): in `test_orchestrator.py`, drive the orchestrator
  through a compensating boundary with a non-partial exception and assert
  `had_partial_text=false` / `was_compensated=true`; drive it with a partial-text exception
  and assert `had_partial_text=true`; drive the `ConversationPersistenceError` path and
  assert both signals are false.
- Regression (`REQ-004`): existing `/stats` and REPL-warning tests pass unchanged.
- Static: `uv run ruff format` and `uv run ruff check` on `orchestrator.py`,
  `audit_event_emitter.py`; `uv run mypy --no-namespace-packages` on both; existing
  orchestrator and audit tests pass.

## Documentation Impact
N/A: no doc describes the `partial_completion` audit field's meaning; if one does (check
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`, which documents the
partial-completion monitoring area per `partialcount001`), note the two separated signals
(drives REQ-001). Not required unless such a doc exists and names the field.

## Assumptions
- `was_compensated` is produced solely by the caller (`orchestrator.py`) via
  `boundary.rollback_partial_turn()` after `execute_turn` returns, so it cannot be carried
  in `execute_turn`'s return tuple; it stays local to `_execute_turn` and is threaded to the
  audit emitter directly.
- On the non-raising (success) path, `execute_turn`'s returned `is_partial` reflects
  `had_partial_text` only (no compensation occurs without an exception), so it can feed
  `had_partial_text`; `was_compensated` is `False` on that path.
- The two signals are independent: a partial-text exception may or may not be compensated,
  and a compensated turn may or may not have partial text, so both must be recorded.
- `emit_turn_end` / `build_turn_end_event` have a single caller each, so extending their
  signatures is contained within the agent package.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any external dashboard/consumer reads the `partial_completion` audit field beyond a count (不明) | No in-repo consumer found; external systems outside this repo are not inspectable | Non-blocking; the issue states nothing downstream depends on it; if a consumer exists it needs the two new fields, which are additive | False |
| UNK-02 | Whether `execute_turn`'s success-path `is_partial` equals `had_partial_text` across every workflow exit path (e.g. engine-level partial handling at `workflow_engine_adapter.py:216`) | Full trace of `is_partial` assignment sites across all workflow exits | Non-blocking; verify in implementation (checked in Step 5 the `_run_execute_stage` site already gates on `partial_text`); if it diverges, derive `had_partial_text` from `exc.partial_text` uniformly and drop reliance on the returned value | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/orchestrator.py` | Modify | Low (single caller of `emit_turn_end`; contained to the except/finally branches) | 13 | N/A | not applicable (rsynced) |
| `scripts/agent/audit_event_emitter.py` | Modify | Low (single internal caller of `build_turn_end_event`; audit dict has no in-repo consumer) | 3 | N/A | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Low (adds assertions on existing paths) | N/A | N/A | not applicable (rsynced) |

## Design
Existing-codebase review (python-design, evidence-based). Responsibility boundaries:
`Orchestrator._execute_turn` owns deriving the two signals from the point they are known;
`AuditEventEmitter` owns recording them independently in the audit event. Nothing else owns
either signal.

Data flow and control flow drive the interface decision. The current combined value is
`is_partial = bool(getattr(exc, "partial_text", "")) or compensated` in the `except
BaseException` handler (`orchestrator.py:196`), where `compensated` comes from
`boundary.rollback_partial_turn()` (`turn_persistence.py:234`). Two facts fix the design:

1. `was_compensated` is produced by the caller AFTER `execute_turn` returns. It cannot be
   carried in `execute_turn`'s return tuple — the issue's "propagate both through
   `execute_turn`" is therefore not achievable as literally stated. `was_compensated` stays
   local to `_execute_turn` and is threaded to the audit emitter directly.
2. `had_partial_text` is known in two places: inside `execute_turn` on the non-raising path
   (set via `result.exception.partial_text` in `_run_execute_stage`, `workflow_engine_adapter.py:366-368`)
   and in the `except BaseException` handler via `exc.partial_text`. On the success path the
   returned `is_partial` equals `had_partial_text` (no compensation occurs without an
   exception), so it can feed `had_partial_text`; `was_compensated` is `False` there.

Recommended approach (C): leave `execute_turn`'s return tuple unchanged (its public
contract is not touched — a containment win over the issue's tuple-extension idea). In the
`except BaseException` handler compute `had_partial_text` and `was_compensated` as separate
locals, both initialized to `False` before the `try` so the success and
`ConversationPersistenceError` paths carry well-defined values. `emit_turn_end` gains the two
parameters and passes them to `build_turn_end_event`, which records both as separate keys in
the turn-end event dict. Because `emit_turn_end` has one caller (`orchestrator.py:200`) and
`build_turn_end_event` one internal caller (`audit_event_emitter.py:132`), the signature
change is fully contained within the `agent` package and crosses no import-linter boundary.

Alternatives considered:
- (A) Extend `execute_turn`'s return tuple to carry both signals. Rejected: impossible for
  `was_compensated` (computed post-return) and needlessly widens a public contract.
- (B) Keep a single `is_partial` but widen its documented meaning to "turn did not complete
  cleanly." Least invasive (no new fields), but does not separate the two conditions, so it
  does not satisfy REQ-001/REQ-002's intent of distinguishing "generation cut off" from
  "rolled back cleanly." Acceptable fallback only if separation proves too risky.

Compatibility impact: the audit event dict gains two keys; no in-repo consumer reads
`partial_completion`, so nothing breaks except possibly `test_audit_log_format.py` if it
pins the exact key set (a Reference-file check, not a production risk). The REPL `/stats` +
warning contract reads `ctx.stats.stat_ns` (`llm_turn_runner.py` writer), which is
independent of the audit field, so REQ-004 holds by construction. Async safety is unchanged:
`rollback_partial_turn` stays awaited in the same position; no sync/async boundary moves.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Separate the signals in `_execute_turn` (REQ-001, REQ-002, REQ-003; `scripts/agent/orchestrator.py`)**
   - [ ] Initialize `had_partial_text = False` and `was_compensated = False` before the `try` so the success and `ConversationPersistenceError` paths carry well-defined values.
   - [ ] In the `except BaseException` handler replace `is_partial = bool(getattr(exc, "partial_text", "")) or compensated` with `had_partial_text = bool(getattr(exc, "partial_text", ""))` and `was_compensated = bool(compensated)`; leave `execute_turn`'s return tuple unchanged.
   - [ ] Pass both signals to `emit_turn_end` in the `finally` block; on the success path derive `had_partial_text` from `execute_turn`'s returned value and set `was_compensated = False`; on the `ConversationPersistenceError` path keep both `False`.
2. **Phase 2: Record the signals in the audit event (REQ-001, REQ-002, REQ-003; `scripts/agent/audit_event_emitter.py`)**
   - [ ] Add `had_partial_text: bool` and `was_compensated: bool` params to `emit_turn_end` and `build_turn_end_event`.
   - [ ] Record both as separate keys in the turn-end event dict alongside the existing fields; verify `test_audit_log_format.py` still holds (Reference-file check).
3. **Phase 3: Tests & verification (REQ-001..REQ-004; `tests/agent/test_orchestrator.py`, `scripts/agent/orchestrator.py`, `scripts/agent/audit_event_emitter.py`)**
   - [ ] Add assertions for the compensated-no-partial, partial-text, and `ConversationPersistenceError` branches (`test_orchestrator.py`).
   - [ ] Run `uv run ruff format` and `uv run ruff check` on `orchestrator.py`, `audit_event_emitter.py`.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/agent/orchestrator.py scripts/agent/audit_event_emitter.py`.
   - [ ] Run `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_audit_log_format.py` and confirm existing partial tests pass.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/orchestrator.py` | Format + lint | `uv run ruff format --check scripts/agent/orchestrator.py` && `uv run ruff check scripts/agent/orchestrator.py` | Pass (no diff, no lint errors) |
| `scripts/agent/audit_event_emitter.py` | Format + lint + type check | `uv run ruff format --check scripts/agent/audit_event_emitter.py` && `uv run ruff check scripts/agent/audit_event_emitter.py` && `uv run mypy --no-namespace-packages scripts/agent/audit_event_emitter.py` | Pass; no mypy issues |
| `scripts/agent/orchestrator.py` | Type check | `uv run mypy --no-namespace-packages scripts/agent/orchestrator.py` | No issues |
| `tests/agent/test_orchestrator.py` | Unit (new branches + regression) | `uv run pytest tests/agent/test_orchestrator.py` | New signal assertions pass; existing partial tests pass unchanged |
| `tests/agent/test_audit_log_format.py` | Regression (audit-event shape) | `uv run pytest tests/agent/test_audit_log_format.py` | Pass (event-shape assertions still hold) |

## Risks
- **Risk**: High 30-day churn on `orchestrator.py` and `workflow_engine_adapter.py` (13
  commits each) means the surrounding turn path is actively changing, so a rebase during
  implementation may meet drift. → **Mitigation**: the change is small and localized to the
  `except BaseException` handler and the two audit-emitter methods; existing partial-completion
  tests guard the behavior, and the plan targets disjoint regions.
- **Risk**: Adding keys to the turn-end event dict could break `test_audit_log_format.py` if
  it pins the exact key set. → **Mitigation**: read it as a Reference-file check and run its
  suite in the validation plan; assert only on the new fields rather than the whole dict.
- **Risk**: If UNK-02 resolves that `execute_turn`'s success-path `is_partial` does not equal
  `had_partial_text` on some workflow exit, deriving `had_partial_text` from the returned
  value would be wrong. → **Mitigation**: fall back to deriving `had_partial_text` uniformly
  from `exc.partial_text` in the except handler and `False` on the non-raising path; the
  change stays a pure metric separation with identical output for clean turns.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Separate `had_partial_text` / `was_compensated` in `_execute_turn` (`scripts/agent/orchestrator.py`, REQ-001..003) | Pending | — | — | |
| 2 | Record both signals in the turn-end audit event (`scripts/agent/audit_event_emitter.py`, REQ-001..003) | Pending | — | — | |
| 3 | Tests + format/lint/type-check (`tests/agent/test_orchestrator.py`, REQ-001..004) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261118-141333_ispartial001_partial-flag-metric-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-143411
- **Related target files**: scripts/agent/orchestrator.py, scripts/agent/audit_event_emitter.py, tests/agent/test_orchestrator.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test / Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Required Changes / AC-1 | `scripts/agent/orchestrator.py`, `scripts/agent/audit_event_emitter.py` | Step 1, Step 2 | compensated-no-partial → `partial_completion=false`, `was_compensated=true` | new orchestrator test; `test_audit_log_format.py` | Confirmed by repository evidence |
| REQ-002 | Problem / Implementation Intent / AC-2 | `scripts/agent/orchestrator.py`, `scripts/agent/audit_event_emitter.py` | Step 1, Step 2 | partial-text exception → `had_partial_text=true` | new orchestrator test | Confirmed by repository evidence |
| REQ-003 | Constraints / AC-3 | `scripts/agent/orchestrator.py`, `scripts/agent/audit_event_emitter.py` | Step 1, Step 2 | `ConversationPersistenceError` → both signals false | existing `test_turn_end_*_n_*` tests | Confirmed by repository evidence |
| REQ-004 | Constraints / AC-4 | `scripts/agent/orchestrator.py` (unchanged stat_ns path) | Step 3 | `/stats` + REPL warning unaffected | existing `/stats` and REPL-warning tests | Confirmed by repository evidence |
