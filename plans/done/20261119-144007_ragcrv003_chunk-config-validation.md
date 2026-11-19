## Goal
Make `ChunkSplitter.__init__` reject contradictory or mistyped chunk-size configuration as a `PipelineValidationError` instead of silently accepting it, so a misconfiguration is distinguishable from a genuinely empty corpus.

## Priority
High

## Scope
- **In-Scope**: Validate the chunk-size group (`min_chunk`, `max_chunk`, `chunk_overlap`, and `md_snippet_max_chars` under `md_index_enable`) as one unit at the constructor boundary; replace bare `int()`/`bool()` coercion with typed getters that reject wrong types; document the relations in the config file and the configuration reference; add regression tests.
- **Out-of-Scope**: Re-tuning the chunk-size constants themselves (NC-034 closed as "no rationale found"); changing any chunking algorithm; adding per-chunker guards for the same values; config hot-reload or per-source overrides; touching the silent-discard logging path (covered by the sibling issue `issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md`).
- **Dependencies**: `N/A: none block this Plan.` The sibling `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` adds regression tests and constructor-construction restructuring for the same size-rule behaviors *after* this fix defines them; it reuses the same test file (see Assumptions). The sibling `issues/20261119-112016_ragcrv004_silent-chunk-discard-logging.md` reduces but does not remove the silent discard this validation surfaces; it does not share a target file.
  - **Depends on**: N/A: none

## Background
`ChunkSplitter.__init__` coerces the chunk-size keys with bare `int()`/`bool()` and raises `PipelineValidationError` only when `max_chunk <= 0`. Nothing relates `min_chunk`, `chunk_overlap`, or `md_snippet_max_chars` to `max_chunk`, so contradictory settings are accepted and produce silently empty or oversized output. The type-coercion policy in `rules/coding.md` gates `*_models.py` config loaders; this module loads config directly and is outside that stated scope, but the issue requires typed rejection regardless.

## Problem
An operator can set `min_chunk` above `max_chunk`, or `chunk_overlap` at or above `max_chunk`, and the pipeline silently produces no chunks or chunks that violate the configured upper bound. Neither the run nor the logs distinguish a misconfiguration from a genuinely empty corpus. A wrong-typed value (for example a string for `max_chunk`) is coerced rather than rejected.

## Reason for Change
Chunk-size bounds are the main quality control of the ingestion corpus, and the current guard covers one of four interacting values. Misconfiguration is the most likely operator failure and is currently invisible.

## Implementation Intent
Validate the chunk-size group as one unit at the construction boundary, before the Sudachi dictionary is constructed so a bad config fails fast. Introduce small typed getters that reject a wrong type instead of coercing it, and raise `PipelineValidationError` naming the offending key, the value read, and the relation that failed. Keep validation in the config boundary; do not add per-chunker guards. Document the relations in the config file and the configuration reference.

## Requirements
- `REQ-001`: `__init__` rejects `min_chunk < 0` and `min_chunk > max_chunk` by raising `PipelineValidationError` that names both keys and the relation that failed.
- `REQ-002`: `__init__` rejects `chunk_overlap < 0` and `chunk_overlap >= max_chunk` by raising `PipelineValidationError` that names the key and the relation that failed.
- `REQ-003`: A wrong-typed chunk-size value (for example a string where an integer is expected) is rejected rather than coerced, with an error naming the key and the value read.
- `REQ-004`: When `md_index_enable` is set, `__init__` validates `md_snippet_max_chars` against `min_chunk` and `max_chunk` and raises `PipelineValidationError` on violation.
- `REQ-005`: No currently-valid configuration changes its chunk output; the current `config/chunk_splitter.toml` defaults and the test `_CRAWL_CONFIG` pass validation unchanged.
- `REQ-006`: `config/chunk_splitter.toml` documents the required relations between the four chunk-size keys.
- `REQ-007`: The configuration reference records the valid ranges, the relations, and the `PipelineValidationError` raised on violation.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Add group validation + typed getters to `ChunkSplitter.__init__`; fail fast before Sudachi construction | REQ-001..REQ-004 | `ChunkSplitter.__init__` guards only `max_chunk <= 0` and uses bare `int()`/`bool()` coercion; runtime repro with `min_chunk > max_chunk` accepts the config with no error (Step 2) | `TestMaxChunkValidation` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Extend `TestMaxChunkValidation` with each rejected relation, wrong-type cases, and accepted-boundary parity; update the two existing tests that rely on configs the new validation rejects | REQ-001..REQ-005 | `TestMaxChunkValidation` constructs via `ChunkSplitter(config=cfg)`; `_CRAWL_CONFIG` chunk-size keys satisfy all proposed relations (Step 2); `TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series` builds `min_chunk=100000 > max_chunk=600` and `TestFetchedAtPropagation.test_md_heading_splits_have_matching_fetched_at` enables `md_index_enable` with `md_snippet_max_chars=600 > max_chunk=500`; both must be reworked to valid configs (Step 3a) | `TestMaxChunkValidation` | Verified |
| `config/chunk_splitter.toml` | Modify | Document the required relations between the four chunk-size keys | REQ-006 | Current chunk-size keys satisfy `min_chunk ≤ max_chunk` and `chunk_overlap < max_chunk`; enabling `md_index_enable` would also require the `md_snippet_max_chars` relation (Step 2) | N/A: documentation only | Verified |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Record valid ranges, relations, and the error raised | REQ-007 | The `config/chunk_splitter.toml` section documents the keys semantically but not the required relations (Step 2) | N/A: documentation only | Verified |

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
| `scripts/rag/ingestion/chunk_english.py` | Confirm validation stays out of the English mixin; the mixin receives already-bounded values | `scripts/rag/ingestion/chunk_splitter.py` |
| `scripts/rag/ingestion/chunk_japanese.py` | Confirm validation stays out of the Japanese mixin; the mixin receives already-bounded values | `scripts/rag/ingestion/chunk_splitter.py` |
| `scripts/rag/ingestion/chunk_utils.py` | `merge_text_items` consumes `min_chunk`/`max_chunk`/`chunk_overlap`; confirm valid configs keep identical merge behavior | `scripts/rag/ingestion/chunk_splitter.py` |
| `rules/coding.md` | Type-coercion policy scope (gates `*_models.py` only); decides whether `get_typed` is mandated here | `scripts/rag/ingestion/chunk_splitter.py` (REQ-003) |
| `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` | Sibling that restructures the same test file; sequencing/overlap judgment | `tests/rag/ingestion/test_chunk_splitter.py` (REQ-005) |

## Acceptance Criteria
- A config with `min_chunk > max_chunk` raises `PipelineValidationError` naming both keys (`REQ-001`, AC from Issue).
- A config with `chunk_overlap >= max_chunk` raises `PipelineValidationError` (`REQ-002`, AC from Issue).
- A config value of the wrong type (for example a string for `max_chunk`) is rejected rather than coerced (`REQ-003`, AC from Issue).
- With `md_index_enable` set, a `md_snippet_max_chars` outside `[min_chunk, max_chunk]` raises `PipelineValidationError` (`REQ-004`).
- No valid existing configuration changes its chunk output (`REQ-005`).
- The config file and configuration reference document the relations and the error raised (`REQ-006`, `REQ-007`).

## Tests
- Unit: `TestMaxChunkValidation` extended with each rejected relation (`min_chunk > max_chunk`, `min_chunk < 0`, `chunk_overlap >= max_chunk`, `chunk_overlap < 0`) and each wrong-type value (`REQ-001`, `REQ-002`, `REQ-003`).
- Unit: `md_snippet_max_chars` out of range with `md_index_enable` set raises (`REQ-004`).
- Unit: accepted boundary configurations produce the same chunk counts as before (`REQ-005`).
- Regression: the whole `tests/rag/ingestion/test_chunk_splitter.py` suite stays green (`REQ-005`).
- Regression: `TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series` currently forces zero chunks by constructing an invalid config (`min_chunk=100000 > max_chunk=600`); the new validation rejects that at construction, so update that one test to force zero chunks through a valid config (raise `min_chunk` above the source content length while keeping `min_chunk <= max_chunk`).
- Regression: `TestFetchedAtPropagation.test_md_heading_splits_have_matching_fetched_at` constructs with `md_index_enable=True` using `_CRAWL_CONFIG`, whose `md_snippet_max_chars=600` exceeds `max_chunk=500`; REQ-004 rejects that combination at construction, so update that one test to a valid `md_snippet_max_chars` (for example `400`, within `[min_chunk, max_chunk]`) while preserving the heading-split intent.

## Documentation Impact
`docs/*.md` must be updated for `REQ-006`/`REQ-007`. The target doc is the RAG configuration reference (`rag_05_01-configuration-reference.md`), named via the `docs/21_rag` area's configuration-reference entry in `docs/00_index.md` "Document References by Task". The config file `config/chunk_splitter.toml` is a separate target row, not a `docs/*.md` update.

## Assumptions
- The chunk-size keys are always present in the loaded config; missing keys are a separate concern and out of scope (the issue validates relations among present keys).
- `md_snippet_max_chars` upper bound uses `≤ max_chunk` (strictness decided during implementation; see UNK-01).
- The `rules/coding.md` type-coercion policy does not bind this module (it gates `*_models.py` only); a local typed getter that rejects wrong types is acceptable and consistent with the issue's Acceptance Criteria.
- The sibling issue `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` lands after this fix; its test-file edits sequence cleanly behind this Plan's `TestMaxChunkValidation` additions (compatible overlap, not a conflict).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Upper-bound strictness of `md_snippet_max_chars` relative to `max_chunk` when `md_index_enable` is set (the issue says "against `min_chunk` and `max_chunk`" without specifying `<` vs `≤`) | The Issue leaves the bound direction unspecified | Decide during implementation; default `min_chunk ≤ md_snippet_max_chars ≤ max_chunk`; document the chosen bound in `config/chunk_splitter.toml` and the reference | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Low | High (42 commits; recently active rag-ingestion batch) | N/A (author log unavailable) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | High | N/A | not applicable (rsynced) |
| `config/chunk_splitter.toml` | Modify | Low | Medium | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_05_01-configuration-reference.md` | Modify | Low | Low | N/A | not applicable (rsynced) |

## Design
**Architecture.** `ChunkSplitter(ChunkEnglishMixin, ChunkJapaneseMixin)` is the single config-boundary constructor. It reads `config/chunk_splitter.toml` (or an injected `config` dict), sets private size attributes, then constructs the Sudachi dictionary. Validation belongs at the top of `__init__`, before Sudachi construction, so a misconfigured run fails fast without loading the dictionary. The chunking mixins (`chunk_english.py`, `chunk_japanese.py`) and `chunk_utils.merge_text_items` receive already-bounded values and must not gain per-chunker guards (Issue AI Implementation Instruction).

**Dependency graphing.** The only production caller is the CLI entry point (`main()`), which loads the default config. Tests construct through the public constructor with a `config` dict (`TestMaxChunkValidation`, `_make_io_splitter`, end-to-end pipeline tests) or bypass `__init__` entirely (`_make_splitter`/`_make_ja_mixin` use `object.__new__`). No other module constructs `ChunkSplitter`, so the blast radius is confined to the constructor boundary.

**Historical.** `chunk_splitter.py` carries 42 commits and was in the recent rag-ingestion defect batch; churn is High. The non-positive `max_chunk` guard was added in a prior fix, establishing the precedent that constructor faults raise `PipelineValidationError`.

**Operational dependency.** `ConfigLoader().load("chunk_splitter.toml")` owns the key set and defaults. The current operational config satisfies every proposed relation, and `md_index_enable` defaults disabled, so enabling the `md_snippet_max_chars` check does not affect the default deployment.

**Type-coercion decision (UNK from Issue resolved).** `rules/coding.md` scopes its `get_typed` mandate to `*_models.py` loaders; `chunk_splitter.py` is outside that scope, so `get_typed` is not strictly required here. The Issue's Acceptance Criteria independently require rejecting wrong types, so implementation adds a small typed getter that raises `PipelineValidationError` naming the key and value. This is a design choice, not a policy obligation.

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

1. **Phase 1: Constructor validation**
   - [ ] Add a typed getter for the chunk-size integers that rejects a wrong type instead of coercing it, and raise `PipelineValidationError` naming the key, the value read, and the failed relation (`scripts/rag/ingestion/chunk_splitter.py`; REQ-001, REQ-003)
   - [ ] Validate the chunk-size group as one unit before Sudachi construction: `min_chunk >= 0`, `min_chunk <= max_chunk`, `chunk_overlap >= 0`, `chunk_overlap < max_chunk` (`scripts/rag/ingestion/chunk_splitter.py`; REQ-001, REQ-002)
   - [ ] When `md_index_enable` is set, validate `md_snippet_max_chars` against `min_chunk` and `max_chunk` (`scripts/rag/ingestion/chunk_splitter.py`; REQ-004)
2. **Phase 2: Regression tests**
   - [ ] Extend `TestMaxChunkValidation` with each rejected relation and each wrong-type value (`tests/rag/ingestion/test_chunk_splitter.py`; REQ-001, REQ-002, REQ-003)
   - [ ] Add the `md_index_enable` `md_snippet_max_chars` out-of-range case (`tests/rag/ingestion/test_chunk_splitter.py`; REQ-004)
   - [ ] Add an accepted-boundary parity case confirming a valid config yields the same chunk counts (`tests/rag/ingestion/test_chunk_splitter.py`; REQ-005)
3. **Phase 3: Documentation and validation gate**
   - [ ] Document the required relations between the four chunk-size keys in `config/chunk_splitter.toml` (`config/chunk_splitter.toml`; REQ-006)
   - [ ] Record valid ranges, relations, and the error raised in the configuration reference (`docs/21_rag/rag_05_01-configuration-reference.md`; REQ-007)
   - [ ] Run the full validation gate (ruff, pytest, docs checks) (`scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`; REQ-005, REQ-006, REQ-007)

### Release units
**Unit**: chunk-size validation + regression tests | **Phases**: 1, 2 | **Reason**: the regression tests (Phase 2) validate the constructor validation (Phase 1); neither passes alone until both land in the same commit.
**Unit**: documentation of chunk-size relations | **Phases**: 3 | **Reason**: single phase; docs/config changes are inert to the test suite and validate alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Unit: each rejected relation raises `PipelineValidationError` naming key+relation; wrong-type rejected; valid config passes | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` | all pass |
| `tests/rag/ingestion/test_chunk_splitter.py` | Regression: break each behavior once and confirm the failure names the rule | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` | failures as expected |
| `config/chunk_splitter.toml`, `docs/21_rag/rag_05_01-configuration-reference.md` | Static: config still parses; docs structure valid | `uv run ruff check` + `tools/check_docs_quality.py` | pass |

## Risks
- **Risk**: A typed getter that rejects non-integers could reject a currently-valid config that passes a float (for example `500.0`), changing behavior. → **Mitigation**: Repository evidence shows the config file and all test configs use plain integers (Step 2); confirm no production consumer passes floats before finalizing. Rejecting the float aligns with the `rules/coding.md` type-coercion policy intent.
- **Risk**: Validating `md_snippet_max_chars` breaks an existing `md_index_enable` deployment. → **Mitigation**: Check runs only when `md_index_enable` is set; the default config disables it, so the default deployment is unaffected.
- **Risk**: Overlap with the sibling plan for `issues/20261119-112021_ragcrv009_chunk-test-construction-fragility.md` on `tests/rag/ingestion/test_chunk_splitter.py`. → **Mitigation**: Sequence this fix first (it defines the locked-down behaviors); the sibling's construction restructuring follows. Recorded as a compatible overlap in Assumptions.
- **Risk**: Validation placed after Sudachi construction still loads the dictionary for a bad config. → **Mitigation**: Place validation ahead of Sudachi dictionary construction so a misconfigured run fails fast.
- **Risk**: An existing test forces zero chunks by constructing an invalid config (`TestForceRechunkPrune.test_zero_chunk_forced_run_removes_old_series` sets `min_chunk=100000 > max_chunk=600`), which the new `min_chunk <= max_chunk` relation rejects at construction. → **Mitigation**: Update that one test to force zero chunks through a valid config (raise `min_chunk` above the source content length; `_chunk_english` already discards anything below `min_chunk`). It is covered by the test-file row (REQ-005), not a new target file.
- **Risk**: `_CRAWL_CONFIG` has `md_snippet_max_chars=600` against `max_chunk=500`; the default config disables `md_index_enable` so this latent inconsistency is never checked in production, but `test_md_heading_splits_have_matching_fetched_at` enables it and would trip REQ-004. → **Mitigation**: REQ-004 correctly rejects the mismatch; update that one test to a valid `md_snippet_max_chars`. The production default (disabled) is unaffected, so this is a test-only fallout, not a deployment risk.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Constructor validation in `ChunkSplitter.__init__` (typed getters + group relations) | Completed | — | 20261119-161000 | Touches `scripts/rag/ingestion/chunk_splitter.py` (REQ-001..REQ-004) |
| 2 | Regression tests for rejected relations, wrong-type cases, accepted-boundary parity | Completed | — | 20261119-161000 | Touches `tests/rag/ingestion/test_chunk_splitter.py` (REQ-001..REQ-005) |
| 3 | Document relations in config + configuration reference; run validation gate | Completed | — | 20261119-161421 | Touches `config/chunk_splitter.toml` and `docs/21_rag/rag_05_01-configuration-reference.md` (REQ-006, REQ-007) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261119-151106_01_scripts_rag_ingestion_chunk_splitter.py.md` | 1 | Procedure | Completed | — | — |
| `implementations/20261119-151106_02_tests_rag_ingestion_test_chunk_splitter.py.md` | 2 | Procedure | Completed | — | — |
| `implementations/20261119-151106_03_config_chunk_splitter.toml.md` | 3 | Procedure | Completed | — | — |
| `implementations/20261119-151106_04_docs_21_rag_rag_05_01-configuration-reference.md.md` | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112015_ragcrv003_chunk-config-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-144007
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `config/chunk_splitter.toml`, `docs/21_rag/rag_05_01-configuration-reference.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes / Acceptance Criteria | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC: `min_chunk > max_chunk` names both keys | `TestMaxChunkValidation` extension | Explicit in issue |
| REQ-001 | Required Changes | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | AC: `min_chunk > max_chunk` names both keys | `TestMaxChunkValidation` extension | Explicit in issue |
| REQ-002 | Required Changes / Acceptance Criteria | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC: `chunk_overlap >= max_chunk` raises | `TestMaxChunkValidation` extension | Explicit in issue |
| REQ-002 | Required Changes | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | AC: `chunk_overlap >= max_chunk` raises | `TestMaxChunkValidation` extension | Explicit in issue |
| REQ-003 | Required Changes / Acceptance Criteria | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC: wrong type rejected, not coerced | wrong-type cases | Explicit in issue |
| REQ-003 | Required Changes | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | AC: wrong type rejected, not coerced | wrong-type cases | Explicit in issue |
| REQ-004 | Required Changes | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC: `md_snippet_max_chars` out of range raises with `md_index_enable` | `md_index_enable` out-of-range case | Explicit in issue |
| REQ-004 | Required Changes | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | AC: `md_snippet_max_chars` out of range raises with `md_index_enable` | `md_index_enable` out-of-range case | Explicit in issue |
| REQ-005 | Constraints: no valid config changes output | `scripts/rag/ingestion/chunk_splitter.py` | 1 | AC: no valid config changes output | accepted-boundary parity | Confirmed by repository evidence |
| REQ-005 | Constraints | `tests/rag/ingestion/test_chunk_splitter.py` | 2 | AC: no valid config changes output | accepted-boundary parity | Confirmed by repository evidence |
| REQ-006 | Documentation Impact | `config/chunk_splitter.toml` | 3 | Doc impact: document relations in config file | docs/config valid | Explicit in issue |
| REQ-007 | Documentation Impact | `docs/21_rag/rag_05_01-configuration-reference.md` | 3 | Doc impact: record ranges/relations/error | docs structure valid | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261119-151106 -->
