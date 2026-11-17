## Goal
Add a fail-fast guard to `_split_overlong` in `scripts/rag/ingestion/chunk_utils.py` so a non-positive `max_chunk` raises instead of entering an infinite loop, converting a misconfigured `chunk_splitter.toml` into a clear error instead of an indefinite ingestion hang.

## Priority
Low

## Scope
- **In-Scope**:
  - Raise at the top of `_split_overlong` when `max_chunk <= 0`, before the `while` loop.
  - Preserve the splitting algorithm, separator handling, and exact-reproduction invariant for all positive `max_chunk` values.
  - Add a unit test asserting `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1` and still splits correctly for `max_chunk >= 1`.
- **Out-of-Scope** (optional, flagged):
  - Validating `max_chunk > 0` at load time in `ChunkSplitter.__init__` (`scripts/rag/ingestion/chunk_splitter.py`) — recommended but optional; kept out of the required gate unless the author wants startup-surfaced validation.
- **Dependencies**:
  - **Depends on**: `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md` | phase all | same unvalidated sizing area; coordinate the value-validation choice if nc034 is still open. No hard sequencing constraint.

## Background
`chunk_utils.py` provides buffer helpers shared by `ChunkEnglishMixin` and `ChunkJapaneseMixin`. `_split_overlong(item, sep, max_chunk)` splits one item longer than `max_chunk` into chunks within `max_chunk`, and is called from `merge_text_items` with the same `max_chunk` that `ChunkSplitter` took from `chunk_splitter.toml`. `ChunkSplitter.__init__` reads `self._max_chunk = int(cfg["max_chunk"])` (line 76 of `chunk_splitter.py`) with no range validation. A prior issue (`issues/done/20261107-055949_ragc001_code-chunk-size.md`) addressed `merge_text_items` letting oversized items pass through unbounded, but did not address the non-positive-`max_chunk` hang in `_split_overlong`.

## Problem
`_split_overlong` advances `start` by the window size each iteration. When `max_chunk <= 0`:
- `window_end = min(start + max_chunk, end)` evaluates to `start` (since `start < end`), so the `window_end == end` early-break never fires.
- `window` is empty, so `gap = max(window.rfind(" "), window.rfind("\n"))` is `-1`, giving `cut = window_end = start`.
- `start = cut` leaves `start` unchanged, so `while start < end` never terminates.

Because `merge_text_items` forwards the config `max_chunk` unchanged, any non-positive `max_chunk` in `chunk_splitter.toml` makes every document hang indefinitely during chunking.

## Reason for Change
A single misconfigured value hangs the whole ingestion run with no timeout and no error. A one-line fail-fast guard at the top of `_split_overlong` (and, more robustly, a positivity check where `max_chunk` is loaded) converts an indefinite hang into a clear error.

## Implementation Intent
Fail fast at the top of `_split_overlong`: raise when `max_chunk <= 0`, before the loop. Do not change the splitting algorithm for positive `max_chunk` values, the separator handling, or the exact-reproduction invariant. Prefer also validating `max_chunk > 0` where `ChunkSplitter` loads it from config so the error surfaces at startup rather than on the first overlong item.

## Requirements
- `REQ-001`: `_split_overlong` raises when `max_chunk <= 0` before entering the loop; positive `max_chunk` behavior and the concatenation-invariant are unchanged. (Target: `scripts/rag/ingestion/chunk_utils.py`)
- `REQ-002` (optional): `ChunkSplitter.__init__` validates `max_chunk > 0` and raises the configured config-error type on a non-positive value, so the error surfaces at startup. (Target: `scripts/rag/ingestion/chunk_splitter.py`)
- `REQ-003`: A unit test asserts `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1`, and still splits correctly for `max_chunk >= 1`. (Target: `tests/rag/ingestion/test_chunk_utils.py`)

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Modify | Add a `if max_chunk <= 0: raise ...` guard at the top of `_split_overlong`, before the `while` loop (lines 30-40); leave the algorithm, `merge_text_items`, and `start_next_buf` untouched. | REQ-001 | `window_end = min(start + max_chunk, end)` (line 31) with `start = cut` (line 39) loops forever when `max_chunk <= 0`; no guard present | `tests/rag/ingestion/test_chunk_utils.py` | Verified |
| `tests/rag/ingestion/test_chunk_utils.py` | Modify | Import `_split_overlong` and add a parametrized test asserting it raises on `max_chunk <= 0` and splits correctly for `max_chunk >= 1`. | REQ-003 | Current imports only `merge_text_items`, `start_next_buf` (line 9); no existing test exercises `max_chunk <= 0` | `scripts/rag/ingestion/chunk_utils.py` | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Validate `max_chunk > 0` at load (line 76) and raise the configured config-error type. | REQ-002 (optional) | `self._max_chunk: int = int(cfg["max_chunk"])` (line 76) has no range validation | `tests/rag/ingestion/test_chunk_utils.py` (via `ChunkSplitter`) | Needs confirmation |

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
| `scripts/rag/ingestion/chunk_splitter.py` | Shows how `max_chunk` flows: `ChunkSplitter.__init__` line 76, `_chunk_code` forwards `self._max_chunk` to `merge_text_items` (lines 239-245). Needed for the optional load-time validation (REQ-002). | `scripts/rag/ingestion/chunk_utils.py`, REQ-002 |
| `scripts/rag/exceptions.py` | Configured error types: `PipelineValidationError(RagLayerError, RuntimeError)` ("invalid configuration or input") and `ChunkFormatError`. Used to choose the error type for the guard / load-time validation. | `scripts/rag/ingestion/chunk_utils.py`, REQ-001/REQ-002 |

## Acceptance Criteria
- `AC-001` (REQ-001): `_split_overlong` raises on `max_chunk = 0` and `max_chunk = -1`; for `max_chunk >= 1` output is byte-identical to the pre-change algorithm (concatenation reproduces the input).
- `AC-002` (REQ-002, optional): `ChunkSplitter` raises the configured config-error type on a non-positive `max_chunk` at construction.
- `AC-003` (REQ-003): The new failure case is covered by a green test; existing `test_chunk_utils.py` tests pass unmodified.

## Tests
- `T-001` (REQ-001/REQ-003): In `tests/rag/ingestion/test_chunk_utils.py`, import `_split_overlong`; assert it raises on `max_chunk = 0` and `max_chunk = -1`; assert a small positive `max_chunk` still splits and concatenates back to the input.
- `T-002` (REQ-002, optional): Construct `ChunkSplitter` with a non-positive `max_chunk` config and assert the configured config-error type is raised.
- `T-003`: Run `uv run pytest tests/rag/ingestion` and confirm no regression; `uv run ruff check` and `uv run mypy` clean on the changed files.

## Documentation Impact
N/A: no `docs/*.md` requires updating. The change is a defensive guard in a utility; no public protocol, config key documented in `docs/`, or operational behavior documented in `docs/` changes.

## Assumptions
- The guard only fires for `max_chunk <= 0`; all positive-`max_chunk` paths are untouched, so the exact-reproduction invariant holds.
- `_split_overlong` is importable in the test (it is a module-level function in `chunk_utils.py`).
- If load-time validation is added, `ChunkSplitter.__init__` already raises on missing keys via `cfg[...]`, so a non-positive value is the only new case to catch.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Error type for the `_split_overlong` guard: `ValueError` (idiomatic for a right-type/wrong-value argument to a pure function; matches the issue's default) vs `PipelineValidationError` (the configured config-error type, but a `RuntimeError` that couples the low-level util to the rag layer). Also whether to add the optional load-time validation in `ChunkSplitter.__init__`. | Author intent on error type and on load-time validation. | Implement `ValueError` at the `_split_overlong` guard (required); add load-time `PipelineValidationError` at `ChunkSplitter.__init__` only if the author wants startup-surfaced validation. | False |
| UNK-02 | Whether nc034 (unvalidated chunk-size bounds) resolves to a specific config-error type or validation policy that should govern this guard. | Status of `issues/done/20260927-211412_nc034_...`. | Coordinate if nc034 is still open; otherwise proceed with UNK-01's choice. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_utils.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Low | 0 | N/A (git-fame not run) | not applicable (rsynced) |

## Design
The required fix is a minimal guard at the top of `_split_overlong`: `if max_chunk <= 0: raise ValueError(...)`, placed before the `while start < end` loop. This leaves the greedy-split algorithm, separator handling, and the concatenation-invariant untouched for every positive `max_chunk`, so existing behavior is provably unchanged. `ValueError` is recommended for the guard because `max_chunk` has the right type (`int`) but an inappropriate value — the idiomatic use of `ValueError` for a pure, language-independent utility — and avoids coupling `chunk_utils.py` (imported by the language mixins) to the rag-layer exception hierarchy.

The optional load-time validation in `ChunkSplitter.__init__` (REQ-002) is the more robust location for surfacing the error at startup; there, `PipelineValidationError` (the configured config-error type in `scripts/rag/exceptions.py`) is the appropriate, layer-appropriate error. If both layers raise, they may use different types (util → `ValueError`, loader → `PipelineValidationError`); unify on one type only if the author prefers.

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

1. **Phase 1: Core Logic — guard `_split_overlong`**
   - [ ] Add `if max_chunk <= 0: raise ValueError(f"max_chunk must be positive, got {max_chunk}")` at the top of `_split_overlong`, before the `while` loop; leave the algorithm and `merge_text_items` untouched (REQ-001; `scripts/rag/ingestion/chunk_utils.py`)
2. **Phase 2: Optional load-time validation**
   - [ ] Validate `max_chunk > 0` in `ChunkSplitter.__init__` after `self._max_chunk = int(cfg["max_chunk"])` and raise the configured config-error type on a non-positive value (REQ-002; `scripts/rag/ingestion/chunk_splitter.py`) — skip if UNK-01 resolves to guard-only
3. **Phase 3: Tests**
   - [ ] Import `_split_overlong` in `tests/rag/ingestion/test_chunk_utils.py`; assert it raises on `max_chunk = 0` and `max_chunk = -1`, and splits correctly + reproduces the input for `max_chunk >= 1` (REQ-003; `tests/rag/ingestion/test_chunk_utils.py`)
   - [ ] Add the optional `ChunkSplitter` load-time assertion if Phase 2 lands (REQ-002; `tests/rag/ingestion/test_chunk_utils.py`)
4. **Phase 4: Deployment & Verification**
   - [ ] Run `uv run pytest tests/rag/ingestion` and confirm no regression across the full suite (T-003)
   - [ ] Run `uv run ruff check` and `uv run mypy` on the changed files; fix any findings (T-003)

### Release units
N/A: no release unit. Each phase passes validation on its own.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_utils.py` + `tests/rag/ingestion/test_chunk_utils.py` | Unit | `uv run pytest tests/rag/ingestion` | green; `_split_overlong` raises on `max_chunk <= 0`; positive-`max_chunk` correctness + invariant preserved; existing tests pass unmodified |
| `scripts/rag/ingestion/chunk_splitter.py` (if REQ-002 lands) | Unit | `uv run pytest tests/rag/ingestion` | green; non-positive `max_chunk` raises the configured config-error type at construction |
| Full suite | Integration | `uv run pytest` | no regression anywhere |
| Changed files | Lint / type | `uv run ruff check` and `uv run mypy` on `scripts/rag/ingestion/chunk_utils.py`, `scripts/rag/ingestion/chunk_splitter.py` | clean (no new findings) |

## Risks
- **Risk**: The guard changes `merge_text_items` behavior for `max_chunk <= 0` from "hang forever" to "raise". → **Mitigation**: this is the intended fix; no existing test exercises `max_chunk <= 0`, so no regression. Production always supplies a positive `max_chunk` from config.
- **Risk**: Choosing `PipelineValidationError` in the low-level util couples `chunk_utils.py` to the rag exception layer. → **Mitigation**: recommend `ValueError` in the util; reserve `PipelineValidationError` for the `ChunkSplitter` load site (UNK-01).
- **Risk**: Adding load-time validation (REQ-002) could mask a previously-passing config if `max_chunk` was legitimately `0` or negative somewhere. → **Mitigation**: verify no config/test sets `max_chunk <= 0`; the guard makes such a config invalid by design.
- **Risk**: The exact-reproduction invariant must hold for positive `max_chunk`. → **Mitigation**: the guard is outside the splitting loop; positive paths are byte-for-byte unchanged.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Core Logic — guard `_split_overlong` (`scripts/rag/ingestion/chunk_utils.py`) | In Progress | — | — | REQ-001 |
| 2 | Optional load-time validation (`scripts/rag/ingestion/chunk_splitter.py`) | In Progress | — | — | REQ-002 (optional; gated on author decision) |
| 3 | Tests (`tests/rag/ingestion/test_chunk_utils.py`) | In Progress | — | — | REQ-003 |
| 4 | Deployment & Verification | Pending | — | — | REQ-003 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261118-070731_01_scripts_rag_ingestion_chunk_utils.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261118-070731_02_tests_rag_ingestion_test_chunk_utils.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261118-070731_03_scripts_rag_ingestion_chunk_splitter.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-18T04:32:00
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`, `tests/rag/ingestion/test_chunk_utils.py`, `scripts/rag/ingestion/chunk_splitter.py` — the full list of `File Path` values from
  `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-070731 -->
