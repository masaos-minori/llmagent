## Goal

Update `tests/rag/ingestion/test_pipeline_utils_strict.py` so the
`read_crawl_json` assertions pin the new return type (`CrawlDocument`) while
keeping the whole strict-validator suite and `TestChunkPayloadKeyContract` green
(REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `read_crawl_json` now returns a `CrawlDocument` (doc 02); the existing
  `TestReadCrawlJson` cases access only crawl-DTO fields (`url`, `content`,
  `title`, `lang`, `code_blocks`, `etag`, `last_modified`), which
  `CrawlDocument` still exposes, so they stay valid unchanged.
- `TestChunkPayloadKeyContract` writes a crawl payload through the real splitter
  and asserts the 16-key payload; it does not inspect the crawl-reader return
  type, so it needs no change.
- `CrawlDocument` lives in `rag.models_data` and is importable here.

## Design decisions
- Add one explicit `isinstance(result, CrawlDocument)` assertion to
  `test_success_case` so the type contract is asserted at runtime, not merely
  implied by field access.
- Leave every other case untouched: they already cover the error paths and the
  crawl-field values, which are identical on a `CrawlDocument`.

## Alternatives considered
- A dedicated test class for the return type: rejected — one assertion in the
  existing success case is sufficient and keeps the suite compact.

## Implementation
### Target file
`tests/rag/ingestion/test_pipeline_utils_strict.py`

### Procedure
1. Add the DTO import alongside the existing reader imports (line 16-19):
   ```python
   from rag.models_data import CrawlDocument
   ```
2. In `TestReadCrawlJson.test_success_case` (line 62), after the field
   assertions (lines 64-70), add:
   ```python
   assert isinstance(result, CrawlDocument)
   ```
3. Confirm no other test constructs or asserts a `ChunkDocument` return from
   `read_crawl_json`; none does (the crawl cases access crawl fields only).

### Method
One import added, one assertion added. Re-run the strict suite to confirm no
regression.

### Details
The crawl cases at lines 62-118 read `result.url`, `result.content`, etc. All
six fields exist on both `ChunkDocument` and `CrawlDocument`, so removing the
placeholder-only chunk fields from the return value (doc 02) does not break
them. Adding the `isinstance` assertion is the only behavioral change and pins
REQ-001's type contract. `TestChunkPayloadKeyContract` (in
`test_chunk_splitter.py`) is unaffected because it exercises the splitter path,
not the reader return type.

## Compatibility considerations
Adding an import and one assertion cannot affect other modules; the strict suite
remains the sole consumer of this file.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Unit: `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q`
  passes, including the new `isinstance(result, CrawlDocument)` assertion.
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -q`
  confirms `TestChunkPayloadKeyContract` still holds after the conversion and
  total-metadata change (docs 02/03).

## Completion criteria
`read_crawl_json` is asserted to return a `CrawlDocument`; the strict suite and
`TestChunkPayloadKeyContract` pass.

## Out of Scope
Changing `TestReadChunkJson`, the 16-key payload contract, or any chunk-only
reader test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `CrawlDocument` import + `isinstance` assertion in `test_success_case` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — the crawl-reader validation tests assert the returned DTO type and fields
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-044650_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-065959
- **Related target files**: `tests/rag/ingestion/test_pipeline_utils_strict.py`
