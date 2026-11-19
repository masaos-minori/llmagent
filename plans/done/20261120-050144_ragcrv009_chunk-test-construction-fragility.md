## Goal
- Finish the construction-and-fixture restructuring that `issue-to-plan` finding F-009 started: the `object.__new__` fabrication and stub-tokenizer seam were already landed by `ragcrv006`, and the size-rule regression tests were landed by `ragcrv001`/`ragcrv002`/`ragcrv003`; this Plan deduplicates the repeated splitter-config construction into one shared config-builder fixture and corrects the now-stale size-rule documentation in `rag_02_03`.

## Priority
Medium

## Scope
- **In-Scope**:
  - Replace the repeated inline splitter-`config` dictionaries in `tests/rag/ingestion/test_chunk_splitter.py` with one shared config-builder fixture and route the existing tests through it.
  - Correct `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` section 3.1.4 so the "Undersized" Markdown path records the discard warning that `ragcrv003` now emits, and link the size-rule behaviors to the tests that guarantee them in the existing invariant-matrix style.
- **Out-of-Scope**:
  - Re-introducing or re-writing the size-rule regression tests (`min_chunk > max_chunk`, `chunk_overlap >= max_chunk`, oversized first sentence, below-`min_chunk` English/Markdown/code) — these already exist and are green.
  - Re-working the `object.__new__` removal or the stub-tokenizer seam — already landed by `ragcrv006`.
  - Changing production chunking behavior (each fix is filed separately).
  - Coverage of the crawler or search layers.
- **Dependencies**: The Issue depends on `ragcrv001`/`ragcrv002`/`ragcrv003` for the behaviors being locked down. Those three are already implemented and archived in `issues/done/`, and their regression tests already cover the behaviors, so nothing here waits on them.
  - **Depends on**: `N/A: none`

## Background
- `tests/rag/ingestion/test_chunk_splitter.py` originally built objects with `object.__new__(ChunkSplitter)` plus hard-coded private attribute assignment, and `_make_ja_mixin` injected a real tokenizer, so constructor validation and the public construction path were untested and the tests depended on Sudachi dictionary availability.
- `ragcrv006` replaced that fabrication with `_make_splitter` (a real `ChunkSplitter` seeded via a `config` dict) and `_make_ja_mixin` (a `_StubTokenizer`), removing the `object.__new__` path and the Sudachi dependency from unit tests.
- `ragcrv001`/`ragcrv002`/`ragcrv003` added the size-rule regression tests this Issue asked for: oversized-first-sentence handling, `min_chunk > max_chunk` and `chunk_overlap >= max_chunk` raising at construction, below-`min_chunk` English/Markdown/code discards that log a warning, and the English stopword effect on stored `content`.
- The chunk suite grew from 88 to 126 passing tests; `test_chunk_utils.py` calls `merge_text_items` directly and `test_chunk_grouping.py` does not construct a splitter, so neither needs the shared config-builder fixture.

## Problem
The splitter-`config` construction is still repeated as inline dictionaries across `test_chunk_splitter.py` instead of one shared builder, and `rag_02_03` section 3.1.4 still describes the undersized Markdown path as "silently dropped, with no error or warning", which contradicts the warning that `ragcrv003` now logs.

## Reason for Change
F-009's construction-and-fixture work is largely complete; the remaining duplicate-config smell and the stale doc statement are the only items left from the Issue's Required Changes.

## Implementation Intent
Introduce one config-builder fixture in `test_chunk_splitter.py` that returns a validated splitter-`config` dict (and, where a test needs a constructed splitter, the splitter itself), then route the existing inline-config tests through it without changing any assertion. Then correct `rag_02_03` section 3.1.4's "Undersized" row to record the discard warning and link each size-rule behavior to its guaranteeing test, following the doc's existing invariant-matrix style. No production code changes; no new size-rule tests.

## Requirements
- `REQ-001`: `tests/rag/ingestion/test_chunk_splitter.py` builds its splitter-`config` through one shared config-builder fixture instead of repeating inline `config` dictionaries; existing assertions are unchanged.
- `REQ-002`: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` section 3.1.4 records that an undersized Markdown section is discarded with a warning (matching `ragcrv003`'s actual behavior) and links each size-rule behavior to the test that guarantees it.
- `REQ-003`: No test constructs a chunk/splitter object with `object.__new__`; the chunk suite runs without relying on Sudachi dictionary availability in unit-level tests.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Replace the repeated inline splitter-`config` dictionaries with one shared config-builder fixture and route existing tests through it; no assertion changes. `test_chunk_utils.py` calls `merge_text_items` directly and `test_chunk_grouping.py` does not construct a splitter, so neither is touched. | REQ-001, REQ-003 | No shared config fixture exists (`rg config_builder|@pytest.fixture.*config|_splitter_config` over `tests/rag/ingestion/` returns no match); `_make_splitter` seeds via a `config` dict (line 43-44); `object.__new__` appears only in docstrings (lines 44, 206) | `test_T_001`/`test_T_002`/`test_T_003` below-`min_chunk` warnings; `test_min_chunk_greater_than_max_chunk_raises_at_construction` | Verified |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Correct the "Undersized" Markdown row (line 53) that states "silently dropped, with no error or warning" to record the discard warning `ragcrv003` now emits, and link size-rule behaviors to their guaranteeing tests in the existing invariant-matrix style. | REQ-002 | Line 53 says "silently dropped, with no error or warning"; production logs `discarded %s item(s) (%s chars) below min_chunk` (`scripts/rag/ingestion/chunk_splitter.py` line 288); `test_T_002_below_min_chunk_markdown_logs_warning` asserts `levelno == logging.WARNING` | REQ-002 | Verified |

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
| `scripts/rag/ingestion/chunk_splitter.py` | Confirm the exact below-`min_chunk` discard warning emitted by the English/Markdown/code paths before correcting `rag_02_03`; the doc must match production, not the Issue's original assumption | REQ-002 |
| `tests/conftest.py` | Isolation guard (`production_paths_allowed`) and existing fixture conventions to follow when introducing the shared config-builder fixture | REQ-001 |

## Acceptance Criteria
- Every splitter-`config` in `test_chunk_splitter.py` is produced by the shared config-builder fixture and no inline `config` dictionary remains for splitter construction — REQ-001, AC-001.
- No existing test assertion changed; the chunk splitter suite still passes 126 tests — REQ-001, AC-002.
- `rag_02_03` section 3.1.4 states that an undersized Markdown section is discarded with a warning, matching `chunk_splitter` production behavior — REQ-002, AC-003.
- No test constructs a chunk/splitter object with `object.__new__`, and the chunk suite runs without the Sudachi dictionary being loaded in unit-level tests — REQ-003, AC-004.

## Tests
- Run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py -q` and confirm all pass with no new isolation-guard failures; the count stays at 126 (REQ-001, REQ-003).
- Verify no inline splitter-`config` dictionary remains by re-running the evidence grep used in the Implementation Target Files row (REQ-001).

## Documentation Impact
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` must be updated: correct the stale "silently dropped, with no error or warning" statement and link the size-rule behaviors to their guaranteeing tests. This maps to the chunksplitter doc in `docs/00_index.md`'s Document References by Task table.

## Assumptions
- Only `test_chunk_splitter.py` constructs a `ChunkSplitter`, so the shared config-builder fixture can live in that file rather than `tests/conftest.py`; `test_chunk_utils.py` (calls `merge_text_items` directly) and `test_chunk_grouping.py` (does not construct a splitter) do not need it.
- The size-rule regression tests already present (`test_T_001`/`test_T_002`/`test_T_003`, oversized-first-sentence, `min_chunk > max_chunk`, `chunk_overlap >= max_chunk`) fully cover the behaviors F-009 listed, so no new size-rule test is required.
- The stub-tokenizer seam (`_StubTokenizer` via `_make_ja_mixin`) keeps the Japanese unit tests independent of the Sudachi dictionary, satisfying the "no Sudachi reliance" constraint at design level.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the shared config-builder fixture belongs in `tests/conftest.py` for cross-file reuse versus locally in `test_chunk_splitter.py`. Resolution: keep it local to `test_chunk_splitter.py` because that is the only file that constructs a splitter; promote to conftest only if a later test requires it. | None blocking: only one file builds a splitter today. | Decide during implementation; recommend local fixture. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Test-only; no production impact. Refactoring construction touches every test that builds a splitter config. | Medium | High | not applicable (rsynced) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Documentation-only; corrects a stale statement. No runtime impact. | Low | High | not applicable (rsynced) |

## Design
- Add a module-level `@pytest.fixture` (e.g. `splitter_config`) in `test_chunk_splitter.py` that returns a validated splitter-`config` dict, and where a test needs the constructed splitter, a second fixture that seeds `ChunkSplitter` through its public constructor using that config. Route the existing inline-config tests through these fixtures without altering any assertion, so behavior is unchanged and the fixture becomes the single construction seam.
- Correct `rag_02_03` section 3.1.4's "Undersized" bullet from "silently dropped, with no error or warning" to "discarded and a `logging.WARNING` is emitted (below_min_chunk)", matching `chunk_splitter` production, then add rows linking each size-rule behavior to its guaranteeing test in the doc's existing invariant-matrix style. Do not alter the documented `max_chunk` exception or non-ja behavior.

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

1. **Phase 1: Preparation / Refactoring**
   - [ ] Add a shared `splitter_config` fixture (and a splitter-seeding fixture where needed) to `tests/rag/ingestion/test_chunk_splitter.py` — REQ-001, `tests/rag/ingestion/test_chunk_splitter.py`.
2. **Phase 2: Core Logic Implementation**
   - [ ] Route the existing inline-config tests through the shared fixture without changing any assertion — REQ-001, `tests/rag/ingestion/test_chunk_splitter.py`.
   - [ ] Correct `rag_02_03` section 3.1.4 "Undersized" row to record the discard warning and link size-rule behaviors to their guaranteeing tests — REQ-002, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`.
3. **Phase 3: Deployment & Verification**
   - [ ] Run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py -q` and confirm all pass with count unchanged at 126 and no new isolation-guard failures — REQ-001, REQ-003, `tests/rag/ingestion/test_chunk_splitter.py`.

### Release units
N/A: every phase passes validation alone; the fixture refactor and the doc correction are independently runnable and testable.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Unit: all existing tests pass through the shared fixture; no new isolation-guard failure | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py -q` | 126 passed, count unchanged |
| `tests/rag/ingestion/test_chunk_splitter.py` | Static: no inline splitter-`config` dictionary remains | `rg -n "config" tests/rag/ingestion/test_chunk_splitter.py` review | config built only via fixture |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Static: "Undersized" row records the warning; size-rule behaviors linked to tests | manual read vs `chunk_splitter` production | Doc matches production |

## Risks
- **Risk**: Routing existing tests through the shared fixture accidentally changes a construction path and alters behavior. → **Mitigation**: the fixture returns the identical `config` dict the inline dictionaries produced; verify by the unchanged 126-pass suite and no assertion edits.
- **Risk**: Correcting the doc overstates or understates production behavior. → **Mitigation**: derive the "Undersized" statement directly from `chunk_splitter`'s below-`min_chunk` warning log (line 288) and the `test_T_002` assertion before editing.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: shared `splitter_config` fixture in `test_chunk_splitter.py` | In Progress | — | — |  |
| 2 | Phase 2: route tests through fixture; correct `rag_02_03` section 3.1.4 | In Progress | — | — |  |
| 3 | Phase 3: run chunk suite, confirm 126 pass, no isolation-guard failures | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261120-071413_01_tests_rag_ingestion_test_chunk_splitter.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261120-071413_02_docs_21_rag_rag_02_03_ingestion_pipeline-chunksplitter.md.md | 2 | Procedure | Pending | — | — |

Type options: Test / Task / Phase / Doc / Config / Infra / Other

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-050144
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (share one config-builder fixture) | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1, 2 | No inline splitter-`config` remains; assertions unchanged | chunk suite 126 pass; static `rg config` review | Planned |
| REQ-002 | Documentation Impact | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Phase 2 | Undersized Markdown path records the discard warning | manual read vs `chunk_splitter` production | Planned |
| REQ-003 | Constraints, Acceptance Criteria | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 2, 3 | No `object.__new__`; no Sudachi reliance in unit tests | chunk suite runs green without Sudachi | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-071413 -->