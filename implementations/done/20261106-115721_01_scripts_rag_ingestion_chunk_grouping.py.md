## Goal

Make `ChunkGroupingStrategy.group` generation-safe: key groups by (url, 9-field generation signature) and report skipped files as a rejected `(path, reason)` list with a per-file `WARNING` (REQ-001: generation-safe key; REQ-002: rejected-file reporting).

## Scope
**Release unit**: group-drain-fix

## Assumptions

- `group()`'s return-type change has exactly one consumer — `ingester.py` (verified import scan; no test imports `ChunkGroupingStrategy`) — handled by sibling procedure 02.
- Payload `chunk_index` contiguity is still validated by `ingest_url_group` unchanged (defense-in-depth; validation rules unchanged per Plan constraint).

## Design decisions

- Group key = `(url, signature)` where signature is exactly the 9-field tuple `ingest_url_group` already compares (`ingester.py:229-244`: url, title, lang, fetched_at, etag, last_modified, source_file, chunking_strategy, chunk_type) — separates both crawl generations and stale-residue mixes; a `source_file` key would not (Plan Design).
- Rejected files are returned as data, not moved inside the grouping loop: `FileRouter` stays the single routing point (sibling procedure 02 routes them in `ingest_all`).

## Alternatives considered

- Key by `(url, source_file)`: rejected — mixed-generation residue shares `source_file` but differs in `fetched_at`/`etag` (Plan Design).

## Implementation
### Target file
`scripts/rag/ingestion/chunk_grouping.py`
### Procedure

- Change `group()` (chunk_grouping.py:24-50) to key its dict by `(url, generation signature)` built from the 9 payload fields, and to also return a rejected list of `(path, IngestionFailureReason)` pairs: `parse_failed` for `ChunkFormatError` payloads (chunk_grouping.py:30-31), `validation_failed` for empty url (chunk_grouping.py:33-39) and invalid url (chunk_grouping.py:41-48).
- Add a per-file `logger.warning` for the `ChunkFormatError` skip — it currently logs nothing (chunk_grouping.py:30-31).
- Add the import `from rag.exceptions import IngestionFailureReason` (new) and keep existing extra-field log conventions (`stage_name: "ingester"`, `source_type: "file"`).

### Method

- Keep the existing empty/invalid-url warning messages; only the `ChunkFormatError` case gains a new WARNING line.
- Signature construction reads the same fields `read_chunk_json` already returns; no new payload parsing.

### Details

- Group values stay `list[Path]`; the key type change is internal to this module's single consumer (sibling procedure 02 reads `fetched_at` from the key for ordering).

### Companion test files
- `tests/rag/ingestion/test_chunk_grouping.py` (new)
  - Procedure: Add unit tests — two `fetched_at` generations of one url form distinct groups; rejected list contents (`parse_failed` for malformed payload, `validation_failed` for empty/invalid url); per-file `WARNING` log assertions via `caplog` for all three skip cases (REQ-001, REQ-002, REQ-006).
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_grouping.py -v` — fails against current grouping (RED), passes after this procedure (GREEN).

## Compatibility considerations

- `group()`'s return shape changes; the only consumer is `RagIngester` (`scripts/rag/ingestion/ingester.py`), updated by sibling procedure 02 in the same change set (Phase 2 order: this file first).
- `chunk_grouping.py` itself has no cross-plan target overlap (overlap tool); the stale-residue groups this key drains are produced by the scenario fixed in plan `20261106-101257_raging004_force-rechunk-stale-chunks.md` — verify designs do not contradict.

## Security considerations

N/A: grouping bookkeeping only; no path-execution or credential change.

## Rollback considerations

N/A: revert the single commit (revert together with sibling procedures 02, 05, 06).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Grouping unit | `uv run pytest tests/rag/ingestion/test_chunk_grouping.py -v` | Generation-split groups; rejected list; per-file WARNING lines |
| Ingestion regression | `uv run pytest tests/rag/ingestion` | All green with sibling procedure 02 landed |

## Completion criteria

- AC-1/AC-2 basis: chunk files from two generations of one URL form distinct groups (test-covered).
- AC-3: grouping skips are reported with reasons and produce a per-file `WARNING` (test-covered).
- AC-6 basis: `uv run pytest tests/rag/ingestion` green; diff-cover ≥ 90%.

## Out of Scope

- Routing of rejected files (sibling procedure 02; `FileRouter` unchanged).
- `ingest_url_group`'s signature validation rules (unchanged as defense-in-depth).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261106-143204 | 20261106-143204 | Companion tests must exist first (RED, Plan Phase 1) |
| 2 | Add or update tests per Validation plan | Completed | 20261106-143204 | 20261106-143204 | Companion `tests/rag/ingestion/test_chunk_grouping.py` (new) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261106-143204 | 20261106-143204 | Includes diff-cover ≥ 90% |

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
- **Requirement ID**: `REQ-001` (generation-safe grouping key), `REQ-002` (rejected-file reporting)
- **Source issue**: `issues/20261106-073538_raging003_recrawled-chunk-group-poisoning.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-095808_raging003_recrawled-chunk-group-poisoning.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-115721
- **Related target files**: `scripts/rag/ingestion/chunk_grouping.py`, `tests/rag/ingestion/test_chunk_grouping.py`