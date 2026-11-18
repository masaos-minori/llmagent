## Goal
Replace the per-message list rebuild in `HistoryManager._apply_unit_drops` with a single
pass so fallback truncation does not degrade to O(N·M) when many turn units must be
dropped. Output stays identical to the current implementation.

## Priority
Low

## Scope
- **In-Scope**: Rewrite `_apply_unit_drops` to drop candidate units in a single pass over
  the history while preserving every current guarantee; add an equivalence unit test
  covering heavy truncation.
- **Out-of-Scope**: Selection policy, protected-turn handling, `_fallback_truncate`
  gating/reporting, token estimation, and compression selection.
- **Dependencies**: The Issue names one constraint (not a sequencing dependency).
  - **Depends on**: `issues/done/20261026-224931_history001_token-overflow-compression-fallback.md` | phase all | constrains the invariant (`no-orphan-tool-row`, `never-empty-history`) this rewrite must preserve; already closed, no ordering required.

## Background
`scripts/agent/history.py::_fallback_truncate` drops whole turn units (never splitting one,
never orphaning a tool row, never emptying the history) to bring context under the char
limit when LLM-based compression fails. It is a fallback path, not the hot compression
path.

## Problem
`_apply_unit_drops` rebuilds `new_history = [x for x in new_history if x is not m]` for
every message in every drop-candidate unit. Dropping U units of k messages each from a
history of N messages is O(U·k·N); when most of the history must be dropped this
approaches O(N²).

## Reason for Change
Correctness is unaffected and the path is a fallback, but a large history that needs heavy
truncation pays a quadratic cost for an otherwise linear operation. Practical risk is
unconfirmed (不明) without profiling or history-size data; the change is a non-blocking
robustness improvement.

## Implementation Intent
Compute the set of protected/drop message ids once, then build the dropped history in a
single pass over `history`, keeping only messages outside the drop set. Preserve the
existing guarantees: whole-unit drops, no orphaned tool row, never-empty history, system
messages and the `protect_turns` tail preserved. Do not change the selection policy,
protected-turn handling, or the `_fallback_truncate` gating/reporting.

## Requirements
- `REQ-001`: `_apply_unit_drops` drops the same candidate units and returns the same list
  as the current implementation, computed in a single pass over the history instead of a
  per-message full-list scan.
- `REQ-002`: An equivalence unit test asserts the rewritten method produces identical output
  to the current output across several drop scenarios, including heavy truncation.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/history.py` | Modify | Rewrite `_apply_unit_drops` (lines 373-389) to a single-pass partition over the history, preserving whole-unit drops, no-orphan-tool-row, and never-empty-history guarantees. | REQ-001 | Observed: nested identity-scan rebuild `new_history = [x for x in new_history if x is not m]` per message in each unit (`checked in Step 2/3`) | `tests/agent/test_history_manager.py` | Verified |
| `tests/agent/test_history_manager.py` | Modify | Add an equivalence test asserting the rewritten `_apply_unit_drops` matches the current output across drop scenarios including heavy truncation. | REQ-002 | Existing `_fallback_truncate`/`_apply_unit_drops` tests at lines 821-981 exercise the fallback path (`checked in Step 3`) | `tests/agent/test_history_manager.py` | Verified |

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
| `issues/done/20261026-224931_history001_token-overflow-compression-fallback.md` | States the invariant (`no-orphan-tool-row`, `never-empty-history`) the rewrite must preserve. | `scripts/agent/history.py` / REQ-001 |

## Acceptance Criteria
- `_apply_unit_drops` returns a list identical (by identity and order) to the current
  implementation for the same inputs, across light and heavy truncation (`REQ-001`,
  AC via REQ-002 test).
- A history where most units are dropped completes in a single linear pass over the
  history instead of a per-message full-list scan (`REQ-001`).
- Whole-unit boundaries, no-orphan-tool-row, and never-empty-history invariants still hold
  (`REQ-001`).

## Tests
- Equivalence test (`REQ-002`): for several drop scenarios including heavy truncation,
  assert the rewritten `_apply_unit_drops` output equals the current output element-by-element.
- Existing `_fallback_truncate`/`_apply_unit_drops` tests in `tests/agent/test_history_manager.py`
  pass unchanged (`REQ-001`).

## Documentation Impact
N/A: no doc describes the fallback truncation algorithm's complexity; if one does, note the
drop is now single-pass (drives REQ-001).

## Assumptions
- Identity-based membership (`id(m)`) stays correct even when two messages have equal
  content, because they are distinct objects; the single-pass drop set keyed on `id()`
  preserves this.
- Deriving the drop-id set once and partitioning in a single pass selects exactly the same
  candidate units and protected tail as the current nested scan, so selection policy and
  protected-turn handling are unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether history size ever makes the O(N·M) cost measurable (不明) | No profiling or typical history-size data | Non-blocking; profile before merging if uncertain; the change is a pure refactor with identical output regardless | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/history.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A (small task): affects one source file plus one test file, touches only private
methods (`_apply_unit_drops`, called solely by `_fallback_truncate`), changes no public or
runtime-facing interface, and modifies no schema.

The decision of WHICH candidate units to drop is unchanged: units are consumed in
importance order and dropped while `_is_over_any_limit(new_history)` holds and dropping the
unit leaves at least one message (`len(new_history) - len(unit) >= 1`), breaking at the
first unit that fails either condition. The single-pass optimization replaces only the
REMOVAL: instead of rebuilding `new_history` once per message in each dropped unit
(`[x for x in new_history if x is not m]`, O(k\u00b7N) per unit), the drop-id set is
accumulated for the units selected by that gate and the result is built in ONE
comprehension over `history` keeping messages whose `id()` is outside the drop set.

Because `count_chars` and `estimate_tokens` are additive over messages, the over-limit gate
can be evaluated on running totals (`total - sum(dropped-unit contributions)`) that
reproduce `_is_over_any_limit(new_history)` exactly for every prefix of dropped units, so
the selected prefix — and therefore the drop-id set — is identical to the nested scan's.
The result is the identical list, computed in a single linear pass over `history` instead
of a per-message full-list scan. The drop-id set is determined by that gate, NOT by
unconditionally dropping every candidate: dropping all candidates would ignore the early
break and the never-empty guard and diverge from the current output.

The whole-unit-drop guard (`_is_over_any_limit(new_history)` and the `len(new_history) -
len(unit) >= 1` never-empty check) stays inside `_apply_unit_drops` as it always was; it
now drives accumulation into the drop-id set under the same early-break rather than a
per-message list rebuild, so `_fallback_truncate`'s contract is unchanged and no guard
moves to the caller.

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

1. **Phase 1: Rewrite `_apply_unit_drops` (REQ-001; `scripts/agent/history.py`)**
   - [ ] Replace the nested `for m in unit: new_history = [x for x in new_history if x is not m]` rebuild with a single-pass partition that keeps messages whose `id()` is outside the drop set.
   - [ ] Preserve whole-unit drops, no-orphan-tool-row, and never-empty-history behavior; keep the method's "drop whole candidate units, never empty" contract.
   - [ ] Keep `_fallback_truncate`'s per-unit over-limit guard intact (it already gates each unit before calling `_apply_unit_drops`).
2. **Phase 2: Add equivalence test (REQ-002; `tests/agent/test_history_manager.py`)**
   - [ ] Add a test asserting the rewritten `_apply_unit_drops` returns output identical (identity + order) to the current output across several drop scenarios, including heavy truncation where most units are dropped.
3. **Phase 3: Deployment & Verification (REQ-001, REQ-002; `scripts/agent/history.py`, `tests/agent/test_history_manager.py`)**
   - [ ] Run `uv run ruff format` and `uv run ruff check` on `scripts/agent/history.py`.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/agent/history.py`.
   - [ ] Run `uv run pytest tests/agent/test_history_manager.py` and confirm existing fallback tests pass unchanged.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/history.py` | Format + lint | `uv run ruff format --check scripts/agent/history.py` && `uv run ruff check scripts/agent/history.py` | Pass (no diff, no lint errors) |
| `scripts/agent/history.py` | Type check | `uv run mypy --no-namespace-packages scripts/agent/history.py` | No issues |
| `tests/agent/test_history_manager.py` | Unit (equivalence + regression) | `uv run pytest tests/agent/test_history_manager.py` | New equivalence test passes; existing fallback tests pass unchanged |

## Risks
- **Risk**: The single-pass partition could diverge from the nested scan's output (e.g.
  different ordering or an edge case in the never-empty guard). → **Mitigation**: the
  equivalence test (`REQ-002`) asserts byte-identical output across several drop scenarios,
  including heavy truncation; the never-empty guard is preserved.
- **Risk**: Profiling shows the cost is never material, making the change low-value. →
  **Mitigation**: non-blocking; UNK-01 records the open question. The change is a pure
  refactor with identical output, so it carries no regression risk if merged.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `_apply_unit_drops` to a single-pass partition (`scripts/agent/history.py`, REQ-001) | Completed | — | 20261118-181038 |  |
| 2 | Add equivalence test (`tests/agent/test_history_manager.py`, REQ-002) | Completed | — | 20261118-181038 |  |
| 3 | Format/lint/type-check and run history tests | Completed | — | 20261118-181038 |  |

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
- **Source issue**: issues/20261118-141240_histperf001_history-fallback-truncation-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-142439
- **Related target files**: scripts/agent/history.py, tests/agent/test_history_manager.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test / Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Implementation Intent / AI Implementation Instruction | `scripts/agent/history.py` | Step 1 | Identical output; single linear pass; invariants held | ruff, mypy, `pytest tests/agent/test_history_manager.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes / Testing Expectations | `tests/agent/test_history_manager.py` | Step 2 | Equivalence test covers heavy truncation | new equivalence test | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-163938 -->