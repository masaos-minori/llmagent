# Prune stale chunk files when force re-chunking reduces chunk count

## Goal
- Make a `ChunkSplitter` forced run authoritative for the document's chunk series: after a
  `force=True` run, `rag-src/chunk/` contains exactly the newly produced series for that
  source stem, so obsolete chunks can never be re-ingested alongside fresh ones.

## Priority
High

## Scope
- **In-Scope**: stem-scoped pruning of the old chunk series on `force=True` in
  `ChunkSplitter`; pruning even when the new series is empty; regression tests; idempotency
  doc note.
- **Out-of-Scope**: the `code_blocks` payload/validator mismatch discovered during
  verification (new issue candidate — see Unknowns); `registered/` retention or archiving;
  group-validation routing (issue `20261106-073538_raging003_recrawled-chunk-group-poisoning.md`);
  removing already-ingested stale DB rows.
- **Dependencies**: see Dependencies note in Design — same-test-file coordination with
  `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md`.

## Background
`ChunkSplitter.process_file` skips when the sentinel `chunk/{stem}-0000.json` exists and
`force=False` (`chunk_splitter.py:108-116` via `is_already_processed`,
`pipeline_utils.py:254-256`). On `force=True` it writes `{stem}-{idx:04d}.json` for each new
chunk (`chunk_splitter.py:249-261`) and deletes nothing. Reproduction at HEAD `bdb9bed66`:
run 1 (`max_chunk=200`) wrote 20 files; forced run 2 (`max_chunk=600`) wrote 10 files and
left all 20 in `chunk/`; the merged index set was exactly `range(20)` with uniform 9-field
metadata, i.e. `ingest_url_group`'s contiguity and signature checks pass and the 10 stale
chunks would be re-ingested. New series of zero chunks early-returns at
`chunk_splitter.py:244-245` and also leaves the old series. Verified in Step 2 of this cycle
(`/tmp/opencode/raging004/repro.py`). Step 3a re-check (2026-11-06, HEAD `97b8f4f6b`): the behavior is unchanged; the cited
line ranges drifted slightly, so the code is identified by symbol: the sentinel skip is in
`process_file`, the empty-list early return is the first statement of `_write_chunk_files`,
and the write loop is the `for idx, ...` loop of `_write_chunk_files`.

## Problem
Any config or code change that reduces chunk count for an already-chunked document silently
mixes obsolete chunks into the RAG index under one document. The current group-unreachable
state (see Unknowns UNK-01) masks this; it becomes live as soon as the chunk payload can be
read by the ingester.

## Reason for Change
Silent data-corruption path in a supported operational flow (`--force` is the documented
re-processing mechanism, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md:33`).

## Implementation Intent
Prune inside `ChunkSplitter`'s chunk-writing responsibility: on `force=True` (and only then),
after the source payload reads successfully, delete every file in `chunk/` matching the
exact `^{stem}-\d{4,}\.json$` pattern for that source, then write the new series — including
the case where the new series is empty. Non-forced behavior is unchanged.

## Requirements
- `REQ-001`: `ChunkSplitter.process_file`, when `force=True` and both `_read_source_data` and
  `_build_chunk_list` succeeded (Step 3a correction 2026-11-06: chunking itself can raise, as
  the Japanese merge crash of the 001 Plan shows, and a raised error must not destroy the
  existing series), removes all existing `chunk/` files matching `^{escaped-stem}-\d{4,}\.json$`
  before writing the new series; pruning runs even when the produced chunk list is empty, so
  a forced run always leaves the on-disk series exactly equal to the new output. When the
  source payload cannot be read, or chunking raises, no pruning occurs (a broken source must not destroy the
  existing series).
- `REQ-002`: Pruning is limited to the exact stem pattern — files of other stems (including
  stems with numeric suffixes, e.g. `page-1234-0000.json`) are never touched; the pruning
  count is logged (`INFO`) when greater than zero; the non-forced sentinel-skip path is
  unchanged.
- `REQ-003`: Regression tests cover: count-shrink under `force=True` (only the new series
  remains; payload index set equals `range(new_count)`); count-grow (no gaps, on-disk set
  equals new series); zero-chunk forced run (old series fully removed); stem isolation
  (other stems' files untouched); non-forced rerun keeps skipping (characterization).
- `REQ-004`: Update `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`'s
  idempotency paragraph (line 33) to state that a `--force` run replaces the document's
  full chunk series in `chunk/`.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-101257 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Add stem-pattern pruning on the `force=True` path (helper `_prune_stale_chunk_files(stem) -> int`), called from `process_file` after a successful source read and before writing, including zero-chunk runs | REQ-001, REQ-002; AC-1, AC-2, AC-3 | Write loop `:249-261` deletes nothing; zero-chunk early return `:244-245`; sentinel skip `:108-116`; reproduction confirmed stale residue (20 files kept after a 10-chunk forced run) (checked in Step 2) | `tests/rag/ingestion/test_chunk_splitter.py` | Verified |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Add the shrink/grow/zero-chunk/stem-isolation force tests and the non-forced characterization assertion | REQ-003; AC-1, AC-2, AC-3, AC-4, AC-6 | Existing force tests (`:483-536`, `:617`, `:655`) assert written counts only; nothing pins stale-file presence or absence (`rg force` scan, checked in Step 3) | itself | Verified |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Extend the idempotency/--force description: a forced run replaces the full chunk series in `chunk/` | REQ-004; AC-5 | Line 33 describes only the sentinel skip and "can be overwritten with `--force`" (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/pipeline_utils.py` | `is_already_processed` semantics (`:254-256`) and `read_chunk_json` required keys (`:164-182`) — the latter is why group-visible integration is currently blocked (UNK-01); file unchanged | REQ-001 rationale |
| `scripts/rag/ingestion/chunk_grouping.py` | Downstream consumer that benefits from a drained residue series; read-only | REQ-001 rationale |
| `scripts/rag/ingestion/ingester.py` | `ingest_url_group` contiguity/signature checks the stale series currently passes; read-only | REQ-003 integration-simulation basis |
| `tests/rag/ingestion/test_rag_ingestion_pipeline.py` | Second test-only importer of `ChunkSplitter`; must stay green | REQ-001 |
| `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md` | Co-targets `tests/rag/ingestion/test_chunk_splitter.py` (cross-plan overlap flagged by `check_plan_target_overlaps.py`); implement 001 before this plan to avoid rebase friction | REQ-003 sequencing |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-003): After a force re-chunk that produces fewer chunks, `chunk/`
  contains exactly the new series for that stem, and the payload index set equals
  `range(new_count)` (covered by a test).
- AC-2 (REQ-001, REQ-003): A forced run whose new series is empty leaves zero files for
  that stem (covered by a test).
- AC-3 (REQ-002, REQ-003): Files of other stems — including numeric-suffix stems — are
  untouched by pruning (covered by a test).
- AC-4 (REQ-001, REQ-002): Non-forced runs keep the sentinel-skip behavior unchanged
  (existing tests stay green, plus an explicit characterization test).
- AC-5 (REQ-004): The chunksplitter doc describes `--force` as replacing the full series.
- AC-6 (REQ-001..004): `uv run pytest tests/rag/ingestion` passes and changed lines reach
  the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-003 shrink: chunk one source at `max_chunk=200`, force-rerun at `max_chunk=600` → on
  disk exactly the new series, `chunk_index` set == `range(new_count)` (payload-level
  simulation of group contiguity; full `ChunkGroupingStrategy` integration is blocked by
  UNK-01).
- REQ-003 grow: reverse config order → no gaps; on-disk set == new series.
- REQ-003 zero-chunk: prior series exists; force-rerun with `min_chunk` raised above the
  content size → zero files remain for that stem.
- REQ-003 stem isolation: two stems (one with a numeric suffix, e.g. `page` and
  `page-1234`) chunked; force-rerun one → the other stem's files byte-identical.
- REQ-003 broken source: source payload replaced with invalid JSON, `force=True` → existing
  series preserved, no pruning (REQ-001 guard).
- REQ-003 chunking error (Step 3a addition): `_build_chunk_list` patched to raise, `force=True`
  → the exception propagates as today and the existing series is preserved.
- Characterization: all existing tests in `tests/rag/ingestion/test_chunk_splitter.py`
  unchanged and green.

## Documentation Impact
REQ-004: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` line 33 gains the
"forced run replaces the full chunk series" statement. No other doc change required —
`docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`'s lifecycle table is owned by the
003 Plan (no overlap).

## Assumptions
- `ChunkSplitter` always writes contiguous 0-based `:04d`-padded indices for a source
  (verified in the Step 2 reproduction), so prune-then-write never removes a file the same
  run would rewrite.
- Source crawl payloads are immutable per source file; count changes come from config or
  chunker-code changes only (the crawler writes a new timestamped source file per crawl).
- `/opt/llm/rag-src/chunk/` was empty at plan time (observed in Step 3), so no existing
  production residue needs migration for this fix.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | New defect found in Step 2 verification: `ChunkSplitter._build_chunk_payload` (`chunk_splitter.py:278-296`) omits `code_blocks`, but `read_chunk_json` (`pipeline_utils.py:164-182`) requires it, so `ChunkGroupingStrategy.group` silently skips 100% of ChunkSplitter output (empirically 0 groups from 20 real chunk files). Out of scope here; it also blocks a full group-visible integration test and re-arms this issue's corruption path once fixed | Filed since this Plan was written (Step 3a, 2026-11-06): `issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md` (High). Its fix edits `_build_chunk_payload` in the same file as this Plan; the two edits are in different functions, so they are compatible, with no ordering requirement. The 9-field group signature includes `chunk_type`, so text+code documents would fail group validation even after the payload fix | Implement `ragfix001` before or together with the group-visible end-to-end test of this Plan; this Plan's payload-level tests do not depend on it | False |
| UNK-02 | Whether production runs the current `scripts/rag/ingestion/chunk_splitter.py` source or an older Nuitka-packaged binary (commit `a902feb76`) | Production deployment artifact inventory | Confirm at deploy time via `skills/deploy/SKILL.md` sync verification | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Modify | Low | 2 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_chunk_splitter.py` | Modify | Low | 2 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Modify | Low | 7 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path A classification: one production module, its test file, and one doc paragraph; no
  cross-module contract change.
- Prune placement decision — in `process_file` (force branch) via a private
  `_prune_stale_chunk_files(stem)` helper, not inside `_write_chunk_files`: the write helper
  early-returns on an empty chunk list (`:244-245`) and would miss the zero-chunk case
  (verified in Step 2); `process_file` is where `force` is known, and the helper keeps the
  deletion inside `ChunkSplitter`'s chunk-writing responsibility (issue constraint).
  Pruning runs only after a successful `_read_source_data` and a successful
  `_build_chunk_list` — a broken source payload or a chunking error must not destroy the
  existing series (Step 3a correction 2026-11-06; the call goes between the chunk-list build
  and `_write_chunk_files` in `process_file`).
- Pattern decision — `re.compile(rf"^{re.escape(stem)}-\d{{4,}}\.json$")` matched against
  `chunk_dir.iterdir()`, not `glob(f"{stem}-*.json")`: a glob cross-matches other stems with
  numeric suffixes (e.g. stem `page` would match `page-1234-...json` variants such as
  `page-1234.json`-style residues), violating the stem-scoping constraint. `\d{{4,}}`
  mirrors the writer's `:04d` format including its growth beyond 9999. Given the writer's
  naming scheme the pattern is unambiguous: another stem's chunk files always carry an
  extra dash before the index.
- Interaction with the 003 Plan: this fix removes the stale-residue producer, so
  residue-mixed groups (003's Design risk row) largely stop occurring; no shared target
  files, order-independent.
- Cross-plan overlap: `tests/rag/ingestion/test_chunk_splitter.py` is co-targeted by the
  001 Plan (ja-merge fix tests). Designs do not contradict — 001 edits `_make_ja_mixin` and
  the ja end-to-end test; this plan adds a new force-prune test class — but implement 001
  first (dependency path: `plans/20261106-093438_raging001_japanese-chunk-merge-crash.md`).
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared constant
  changes; `ChunkSplitter`'s importers are two test files (`rg` scan in Step 3) and it has
  no production importers (CLI entry module).
- Historical analysis (Step 3): churn (30d) 2/2/7 for the three targets; all single
  maintainer. Operational check: inherited from this batch's `fuser /opt/llm/db/rag.sqlite`
  (no holders); production `chunk/` observed empty. Persisted schema check: N/A — file
  system only, no DDL.
- Validation quality baseline (Step 5): `radon cc scripts/rag/ingestion/chunk_splitter.py`
  — no C-or-worse grade; `vulture --min-confidence 80` and `bandit -q -c pyproject.toml` on
  the file — zero findings (both run this cycle, exit 0); `pip-audit` N/A: no dependency
  change. Diff-cover current number not measured (no code change yet); ≥ 90% on changed
  lines required at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Add the shrink/grow/zero-chunk/stem-isolation/broken-source force tests and the
     non-forced characterization assertion to `tests/rag/ingestion/test_chunk_splitter.py`
     (REQ-003; must fail against current code before Phase 2, except the characterization cases)
2. **Phase 2: Force-prune fix (GREEN)**
   - [ ] Add `_prune_stale_chunk_files(stem)` and call it from `process_file`'s force path
     after a successful source read, before `_write_chunk_files`, including zero-chunk runs
     (REQ-001, REQ-002; `scripts/rag/ingestion/chunk_splitter.py`)
3. **Phase 3: Documentation & verification & deploy hand-off**
   - [ ] Update the idempotency/--force paragraph (REQ-004;
     `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`)
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%)
     (REQ-001..003; `scripts/rag/ingestion/chunk_splitter.py`,
     `tests/rag/ingestion/test_chunk_splitter.py`)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate); confirm the Nuitka
     binary question (UNK-02) at that point (REQ-001)

### Release units
**Unit**: force-prune-fix | **Phases**: 1, 2 | **Reason**: Phase 1 adds tests that fail against the current no-prune behavior; the suite is green only after Phase 2, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | Unit | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | Shrink/grow/zero-chunk force runs leave exactly the new series; other stems untouched |
| `scripts/rag/ingestion/chunk_splitter.py` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green, including `test_rag_ingestion_pipeline.py` |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: pattern over-deletion of another stem's series → **Mitigation**: exact regex
  (`re.escape(stem)` + `\d{4,}` + full-match) instead of glob, plus the explicit
  stem-isolation and numeric-suffix-stem tests (AC-3).
- **Risk**: pruning a series whose source later turns out unreadable in a non-forced rerun
  (sentinel gone → full rechunk from the same source on next run) → **Mitigation**: intended
  semantics — a forced run is authoritative; rechunking the same source reproduces the
  series for unchanged config (assumption pinned by the grow test).
- **Risk**: deleting stale files before embedding services finish re-ingesting the new
  series (operator runs ingester later) → **Mitigation**: none needed — pruning happens in
  the chunk stage; the ingester only ever sees the new series, which is the fix's goal.
- **Risk**: cross-plan edit conflict on `test_chunk_splitter.py` with the 001 Plan →
  **Mitigation**: implement 001 first; this plan adds a separate test class.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add force-prune regression tests in `tests/rag/ingestion/test_chunk_splitter.py` | Completed | — | 2026-11-06 | REQ-003 |
| 2 | Force-prune in `scripts/rag/ingestion/chunk_splitter.py` | Completed | — | 2026-11-06 | REQ-001, REQ-002 |
| 3 | Docs update + gate sequence + deploy hand-off | Completed | — | 2026-11-06 | REQ-004 Docs paragraph updated by procedure 131606_03; gate sequence run; deploy of changed scripts/ files is the user's decision |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261106-131606_01_scripts_rag_ingestion_chunk_splitter.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261106-131606_03_docs_21_rag_rag_02_03_ingestion_pipeline-chunksplitter.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging004_force-rechunk-stale-chunks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-101257
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`,
  `tests/rag/ingestion/test_chunk_splitter.py`,
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1; no-delete write loop verified at `chunk_splitter.py:249-261`, zero-chunk early return at `:244-245`, residue reproduced in Step 2 | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-1, AC-2 | Phase 1 shrink/zero-chunk tests | Confirmed by repository evidence |
| REQ-002 | Issue Constraints "exact `{stem}-NNNN.json` pattern"; cross-stem glob hazard identified in Step 2 verification | `scripts/rag/ingestion/chunk_splitter.py` | Phase 2 | AC-3, AC-4 | Phase 1 stem-isolation + characterization tests | Confirmed by repository evidence |
| REQ-003 | Issue Testing Expectations | `tests/rag/ingestion/test_chunk_splitter.py` | Phase 1 | AC-1, AC-2, AC-3, AC-4, AC-6 | New force-prune test class | Explicit in issue |
| REQ-004 | Issue Documentation Impact; current wording verified at `rag_02_03_...md:33` (checked in Step 3) | `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` | Phase 3 | AC-5 | Review of updated paragraph | Explicit in issue |