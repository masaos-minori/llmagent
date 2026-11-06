## Goal
- Make `ChunkSplitter`-written chunk JSON payloads satisfy the canonical chunk-artifact key contract
  (`read_chunk_json` requires `code_blocks`), so file-based ingestion persists documents from real
  ChunkSplitter output instead of rejecting every chunk file.

## Priority
High

## Scope
- **In-Scope**:
  - Add the `code_blocks` key (empty list for all current chunk paths) to the chunk payload built by
    `ChunkSplitter._build_chunk_payload` in `scripts/rag/ingestion/chunk_splitter.py`.
  - Add a payload key-set pin test that feeds real ChunkSplitter writer output through `read_chunk_json`.
  - Add an end-to-end regression test: ChunkSplitter `process_file` output → `ChunkGroupingStrategy.group`
    non-empty groups → ingester persists documents.
- **Out-of-Scope**:
  - Carrying non-empty per-chunk code-block content into chunk payloads (future code-chunk feature; this
    Plan closes the key contract only, empty list allowed).
  - Changing `code_blocks` semantics in crawl artifacts (`read_crawl_json` and the crawler are unchanged).
  - Stale-chunk pruning (already implemented and Completed via `plans/done/20261106-101257_raging004_force-rechunk-stale-chunks.md`).
  - Group-signature semantics: `ChunkGeneration` includes `chunk_type`, so a text+code document forms two
    groups; unchanged by this Plan (note carried from the 004 Plan's UNK-01).
  - Weakening `read_chunk_json`'s exact key-set check or its unknown-key rejection.
- **Dependencies**: the 004 Plan ordering dependency (004 Plan → this Plan, same-file edits serialized) is
  already satisfied: every row of that Plan's Execution Status is `Completed`, and its change
  (`ChunkSplitter._prune_stale_chunk_files`) is confirmed present in current source. The 003 Plan
  (`plans/done/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`) has no blocking order; its
  hand-written chunk-payload fixtures may optionally switch to real ChunkSplitter output after this fix.

## Milestones
- Phase 1 (tests) → Phase 2 (fix) is the release unit that restores producer/consumer consistency; Phase 1
  tests intentionally fail until Phase 2 lands.
- Phase 3 gates full validation, then hands off to the user-approval deploy step (scripts changed).

## Dependencies
| Depends on | Scope | Reason | Status |
|---|---|---|---|
| plans/done/20261106-101257_raging004_force-rechunk-stale-chunks.md | all | ordering dependency already satisfied (all its Execution Status rows are `Completed`; its `_prune_stale_chunk_files` is confirmed in current source). Re-verify at implementation time that `_build_chunk_payload` is unchanged | Satisfied |

- **Blockers**: None.

## Quality Gates Baseline
| Gate | Command | Current result | Planned threshold at completion |
|---|---|---|---|
| radon complexity | `uv run radon cc scripts/rag/ingestion/chunk_splitter.py -n B` | no C+ blocks (baseline re-run 2026-11-07 at HEAD `4c6491555`; four B-grade blocks: `_chunk_markdown_by_heading`, `process_file`, `_prune_stale_chunk_files`, `_build_text_triples`) | no C+ blocks introduced by this Plan |
| vulture dead code | `uv run vulture scripts tests` | pre-existing findings only (e.g. unused attributes `_en_stopwords`, `_ja_stop_pos` etc. in `chunk_splitter.py`; unused locals in `agent/agent.py`) | no new vulture finding in the target files |
| bandit | `uv run bandit -q -r scripts -ll` | "No issues identified." at low-and-above (re-run 2026-11-07 at HEAD `4c6491555`) | no new medium/high finding |
| diff-cover | `uv run diff-cover coverage.xml --compare-branch=HEAD --fail-under=90` | N/A at Plan time: working tree clean at Plan freeze (HEAD `4c6491555`), no diff to measure | ≥90% coverage on the implementation diff |

## Plan Type
- **Classification**: Path A (Small / Self-contained / Single module)
- **Rationale**: 3 target files, no public-interface or schema change; the producer change is confined to
  one method (`_build_chunk_payload`) inside the ChunkSplitter class; the rest is test additions.
- **Design phase applied**: no. Architectural safeguards required: none.

## Background
- **Data flow**: crawler → `rag-src/*.json` → ChunkSplitter (`_build_chunk_payload`) → `rag-src/chunk/*.json`
  → `ChunkGroupingStrategy.group` (validates each file via `pipeline_utils.read_chunk_json`) → `RagIngester`
  → `rag_web.db`.
- **Current architecture**: `_build_chunk_payload` builds a payload dict (envelope `schema_version`,
  `artifact_type`, `created_by`, then 8 copied metadata keys, `source_file`, `chunking_strategy`,
  `chunk_index`, `chunk_type`, `content`, `normalized_content`) and a separate `metadata` dict; no code path
  adds `code_blocks`. The validator in `pipeline_utils.py` enforces a flat 13-key exact top-level key set
  (inline literal in `read_chunk_json`, including `code_blocks`) plus three allowed envelope keys.
- **Prior analysis**: `plans/done/20261106-101257_raging004_force-rechunk-stale-chunks.md` UNK-01 discovered
  the mismatch and filed this issue; `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (3.4a Field
  contract) already documents the 13-key chunk shape, lists `code_blocks` as a required key with an
  optional-keys-with-defaults note, and states the cross-field code rule for crawl artifacts.

## Problem
- **What's broken**: `ChunkSplitter._build_chunk_payload` writes chunk files without the `code_blocks` key,
  while `read_chunk_json` requires it. Every chunk file written by the current splitter is rejected by the
  downstream consumer.
- **Observable failure mode**: rejection is warning-and-route, not fully silent — `ChunkGroupingStrategy.group`
  logs `WARNING rag.ingestion.group: {path} [PARSE_FAILED]: missing required key: code_blocks`, the batch
  group for that source fails, and `RagIngester._route_group_failed` moves the files to `failed/` with a
  sibling `.error.json`. Net effect matches the issue: zero documents ingested from freshly produced chunk
  files; each failed chunk file produces a WARNING log line.
- **Current work-around (if any)**: none. Unit tests pass because their fixtures hand-write chunk payloads
  that already include `code_blocks` (`tests/rag/ingestion/test_chunk_splitter.py`,
  `tests/rag/ingestion/test_rag_ingestion_pipeline.py::_make_chunk_output_json`).

## Reason for Change
- **Why now**: the chunk-splitter → ingester path is non-functional end-to-end for new files, and the closed
  RAGING-004 `--force` feature now rewrites chunk series with the malformed shape on every force re-chunk,
  feeding `failed/`.
- **Why this approach**: producer-side fix, as the issue proposes. Docs (3.4a Field contract) and the
  validator already agree on the canonical key contract; the splitter is the single divergent writer. The
  004 Plan's R-003 already flagged this key-set divergence as a latent trap for force re-chunks.
- **Why not alternatives**:
  - Make `code_blocks` optional in `read_chunk_json`: rejected — contradicts the documented contract
    (`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`) and weakens validation.
  - Carry non-empty crawl `code_blocks` into chunk payloads: rejected for this Plan — the docs cross-field
    rule applies to crawl artifacts only; `chunk_type="code"` chunks already exist via
    `_build_code_triples` (the issue's "no code-chunk writer exists today" claim is outdated), and grouping
    already handles code chunks through `ChunkGeneration.chunk_type`. An empty list satisfies the contract
    without inventing content semantics.
  - Injecting `code_blocks` per path in `_build_text_triples`/`_build_code_triples` instead of the shared
    builder: rejected — `_build_chunk_payload` (called from `_write_chunk_files`) is the single construction
    point for all chunk paths, so the builder-level change covers every path at once. (Symbol names corrected
    2026-11-07 during procedure generation: `_generate_chunks`/`_split_markdown_file`/`_split_text_file` from
    the first draft do not exist in current source.)

## Implementation Intent
- Emit the canonical chunk shape from the producer (uniform empty `code_blocks`), pin the exact payload key
  set with a test, and prove the producer→validator boundary with an end-to-end test.

## Requirements
- `REQ-001`: `ChunkSplitter._build_chunk_payload` writes `code_blocks` as an empty list for every chunk it
  produces, so `read_chunk_json` accepts the file unchanged. Validation rules in `pipeline_utils.py` are not
  modified.
- `REQ-002`: a test pins the exact payload key set produced by the ChunkSplitter writer and reads the written
  file through `read_chunk_json`; any future addition or removal of a payload key fails deterministically
  (mirrors the RAGING-004 pin-test pattern).
- `REQ-003`: an end-to-end regression test runs the real ChunkSplitter on a source file, groups the real
  output through `ChunkGroupingStrategy` (or the real `RagIngester`), and asserts documents are persisted and
  no file is routed to `failed/`. A negative control (chunk file with `code_blocks` removed) must still be
  rejected and routed to `failed/`, proving the validator is not weakened.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed 2026-11-07: every row `Verified` against current
source; `tools/check_plan_target_overlaps.py` returned "No findings"; `tools/check_workitem_structure.py`
clean.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/ingestion/chunk_splitter.py | Add `code_blocks` (empty list) to the chunk payload dict built by `ChunkSplitter._build_chunk_payload`; no other behavior change | Producer omits a key the canonical validator requires, so every real chunk file is rejected at ingestion | REQ-001 / AC-001, AC-002 | `scripts/rag/ingestion/chunk_splitter.py` `_build_chunk_payload` payload dict has no `code_blocks`; `scripts/rag/ingestion/pipeline_utils.py` `read_chunk_json` exact top-level key set includes it | `tests/rag/ingestion/test_chunk_splitter.py`; `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Verified |
| tests/rag/ingestion/test_chunk_splitter.py | Add a writer-output pin test: run the real ChunkSplitter path, assert the written payload's exact top-level key set, and read it back through `read_chunk_json` | Locks the payload shape so future key additions/removals fail deterministically | REQ-002 / AC-003 | File already exercises ChunkSplitter writer paths; existing fixtures hand-write payloads (which is why the defect is invisible today) | itself | Verified |
| tests/rag/ingestion/test_rag_ingestion_pipeline.py | Add a ChunkSplitter-output → group → ingest end-to-end regression test using real writer output; add a negative control with `code_blocks` removed asserting rejection and routing to `failed/` | Current pipeline test hand-writes chunk payloads (`_make_chunk_output_json`); no test currently feeds real ChunkSplitter output through the validator boundary | REQ-003 / AC-002, AC-004 | File holds crawler→splitter scaffolding and `_make_rag_db`/`_make_chunk_output_json` helpers already | itself | Verified |

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
| scripts/rag/ingestion/pipeline_utils.py | Defines `read_chunk_json`'s exact top-level key-set check and per-field validators that the fixed payload must satisfy | scripts/rag/ingestion/chunk_splitter.py; REQ-001, REQ-002 |
| scripts/rag/ingestion/chunk_grouping.py | Consumer side: `ChunkGroupingStrategy.group` calls `read_chunk_json` and reports `PARSE_FAILED` rejections; grouping key semantics | REQ-003 |
| scripts/rag/ingestion/ingester.py | End-to-end target: `RagIngester` flow and `_route_group_failed` routing to `failed/` for the regression and negative-control assertions | REQ-003 |
| docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md | Canonical 3.4a Field contract (13-key chunk shape, `code_blocks` requirement, cross-field rule) confirming the producer-side direction | REQ-001 |
| docs/21_rag/rag_02_08_ingestion_pipeline-shared.md | Overview of `pipeline_utils.py` shared validators used by grouping and ingestion | REQ-003 |

## Acceptance Criteria
- **AC-001**: Given a chunk produced by the real ChunkSplitter writer path (any chunk path), When the written
  file is read through `read_chunk_json`, Then validation succeeds and `code_blocks` equals `[]`. (REQ-001,
  REQ-002)
- **AC-002**: Given a crawler-format source file processed by `ChunkSplitter.process_file`, When its chunk
  output is ingested through `RagIngester`, Then at least one chunk is processed and none fails (asserted as
  ≥1 row in the `documents` table and ≥1 row in `chunks`), no file lands in `failed/`, and the `documents`
  table contains the document. (REQ-003) — corrected 2026-11-07 during procedure generation: the original
  "`processed_docs`/`failed_docs`/`rag_web` table" wording was stale; current persistence uses the
  `documents`/`chunks` tables (`scripts/db/models.py` schema; test fixture `_make_rag_db`), and
  `RagIngester.ingest_all` returns a `RagConsistencyReport`, not per-run counters.
- **AC-003**: Given a payload key-set change (addition or removal) against the pinned key list, When the pin
  test runs, Then it fails with a clear assertion. (REQ-002)
- **AC-004**: Given a chunk file with `code_blocks` removed, When `RagIngester` ingests it, Then the batch is
  rejected (`PARSE_FAILED`), routed to `failed/` with an `.error.json`, and not persisted. (REQ-003)
- **Boundary**: producer-side key addition only; `read_chunk_json` rules, crawl-artifact `code_blocks`
  semantics, and grouping semantics unchanged; failure semantics unchanged.

## Tests
- New tests (unit): pin test in `tests/rag/ingestion/test_chunk_splitter.py` — real writer output file, exact
  key-set assertion, `read_chunk_json` round-trip. (REQ-002)
- New tests (integration): real ChunkSplitter → `ChunkGroupingStrategy`/`RagIngester` pipeline test in
  `tests/rag/ingestion/test_rag_ingestion_pipeline.py`, plus the negative control. (REQ-003)
- Regression suite to run before completion: `uv run pytest tests/rag/ingestion`, then full `uv run pytest`
  (all gates at completion per `rules/toolchain.md`).

## Documentation Impact
- N/A: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (3.4a Field contract) already documents
  the required `code_blocks` key and the canonical 13-key chunk shape — verified 2026-11-07 against the
  current doc; the fix aligns code with the existing documented contract, so no doc update is required.
  (docs→implementation links already exist at `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
  sections 3 and 3.4a; new links: N/A.)

## Assumptions
- **A-001**: `code_blocks: []` uniformly for all chunk paths is correct — the docs cross-field rule governs
  crawl artifacts only, and no code path reads chunk-level `code_blocks` values today. Confidence: High.
  Validation: grep `code_blocks` in `scripts/rag/ingestion` confirms only the validator references it on the
  chunk side (done 2026-11-07); AC-002.
- **A-002**: Adding an empty list cannot change grouping outcomes — the grouping key is
  `ChunkGeneration.to_group_key()` and does not include payload content. Confidence: High. Validation:
  `scripts/rag/ingestion/chunk_grouping.py` read (done); AC-002.
- **A-003**: Existing malformed chunk files already on production disk remain in `rag-src/chunk/` and will be
  re-chunked (`--force`) or replaced by re-crawl after deploy; this Plan does not migrate them. Confidence:
  Medium. Validation: confirm the cleanup/re-chunk step with the user at deploy hand-off.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `read_chunk_json` also enforces `code_blocks` inside a `metadata` sub-object in addition to the top level | Resolved 2026-11-07: `read_chunk_json` validates a flat exact top-level key set (13 required keys + `schema_version`/`artifact_type`/`created_by` allowed envelope keys); chunk files have no `metadata` sub-object — `_build_chunk_payload` spreads `**metadata` into the top level | Resolution path executed: read `scripts/rag/ingestion/pipeline_utils.py` `read_chunk_json` in full. The fix is a single top-level addition | False |
| UNK-02 | Whether existing deployed production chunk files under `/opt/llm/rag-src/chunk/` are currently rejected on each ingester run (volume of `failed/` entries) | Live production logs / `failed/` directory listing | Confirm at Phase 3 deploy hand-off with the user; affects cleanup steps, not the code fix | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/ingestion/chunk_splitter.py | payload key addition in `_build_chunk_payload` | Low — single method, single writer; consumers are `chunk_grouping.py`/`ingester.py` via the validator | 4 commits in 30d (`a902feb76`, `df1ff8ed4`, `213a02121` RAGING-004, `f127f0a02` RAGING-007) | 1 author lineage (recent ingestion-pipeline work) | Yes — `scripts/` change; `deploy.sh` syncs `scripts/rag/ingestion/` |
| tests/rag/ingestion/test_chunk_splitter.py | new test only | None | 0 in 30d (last touched earlier) | 1 | No |
| tests/rag/ingestion/test_rag_ingestion_pipeline.py | new test only | None | 1 commit (2026-11-06 RAGING-003) | 1 | No |

## Design
- Single-writer boundary fix: `_build_chunk_payload` is the only construction point for chunk payload dicts
  (all split paths — markdown heading, English, Japanese, code — flow through `_build_chunk_list` →
  `_build_text_triples`/`_build_code_triples` → `_write_chunk_files` → `_build_chunk_payload`; verified
  2026-11-07), so one key addition covers every path and keeps the key set uniform. Validation stays strict
  and unchanged. No new module, interface, or config.
- Consumer scan result: `tools/scan_change_consumers.py --seed scripts/rag/ingestion/chunk_splitter.py`
  returned `deploy/setup_services.sh` (process launch only; payload-shape independent), docs/ADR mentions
  (no code coupling), and the two test files (in scope). Judgment: no additional affected consumers.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`.

1. **Phase 1: RED tests**
   - [ ] Add the key-set pin test exercising real ChunkSplitter writer output read back through
     `read_chunk_json` (REQ-002; tests/rag/ingestion/test_chunk_splitter.py). Expect RED: failure names
     `missing required key: code_blocks` and/or the pinned-key assertion.
   - [ ] Add the end-to-end ChunkSplitter→group→ingest test and the `code_blocks`-removed negative control
     (REQ-003; tests/rag/ingestion/test_rag_ingestion_pipeline.py).
2. **Phase 2: Producer fix**
   - [ ] Add `code_blocks` empty list to the payload dict in `ChunkSplitter._build_chunk_payload` (REQ-001;
     scripts/rag/ingestion/chunk_splitter.py). UNK-01 resolved: top-level addition only, chunk files have no
     metadata sub-object.
   - [ ] Re-run Phase 1 tests: all green.
3. **Phase 3: Gates and deploy hand-off**
   - [ ] Run the completion gates per `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, diff-cover
     ≥90%, full `uv run pytest`).
   - [ ] Deploy validation/scripts check: `scripts/` changed → hand off to the user-approval deploy step per
     `skills/DESIGN.md` production-deploy-scope rule (deploy.sh syncs `scripts/rag/ingestion/`); after
     deploy, confirm a live chunk-splitter→ingester cycle produces `processed_docs` > 0.

### Release units
**Unit**: chunk-payload contract closure | **Phases**: 1, 2 | **Reason**: Phase 1 tests are RED until Phase 2 lands; validating Phase 1 alone would report a failing suite, so Phases 1+2 must be delivered and validated as one unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/ingestion/chunk_splitter.py | unit + integration via new tests | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py tests/rag/ingestion/test_rag_ingestion_pipeline.py -v` | all green after Phase 2; RED with `code_blocks` failure names before it |
| scripts/rag/ingestion/chunk_splitter.py | full regression | `uv run pytest` | no failures; pre-existing suites unaffected |
| scripts/rag/ingestion/chunk_splitter.py | gates | `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy scripts`, `uv run lint-imports`, `uv run bandit -q -r scripts -ll`, `uv run diff-cover coverage.xml --compare-branch=HEAD --fail-under=90` | all pass; diff coverage ≥90% |
| scripts/rag/ingestion/chunk_splitter.py | gate baselines | `uv run radon cc scripts/rag/ingestion/chunk_splitter.py -nc B`; `uv run vulture scripts tests` | no new C+ blocks; no new vulture finding in target files |
| deployment | operational check after user-approved deploy | rerun chunk_splitter + ingester on one test source (per execution guide `docs/21_rag/rag_05_02-execution-guide.md`) | chunk files validate, `processed_docs` ≥ 1, no new `failed/` entries |

## Risks
- **Risk**: (resolved) UNK-01 — metadata-level `code_blocks` requirement → **Mitigation**: closed 2026-11-07
  by reading `read_chunk_json`: validation is a flat top-level key set only; a single payload addition
  suffices.
- **Risk**: existing production chunk files are malformed and continue failing until re-chunked →
  **Mitigation**: confirm a `--force` re-chunk (RAGING-004 feature) or re-crawl step with the user at deploy
  hand-off (UNK-02); recoverability confirmed by 004 Plan UNK-02 evidence (re-chunk restores docs).
- **Risk**: producer fix applied while an ingester run is mid-batch could mix old/new files in one group →
  **Mitigation**: deploy during an idle window; group-level failure is recoverable (files moved to `failed/`,
  re-chunk restores).
- **Risk**: tests elsewhere hand-write chunk payloads and mask future key drift →
  **Mitigation**: REQ-002 pin test now locks the real writer output; 003 Plan's optional fixture-switch note
  recorded in Scope.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: RED tests (REQ-002, REQ-003) | In Progress | — | — |  |
| 2 | Phase 2: Producer fix (REQ-001) | In Progress | — | — |  |
| 3 | Phase 3: Gates + deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261107-054235_01_scripts_rag_ingestion_chunk_splitter_py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261107-054235_03_tests_rag_ingestion_test_rag_ingestion_pipeline_py.md | 1 | Procedure | Pending | — | — |

Quality self-assessment (Step 9): all section claims trace to the Traceability table; assumptions separated
(A-001..A-003); UNK-01 resolved with source evidence (flat top-level key set); remaining operational
vagueness bounded by UNK-02 with a validation path at deploy hand-off; no scope creep — validator, crawler,
docs, grouping untouched; tests cover regression (AC-002 end-to-end), contract (AC-001/AC-003), and
non-weakening (AC-004 negative control); phases independently verifiable except the declared release unit;
deploy hand-off flagged as user-approval point.

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 2026-11-07
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py,
  tests/rag/ingestion/test_chunk_splitter.py, tests/rag/ingestion/test_rag_ingestion_pipeline.py

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Object | Source Requirement | Notes |
|---|---|---|
| REQ-001 | issue `issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md` Problem + Suggested fix | producer-side `code_blocks` addition, as the issue proposes |
| REQ-002 | issue acceptance criteria (contract lock) | mirrors the pattern in `plans/done/20261106-101257_raging004_force-rechunk-stale-chunks.md` |
| REQ-003 | issue acceptance criteria (end-to-end ingestion works) | negative control added by this Plan (issue did not state it; protects validator strictness) |
| AC-001..AC-004 | `## Requirements` above | |
| scripts/rag/ingestion/chunk_splitter.py | REQ-001 | `## Implementation Target Files` |
| tests/rag/ingestion/test_chunk_splitter.py | REQ-002 | `## Implementation Target Files` |
| tests/rag/ingestion/test_rag_ingestion_pipeline.py | REQ-003 | `## Implementation Target Files` |
| docs impact (N/A) | verified against `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` 3.4a | Documentation Impact above |

## Freeze Decision Log

| Timestamp | Freeze status | Validation evidence |
|---|---|---|
| 2026-11-07 07:40 | Frozen | All `Implementation Target Files` rows `Verified` and the table marked `Frozen`. No blocking Unknown: UNK-01 `Blocking? = False` (resolved), UNK-02 `Blocking? = False` (deploy-time item). No open dependency. Frozen inventory re-verified against rebased HEAD `c2e8b68ed`: `_build_chunk_payload` omits `code_blocks` (chunk_splitter.py:318-336); `read_chunk_json` required key set includes `"code_blocks"` (pipeline_utils.py:169,193); `_make_chunk_output_json` fixture exists (test_rag_ingestion_pipeline.py:117). `tools/check_plan_target_overlaps.py` returned "No findings" for this plan's rows at freeze time; overlap judgment against the other current Frozen plan (ragfix002) at 2026-11-07 07:40: no shared target files or same-kind behavior on shared paths (chunk payload vs crawler fallback defaults; zero overlap). |