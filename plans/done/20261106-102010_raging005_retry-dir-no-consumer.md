# Give retry/ a consumer or remove the embedding-failure retry routing

## Goal
- Eliminate the orphan `retry/` tier: every chunk file that leaves `rag-src/chunk/` lands
  in a directory with a defined consumer or documented terminal meaning, and failure
  classification is expressed over `IngestionFailureReason` members instead of substring
  matches.

## Priority
Medium

## Scope
- **In-Scope (design 2, recommended)**: removal of the `retry/` branch from
  `FileRouter.route`; enum-based classification replacing both substring tests
  (`file_routing.py`, `chunk_preparation.py`); WARNING for unknown reason strings; test
  flips; lifecycle doc update.
- **Out-of-Scope**: an attempt-budget retry consumer (design 1 — see Design); embedding
  HTTP retry tuning (`embed_retry`); group-validation routing (issue
  `20261106-073538_raging003_recrawled-chunk-group-poisoning.md`); `registered/` retention.
- **Dependencies**: coordination with `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
  (co-targeted docs table row; see Design).

## Background
`FileRouter.route` creates `retry/` unconditionally on every call (`file_routing.py:36-37`)
and moves any failed chunk whose reason string contains "embedding" there
(`file_routing.py:80-81`); everything else goes to `failed/` (`:82-83`). A repository-wide
scan finds no reader of `retry/`. The same substring test is duplicated in
`ChunkFactory.prepare`'s `embed_failed` metric counter (`chunk_preparation.py:56-60`), and
exception-path reasons are raw `str(e)` (`chunk_preparation.py:73`) — httpx error text
embeds the `/v1/embeddings` URL, so network errors already misland in `retry/` today.
Embedding HTTP retries already exist inside `EmbeddingService` (`embed_retry`,
`config/ingester.toml:18`, `embedding.py:44-67`). All claims verified against HEAD
`bdb9bed66` in Step 2 of this cycle.

## Problem
Embedding-failed chunks are moved out of the processing queue into a directory nothing
reads: they accumulate on disk, vanish from queue metrics, and the only recovery is
undocumented manual movement back to `chunk/`. The substring classification is also a
latent misrouting channel for any future or exception-derived reason that happens to
contain "embedding".

## Reason for Change
Broken workflow: an operator following the documented routing (`docs/21_rag/
rag_02_01_ingestion_pipeline-overview.md:35`) expects automatic retry; none exists.

## Implementation Intent
Design 2 (remove the retry tier), per the issue's own steer and this plan's decision
record: `FileRouter.route` stops creating `retry/`, routes every failed chunk to `failed/`
with its `.error.json` metadata, and classifies nothing by substring;
`ChunkFactory.prepare` counts `embed_failed` by enum identity. No attempt counter, no new
directory, no consumer.

## Requirements
- `REQ-001`: `FileRouter.route` removes the `retry_dir` creation and branch entirely: every
  entry of `failed_paths` moves to `failed/` next to its `.error.json`; module, class, and
  `route()` docstrings drop the `retry/` description; `route()`'s public signature is
  unchanged (consumers `ingester.py` and `transaction_commit.py` untouched).
- `REQ-002`: `FileRouter.route` logs a `WARNING` for any failed-path reason that is not a
  value of `IngestionFailureReason` and is not a known production reason (e.g.
  exception-derived `str(e)` reasons), then routes it to `failed/` like every other failure.
  Step 3a correction 2026-11-06: `RagIngester.ingest_url_group` passes the fixed string
  `"embedding_partial_failure"` for every prepared chunk of a group that also had a failed
  chunk; it is not an `IngestionFailureReason` member, so without an exception the new
  `WARNING` would fire for each such chunk on every partial failure. `file_routing.py`
  therefore keeps a small module-level collection of known non-enum production reasons
  containing that string, which routes to `failed/` without a warning; no substring test remains anywhere in
  `file_routing.py`.
- `REQ-003`: `ChunkFactory.prepare` counts `embed_failed` with
  `result is IngestionFailureReason.EMBEDDING_FAILED` instead of
  `"embedding" in reason_str.lower()` (`chunk_preparation.py:56-60`); the metric's
  observable semantics are unchanged (the enum branch's `reason_str` is always the enum
  `value`, so only `EMBEDDING_FAILED` ever matched — verified in Step 2).
- `REQ-004`: Tests (Step 3a addition: the flipped `test_mixed_success_and_failure_routes_correctly`,
  whose group has a prepared and a failed chunk, also asserts that no `WARNING` is logged for
  the `embedding_partial_failure` reason): `test_embedding_failure_moves_to_retry_not_registered` and
  `test_mixed_success_and_failure_routes_correctly` flip to asserting `failed/`
  destination plus `.error.json`; `test_retry_directory_created_for_embedding_failures`
  is replaced by an assertion that `retry/` is never created; a new test asserts the
  unknown-reason `WARNING` and `failed/` destination; `embed_failed` counts stay pinned by
  the existing `test_ingest_url_group_embed_failed_count` (`test_ingester.py:665`).
- `REQ-005`: Update `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md:35`: the chunk
  lifecycle becomes `chunk/` → `registered/` (success) / `failed/` (all failures, with
  `.error.json`); no `retry/` row or mention remains in RAG ingestion docs.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-102010 — every row
`Verified`). Frozen for design 2 only; choosing design 1 (a retry consumer) unfreezes this
table and requires a revised Plan (see Design and UNK-01).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/rag/ingestion/test_ingester.py` | Modify | Flip the three retry-destination tests to `failed/` + `.error.json`; add never-`retry/`-created and unknown-reason `WARNING` assertions | REQ-004; AC-1, AC-2, AC-3, AC-4 | Pinned tests at `:736-767`, `:769-819`, `:857+`; metric test at `:665` (checked in Step 2) | itself | Verified |
| `scripts/rag/ingestion/file_routing.py` | Modify | Delete `retry_dir` mkdir/branch and the substring test; uniform `failed/` destination; unknown-reason `WARNING`; docstring updates | REQ-001, REQ-002; AC-1, AC-2, AC-3 | `retry_dir` at `:36-37`; substring test at `:80`; split state (`.error.json` to `failed/`, body to `retry/`) at `:67-71` vs `:80-81`; docstring `retry/` mentions at `:8`, `:34` (checked in Step 2) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `scripts/rag/ingestion/chunk_preparation.py` | Modify | Replace the substring `embed_failed` counter with enum identity | REQ-003; AC-4 | Substring copy at `:56-60`; enum branch values confirmed to be `IngestionFailureReason` members from `embedding.py:78,103` (checked in Step 2) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Modify | Update the chunk-file lifecycle row to the two-terminal-directory design | REQ-005; AC-5 | Line 35 documents "to `retry/` (embedding failures) or `failed/`" (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/exceptions.py` | `IngestionFailureReason` members (`:51-59`) — the classification source for REQ-002/REQ-003 | REQ-002, REQ-003 |
| `scripts/rag/ingestion/embedding.py` | Produces `EMBEDDING_FAILED` / `PARSE_FAILED` after its own HTTP retries (`:44-67`, `:78`, `:103`); unchanged | REQ-003 rationale |
| `scripts/rag/ingestion/ingester.py` | `route()` call sites (`:294`, `:320-325`) pass reason strings through; signature unchanged | REQ-001 |
| `scripts/rag/ingestion/transaction_commit.py` | Second production consumer of `FileRouter`; must stay green | REQ-001 |
| `tests/integration/test_ingestion_e2e.py` | End-to-end consumer asserting result counts; must stay green | REQ-004 |
| `deploy/deploy.sh` | Creates `registered/` at `:59`; no `retry/` or cleanup references — confirmed no deployment change needed (issue's `setup_services.sh` claim corrected in verification) | Scope confirmation |
| `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md` | Co-targets the same lifecycle table (`rag_02_01...:35-38`); coordination ordering in Design | REQ-005 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-004): After an ingester run, embedding-failed chunks are in `failed/`
  with `.error.json`, and `retry/` is never created (covered by flipped tests).
- AC-2 (REQ-001, REQ-003, REQ-004): No `"embedding" in ...lower()` classification remains
  in `scripts/` (`rg` scan after implementation is empty).
- AC-3 (REQ-002, REQ-004): A reason string that is not an `IngestionFailureReason` value
  produces a `WARNING` and lands in `failed/` (covered by a test).
- AC-4 (REQ-003, REQ-004): `embed_failed` metric values are unchanged for all enum
  reasons (existing pinned test stays green; semantics equivalence recorded in Design).
- AC-5 (REQ-005): The lifecycle doc shows only `registered/` and `failed/` as destinations.
- AC-6 (REQ-001..005): `uv run pytest tests/rag/ingestion` passes and changed lines reach
  the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-004 flips: `test_embedding_failure_moves_to_retry_not_registered` →
  `failed/c.json` exists with `failed/c.error.json`; `retry/` does not exist.
- REQ-004 flip: `test_mixed_success_and_failure_routes_correctly` → success file in
  `registered/`, failed file in `failed/`; no `retry/`.
- REQ-004 replacement: `test_retry_directory_created_for_embedding_failures` → assert
  `(rag_src / "retry")` is absent after a run with zero or embedding failures.
- REQ-004 new: direct `FileRouter.route` unit test with a non-enum reason
  (e.g. `"some httpx error text"`) → `WARNING` logged (caplog) + file in `failed/`.
- Characterization: `test_ingest_url_group_embed_failed_count` (`test_ingester.py:665`) and
  `tests/integration/test_ingestion_e2e.py` unchanged and green.

## Documentation Impact
REQ-005: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md:35` lifecycle row updated.
Verified in Step 3 that no other RAG doc references the `retry/` directory
(`rag_05_04-error-handling-reference.md` describes `EmbeddingService` backoff retry only —
remains correct; `rag_05_03-logging.md:19` lists log categories, not directories).

## Assumptions
- Step 3a (2026-11-06, HEAD `97b8f4f6b`): the cited line numbers have drifted slightly (for
  example the `retry_dir` creation is at `file_routing.py:36-37` and the substring test at
  `:80`, which still match; `ingester.py` passes reasons at `:322-325`); the code is identified
  by symbol in the procedures. The 003 Plan's procedures (not yet executed) edit
  `ingester.py` and the same lifecycle row of `rag_02_01_ingestion_pipeline-overview.md`;
  the order recommended by this Plan (005 first) is kept.
- No stranded files exist in production `retry/`: `/opt/llm/rag-src/` contains only
  `chunk/` and `registered/` (observed in Step 3), so removal needs no data migration.
- All enum-branch reasons in `chunk_preparation.py` pass through as enum `value` strings;
  enum identity and the substring match select exactly the same members today (verified in
  Step 2) — REQ-003 is semantics-preserving.
- `failed/` remains the documented terminal directory (issue constraint); operator cleanup
  of `failed/` stays out of scope, mirroring `registered/` retention.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The issue requires an operator decision between design 1 (consumer) and design 2 (removal); this Plan freezes design 2 | Resolved 2026-11-06: the operator approved design 2 (answer to the procedure-generation question in the working session) | Resolved; if design 1 were ever chosen instead, this Plan is revised from scratch (attempt budget, promotion rules, deployment cleanup list) | False |
| UNK-02 | WARNING-level logging for unknown reason strings may add noise from exception-derived reasons (`chunk_preparation.py:73` passes raw `str(e)`); the deterministic `embedding_partial_failure` reason is excluded by REQ-002 (Step 3a) | No production volume data for exception-path failures | Observe `ingest.log` WARNING volume after deploy; downgrade to DEBUG if noisy (one-line change) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/file_routing.py` | Modify | Medium | 0 | High (single maintainer) | not applicable (rsynced) |
| `scripts/rag/ingestion/chunk_preparation.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Modify | Low | 3 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path B classification: a design decision (consumer vs removal) plus routing behavior
  change across two production modules, intentional test flips, and a docs update.
- Design decision — design 2 (remove the retry tier), as recommended by the issue itself:
  embedding HTTP retry already exists in `EmbeddingService` (`embed_retry`), so a file-level
  retry tier duplicates it without adding any retry; design 1 would require an attempt
  counter, promotion rules, and a consumption trigger that do not exist anywhere in the
  codebase (verified scan). Rejected alternative (design 1): larger blast radius, new
  state (attempt counts) with no existing home, and the issue's constraint forbids a
  parallel retry mechanism. The operator gate remains (UNK-01).
- Enum-based classification design: `route()` keeps its `list[tuple[Path, str]]` signature
  (consumers unchanged); inside, each reason is checked with
  `IngestionFailureReason(reason)` in a `try/except ValueError`; unknown values log a
  `WARNING` (naming the reason) and route to `failed/` — destination no longer depends on
  reason content at all. In `chunk_preparation.py`, counting uses enum identity before the
  `value` conversion.
- `.error.json` behavior is unchanged; the fix resolves today's split state (metadata in
  `failed/`, body in `retry/`) by co-locating body and metadata.
- Cross-plan coordination: `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md:35-38` is
  co-targeted by the 003 Plan (group-validation drain semantics). Recommended implementation
  order: 005 first (drop the `retry/` wording), then 003 rewrites the same row to the final
  lifecycle — 003's plan explicitly allows either order and its routing lands in `failed/`
  under both designs (none of its reasons contains "embedding" today, and after this plan no
  substring branch exists at all). Dependency path:
  `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`.
- `retry/` cleanup: no code removes an existing `retry/` directory; production has none
  (observed), and creating it stops immediately with REQ-001. If an operator ever has one,
  manual move-back-to-`chunk/` or delete is an ops task, not code.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared constant
  changes — `route()`'s signature is unchanged; consumer scan in Step 3: `FileRouter`
  importers are `ingester.py`, `transaction_commit.py`, `tests/integration/test_ingestion_e2e.py`.
  Historical analysis (Step 3): churn (30d) 0 for both production files and the test file,
  3 for the doc; single maintainer throughout. Operational check: inherited from this
  batch's `fuser /opt/llm/db/rag.sqlite` (no holders) and the `/opt/llm/rag-src/` listing.
  Persisted schema check: N/A — file routing only, no DDL.
- Validation quality baseline (Step 5): `radon cc` on both production files — no C-or-worse
  grade; `vulture --min-confidence 80` — no findings; `bandit -q -c pyproject.toml` — exit
  0, no findings (all run this cycle). `pip-audit` N/A. Diff-cover current number not
  measured (no code change yet); ≥ 90% on changed lines required at implementation per
  `rules/toolchain.md`.

## Implementation steps
0. **Gate**: operator approval of design 2 (UNK-01). Phases 1-3 must not start without it.
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Flip the three retry-destination tests and add the never-`retry/`-created and
     unknown-reason `WARNING` tests in `tests/rag/ingestion/test_ingester.py`
     (REQ-004; must fail against current code before Phase 2)
2. **Phase 2: Retry-tier removal (GREEN)**
   - [ ] Delete `retry_dir` mkdir/branch and the substring test in
     `scripts/rag/ingestion/file_routing.py`; add the unknown-reason `WARNING`; update the
     module/class/`route()` docstrings (REQ-001, REQ-002)
   - [ ] Replace the substring `embed_failed` counter with enum identity in
     `scripts/rag/ingestion/chunk_preparation.py` (REQ-003)
3. **Phase 3: Documentation & verification & deploy hand-off**
   - [ ] Update the lifecycle table row (REQ-005;
     `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`)
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted +
     `tests/rag/ingestion` + `tests/integration/test_ingestion_e2e.py`, ruff, mypy,
     lint-imports, bandit, diff-cover ≥ 90%)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via
     `skills/deploy/SKILL.md` is the user's decision (approval gate); confirm no `retry/`
     exists in production `rag-src/` at deploy time (REQ-001)

### Release units
**Unit**: retry-tier-removal | **Phases**: 1, 2 | **Reason**: Phase 1 flips tests that pin the current `retry/` destination; the suite is green only after Phase 2 removes the tier, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/file_routing.py` | Unit + flipped regression | `uv run pytest tests/rag/ingestion/test_ingester.py -v` | Failed chunks land in `failed/` with `.error.json`; `retry/` never created; unknown reason logs `WARNING` |
| `scripts/rag/ingestion/chunk_preparation.py` | Characterization | `uv run pytest tests/rag/ingestion/test_ingester.py -v` | `embed_failed` counts unchanged (`test_ingest_url_group_embed_failed_count`) |
| whole `scripts/` | Classification scan | `uv run rg '"embedding" in' scripts/rag/` | Zero matches (AC-2) |
| entry points | Regression | `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py` | All ingestion tests green |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: operators relying on the undocumented manual recovery path (`retry/` → manual
  move-back) lose it → **Mitigation**: `failed/` + `.error.json` is the documented terminal
  state; re-chunking from source (`--force`) or re-running the ingester after fixing the
  embedding service are the supported paths; stated in the REQ-005 doc update (via 003's
  final lifecycle row).
- **Risk**: flipping three pinned tests at once could mask a routing regression →
  **Mitigation**: each flipped test asserts a distinct path (single embedding failure,
  mixed success/failure, directory non-creation) plus the new unknown-reason test.
- **Risk**: WARNING noise from exception-derived reasons (UNK-02) → **Mitigation**: observe
  post-deploy log volume; one-line downgrade option recorded.
- **Risk**: docs-row edit conflict with the 003 Plan → **Mitigation**: recommended 005→003
  ordering in Design; 003's plan already allows either order.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 0 | Operator approval of design 2 | Completed | — | 20261106 | UNK-01 gate; approved 2026-11-06 |
| 1 | Flip/add tests in `tests/rag/ingestion/test_ingester.py` | In Progress | — | — | REQ-004 |
| 2 | Remove retry tier in `scripts/rag/ingestion/file_routing.py` and `scripts/rag/ingestion/chunk_preparation.py` | In Progress | — | — | REQ-001, REQ-002, REQ-003 |
| 3 | Docs update + gate sequence + deploy hand-off | In Progress | — | — | REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 0 | Design approval pending (design 2 recommended; issue requires operator decision) | Yes | 20261106 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261106-132221_01_tests_rag_ingestion_test_ingester.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261106-132221_02_scripts_rag_ingestion_file_routing.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261106-132221_03_scripts_rag_ingestion_chunk_preparation.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261106-132221_04_docs_21_rag_rag_02_01_ingestion_pipeline-overview.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging005_retry-dir-no-consumer.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-102010
- **Related target files**: `scripts/rag/ingestion/file_routing.py`,
  `scripts/rag/ingestion/chunk_preparation.py`, `tests/rag/ingestion/test_ingester.py`,
  `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes design-2 bullet; `retry_dir` branch verified at `file_routing.py:36-37,80-83` (checked in Step 2) | `scripts/rag/ingestion/file_routing.py` | Phase 2 | AC-1 | Flipped tests in `test_ingester.py` | Confirmed by repository evidence |
| REQ-002 | Issue Problem "Secondary" bullet + acceptance criterion 3; raw `str(e)` reasons verified at `chunk_preparation.py:73` (checked in Step 2) | `scripts/rag/ingestion/file_routing.py` | Phase 2 | AC-2, AC-3 | New unknown-reason unit test | Confirmed by repository evidence |
| REQ-003 | Step 2 verification finding: duplicate substring test at `chunk_preparation.py:56-60` | `scripts/rag/ingestion/chunk_preparation.py` | Phase 2 | AC-2, AC-4 | `test_ingest_url_group_embed_failed_count` characterization | Confirmed by repository evidence |
| REQ-004 | Issue Testing Expectations | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-1, AC-3, AC-4, AC-6 | Flipped + new tests | Explicit in issue |
| REQ-005 | Issue Documentation Impact; current wording verified at `rag_02_01_...md:35` (checked in Step 3) | `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md` | Phase 3 | AC-5 | Review of updated row | Explicit in issue |