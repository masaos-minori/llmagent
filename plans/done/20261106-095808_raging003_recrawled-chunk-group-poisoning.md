# Route or quarantine chunk groups that fail URL-group validation

## Goal
- Make chunk-group validation failure terminal and visible: every chunk file that could not be ingested leaves `rag-src/chunk/` through `FileRouter`, and chunk files from distinct crawl generations of one URL never compete inside one group.

## Priority
High

## Scope
- **In-Scope**: generation-safe grouping key in `ChunkGroupingStrategy.group`; routing of validation-failed group files and grouping-rejected files through `FileRouter`; deterministic oldest→newest group processing; test updates; docs lifecycle update.
- **Out-of-Scope**: `retry/` consumption design (issue `20261106-073538_raging005_retry-dir-no-consumer.md`); `unexpected_failure` (mid-ingest crash) routing; per-field signature validation rule changes; crawler scheduling.
- **Dependencies**: N/A for implementation order; see Dependencies table for the sequencing note with issue `20261106-073538_raging005_retry-dir-no-consumer.md`.
  - **Depends on**: `issues/20261106-073538_raging005_retry-dir-no-consumer.md` | phase all | sequencing note only: this Plan's routing uses `FileRouter.route` as it exists today and lands before or together with the retry/ decision; it does not require 005 to be implemented first.

## Background
`ChunkGroupingStrategy.group` keys groups by the payload `url` only (`chunk_grouping.py:24-50`) and silently `continue`s on files whose payload fails `read_chunk_json` (no log) or whose url is empty/invalid (log + no routing). The crawler writes a new timestamped source file per crawl (`crawl_persister.py:95-98`: `yyyymmddhhmmss-{slug}.json`), so two crawl runs before one ingester run leave chunk files of two generations with the same `url` but different `fetched_at`/`etag`/`source_file` in `chunk/`. `ingest_url_group` then compares a 9-field signature across the group and returns `GROUP_VALIDATION_FAILED` (`ingester.py:225-275`); `_process_url_groups` (`ingester.py:370-387`) never calls `FileRouter` for those results, so the files stay in `chunk/` and re-fail every run. `TestGroupValidation` in `tests/rag/ingestion/test_ingester.py:891-1001` pins this with "Files stay at original location" assertions. All claims verified line-by-line against HEAD `bdb9bed66` in Step 2 of this cycle.

## Problem
A single malformed or multi-generation group is a permanent poison entry: every ingester run re-processes it, logs the failure, counts it, and never moves the files out of `chunk/`. No operator-visible quarantine and no recovery path exist.

## Reason for Change
Broken workflow with growing operational cost: poisoned groups never leave the queue and mask real progress metrics.

## Implementation Intent
Group chunk files by (url, generation signature) instead of url alone, so each crawl generation forms its own group. Route every file that cannot be ingested — signature-mismatch and non-contiguous-index group failures, and grouping-rejected files (unreadable payload, empty/invalid url) — through the existing `FileRouter.route` into `failed/` with `.error.json` metadata, so the queue drains. Process groups of the same URL oldest-first so the newest generation ends up as the final `documents` row.

## Requirements
- `REQ-001`: `ChunkGroupingStrategy.group` keys each group by the URL plus the same 9-field per-file signature that `ingest_url_group` validates (url, title, lang, fetched_at, etag, last_modified, source_file, chunking_strategy, chunk_type); chunk files from two generations of one URL form distinct groups.
- `REQ-002`: `ChunkGroupingStrategy.group` reports the files it currently skips — `ChunkFormatError` payload, empty url, invalid url — as a rejected list paired with an `IngestionFailureReason` (`parse_failed` / `validation_failed`), and logs a per-file `WARNING` for all three skip cases (the `ChunkFormatError` skip currently logs nothing).
- `REQ-003`: On `GROUP_VALIDATION_FAILED` and on the `validation_failure` return sites in `ingest_url_group`, all group files are routed via `self._file_router.route([], [(path, reason), ...])` into `failed/` with `.error.json` metadata before the result is returned; grouping-rejected files are likewise routed once, centrally, after grouping in `ingest_all`. `FileRouter` stays the only move mechanism.
- `REQ-004`: Groups belonging to the same URL are processed in ascending `fetched_at` order so that, when two valid generations coexist, the newest generation is the last to write the `documents` row (its replace path re-inserts over the older one).
- `REQ-005`: `IngestUrlResult.validation_failure` carries an explicit `failure_reason` (`parse_failed`) instead of `None`.
- `REQ-006`: Tests: two-generation chunk sets ingest independently with the newest generation as final DB state; a malformed/unurl'd file is routed out and logged; validation-failed group files land in `failed/` with `.error.json`; a second `ingest_all` after draining reports zero re-processing of those files; grouping-rejected files are reported by `group()`.
- `REQ-007`: Update `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` (queue lifecycle table rows for `chunk/` → `failed/` including `group_validation_failed` semantics) and `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` §4.6 (the `validation_failure()` description — the group is now routed, not left in place).

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-095808 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_grouping.py` | Modify | Key groups by (url, 9-field generation signature); return rejected files with failure reasons; add per-file `WARNING` for `ChunkFormatError` skips | REQ-001, REQ-002; AC-1, AC-3 | `group()` keys `url_groups[url]` only (`:24-50`); `except ChunkFormatError: continue` logs nothing (`:30-31`); empty/invalid url log+skip with no routing (`:33-48`) (checked in Step 2) | `tests/rag/ingestion/test_chunk_grouping.py` | Verified |
| `scripts/rag/ingestion/ingester.py` | Modify | Route validation-failed group files and grouping-rejected files via `FileRouter.route`; iterate groups in (url, fetched_at) order; set `failure_reason` on `validation_failure` results | REQ-003, REQ-004, REQ-005; AC-1, AC-2, AC-4 | `validation_failure`/`GROUP_VALIDATION_FAILED` returns at `:225-275` with no `FileRouter` call; `_process_url_groups` (`:370-387`) only appends results; `validation_failure()` leaves `failure_reason=None` (`:54-59`) (checked in Step 2) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `tests/rag/ingestion/test_ingester.py` | Modify | Replace the "files stay at original location" assertions in `TestGroupValidation` with routed-to-`failed/` + `.error.json` assertions; add the two-generation end-to-end and re-run idempotency tests | REQ-006; AC-1, AC-2, AC-4 | `TestGroupValidation` pins the poison behavior at `:891-1001` (`assert path0.exists()` comments "validation rejects before any move") (name corrected in this cycle — actual class name is `TestGroupValidation`, not `TestURLGroupValidation`) | itself | Verified |
| `tests/rag/ingestion/test_chunk_grouping.py` | Create | Unit tests for generation-safe grouping (two `fetched_at` generations → distinct groups), rejected-file reporting with reasons, and the per-file `WARNING` log lines | REQ-001, REQ-002, REQ-006; AC-1, AC-3 | No test file imports `ChunkGroupingStrategy` today (`rg -l ChunkGroupingStrategy tests/` → no matches) (checked in Step 3) | itself | Verified |
| `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Modify | Update the chunk-file lifecycle table: validation-failed groups now drain to `failed/` with `.error.json`; describe the per-generation grouping | REQ-007; AC-5 | Lifecycle table at lines 35-38 describes routing only for success/embedding/other failures; no `group_validation_failed` entry (checked in Step 3) | N/A: documentation file, validated by review | Verified |
| `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Modify | Update §4.6: `IngestUrlResult.validation_failure()` now routes the group to `failed/` instead of leaving it in `chunk/` | REQ-007; AC-5 | §4.6 at `:105-108` describes validation failure with no routing ("no `WARNING` is logged at this layer") (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/file_routing.py` | `route()` is the single move mechanism (REQ-003); `group_validation_failed`/`parse_failed`/`validation_failed` contain no "embedding" substring, so they always land in `failed/`; file unchanged | REQ-003 |
| `scripts/rag/ingestion/crawl_persister.py` | Source filenames `yyyymmddhhmmss-{slug}.json` (`:95-98`) make per-crawl generations distinct — the factual basis of REQ-001's key choice | REQ-001 |
| `scripts/rag/exceptions.py` | `IngestionFailureReason` members (`:51-59`) used as rejection/routing reasons (REQ-002, REQ-005) | REQ-002, REQ-005 |
| `scripts/rag/ingestion/pipeline_utils.py` | `read_chunk_json` / `ChunkFormatError` semantics that define the rejection cases | REQ-002 |
| `scripts/rag/ingestion/chunk_splitter.py` | Defines the `{stem}-{idx:04d}.json` chunk-file naming and the stale-chunk residue scenario (issue `20261106-073538_raging004_force-rechunk-stale-chunks.md`) that REQ-003 must drain | REQ-003 |
| `tests/integration/test_ingestion_e2e.py` | End-to-end consumer of `RagIngester` that must stay green | REQ-003, REQ-004 |
| `docs/21_rag/rag_05_03-logging.md` | Records the mixed text/JSON log-format property of `ingest.log` (context for the new `WARNING` lines); needs no change because it enumerates formats, not messages | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-006): After one ingester run, no chunk file for a validation-failed group remains in `rag-src/chunk/`; each landed in `failed/` with `.error.json` naming the group reason (covered by a test).
- AC-2 (REQ-001, REQ-004, REQ-006): Two generations of chunk files for one URL resolve independently; the newest generation is the final `documents` row (covered by a test).
- AC-3 (REQ-002, REQ-006): Grouping skips (unreadable payload, empty/invalid url) leave `chunk/` via `FileRouter` and produce a per-file `WARNING` (covered by a test).
- AC-4 (REQ-003, REQ-006): A second `ingest_all` after a drained failed group reports zero re-processing of those files (covered by a test).
- AC-5 (REQ-007): Both docs files describe the drained-queue lifecycle and the new validation-failure routing.
- AC-6 (REQ-001..007): `uv run pytest tests/rag/ingestion` passes and changed lines reach the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-006: `tests/rag/ingestion/test_chunk_grouping.py` (new): two-generation grouping (distinct `fetched_at` → distinct groups), rejected-list content (`parse_failed` for malformed payload, `validation_failed` for empty/invalid url), per-file `WARNING` log assertions (caplog).
- REQ-006: `tests/rag/ingestion/test_ingester.py` `TestGroupValidation` updates: validation-failed groups → files in `failed/` with `.error.json` (`failure_reason` = `group_validation_failed` / `parse_failed`), not in `chunk/`.
- REQ-006: two-generation end-to-end test via `ingest_all` on a real in-memory DB: both groups processed oldest-first, final `documents.fetched_at` equals the newest generation, all files routed out of `chunk/`.
- REQ-006: re-run idempotency test: second `ingest_all` after a drained group logs/processes zero failed files.
- Characterization: successful single-group tests in `test_ingester.py` and `tests/integration/test_ingestion_e2e.py` keep their assertions unchanged.

## Documentation Impact
REQ-007: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` lifecycle table gains the group-validation drain path, and `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` §4.6 is updated to the routing behavior. `docs/21_rag/rag_05_03-logging.md` needs no change (it documents log formats, not message inventory — verified in Step 3).

## Assumptions
- `FileRouter.route`'s substring branch never sends `group_validation_failed`, `parse_failed`, or `validation_failed` to `retry/` (none contains "embedding"); this Plan's routing behavior is therefore compatible with either design of issue 005 (checked in Step 3).
- Payload `chunk_index` values in a generation are 0-based contiguous as `ChunkSplitter` writes them; a subgroup with a gap is by definition damaged (stale-residue scenario) and must fail whole-group.
- Grouping-rejected files are never ingestable in later runs (their payload shape/url is what it is); routing them out once is terminal.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Volume of already-poisoned groups sitting in the production `rag-src/chunk/` that will drain to `failed/` on the first run after deploy | Production `rag-src` directory inspection, out of reach for this planning phase | Post-deploy operator check of `failed/` contents and `.error.json` reasons | False |
| UNK-02 | Open sibling dependency: issue 005 (retry/ design) is still in `issues/` at plan time | Its plan does not exist yet (later in this batch) | Sequencing only — implement this Plan first or together with the 005 Plan; keep `file_routing.py` untouched here to avoid conflict (dependency path: `issues/20261106-073538_raging005_retry-dir-no-consumer.md`) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_grouping.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium | 2 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_grouping.py` | Create | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Modify | Low | 3 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Modify | Low | 8 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path B classification: cross-module contract change (`ChunkGroupingStrategy.group` return type), a routing behavior change in the ingestion entry module, intentional test-behavior flips, and two doc updates.
- Grouping key decision — (url, 9-field generation signature), not (url, source_file): the crawler's timestamped source files (`crawl_persister.py:95-98`) make generations differ in `source_file` only for crawl-produced groups; the stale-residue scenario (issue 004) mixes generations that share the same `source_file` but differ in `fetched_at`/`etag`. A signature-based key separates both scenarios; a `source_file` key does not (verified against both producer scenarios in Step 2). The signature members are exactly the tuple `ingest_url_group` already compares (`ingester.py:229-256`), so grouping consistency is by construction and the existing validation stays as defense-in-depth (constraint: validation rules unchanged).
- Mixed-generation policy (resolves the issue's unresolved question): every valid generation is ingested, oldest→newest (REQ-004 sort), no operator action; the final `documents` row is the newest generation via the existing replace path. Rejected alternative (auto-skip older generations): silently discards valid crawl data and needs a new skip mechanism.
- Rejected files are reported by `group()` as a `(path, IngestionFailureReason)` list; `ingest_all` routes them once via `FileRouter` after grouping — keeps "FileRouter as the single routing point" (constraint) instead of moving files ad hoc inside the grouping loop.
- `ingest_url_group` and `ingest_all` already grade C in `radon cc` (C16 / C14, measured this cycle): routing additions go through one small helper (`_route_group_failed(paths, reason)` in `ingester.py`) instead of inline branches at each return site, so cyclomatic complexity does not grow further. No refactoring of those functions beyond that (AGENTS.md rule 5).
- `unexpected_failure` (mid-ingest crash) leaves files in `chunk/` too but is out of scope: the issue's AC covers validation-failed groups; recorded as an adjacent finding, candidate for a future issue.
- Dependency graph (Step 3): `ChunkGroupingStrategy` consumers — only `ingester.py` (no test imports it directly); `RagIngester` consumers — 6 test files including `tests/integration/test_ingestion_e2e.py`, no production importers (CLI entry module). Historical analysis (Step 3): churn (30d) 0/2/0 for the code/test targets, 3 and 8 for the two docs files; single-maintainer authorship for all targets. Operational check: inherited from this cycle's earlier `fuser /opt/llm/db/rag.sqlite` — no holders. Persisted schema check: N/A — file-movement behavior only, no DDL.
- `scan_change_consumers.py` not run: no persisted schema, public API of a shared service, or shared constant changes; `group()`'s return-type change has exactly one consumer (the import scan above).
- Validation quality baseline (Step 5): `radon cc` — ingest_all C(16), ingest_url_group C(14), chunk_grouping methods A/B (measured this cycle); `vulture scripts/ --min-confidence 80` and `bandit -r scripts/ -c pyproject.toml` — no findings in target files (run this cycle). Diff-cover current number not measured in this cycle (no code change yet); ≥ 90% on changed lines is required at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Create `tests/rag/ingestion/test_chunk_grouping.py` with generation-splitting, rejected-list, and log assertions (REQ-006; must fail against current grouping)
   - [ ] Flip `TestGroupValidation` assertions in `tests/rag/ingestion/test_ingester.py` from "files stay" to routed-to-`failed/` with `.error.json`; add the two-generation `ingest_all` test and the re-run idempotency test (REQ-006)
2. **Phase 2: Generation-safe grouping and drain routing (GREEN)**
   - [ ] Change `ChunkGroupingStrategy.group` to key by (url, generation signature), return the rejected `(path, reason)` list, and log per-file `WARNING` for all skip cases (REQ-001, REQ-002; `scripts/rag/ingestion/chunk_grouping.py`)
   - [ ] In `RagIngester`: route validation-failed groups and grouping-rejected files through one `_route_group_failed` helper using `FileRouter.route`; iterate groups sorted by (url, fetched_at); set `failure_reason` on `validation_failure` (REQ-003, REQ-004, REQ-005; `scripts/rag/ingestion/ingester.py`)
3. **Phase 3: Documentation & verification & deploy hand-off**
   - [ ] Update the lifecycle table and §4.6 descriptions (REQ-007; `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`, `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`)
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted + `tests/rag/ingestion` + `tests/integration/test_ingestion_e2e.py`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%) (REQ-001..005; `scripts/rag/ingestion/chunk_grouping.py`, `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_chunk_grouping.py`, `tests/rag/ingestion/test_ingester.py`)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via `skills/deploy/SKILL.md` is the user's decision (approval gate); the first production run will drain existing poisoned groups (UNK-01) (REQ-003)

### Release units
**Unit**: group-drain-fix | **Phases**: 1, 2 | **Reason**: Phase 1 intentionally flips pinned test expectations; the suite is green only after Phase 2's production change, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_grouping.py` | Unit | `uv run pytest tests/rag/ingestion/test_chunk_grouping.py -v` | Generation-split groups, rejected list with reasons, per-file WARNING log lines |
| `scripts/rag/ingestion/ingester.py` | Integration | `uv run pytest tests/rag/ingestion/test_ingester.py -v` | Failed groups land in `failed/` with `.error.json`; oldest-first ordering makes the newest generation final; idempotent re-run |
| `scripts/rag/ingestion/ingester.py` | Regression (entry point) | `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py` | All ingestion tests green; single-generation semantics unchanged |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: flipping `TestGroupValidation` assertions could mask a regression if routing silently fails for only some return sites → **Mitigation**: each failure return site (first-file `ChunkFormatError`, mid-group `ChunkFormatError`, signature mismatch, index non-contiguity) gets its own routed-out assertion in Phase 1.
- **Risk**: signature-keyed grouping hides genuine cross-generation data loss (e.g., generation A has 3 chunks, generation B has 2, residue mixes) → **Mitigation**: residue subgroups fail index contiguity and are routed to `failed/` visibly (AC-1), and the upstream producer is fixed by the 004 Plan.
- **Risk**: oldest-first ingestion embeds stale generations (wasted embedding work) before the newest wins → **Mitigation**: accepted trade-off at plan level (embedding runs after generation-split already deduplicate DB state; 004 Plan removes most residue sources); recorded here for operator awareness.
- **Risk**: large existing poison backlog floods `failed/` on the first production run → **Mitigation**: UNK-01 operator check after deploy; `failed/` is already the documented terminal directory.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add/flip regression tests in `tests/rag/ingestion/test_chunk_grouping.py` (new) and `tests/rag/ingestion/test_ingester.py` | Completed | 2026-11-06 | 2026-11-06 | REQ-006: 13 grouping unit tests + flipped TestGroupValidation drain assertions + 2 parse-failure site tests + 2 generation-drain e2e tests + oldest-first ordering test (RED confirmed pre-fix) |
| 2 | Generation-safe grouping in `scripts/rag/ingestion/chunk_grouping.py` and drain routing in `scripts/rag/ingestion/ingester.py` | Completed | 2026-11-06 | 2026-11-06 | REQ-001..005: ChunkGeneration 9-field key + rejected list, `_route_group_failed` at all four failure sites, oldest-first `_process_url_groups`, `validation_failure` carries PARSE_FAILED |
| 3 | Docs updates + gate sequence + deploy hand-off | Completed | 2026-11-06 | 2026-11-06 | REQ-007: rag_02_01 lifecycle row + grouping sentence, rag_02_04 §4.6 rewritten; gates passed 2026-11-06 (full suite 11790 passed, diff-cover 98% / ingester.py 100%); deploy hand-off (UNK-01 `failed/` check) remains an operational decision for the owner |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-115721_01_scripts_rag_ingestion_chunk_grouping.py.md` | 1, 2 | Procedure | Completed | 2026-11-06 | 2026-11-06 |
| `implementations/20261106-115721_02_scripts_rag_ingestion_ingester.py.md` | 1, 2 | Procedure | Completed | 2026-11-06 | 2026-11-06 |
| `implementations/20261106-115721_05_docs_21_rag_rag_02_01_ingestion_pipeline-overview.md.md` | 3 | Procedure | Completed | 2026-11-06 | 2026-11-06 |
| `implementations/20261106-115721_06_docs_21_rag_rag_02_04_ingestion_pipeline-ingester.md.md` | 3 | Procedure | Completed | 2026-11-06 | 2026-11-06 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-095808
- **Related target files**: `scripts/rag/ingestion/chunk_grouping.py`, `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester.py`, `tests/rag/ingestion/test_chunk_grouping.py`, `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`, `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Implementation Intent "make grouping generation-safe"; url-only key verified at `chunk_grouping.py:24-50`; crawler timestamped naming at `crawl_persister.py:95-98` (checked in Step 2) | `scripts/rag/ingestion/chunk_grouping.py` | Phase 2 | AC-1, AC-2 | `test_chunk_grouping.py` generation tests | Confirmed by repository evidence |
| REQ-002 | Issue Background "silently drops files"; `except ChunkFormatError: continue` verified at `chunk_grouping.py:30-31` (checked in Step 2) | `scripts/rag/ingestion/chunk_grouping.py` | Phase 2 | AC-3 | `test_chunk_grouping.py` rejected-list + caplog tests | Confirmed by repository evidence |
| REQ-003 | Issue Required Changes bullets 1-2; no-`FileRouter` returns verified at `ingester.py:225-275` and `_process_url_groups` `:370-387` (checked in Step 2) | `scripts/rag/ingestion/ingester.py` | Phase 2 | AC-1, AC-3, AC-4 | `test_ingester.py` flipped `TestGroupValidation` assertions | Confirmed by repository evidence |
| REQ-004 | Issue Unresolved Questions (mixed-generation policy); generation coexistence verified via crawler filename scheme (checked in Step 2) | `scripts/rag/ingestion/ingester.py` | Phase 2 | AC-2 | two-generation end-to-end `ingest_all` test | Confirmed by repository evidence |
| REQ-005 | Step 2 verification finding: `validation_failure()` leaves `failure_reason=None` (`ingester.py:54-59`) | `scripts/rag/ingestion/ingester.py` | Phase 2 | AC-1 | `.error.json` reason assertions in `test_ingester.py` | Confirmed by repository evidence |
| REQ-006 | Issue Testing Expectations | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-1, AC-2, AC-4, AC-6 | flipped assertions + idempotency test | Explicit in issue |
| REQ-006 | Issue Testing Expectations | `tests/rag/ingestion/test_chunk_grouping.py` | Phase 1 | AC-1, AC-3, AC-6 | new grouping unit tests | Explicit in issue |
| REQ-007 | Issue Documentation Impact; current doc wordings verified at `rag_02_01_...md:35-38` and `rag_02_04_...md:105-108` (checked in Step 3) | `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Phase 3 | AC-5 | review of updated table | Explicit in issue |
| REQ-007 | Issue Documentation Impact | `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Phase 3 | AC-5 | review of updated §4.6 | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-115721 -->