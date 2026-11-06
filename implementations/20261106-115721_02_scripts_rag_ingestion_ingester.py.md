## Goal

Make chunk-group failures terminal and visible in `RagIngester`: route validation-failed groups and grouping-rejected files through `FileRouter` into `failed/`, process same-URL groups oldest-first, and give `validation_failure` results an explicit `failure_reason` (REQ-003: drain routing; REQ-004: ordering; REQ-005: reason propagation).

## Scope
**Release unit**: group-drain-fix

## Assumptions

- Grouping key/rejected-list production is created by sibling procedure 01 — implement 01 first (`group()`'s new return shape is consumed here).
- `FileRouter.route([], [(path, reason), ...])`'s substring branch (file_routing.py:80) never sends `group_validation_failed` / `parse_failed` / `validation_failed` to `retry/` — none contains "embedding" — so routing is compatible with either design of issue 005 (Plan Assumption).

## Design decisions

- One small helper `_route_group_failed` (new) performs the routing instead of inline branches at each failure return site — `ingest_all`/`ingest_url_group` already grade C(16)/C(14) in radon; complexity must not grow (Plan Design).
- No refactoring of `ingest_all` / `ingest_url_group` beyond the helper and the ordering change (AGENTS.md rule 5).

## Alternatives considered

- Routing ad hoc inside the grouping loop: rejected — `FileRouter` must stay the single move mechanism (Plan Design).

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`
### Procedure

- Add `_route_group_failed` (new): calls `self._file_router.route([], [(path, reason), ...])` so each file lands in `failed/` with `.error.json` naming the reason.
- Call it at every group-failure return site: the two `IngestUrlResult.validation_failure(...)` returns (ingester.py:225-226 and ingester.py:243-244) and the two `GROUP_VALIDATION_FAILED` results (ingester.py:257-263 and ingester.py:266-274), before returning the result.
- In `ingest_all` (ingester.py:143), route the grouping-rejected `(path, reason)` list returned by `group()` once, centrally, via `_route_group_failed` (new) after grouping.
- In `_process_url_groups` (ingester.py:370-387), iterate groups sorted ascending by `(url, fetched_at)` so the newest generation of one URL writes the `documents` row last (REQ-004).
- Make `validation_failure()` (ingester.py:58-59) carry `failure_reason=IngestionFailureReason.PARSE_FAILED` instead of `None` (REQ-005).

### Method

- Existing route sites (ingester.py:294, ingester.py:320, ingester.py:325) and `IngestUrlResult` semantics stay unchanged; only failure paths gain routing.
- The 9-field signature validation and index-contiguity checks stay exactly as-is (defense-in-depth after generation-safe grouping).

### Details

- `fetched_at` for ordering comes from the generation signature key produced by sibling procedure 01; do not re-read payloads just for sorting.
- Successful single-group behavior (route to `registered/`) is unchanged.

### Companion test files
- `tests/rag/ingestion/test_ingester.py`
  - Procedure: Flip the "files stay at original location" assertions in `TestGroupValidation` (test_ingester.py:891-1001, e.g. the comment at `:942`) to routed-to-`failed/` with `.error.json` assertions per failure return site; add the two-generation `ingest_all` end-to-end test (newest generation final in `documents`) and the re-run idempotency test (REQ-006).
  - Validation: `uv run pytest tests/rag/ingestion/test_ingester.py -v` — flipped assertions fail before this procedure (RED) and pass after; then `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py`.

## Compatibility considerations

- Co-target: `ingester.py` is also targeted by plans `20261106-102010_raging005_retry-dir-no-consumer.md` and `20261106-102657_raging006_ingester-index-generation-dup.md` (overlap tool) — implement 003 first or together (Plan Dependencies note: sequencing only, 005 need not land first); keep `file_routing.py` untouched here.
- `tests/integration/test_ingestion_e2e.py` consumes `RagIngester` and must stay green unchanged (characterization).

## Security considerations

N/A: file routing through the existing `FileRouter` mechanism; no new move primitive.

## Rollback considerations

N/A: revert the single commit (revert together with sibling procedures 01, 05, 06). Note: a production run before rollback will already have drained poisoned groups into `failed/` (UNK-01) — files are recoverable from `failed/`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Integration | `uv run pytest tests/rag/ingestion/test_ingester.py -v` | Failed groups land in `failed/` with `.error.json`; oldest-first ordering; idempotent re-run |
| Entry-point regression | `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py` | All green; single-generation semantics unchanged |
| Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |

## Completion criteria

- AC-1: no chunk file of a validation-failed group remains in `chunk/` after a run; all in `failed/` with `.error.json` naming the group reason.
- AC-2: two generations resolve independently; newest generation is the final `documents` row.
- AC-4: a second `ingest_all` after a drained group re-processes zero failed files.
- AC-6: `uv run pytest tests/rag/ingestion` passes; diff-cover ≥ 90%.

## Out of Scope

- `unexpected_failure` (mid-ingest crash) routing (Plan Design: adjacent finding, future issue).
- `retry/` consumption design (issue `20261106-073538_raging005_retry-dir-no-consumer.md`).
- `file_routing.py` and per-field signature validation rule changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Requires sibling procedure 01 (new `group()` shape) to land in the same change set |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/rag/ingestion/test_ingester.py` flips land in Plan Phase 1 (RED) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Includes diff-cover ≥ 90% |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (drain routing), `REQ-004` (oldest-first ordering), `REQ-005` (explicit `failure_reason`)
- **Source issue**: `issues/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-115721
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester.py`
