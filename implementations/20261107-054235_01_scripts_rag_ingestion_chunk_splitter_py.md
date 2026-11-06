## Goal

- Make `ChunkSplitter._build_chunk_payload` emit `code_blocks` (empty list) so every chunk file it writes
  passes `read_chunk_json` (REQ-001: producer-side `code_blocks` addition; REQ-002: payload key-set pin test).

## Scope
**Release unit**: chunk-payload contract closure

- Single literal addition to the payload dict built by `ChunkSplitter._build_chunk_payload`, plus its
  companion pin test in `tests/rag/ingestion/test_chunk_splitter.py`. Tests land first (Phase 1, RED),
  then the fix (Phase 2) — the two are one release unit and must be delivered together.

## Assumptions

- `code_blocks: []` uniformly for all chunk paths is correct (Plan A-001, High confidence: no code path
  reads chunk-level `code_blocks` values today; only `read_chunk_json` validates its presence/type).
- `read_chunk_json` enforces a flat top-level key set only — no `metadata` sub-object check (Plan UNK-01,
  resolved).
- Adding the key cannot change grouping outcomes (Plan A-002: group key is `ChunkGeneration.to_group_key()`,
  content-independent).

## Design decisions

- Fix at the single shared construction point: all split paths (markdown heading, English, Japanese, code)
  flow through `_build_chunk_list` → `_build_text_triples`/`_build_code_triples` → `_write_chunk_files` →
  `_build_chunk_payload`, so one key addition covers every path and keeps the key set uniform.
- Validator stays strict and unchanged: `pipeline_utils.py` is a Reference File — read-only for this row.

## Alternatives considered

- Making `code_blocks` optional in `read_chunk_json`: rejected by the Plan (contradicts the documented
  3.4a field contract).
- Per-path injection in `_build_text_triples` / `_build_code_triples`: rejected — the shared builder already
  covers every path.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Add the companion pin test first (see Companion test files) and confirm it is RED with a
   `Missing keys in chunk payload: ['code_blocks']` / pinned-key failure (Plan Phase 1).
2. Add the key (Plan Phase 2, REQ-001).
3. Re-run the companion test: green.

### Method
- In `_build_chunk_payload` (currently lines 318-336), add one entry to the returned payload dict:
  `"code_blocks": [],`. Place it after the `"normalized_content"` entry so the envelope/metadata spread and
  chunk-specific fields stay in their current order.

### Details
- No import changes; no other statement in the file changes; the separate `metadata` dict is untouched — the
  addition goes in the top-level payload dict only.
- Expected post-change top-level key set (16 keys): envelope `schema_version`, `artifact_type`, `created_by`;
  13 required chunk keys `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`,
  `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `chunking_strategy`, `fetched_at`.

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: add a class `TestChunkPayloadKeyContract` (new) with a test
    `test_written_chunk_payload_satisfies_key_contract` (new): reuse `_make_io_splitter` and
    `_write_crawl_json` with `_CRAWL_WITH_TEXT_AND_CODE`, run `process_all(force=True)`, then for each
    written chunk file assert `set(orjson.loads(...).keys())` equals the exact 16-key set listed in Details
    above, and that `read_chunk_json(cf)` (import `from rag.ingestion.pipeline_utils import read_chunk_json`
    (new import in this test file)) returns without raising and its `code_blocks` equals `[]`.
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` — RED (names `code_blocks`)
    before step 2 of Procedure, all green after.

## Compatibility considerations

- Existing unit-test fixtures hand-write payloads that already include `code_blocks` — unaffected.
- Existing production chunk files written before the fix stay malformed and are still rejected until
  `--force` re-chunk or re-crawl; the Plan deliberately does not migrate them (Plan UNK-02, handled at the
  Phase 3 deploy hand-off).

## Security considerations

- N/A: no trust-boundary change; the added key is an internal artifact field validated as `list[str]`.

## Rollback considerations

- N/A: revert the commit (single-commit change, no data migration).

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` — target + companion tests green.
- `uv run pytest tests/rag/ingestion` — suite green.
- Completion gates per `rules/toolchain.md`: `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy scripts`, `uv run lint-imports`, `uv run bandit -q -r scripts -ll`,
  `uv run diff-cover coverage.xml --compare-branch=HEAD --fail-under=90` (≥90% on the diff).
- Gate baselines: `uv run radon cc scripts/rag/ingestion/chunk_splitter.py -n B` (no new C+ block),
  `uv run vulture scripts tests` (no new finding in target files).

## Completion criteria

- A chunk file written by the real ChunkSplitter writer path passes `read_chunk_json` unchanged with
  `code_blocks == []` (AC-001).
- The pin test fails deterministically on any future payload key addition/removal (AC-003).
- `pipeline_utils.py`, crawl-artifact semantics, grouping semantics, and failure routing are byte-identical
  (Boundary row of the Plan's Acceptance Criteria).

## Out of Scope

- Non-empty per-chunk `code_blocks` content (future feature).
- End-to-end ChunkSplitter→ingester regression test — own document (`seq03`,
  `tests/rag/ingestion/test_rag_ingestion_pipeline.py`).
- Any change to `scripts/rag/ingestion/pipeline_utils.py` (Reference File).
- Deploy: Phase 3 hands off to the user-approval deploy step (`scripts/` change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add companion pin test `TestChunkPayloadKeyContract` (new) in tests/rag/ingestion/test_chunk_splitter.py; confirm expected RED (Plan Phase 1) | Pending | — | — | Release unit "chunk-payload contract closure": intentionally RED until step 2 |
| 2 | Add `"code_blocks": []` to `_build_chunk_payload` payload dict (Plan Phase 2, REQ-001) | Pending | — | — | |
| 3 | Re-run companion + `tests/rag/ingestion` suite: all green | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) incl. radon/vulture baselines and diff-cover ≥90% | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (producer-side `code_blocks` addition), REQ-002 (payload key-set pin test)
- **Source issue**: issues/done/20261106-110845_ragfix001_chunk-payload-code-blocks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-050704_ragfix001_chunk-payload-code-blocks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-054235
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py, `tests/rag/ingestion/test_chunk_splitter.py`
