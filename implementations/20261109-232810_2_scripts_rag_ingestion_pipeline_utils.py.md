## Goal

- Make `read_chunk_json` accept only `text` and `code` for `chunk_type` (including rejecting empty), so out-of-schema chunk files fail at read time and take the existing group `PARSE_FAILED` routing (`REQ-002`: `chunk_type` restriction mirroring the `chunks` CHECK constraint).

## Scope
**Release unit**: N/A: not part of a release unit

- One validation line in `read_chunk_json` in `scripts/rag/ingestion/pipeline_utils.py`, plus its companion test file.

## Assumptions

- Mirroring `scripts/db/schema_sql.py` L45 `CHECK (chunk_type IN ('text', 'code'))` at read time changes no previously successful outcome: such files already fail at commit every run (Plan Assumptions); whether legacy files with empty/unknown `chunk_type` exist in production is UNK-01 (owner-side scan before deploy).
- `ChunkSplitter` writes only `text` or `code` (`scripts/rag/ingestion/chunk_splitter.py`), so the producer side is unaffected.

## Design decisions

- Raise `ChunkFormatError` (the function's existing failure type) so every caller keeps its current handling: `ingest_url_group` routes the whole group to `failed/` with `PARSE_FAILED`, `embed_and_store` returns `PARSE_FAILED`.
- Keep `_validate_str_or_empty` for `source_file`; only `chunk_type` is restricted (the schema constrains exactly that field).

## Alternatives considered

- Rejecting at commit only (status quo): rejected — every run re-embeds the group before the CHECK fails (Plan Problem).
- A shared domain constant exported to other modules: rejected as unnecessary surface for one field; the inline tuple mirrors the CHECK and is tested against it.

## Implementation
### Target file
- `scripts/rag/ingestion/pipeline_utils.py`

### Procedure
- Replace the lenient `chunk_type` validation in `read_chunk_json` with a strict non-empty string check plus a membership check against the schema domain.

### Method
- At the per-field validation block (current L199), replace `chunk_type = _validate_str_or_empty(data, "chunk_type", "chunk")` with:
  - `chunk_type = _validate_str(data, "chunk_type", "chunk")`
  - `if chunk_type not in ("text", "code"):` raise `ChunkFormatError(f"Invalid chunk_type in chunk payload: {chunk_type!r}")`

### Details
- `_validate_str` already exists in the module and rejects empty/non-string values with `ChunkFormatError`.
- The `data.chunk_type or ""` fallback in `scripts/rag/ingestion/embedding.py` L85 becomes dead for missing/empty values (read time now rejects them) — intentionally left untouched (out of scope).
- No signature, return type, or `ChunkDocument` model change.

### Companion test files
- `tests/rag/ingestion/test_pipeline_utils_strict.py`
  - Procedure: in `TestReadChunkJson`, add parametrized cases asserting `ChunkFormatError` for `chunk_type` values `""`, `"chunk"`, and `"foo"` and acceptance for `"text"` and `"code"` (AC-2); review fixtures built from `CHUNK_PAYLOAD` (current value `"text"` is already compliant) for any payload relying on lenient values.
  - Validation: `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q` green; each new case fails on HEAD where applicable.

## Compatibility considerations

- Any other `read_chunk_json` caller (`embedding.py`, `chunk_grouping.py`, `ingester.py`) inherits the stricter check with no code change; out-of-domain files move from "fail at commit" to "fail at read", same terminal `failed/` destination, earlier and cheaper.

## Security considerations
N/A: domain validation on an already-validated string field.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q` — rejection cases pass.
- `uv run pytest tests/rag/ingestion -q` regression.
- `uv run ruff check`, `uv run mypy`.

## Completion criteria

- `read_chunk_json` raises `ChunkFormatError` for `""`, `"chunk"`, and `"foo"` and accepts `"text"` and `"code"` (AC-2); the ingestion suites are green.

## Out of Scope

- `chunk_type` handling in `embed_and_store` (fallback line stays), the production directory scan (UNK-01, deploy-side), other field validations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update companion tests per Validation plan | Pending | — | — | Companion: `tests/rag/ingestion/test_pipeline_utils_strict.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (reject out-of-schema `chunk_type` at read time)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `scripts/rag/ingestion/pipeline_utils.py`, `tests/rag/ingestion/test_pipeline_utils_strict.py`
