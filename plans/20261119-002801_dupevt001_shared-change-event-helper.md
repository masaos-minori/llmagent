## Goal
Extract the duplicated JSONL change-event emission shared by `write_ops._emit_delete_event`
and `pin_ops._emit_event` into a single helper, so both writers resolve the archive path
and append once instead of each carrying a copy.

## Priority
Low

## Scope
- **In-Scope**:
  - Add one shared change-event emitter in `scripts/agent/memory/jsonl_store.py` that
    resolves the archive path via `resolve_memory_jsonl_dir()` and appends an event.
  - Route `scripts/agent/memory/write_ops.py::_emit_delete_event` through the shared
    emitter.
  - Route `scripts/agent/memory/pin_ops.py::_emit_event` through the shared emitter.
  - Delete the duplicated inline `JsonlMemoryStore` construction and late import from
    both callers.
- **Out-of-Scope**:
  - Changing what data the change event records (`{"event", "memory_id", "at"}`).
  - Refactoring the JSONL read path or `iter_records`.
  - Any change to the SQLite transaction boundaries in `write_ops.delete`.
  - Changing the archive filename or its location resolution.
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
Both helpers exist to append a change event to the append-only JSONL archive after a
SQLite write (SQLite-first semantics). `pin_ops.py` documents this: `_emit_event`
"Mirrors `write_ops._emit_delete_event`." The two implementations differ only in the
event name passed through. Both lazy-import `JsonlMemoryStore`, build
`Path(resolve_memory_jsonl_dir()) / "memories.jsonl")`, and call the existing sync
primitive `append_event(event, memory_id)`.

## Problem
Two copies of the same ~4-line helper exist across `write_ops.py` and `pin_ops.py`. A
future change (archive filename, error handling, timestamp format, path construction)
must be applied in two places; a miss leaves them diverging and the archive layout
without a single source of truth.

## Reason for Change
The duplication was carried through the refactor (the commit routed writers through the
shared flat-config resolver). It is a localized maintainability risk with no runtime
effect today, but it is exactly the kind of cross-file duplication that grows silently
over time.

## Implementation Intent
Add a single shared emitter that resolves the archive path via `resolve_memory_jsonl_dir()`
and appends an event, and route both `write_ops._emit_delete_event` and
`pin_ops._emit_event` through it (replacing their bodies with a single call). Preserve
the SQLite-first ordering and the "error propagates so the caller can surface M-07"
behavior. Keep the emitter synchronous.

## Requirements
- `REQ-001`: exactly one implementation resolves the archive path and appends an event.
- `REQ-002`: `write_ops._emit_delete_event` and `pin_ops._emit_event` no longer import
  `JsonlMemoryStore` or construct the archive path themselves; they call the shared
  emitter.
- `REQ-003`: the shared emitter MUST stay synchronous and preserve SQLite-first ordering
  and error propagation (a failed append still propagates to the caller).
- `REQ-004`: the archive filename and its location resolution via
  `resolve_memory_jsonl_dir()` are unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/memory/jsonl_store.py` | Modify | Add the single shared change-event emitter that resolves the archive path and appends (synchronous). | REQ-001, REQ-003, REQ-004 / one implementation; sync; path unchanged | `append_event(event, memory_id)` exists as the sync primitive at `jsonl_store.py:72`; no shared path-resolving emitter exists (checked in Step 3) | new test for archive-path resolution | Verified |
| `scripts/agent/memory/write_ops.py` | Modify | Replace the inline `JsonlMemoryStore` construction + late import in `_emit_delete_event` with a call to the shared emitter. | REQ-002, REQ-003 / no private construction; SQLite-first preserved | `_emit_delete_event` at `write_ops.py:137-146` builds the store and calls `append_event("delete", ...)`; called after commit at `write_ops.py:133` (checked in Step 3) | delete handler tests | Verified |
| `scripts/agent/memory/pin_ops.py` | Modify | Replace the inline `JsonlMemoryStore` construction + late import in `_emit_event` with a call to the shared emitter. | REQ-002, REQ-003 / no private construction; SQLite-first preserved | `_emit_event` at `pin_ops.py:63-72` builds the store and calls `append_event(event, ...)`; called on the main path after `_set_pinned` (checked in Step 3) | pin/unpin handler tests | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/memory/config_path.py` | Confirm `resolve_memory_jsonl_dir()` is the single archive-path resolver both callers already use, so the shared emitter reuses the identical resolution. | jsonl_store.py / REQ-004 |
| `scripts/agent/memory/import_ops.py` | Confirm it does not share the duplicated emit pattern (it is out of scope); verify no third caller of the removed inline construction exists. | write_ops.py, pin_ops.py / REQ-002 |

## Acceptance Criteria
- Exactly one implementation resolves the archive path and appends an event (REQ-001 /
  Acceptance: single source of truth).
- `write_ops` and `pin_ops` no longer import `JsonlMemoryStore` for emission (REQ-002 /
  Acceptance: no JsonlMemoryStore import in the two callers).
- The shared emitter stays synchronous and preserves SQLite-first ordering and error
  propagation (REQ-003 / Acceptance: append error still propagates).
- Existing delete/pin/unpin behavior is unchanged under test (REQ-003).
- Type checks pass with the refactor in place (Acceptance: mypy clean).

## Tests
- Run `tests/agent/memory/test_import_ops.py`, `tests/agent/memory/test_memory_store.py`,
  and the pin/delete handler tests; confirm they still pass (REQ-003).
- Add a test for the shared emitter covering the archive-path resolution (REQ-001,
  REQ-004).
- Run `uv run ruff check` and `uv run mypy` on the touched files (REQ-001–REQ-004).

## Documentation Impact
`N/A: no docs change` — no `docs/*.md` describes the internal emit helpers; the
`pin_ops.py` docstring reference to `write_ops._emit_delete_event` remains accurate
since both now delegate to the same shared emitter.

## Assumptions
- The shared emitter can be a module-level function in `jsonl_store.py` used only by the
  two private emit functions, keeping the change within private symbols and preserving
  the Path A (no public interface change) classification.
- Behavior is exercised indirectly through `delete`/`pin`/`unpin`, so no existing test
  references the emit functions by name and none needs editing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the shared emitter belongs on `JsonlMemoryStore` (as a method) versus a free function in `jsonl_store.py`. | A home choice between two valid options. | Default to a module-level function in `jsonl_store.py` (keeps the contract stable and the change private); reopen the public-method option only if review prefers it. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/memory/jsonl_store.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/memory/write_ops.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `scripts/agent/memory/pin_ops.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path A classification (small task): affects 3 files, no database schema change, and the
extraction can be contained within private symbols (a module-level helper in
`jsonl_store.py` used by the two private emit functions), so no public/runtime
interface change is required. Path B analysis (architecture graphing, historical churn)
is skipped per `SKILL.md`; the qualitative `Blast Radius` above is judged from Step 3
direct verification.

Design decision (carries UNK-01 to implementation): the shared emitter's home. Two
options — (a) a module-level function in `jsonl_store.py` that resolves the path and
appends, called by both private emit functions; or (b) a method on `JsonlMemoryStore`.
Option (a) is preferred: it keeps the change private (preserving the Path A
classification and the current `.importlinter` layer state), matches the existing sync
primitive's module, and removes both copies with one definition. The choice stays open at
this phase and is recorded as UNK-01; it is non-blocking because either option yields
identical behavior.

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

1. **Phase 1: Add shared emitter**
    - [ ] Add a synchronous module-level emitter to `scripts/agent/memory/jsonl_store.py`
      that resolves the archive path via `resolve_memory_jsonl_dir()` and appends an
      event (`REQ-001, REQ-003, REQ-004` / `scripts/agent/memory/jsonl_store.py`)
2. **Phase 2: Route both writers through the emitter**
    - [ ] Replace the inline `JsonlMemoryStore` construction and late import in
      `write_ops._emit_delete_event` with a call to the shared emitter
      (`REQ-002` / `scripts/agent/memory/write_ops.py`)
    - [ ] Replace the inline `JsonlMemoryStore` construction and late import in
      `pin_ops._emit_event` with a call to the shared emitter
      (`REQ-002` / `scripts/agent/memory/pin_ops.py`)
3. **Phase 3: Deployment & Verification**
    - [ ] Add a test for the shared emitter covering archive-path resolution; run the
      delete/pin/unpin handler tests, `tests/agent/memory/test_import_ops.py`,
      `tests/agent/memory/test_memory_store.py`, `uv run ruff check`, and `uv run mypy`
      (`REQ-001`–`REQ-004`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/jsonl_store.py` | Unit: shared emitter resolves archive path and appends | `uv run pytest tests/agent/memory/test_jsonl_store.py` | all pass |
| `scripts/agent/memory/write_ops.py` | Integration: delete emits one event after SQLite commit | `uv run pytest tests/agent/memory/ (delete handler tests)` | all pass |
| `scripts/agent/memory/pin_ops.py` | Integration: pin/unpin emit one event after SQLite write | `uv run pytest tests/agent/memory/ (pin/unpin handler tests)` | all pass |
| Both source files | Static: format, lint, type | `uv run ruff format --check` / `uv run ruff check` / `uv run mypy` | clean |

## Risks
- **Risk**: moving the shared emitter to a public `JsonlMemoryStore` method widens the
  public interface and could reclassify this as Path B. → **Mitigation**: default to a
  private module-level function (UNK-01); only choose the public method if review
  explicitly prefers it, then reclassify before freezing.
- **Risk**: reordering the SQLite write and the archive append while extracting could
  break SQLite-first semantics. → **Mitigation**: keep the emit call after the commit on
  the main path exactly as it is today; the emitter only changes WHERE the append logic
  lives, not WHEN it runs.
- **Risk**: a third caller of the removed inline construction exists and is missed. →
  **Mitigation**: scan for other `JsonlMemoryStore(Path(resolve_memory_jsonl_dir()) /
  "memories.jsonl")` constructions in Step 3; only `write_ops` and `pin_ops` contain it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add synchronous shared emitter to jsonl_store.py | Pending | — | — | |
| 2 | Route write_ops._emit_delete_event and pin_ops._emit_event through the emitter | Pending | — | — | |
| 3 | Add archive-path test and run ruff/mypy/tests | Pending | — | — | |

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
- **Source issue**: issues/20261118-224741_dupevt001_shared-change-event-helper.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-002801
- **Related target files**: scripts/agent/memory/jsonl_store.py, scripts/agent/memory/write_ops.py, scripts/agent/memory/pin_ops.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Acceptance Criteria | scripts/agent/memory/jsonl_store.py | Phase 1 | single implementation resolves path + appends | new archive-path test | Confirmed by repository evidence |
| REQ-002 | Required Changes; Acceptance Criteria | scripts/agent/memory/write_ops.py, scripts/agent/memory/pin_ops.py | Phase 2 | no JsonlMemoryStore import in callers | delete/pin/unpin handler tests | Confirmed by repository evidence |
| REQ-003 | Constraints; Acceptance Criteria | scripts/agent/memory/jsonl_store.py, scripts/agent/memory/write_ops.py, scripts/agent/memory/pin_ops.py | Phase 1, Phase 2 | SQLite-first + error propagation preserved | delete/pin/unpin handler tests | Confirmed by repository evidence |
| REQ-004 | Constraints; Acceptance Criteria | scripts/agent/memory/jsonl_store.py | Phase 1 | archive filename/resolution unchanged | new archive-path test | Confirmed by repository evidence |
