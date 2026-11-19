## Goal
- Give the crawl-input path its own DTO (`CrawlDocument`) and make `read_crawl_json` return it instead of a `ChunkDocument` stuffed with placeholder chunk fields, so each reader's return type describes the artifact it validated; make `ChunkMetadata` total so a missing key fails where it is built.

## Priority
Medium

## Scope
- **In-Scope**:
  - Extend `CrawlDocument` in `scripts/rag/models_data.py` with the fields `ChunkSplitter` reads from the source document, and change `read_crawl_json` in `scripts/rag/ingestion/pipeline_utils.py` to return a `CrawlDocument` with no manufactured chunk-only fields.
  - Add an explicit `CrawlDocument` -> `ChunkDocument` conversion at the `process_file` seam in `scripts/rag/ingestion/chunk_splitter.py` so the rest of the splitter keeps operating on a `ChunkDocument`.
  - Make `ChunkMetadata` total (all eight keys required) or replace it with a frozen dataclass, keeping the 16-key payload contract intact.
  - Update `tests/rag/ingestion/test_pipeline_utils_strict.py` to assert the returned crawl DTO type and fields; keep `TestChunkPayloadKeyContract` green.
  - Document which DTO each reader returns in `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`.
- **Out-of-Scope**:
  - Changing the chunk JSON payload field set or their order (published artifact contract).
  - Deleting `CrawlDocument` without a recorded reason.
  - Crawler-side config work.
  - Any change to `read_chunk_json` or the chunk-only readers (`chunk_grouping`, `embedding`, `file_routing`, `ingester`).
- **Dependencies**: The issue lists `N/A: none`. Two related closed issues provide historical context but do not gate this work (see Assumptions).
  - **Depends on**: `N/A: none`

## Background
- `pipeline_utils.read_crawl_json` builds a `ChunkDocument` with `chunking_strategy="text"`, `chunk_index=0`, `source_file=""`, `chunk_type=""` for a payload that has no chunk, and `_splitter._extract_chunk_metadata` overwrites those fields when writing.
- `models_data.CrawlDocument` exists (`scripts/rag/models_data.py:41`) but is imported by no file under `scripts/` or `tests/`; the only reference anywhere outside this issue is its own definition.
- `ChunkSplitter.ChunkMetadata` is a `TypedDict(total=False)` whose docstring claims spreading requires `total=False`; `_extract_chunk_metadata` always returns all eight keys and `_build_chunk_payload` relies on the spread to produce the payload key set asserted by `TestChunkPayloadKeyContract`.
- `read_crawl_json` is consumed only by `chunk_splitter._read_source_data`; no other production caller exists. `CrawlDocument` already holds every field the splitter reads (`url`, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `content`, `code_blocks`).

## Problem
Two different documents share one class, so the type no longer says which fields are real: four chunk fields are always fake values on the crawl side. The unused `CrawlDocument` makes the intended boundary invisible, and the optional metadata `TypedDict` hides a missing key instead of failing at construction.

## Reason for Change
`read_chunk_json` and `read_crawl_json` are the strict validators of the artifact contract; their return types should describe the artifact they validated. Right now the crawl validator returns the chunk DTO, so the boundary between "raw crawl payload" and "chunk-ready document" is not expressible in the type system.

## Implementation Intent
Return the crawl DTO from `read_crawl_json`, extend `CrawlDocument` with whatever fields `ChunkSplitter` reads (already present), and convert the `CrawlDocument` to a `ChunkDocument` at the single seam where chunk processing begins (`process_file`), filling the chunk-only fields with real values instead of placeholders. Make `ChunkMetadata` total so a missing key fails where it is built. Keep the 16-key payload contract unchanged.

## Requirements
- `REQ-001`: `read_crawl_json` returns a `CrawlDocument` and constructs no chunk-only fields (`chunking_strategy`, `chunk_index`, `source_file`, `chunk_type`).
- `REQ-002`: `CrawlDocument` carries every field `ChunkSplitter` reads from the source document; a single explicit conversion builds a `ChunkDocument` from it at the `process_file` seam.
- `REQ-003`: `ChunkMetadata` is total (all eight keys required) or a frozen dataclass, so a missing key fails at construction rather than producing a payload missing a key later.
- `REQ-004`: The 16-key chunk payload contract (`TestChunkPayloadKeyContract`) still holds; the crawl-reader validation tests assert the returned DTO type and fields.
- `REQ-005`: `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` records which DTO each of `read_chunk_json` / `read_crawl_json` returns.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/models_data.py` | Modify | Extend `CrawlDocument` with the fields `ChunkSplitter` reads and set `read_crawl_json`'s return type to `CrawlDocument`; `CrawlDocument` is currently defined at line 41 and referenced nowhere else (Step 2) | REQ-001, REQ-002 | `test_pipeline_utils_strict.py` asserts the crawl DTO shape today (Step 3) | Verified |
| `scripts/rag/ingestion/pipeline_utils.py` | Modify | `read_crawl_json` (line 84) currently returns a `ChunkDocument` built with placeholder chunk fields; change it to return a `CrawlDocument` with no manufactured chunk-only fields (Step 2) | REQ-001 | `read_crawl_json` body lines 84-144 build a `ChunkDocument` (Step 2) | Verified |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Add an explicit `CrawlDocument` -> `ChunkDocument` conversion at the `process_file` seam (currently `_read_source_data` returns the reader result directly, line 447); make `ChunkMetadata` (line 93) total so all eight keys are required (Step 2/3) | REQ-002, REQ-003 | `_extract_chunk_metadata` returns 8 keys (lines 555-564); `_build_chunk_payload` spreads them into the 16-key payload (lines 575-585); `TestChunkPayloadKeyContract._EXPECTED_KEYS` has 16 entries (Step 2) | Verified |
| `tests/rag/ingestion/test_pipeline_utils_strict.py` | Modify | Assert `read_crawl_json` returns a `CrawlDocument` with the expected fields; keep the strict validator suite green (Step 3) | REQ-004 | `read_crawl_json` tests at lines 105-124 access only crawl-DTO fields (Step 3) | Verified |
| `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Modify | Record which DTO each of `read_chunk_json` / `read_crawl_json` returns; the doc currently names neither reader (Step 8b) | REQ-005 | `rg read_crawl_json|read_chunk_json` over the doc returns no matches (Step 8b) | Verified |

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
| `scripts/rag/ingestion/chunk_grouping.py` | Consumes chunk payloads via `read_chunk_json` (unchanged); must keep working per the issue constraints | REQ-004 |
| `scripts/rag/ingestion/embedding.py` | Uses `read_chunk_json`, not `read_crawl_json`; confirms the crawl-return change does not reach the embedding path | REQ-004 |
| `scripts/rag/ingestion/file_routing.py` | Uses `read_chunk_json`; confirms no impact from the crawl-return change | REQ-004 |
| `scripts/rag/ingestion/ingester.py` | Reads chunk files via `_read_chunk_json`; confirms no impact from the crawl-return change | REQ-004 |
| `tests/rag/ingestion/test_chunk_splitter.py` | `TestChunkPayloadKeyContract` writes a crawl payload through the real splitter and asserts the 16-key contract; must stay green without modification | REQ-004 |
| `tests/rag/ingestion/test_chunk_grouping.py` | Regression: must stay green after the splitter change | REQ-004 |
| `tests/rag/ingestion/test_ingester.py` | testmon records it executing `pipeline_utils.py`; must stay green after the module change | REQ-004 |
| `tests/rag/ingestion/test_rag_ingester.py` | testmon records it executing `pipeline_utils.py`; must stay green after the module change | REQ-004 |
| `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Regression: must stay green after the splitter change | REQ-004 |

## Acceptance Criteria
- `read_crawl_json` returns a `CrawlDocument` and constructs no chunk-only fields (`chunking_strategy`, `chunk_index`, `source_file`, `chunk_type`) — REQ-001, AC-004.
- A `ChunkDocument` is built from the `CrawlDocument` at the `process_file` seam before any chunk processing — REQ-002, AC-005.
- `ChunkMetadata` no longer declares any key optional that the producer always sets; a missing key fails where it is built — REQ-003, AC-006.
- The 16-key chunk payload contract asserted by `TestChunkPayloadKeyContract` is unchanged — REQ-004, AC-007.
- `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` states which DTO each reader returns — REQ-005, AC-008.

## Tests
- Unit: `test_pipeline_utils_strict.py` asserts `read_crawl_json` returns a `CrawlDocument` with the expected fields (REQ-001, REQ-004).
- Unit: metadata construction rejects a missing key once `ChunkMetadata` is total (REQ-003, REQ-004).
- Regression: run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py tests/rag/ingestion/test_pipeline_utils_strict.py -q` and confirm no new failures; `test_ingester.py` / `test_rag_ingester.py` remain green (testmon) (REQ-004).

## Documentation Impact
- `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` must be updated to record which DTO each of `read_chunk_json` / `read_crawl_json` returns (REQ-005). This maps to the ingestion-pipeline-utils doc in `docs/00_index.md`'s Document References by Task table.

## Assumptions
- The 16-key chunk JSON payload field set and order are a published artifact contract and must not change (stated constraint in the issue).
- `CrawlDocument` already holds every field `ChunkSplitter` reads from the source document (`url`, `title`, `lang`, `fetched_at`, `etag`, `last_modified`, `content`, `code_blocks`); no new field beyond these is required.
- Making `ChunkMetadata` total does not break any existing constructor call: `_extract_chunk_metadata` already returns all eight keys, and it is the only builder of the dict.
- The single `CrawlDocument` -> `ChunkDocument` conversion belongs at the `process_file` seam, so the remainder of the splitter keeps operating on a `ChunkDocument` and the payload contract is produced unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `CrawlDocument` was created for a crawler-side refactor that never landed, which would argue for deletion rather than use. Git history shows it replaced `ChunkRecord` in `26832fa22` (`feat: improve RAG ingestion pipeline and organize implementation docs`) and its fields are exactly what the splitter reads, so the recommended outcome is to use it, not delete it. | None blocking: the splitter consumes these fields regardless of origin. | Decide use-vs-remove only after the implementation reads git blame; recommend use because the fields are required. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/models_data.py` | Modify | `CrawlDocument` is referenced nowhere under `scripts/` or `tests/`; extending its fields has no external caller impact. | Low | High (single owner) | not applicable (rsynced) |
| `scripts/rag/ingestion/pipeline_utils.py` | Modify | `read_crawl_json` return type changes; only `chunk_splitter._read_source_data` consumes it in production. | Medium | High | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Adds the `CrawlDocument` -> `ChunkDocument` conversion at the `process_file` seam and makes `ChunkMetadata` total; downstream readers still consume the unchanged 16-key payload. | High | High | not applicable (rsynced) |
| `tests/rag/ingestion/test_pipeline_utils_strict.py` | Modify | Strict validator suite; must assert the new crawl DTO type. | Low | High | not applicable (rsynced) |

## Design
- Keep the artifact boundary explicit in the type system: `read_crawl_json` returns the raw-crawl DTO (`CrawlDocument`), `read_chunk_json` returns the chunk-ready DTO (`ChunkDocument`). Each strict validator's return type names the artifact it validated.
- Introduce exactly one conversion point at the `process_file` seam in `chunk_splitter.py`. `_read_source_data` currently returns the reader result directly; wrap it so the `CrawlDocument` is converted to a `ChunkDocument` before `_build_chunk_list` runs. Everything downstream keeps operating on `ChunkDocument`, so the payload contract and chunk-only field semantics are produced unchanged.
- The conversion fills the four chunk-only fields (`chunking_strategy`, `chunk_index`, `source_file`, `chunk_type`) with real values instead of placeholders: `chunking_strategy` from the splitter's configured strategy, `chunk_index=0`, `source_file` from the source path, `chunk_type` from the splitter's default. This removes the fake-value smell while preserving the payload shape.
- Make `ChunkMetadata` total (all eight keys required) or replace it with a frozen dataclass. `_extract_chunk_metadata` already returns all eight keys, so a total contract fails at construction rather than silently producing a payload missing a key. This is the single producer of the dict.
- Do not touch `read_chunk_json`, `chunk_grouping`, `embedding`, `file_routing`, or `ingester`; they consume the chunk path only.

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
    - [ ] Extend `CrawlDocument` in `scripts/rag/models_data.py` with the fields `ChunkSplitter` reads from the source document (already present; confirm no gap) — REQ-002, `scripts/rag/models_data.py`.
    - [ ] Make `ChunkMetadata` total (or a frozen dataclass) in `scripts/rag/ingestion/chunk_splitter.py` so all eight keys are required — REQ-003, `scripts/rag/ingestion/chunk_splitter.py`.
2. **Phase 2: Core Logic Implementation**
    - [ ] Change `read_crawl_json` in `scripts/rag/ingestion/pipeline_utils.py` to return a `CrawlDocument` with no manufactured chunk-only fields — REQ-001, `scripts/rag/ingestion/pipeline_utils.py`.
    - [ ] Add the single `CrawlDocument` -> `ChunkDocument` conversion at the `process_file` seam in `scripts/rag/ingestion/chunk_splitter.py` (`_read_source_data`), filling the four chunk-only fields with real values — REQ-002, `scripts/rag/ingestion/chunk_splitter.py`.
3. **Phase 3: Deployment & Verification**
    - [ ] Update `tests/rag/ingestion/test_pipeline_utils_strict.py` to assert `read_crawl_json` returns a `CrawlDocument` with the expected fields; keep `TestChunkPayloadKeyContract` green — REQ-004, `tests/rag/ingestion/test_pipeline_utils_strict.py`.
    - [ ] Run regression suite `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py tests/rag/ingestion/test_pipeline_utils_strict.py -q` and confirm no new failures; verify `test_ingester.py` / `test_rag_ingester.py` remain green (testmon) — REQ-004.
    - [ ] Update `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` to record which DTO each of `read_chunk_json` / `read_crawl_json` returns — REQ-005, `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`.

### Release units
N/A: each phase lands in its own commit and passes validation alone. Phase 2's two changes (the `read_crawl_json` return-type change and the `CrawlDocument` -> `ChunkDocument` conversion) are coupled within that single phase, so they are not a cross-phase release unit; neither Phase 1 nor Phase 3 breaks a caller until the other lands.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/pipeline_utils.py` | Unit: assert `read_crawl_json` returns a `CrawlDocument` with the expected fields and no chunk-only fields | `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q` | Test passes; new assertion holds |
| `scripts/rag/ingestion/chunk_splitter.py` | Unit: `TestChunkPayloadKeyContract` still asserts the unchanged 16-key payload after the conversion and total-metadata change | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q` | No new failures; contract intact |
| `scripts/rag/ingestion/chunk_splitter.py` | Regression: chunk grouping and utils still work after the splitter change | `uv run pytest tests/rag/ingestion/test_chunk_grouping.py tests/rag/ingestion/test_chunk_utils.py -q` | No new failures |
| Whole ingestion module | Integration/regression across the splitter path | `uv run pytest tests/rag/ingestion/ -q` | No new failures |
| `test_ingester.py` / `test_rag_ingester.py` | testmon regression: `pipeline_utils.py` still executes cleanly | existing testmon records | Remain green |
| `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Static: doc names the correct DTO per reader | manual / checker | AC-008 satisfied |

## Risks
- **Risk**: Making `ChunkMetadata` total breaks a constructor call that omits a key, producing a type/runtime failure mid-pipeline. → **Mitigation**: `_extract_chunk_metadata` is the only builder and already returns all eight keys; verified before editing. If a second builder exists, convert it too rather than loosening the contract.
- **Risk**: The `CrawlDocument` -> `ChunkDocument` conversion duplicates field mapping and drifts from the real reader fields. → **Mitigation**: derive the mapping directly from `_extract_chunk_metadata` and `_build_chunk_list` field access; add a unit test asserting the converted `ChunkDocument` carries the same field values the pipeline expects.
- **Risk**: Changing `read_crawl_json`'s return type breaks a hidden caller outside `scripts/` and `tests/`. → **Mitigation**: consumer scan (`scan_change_consumers.py`) confirms `read_crawl_json` is consumed only by `chunk_splitter._read_source_data`; regression suite covers the rest.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation / Refactoring — extend `CrawlDocument`, make `ChunkMetadata` total | In Progress | — | — |  |
| 2 | Phase 2: Core Logic Implementation — `read_crawl_json` return type + `CrawlDocument` -> `ChunkDocument` conversion | In Progress | — | — |  |
| 3 | Phase 3: Deployment & Verification — update strict tests, run regression, update docs | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261120-065959_01_scripts_rag_models_data.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261120-065959_02_scripts_rag_ingestion_pipeline_utils.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261120-065959_03_scripts_rag_ingestion_chunk_splitter.py.md` | 1, 2 | Procedure | Pending | — | — |
| `implementations/20261120-065959_04_tests_rag_ingestion_test_pipeline_utils_strict.py.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261120-065959_05_docs_21_rag_rag_02_07_ingestion_pipeline-utils.md.md` | 3 | Procedure | Pending | — | — |

Type options: Test / Task / Phase / Doc / Config / Infra / Other

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261120-044650
- **Related target files**: `scripts/rag/models_data.py`, `scripts/rag/ingestion/pipeline_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_pipeline_utils_strict.py`, `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Implementation Intent; `read_crawl_json` builds a `ChunkDocument` with placeholder chunk fields | `scripts/rag/ingestion/pipeline_utils.py` | Phase 2 | `read_crawl_json` returns a `CrawlDocument`, no chunk-only fields | `test_pipeline_utils_strict.py` asserts returned DTO type and fields | Planned |
| REQ-002 | Implementation Intent; single seam where chunk processing begins | `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/models_data.py` | Phase 1, 2 | `ChunkDocument` built from `CrawlDocument` at `process_file` seam | `TestChunkPayloadKeyContract` stays green | Planned |
| REQ-003 | Problem; `ChunkMetadata` is `TypedDict(total=False)` | `scripts/rag/ingestion/chunk_splitter.py` | Phase 1 | Missing key fails at construction | Unit: metadata construction rejects missing key | Planned |
| REQ-004 | Constraint: 16-key payload contract unchanged; Tests section | `tests/rag/ingestion/test_pipeline_utils_strict.py` | Phase 3 | 16-key payload contract intact | `test_chunk_splitter.py`, `test_chunk_grouping.py`, full ingestion suite | Planned |
| REQ-005 | Documentation Impact; which DTO each reader returns | `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md` | Phase 3 | Doc states each reader's return DTO | Manual / checker | Planned |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261120-065959 -->