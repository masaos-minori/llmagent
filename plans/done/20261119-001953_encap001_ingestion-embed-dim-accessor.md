## Goal
Replace the private-attribute access `self._store._embed_dim` in
`MemoryIngestionService._persist_entry_with_embedding` with a public accessor on
`MemoryStore`, removing a cross-module private dependency while preserving the exact
`None`-disables-validation behavior.

## Priority
Low

## Scope
- **In-Scope**:
  - Add a public read-only accessor (`embed_dim`) on `scripts/agent/memory/store.py`
    that returns the dimension stored in `MemoryStore.__init__`.
  - Route `scripts/agent/memory/ingestion.py`'s forward of the embedding dimension to
    `write_upsert` through that public accessor instead of `self._store._embed_dim`.
  - Update the `MagicMock`-based tests that set `mock_store._embed_dim` so they expose
    the new public accessor (`.embed_dim`); otherwise they pass a child mock as
    `embed_dim`.
  - Add a test asserting the public accessor mirrors the constructor dimension.
- **Out-of-Scope**:
  - Changing the `write_upsert` / `add` signature or any write path in
    `write_ops.py`.
  - Changing how `embed_dim` is validated against embeddings.
  - Affecting the manual-write path (`_persist_entry`).
  - Refactoring dedup or duplicate-link behavior.
  - Any change to `import_ops.import_from_jsonl`'s own `embed_dim` handling.
  - Updating `docs/` memory-module reference pages that mention `embed_dim` (document
    changes are out of scope for this workflow phase).
- **Dependencies**: `N/A: none`
  - **Depends on**: N/A: none

## Background
`MemoryStore.__init__` stores the optional embedding dimension in a private field
`self._embed_dim` (`store.py`). `ingestion.py` forwards it on every persisted entry via
`write_upsert(entry, embedding=embedding, embed_dim=self._store._embed_dim)`. The two
classes live in different modules of the memory package, so this crosses a module
boundary through a private name. The dimension is `None` when unset, which disables
dimension validation in the write path.

## Problem
`ingestion.py` reaches into `MemoryStore._embed_dim`, a private implementation detail.
If `MemoryStore` renames the field, computes the dimension differently, or moves it,
ingestion breaks with an `AttributeError` at runtime. The dependency is invisible in
the public type contract of `MemoryStore`.

## Reason for Change
The private access is a latent coupling that the refactor made visible by placing both
classes in the same package with clear module boundaries. It has no runtime effect
today, but it invites future breakage and hides a real dependency.

## Implementation Intent
Add a small public property (for example `embed_dim`) on `MemoryStore` that returns the
stored dimension, and have `ingestion.py` read that public property instead of
`self._store._embed_dim`. Preserve the current `None`-means-unvalidated behavior.

Alternative considered and rejected as primary: inject the dimension through the
service constructor rather than reading it back from the store. That would change the
`MemoryIngestionService` constructor and its wiring in `factory.py`; the issue names
the public accessor as the preferred approach, so it is recorded here as a design
choice (see Design) but not implemented unless the choice is reopened.

**Required deviation from the issue's "AI Implementation Instruction" (only touch
`store.py` and `ingestion.py`):** the instruction assumes no test change is needed, but
the memory-layer and integration tests drive `MemoryIngestionService` with
`MagicMock()` stores that set `mock_store._embed_dim`. Reading a public property off a
`MagicMock` returns an auto-created child mock, not the value assigned to `_embed_dim`,
so those tests would pass a mock as `embed_dim`. The affected test files MUST be updated
to set `.embed_dim`. This is confirmed by repository evidence, not a blocking unknown.

## Requirements
- `REQ-001`: `ingestion.py` MUST NOT reference `MemoryStore._embed_dim` (no private
  cross-module access remains).
- `REQ-002`: `MemoryStore` MUST expose a public accessor that returns the dimension
  stored in `__init__`, equal to the value previously read from `_embed_dim`.
- `REQ-003`: the accessor MUST preserve `None`-disables-validation semantics: `None`
  disables dimension validation, an `int` enables it.
- `REQ-004`: the `write_upsert` / `add` signatures and the write paths in `write_ops.py`
  MUST be unchanged; the manual-write path (`_persist_entry`) MUST be unaffected.
- `REQ-005`: the `MagicMock`-based tests that set `_embed_dim` MUST expose the public
  accessor via `.embed_dim` so a real value (not a child mock) is forwarded as
  `embed_dim`.
- `REQ-006`: a test MUST assert the public accessor mirrors the constructor dimension.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/memory/store.py` | Modify | Add a public read-only `embed_dim` accessor returning `self._embed_dim`; keep the private field as the single source of truth. | REQ-002, REQ-003 / accessor returns stored dimension; None preserved | `store.py:39-42` sets `self._embed_dim = embed_dim` in `__init__`; no public accessor exists (checked in Step 3) | `tests/agent/memory/test_memory_store.py` (new) | Verified |
| `scripts/agent/memory/ingestion.py` | Modify | Forward the dimension via `self._store.embed_dim` instead of `self._store._embed_dim` in `_persist_entry_with_embedding`. | REQ-001, REQ-003 / no private access; None preserved | `ingestion.py:142` calls `write_upsert(..., embed_dim=self._store._embed_dim)` (checked in Step 2) | `tests/agent/memory/test_memory_layer.py` | Verified |
| `tests/agent/memory/test_memory_layer.py` | Modify | Set `mock_store.embed_dim` on the `MagicMock` stores instead of `mock_store._embed_dim` so the public accessor yields a real value. | REQ-005 / tests forward a real embed_dim | 10 assignments `mock_store._embed_dim = ...` on `MagicMock()` stores (checked in Step 3) | test_memory_layer.py | Verified |
| `tests/integration/test_rag_llm_integration.py` | Modify | Set `store.embed_dim = 0` on the `MagicMock(spec=MemoryStore)` instead of `store._embed_dim`. | REQ-005 / integration test forwards a real embed_dim | `test_rag_llm_integration.py:80-81` `store = MagicMock(spec=MemoryStore); store._embed_dim = 0` (checked in Step 3) | integration test | Verified |
| `tests/agent/memory/test_memory_store.py` | Modify | Add an assertion that the public accessor mirrors the constructor dimension. | REQ-006 / accessor mirrors constructor dim | `test_memory_store.py` constructs real `MemoryStore()` instances (checked in Step 3) | test_memory_store.py | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/factory.py` | Confirm the real construction site `MemoryStore(embed_dim=get_embedding_dims())` so the accessor's parameter and the `None` default are understood and left intact. | store.py / REQ-002, REQ-003 |
| `scripts/agent/memory/write_ops.py` | Confirm how `embed_dim` flows into `_write_vec` / `_floats_to_blob` so the accessor preserves the `None`-disables-validation contract and no mock-as-int regression is introduced. | ingestion.py / REQ-003, REQ-004 |

## Acceptance Criteria
- No code in `ingestion.py` references `MemoryStore._embed_dim` (REQ-001 / Acceptance: no
  private access).
- The public accessor returns the same value previously read from `_embed_dim`, including
  `None` when unset (REQ-002, REQ-003 / Acceptance: same value; None preserved).
- `write_upsert` / `add` signatures and write paths are byte-for-byte unchanged; the
  manual-write path is untouched (REQ-004 / Acceptance: signatures unchanged).
- All affected tests pass with the accessor in place and forward a real dimension value
  (REQ-005 / Acceptance: tests pass).
- Type checks pass with the accessor in place (Acceptance: mypy clean).

## Tests
- Run `tests/agent/memory/test_memory_layer.py` and confirm it still passes after
  updating the mock attribute (REQ-001, REQ-005).
- Run `tests/integration/test_rag_llm_integration.py` and confirm it still passes
  (REQ-005).
- Add a test asserting the public accessor mirrors the constructor dimension, including
  the `None` case (REQ-002, REQ-006).
- Run `uv run ruff check` and `uv run mypy` on the touched files (REQ-001–REQ-006).

## Documentation Impact
`N/A: no docs change` — `docs/23_agent/agent_11_03_memory-module-reference.md` and the
generated reference mention `embed_dim` as passed by `factory.py`, but documenting
changes are out of scope for this workflow phase. If the memory-module reference is
maintained as a public API surface, note the new accessor there during a docs-only
follow-up.

## Assumptions
- Exposing a read-only property does not violate the `.importlinter` layer contract:
  `lint-imports` reports 6 contracts kept / 0 broken, and adding a property changes no
  import relationship (checked in Step 3).
- The late/early import style of `store.py` and `ingestion.py` is unchanged; no new
  top-level import is introduced by reading a property.
- The issue's "only touch `store.py` and `ingestion.py"` instruction is superseded by
  the test-update requirement confirmed in repository evidence (see Implementation
  Intent).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the dimension should instead be injected via the `MemoryIngestionService` constructor rather than read back from the store (the issue's open "Needs confirmation" ownership question). | A design decision between two valid approaches. | Implement the public accessor (issue's preferred approach); reopen the ownership question only if review prefers constructor injection. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/memory/store.py` | Modify | Low | 0 commits in last 30d (stable) | N/A: `git-fame` not available | not applicable (rsynced) |
| `scripts/agent/memory/ingestion.py` | Modify | Low | 0 commits in last 30d (stable) | N/A: `git-fame` not available | not applicable (rsynced) |
| `tests/agent/memory/test_memory_layer.py` | Modify | Low | 0 commits in last 30d | N/A: `git-fame` not available | not applicable (rsynced) |
| `tests/integration/test_rag_llm_integration.py` | Modify | Low | 0 commits in last 30d | N/A: `git-fame` not available | not applicable (rsynced) |
| `tests/agent/memory/test_memory_store.py` | Modify | Low | 0 commits in last 30d | N/A: `git-fame` not available | not applicable (rsynced) |

## Design
Path B classification (large task): satisfies two Path B criteria — it changes a public
interface (a new public accessor on `MemoryStore`) and affects more than 3 files
(2 source + 3 test). Rationale recorded here per `SKILL.md` Routing; the full analysis
below is the Path B evidence.

### Architecture analysis (Step 3/5)
- `store.py` imports: `db.helper.SQLiteHelper`, `agent.memory.mapper.row_to_entry`,
  `agent.memory.models.ConsistencyReport`, `agent.memory.sql_constants._count_fts`,
  `agent.memory.types.MemoryEntry`, `logging`. Adding a property adds no import.
- `lint-imports`: 6 contracts kept, 0 broken. The property is a member addition, not an
  import change; layer relationships are unchanged.
- `.importlinter` hierarchy (`agent → rag, db, shared, mcp_servers`): `MemoryStore` lives
  under `agent.memory`; exposing a property does not alter the module's dependencies.

### Dependency graphing (Step 5)
- Real construction site: `scripts/agent/factory.py:203`
  `store = MemoryStore(embed_dim=get_embedding_dims())`.
- Single production reader of the dimension: `ingestion.py`
  (`_persist_entry_with_embedding`). No other production module reads the stored
  dimension.
- `write_ops.add` / `upsert` consume `embed_dim` as a parameter; they are downstream of
  the accessor's return value, not consumers of the accessor itself.
- Concrete change list: `store.py`, `ingestion.py`, plus the two mock-based test files,
  plus one new-assertion test file.

### Historical analysis (Step 5)
- `git log --name-only --since=30.days -- scripts/agent/memory/`: last 30 days touched
  `write_ops.py` (2), `pin_ops.py` (2), `snippet_filter.py` (1), `import_ops.py` (1),
  `config_path.py` (1). `store.py`, `ingestion.py`, and the affected test files did not
  appear — low recent churn, lower risk to touch.
- `git log -S "_embed_dim" -- scripts/agent/memory/store.py`: introduced by earlier
  monolith-split and schema-versioning refactors; no recent churn.
- `git-fame` (bus factor) not available in this environment; column marked `N/A` per the
  Tool availability guard.

### Operational dependency inspection (Step 5)
- No MCP server and no persisted-schema / DDL change is involved. No database locks to
  check. `pip-audit` is not applicable (no dependency upgrade).

### Design decision (carries UNK-01 to implementation)
Public accessor vs. constructor injection. Two viable options:
- (a) Public read-only `embed_dim` property on `MemoryStore` returning `self._embed_dim`;
  `ingestion.py` reads it. Matches the issue's stated preference, keeps the change
  localized, and leaves `MemoryIngestionService`'s constructor and `factory.py` wiring
  untouched.
- (b) Inject the dimension through the `MemoryIngestionService` constructor; drop the
  read-back. Cleaner ownership in principle but changes the service constructor, its
  callers/tests, and `factory.py` wiring — a wider blast radius.

Option (a) is preferred and non-blocking: either option yields identical runtime
behavior, and (a) satisfies every Requirement. The choice stays open as UNK-01 and may
be reopened by review.

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

1. **Phase 1: Add public accessor**
    - [ ] Add a public read-only `embed_dim` accessor to `scripts/agent/memory/store.py`
      returning `self._embed_dim`; keep `self._embed_dim` as the single source of truth
      (REQ-002, REQ-003 / `scripts/agent/memory/store.py`)
2. **Phase 2: Route ingestion through the accessor**
    - [ ] Replace `embed_dim=self._store._embed_dim` with `embed_dim=self._store.embed_dim`
      in `_persist_entry_with_embedding` (`REQ-001, REQ-003` /
      `scripts/agent/memory/ingestion.py`)
3. **Phase 3: Update mock-based tests**
    - [ ] Set `mock_store.embed_dim` instead of `mock_store._embed_dim` in
      `tests/agent/memory/test_memory_layer.py` (all occurrences) and
      `store.embed_dim` instead of `store._embed_dim` in
      `tests/integration/test_rag_llm_integration.py` (`REQ-005` / the two test files)
4. **Phase 4: Add accessor assertion + static checks**
    - [ ] Add a test asserting the accessor mirrors the constructor dimension including
      the `None` case (`REQ-006` / `tests/agent/memory/test_memory_store.py`); run
      `uv run ruff check`, `uv run mypy`, and the memory-layer and integration tests
      (`REQ-001`–`REQ-006`)

### Release units
**Unit**: accessor-and-caller | **Phases**: 1, 2 | **Reason**: Phase 2 routes `ingestion.py` through the accessor added in Phase 1; applying Phase 2 without Phase 1 leaves `self._store.embed_dim` undefined (AttributeError), so the two production phases cannot be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/store.py` | Unit: accessor returns constructor dimension and `None` | `uv run pytest tests/agent/memory/test_memory_store.py` | all pass |
| `scripts/agent/memory/ingestion.py` | Integration: persist forwards a real dimension via the accessor | `uv run pytest tests/agent/memory/test_memory_layer.py` | all pass |
| `tests/integration/test_rag_llm_integration.py` | Integration: embedding-failure path still passes a real embed_dim | `uv run pytest tests/integration/test_rag_llm_integration.py` | all pass |
| Both source files | Static: format, lint, type | `uv run ruff format --check` / `uv run ruff check` / `uv run mypy` | clean |

## Risks
- **Risk**: reading a property off a `MagicMock` returns a child mock, so the affected
  tests could silently forward a mock as `embed_dim` and mask a broken accessor. →
  **Mitigation**: update every affected mock to set `.embed_dim` explicitly (REQ-005) and
  add a real-instance assertion (REQ-006) so the contract is covered by a non-mock test.
- **Risk**: exposing a second public name for the same field could itself become a
  duplication the next refactor targets. → **Mitigation**: the accessor delegates to the
  single private field `self._embed_dim` (one implementation), so no logic is
  duplicated.
- **Risk**: changing the accessor's location (property vs. constructor) mid-cycle. →
  **Mitigation**: implement the preferred public accessor (option a); UNK-01 records the
  open alternative for review without blocking.
- **Risk**: the issue's "only touch `store.py` and `ingestion.py"` instruction conflicts
  with the required test updates. → **Mitigation**: document the deviation in
  Implementation Intent and scope the test edits to the confirmed mock-based files only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add public read-only `embed_dim` accessor to store.py | In Progress | — | — |  |
| 2 | Route ingestion._persist_entry_with_embedding through the accessor | In Progress | — | — |  |
| 3 | Update mock-based tests to expose `.embed_dim` | In Progress | — | — |  |
| 4 | Add accessor assertion and run ruff/mypy/tests | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-072739_01_scripts_agent_memory_store.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261119-072739_02_scripts_agent_memory_ingestion.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261119-072739_03_tests_agent_memory_test_memory_layer.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261119-072739_04_tests_integration_test_rag_llm_integration.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261119-072739_05_tests_agent_memory_test_memory_store.py.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261118-224711_encap001_ingestion-embed-dim-accessor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-001953
- **Related target files**: scripts/agent/memory/store.py, scripts/agent/memory/ingestion.py, tests/agent/memory/test_memory_layer.py, tests/integration/test_rag_llm_integration.py, tests/agent/memory/test_memory_store.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Acceptance Criteria; Required Changes | scripts/agent/memory/ingestion.py | Phase 2 | no private access | test_memory_layer.py runs | Confirmed by repository evidence |
| REQ-002 | Implementation Intent; Required Changes | scripts/agent/memory/store.py | Phase 1 | accessor returns stored dimension | test_memory_store.py (new) | Confirmed by repository evidence |
| REQ-003 | Constraints; Acceptance Criteria | scripts/agent/memory/store.py, scripts/agent/memory/ingestion.py | Phase 1, Phase 2 | None-disables-validation preserved | test_memory_store.py (None case) | Confirmed by repository evidence |
| REQ-004 | Constraints; AI Implementation Instruction | scripts/agent/memory/write_ops.py (reference) | Phase 2 (no change) | signatures unchanged | ruff/mypy diff | Confirmed by repository evidence |
| REQ-005 | AI Implementation Instruction deviation (evidence-confirmed) | tests/agent/memory/test_memory_layer.py, tests/integration/test_rag_llm_integration.py | Phase 3 | tests forward real embed_dim | both suites pass | Confirmed by repository evidence |
| REQ-006 | Testing Expectations | tests/agent/memory/test_memory_store.py | Phase 4 | accessor mirrors constructor dim | new assertion | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-072739 -->