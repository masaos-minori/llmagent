## Goal
Make `import_ops.import_from_jsonl`'s replay order tracking O(1) on delete instead of
O(n), so replay cost is linear in archive size rather than quadratic, without changing
any observable behavior.

## Priority
Low

## Scope
- **In-Scope**:
  - Replace the `order: list[str]` replay tracker in
    `scripts/agent/memory/import_ops.py` with an insertion-ordered structure whose
    removal is O(1) (a `dict[str, None]`, or reuse `state`'s key order).
  - Drop the `order.remove(mid)` call and the `if entry.memory_id not in order` append
    guard.
  - Keep `inserted = len(order)` / `len(state)` semantics unchanged.
- **Out-of-Scope**:
  - Changing what delete/pin/unpin events do to final state.
  - Refactoring the backup / `allow_loss` guard at `import_ops.py:86`.
  - Any change outside `scripts/agent/memory/import_ops.py`.
  - Changing which records are considered parsable or skipped.
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
The replay loop in `import_ops.import_from_jsonl` maintains two structures: `state`
(a `dict[str, MemoryEntry]` of `memory_id -> MemoryEntry`) and `order` (a `list[str]`
of ids in first-seen order). On a `delete` event it does `del state[mid]` (O(1)) and
`order.remove(mid)` (O(n) in the current length of the list). Because `order.remove`
scans the list, an archive with many delete events costs O(d * n) where d is the
number of deletes and n the number of memory lines.

## Problem
For archives dominated by deletes (or large rebuilds), the replay becomes quadratic.
Import/rebuild is a batch operation, so it is not a per-turn hot path, but a large
archive makes `/memory rebuild` and no-loss backups noticeably slower than necessary,
and the cost is easy to introduce accidentally.

## Reason for Change
The refactor committed the replay logic as-is. The linear-time fix is small and
removes an avoidable performance cliff without changing any observable behavior.

## Implementation Intent
Track order using a structure whose removal is O(1) while preserving first-seen order.
In CPython 3.7+ a plain `dict` preserves insertion order and supports O(1) deletion, so
`order` can become a `dict[str, None]` (or reuse `state`, which already holds every
live id in first-seen order). Drop the separate membership check
`if entry.memory_id not in order` when appending, since dict assignment handles dedup.
Preserve the returned `(jsonl_count, inserted_count)` contract and `dry_run` behavior.

## Requirements
- `REQ-001`: replay removal of a deleted id is O(1); replay is O(n) in the number of
  archive records regardless of delete count.
- `REQ-002`: `import_ops.py` no longer calls `order.remove(...)` nor guards the append
  with `not in order`.
- `REQ-003`: the set of inserted rows and their write order (`for mid in order: add(...)`)
  is identical to before.
- `REQ-004`: `jsonl_count` still counts memory lines seen; `inserted_count` still equals
  the number of final live entries.
- `REQ-005`: `dry_run=True` still returns `(jsonl_count, 0)` with tables untouched.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/memory/import_ops.py` | Modify | Replace `order: list[str]` with an insertion-ordered dict (or reuse `state`'s key order); drop `order.remove(mid)` and the `not in order` append guard; keep `inserted = len(order)` / `len(state)`. | REQ-001–REQ-005 / O(1) removal; counts and write order unchanged | `import_ops.py:51-52` declares `state` + `order`; `order.remove(mid)` at L64-65; `not in order` guard at L75-76; `inserted = len(order)` at L100 (checked in Step 2) | `tests/agent/memory/test_import_ops.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/memory/import_ops.py` (test fixtures) | Confirm the existing import test fixtures exercise delete/pin/unpin interleaving so the O(n) behavior is covered and the rewrite is validated against real replay sequences. | import_ops.py / REQ-003, REQ-004 |

## Acceptance Criteria
- Replay runs in O(n) in the number of archive records regardless of delete count
  (REQ-001 / Acceptance: linear replay).
- Output of `import_from_jsonl` (counts and written rows) is unchanged for the existing
  import test fixtures (REQ-003, REQ-004 / Acceptance: identical output).
- `dry_run=True` still returns `(jsonl_count, 0)` with tables untouched (REQ-005).
- Type checks pass with the refactor in place (Acceptance: mypy clean).

## Tests
- Run `tests/agent/memory/test_import_ops.py`; confirm all cases still pass (REQ-003,
  REQ-004, REQ-005).
- Add a fixture with many interleaved delete/re-add events to bound the replay cost and
  assert correctness (REQ-001).
- Run `uv run ruff check` and `uv run mypy` on `import_ops.py` (REQ-001–REQ-005).

## Documentation Impact
`N/A: no docs change` — no `docs/*.md` describes the internal replay tracker.

## Assumptions
- `order` is a local variable inside `import_from_jsonl`; nothing external depends on
  it, so reusing `state`'s key order or switching to a `dict[str, None]` changes no
  cross-module contract.
- The rewrite is a pure internal-data-structure swap; no public API, signature, or
  return contract changes, so this stays a Path A (small task, no public/runtime
  interface change).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether to reuse `state`'s key order directly (dropping `order` entirely) versus a separate `dict[str, None]`. | A home choice between two valid options. | Reuse `state`'s key order (drop `order`): `state` already holds every live id in first-seen order, so one fewer structure. Reopen a separate dict only if review prefers an explicit, independent tracker. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/memory/import_ops.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification (small task): affects 1 file, no database schema change, and no
public/runtime interface change (the tracker is a local variable; the function
signature and return contract are unchanged). Path B analysis (architecture graphing,
historical churn) is skipped per `SKILL.md`; the qualitative `Blast Radius` above is
judged from Step 3 direct verification.

Design decision (carries UNK-01 to implementation): reuse `state` vs. a separate
`dict[str, None]`. Two options — (a) reuse `state`'s key order and drop `order`
entirely, or (b) keep a separate `dict[str, None]` as the tracker. Option (a) is
preferred: `state` already holds every live id in first-seen order, so this removes one
structure and one `not in order` guard with no behavior change. The choice stays open at
this phase and is recorded as UNK-01; it is non-blocking because either option yields
identical replay output.

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

1. **Phase 1: Make replay order tracking O(1)**
    - [ ] Replace `order: list[str]` with an insertion-ordered dict (or reuse
      `state`'s key order) in `scripts/agent/memory/import_ops.py`; remove
      `order.remove(mid)` and the `not in order` append guard; keep
      `inserted = len(order)` / `len(state)` (`REQ-001`–`REQ-005` /
      `scripts/agent/memory/import_ops.py`)

### Release units
N/A: no release unit — the single phase passes validation alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/import_ops.py` | Unit/Integration: replay counts and written rows unchanged; many-interleaved-delete fixture asserts correctness | `uv run pytest tests/agent/memory/test_import_ops.py` | all pass |
| `scripts/agent/memory/import_ops.py` | Static: format, lint, type | `uv run ruff format --check` / `uv run ruff check` / `uv run mypy` | clean |

## Risks
- **Risk**: reusing `state`'s key order while pin/unpin mutate `state[mid]` could
  reorder keys. → **Mitigation**: `replace()` reassigns the value under the same key,
  which does not move the key in a CPython 3.7+ insertion-ordered dict, so first-seen
  order is preserved; verify against the existing fixtures (UNK-01).
- **Risk**: changing the tracker breaks the `(jsonl_count, inserted_count)` contract. →
  **Mitigation**: keep `inserted = len(order)` / `len(state)` and `jsonl_count =
  memory_lines` semantics; the existing import tests assert these (REQ-004, REQ-005).
- **Risk**: a delete of an id never inserted (present in `order` check but absent from
  `state`) behaves differently. → **Mitigation**: preserve the `if mid in state` outer
  guard around the removal so a missing entry still emits nothing (REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Make import replay order tracking O(1) in import_ops.py | In Progress | — | — | impl doc: implementations/20261119-074329_01_scripts_agent_memory_import_ops.py.md |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-074329_01_scripts_agent_memory_import_ops.py.md | 1 | implementation-procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261118-224811_importperf001_jsonl-import-replay-order.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-003055
- **Related target files**: scripts/agent/memory/import_ops.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary; Acceptance Criteria; Required Changes | scripts/agent/memory/import_ops.py | Phase 1 | O(1) removal; O(n) replay | new interleaved-delete fixture | Confirmed by repository evidence |
| REQ-002 | Required Changes | scripts/agent/memory/import_ops.py | Phase 1 | no order.remove / no `not in order` | ruff diff | Confirmed by repository evidence |
| REQ-003 | Constraints; AI Implementation Instruction | scripts/agent/memory/import_ops.py | Phase 1 | insert set + write order unchanged | test_import_ops.py | Confirmed by repository evidence |
| REQ-004 | Constraints; Acceptance Criteria | scripts/agent/memory/import_ops.py | Phase 1 | counts unchanged | test_import_ops.py | Confirmed by repository evidence |
| REQ-005 | Constraints | scripts/agent/memory/import_ops.py | Phase 1 | dry_run returns (jsonl_count, 0) | test_import_ops.py | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-074329 -->