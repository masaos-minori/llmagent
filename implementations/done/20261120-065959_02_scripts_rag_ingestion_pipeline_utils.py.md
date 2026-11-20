## Goal

Make `read_crawl_json` in `scripts/rag/ingestion/pipeline_utils.py` return the
raw-crawl DTO (`CrawlDocument`) with no manufactured chunk-only fields, so its
return type names the artifact it validated (REQ-001).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `CrawlDocument` (frozen dataclass, `scripts/rag/models_data.py:41`) already holds
  every field `read_crawl_json` produces (`url`, `title`, `lang`, `content`,
  `code_blocks`, `etag`, `last_modified`, `fetched_at`).
- The only production caller is `chunk_splitter._read_source_data`, which converts
  the result to a `ChunkDocument` (doc 03).

## Design decisions
- Change the return type annotation and the constructor call from
  `ChunkDocument` to `CrawlDocument`; drop the four chunk-only fields
  (`chunking_strategy`, `chunk_index`, `source_file`, `chunk_type`) that had only
  placeholder values.
- Keep the strict validation (key-set check, per-field validation, the
  empty-content/code_blocks cross-field rule) unchanged.

## Alternatives considered
- Returning a plain `dict`: rejected — the plan keeps a typed DTO so each reader's
  return type describes the artifact it validated.

## Implementation
### Target file
`scripts/rag/ingestion/pipeline_utils.py`

### Procedure
1. Update the import at line 16 to also import `CrawlDocument`:
   `from rag.models_data import CrawlDocument, ChunkDocument`.
2. Change the signature at line 84 from
   `def read_crawl_json(path: Path) -> ChunkDocument:` to
   `-> CrawlDocument:` and update the docstring ("return a ChunkDocument" →
   "return a CrawlDocument").
3. Replace the `return ChunkDocument(...)` block (lines 130-144) with a
   `return CrawlDocument(...)` that omits the four chunk-only placeholder fields:
   ```python
   return CrawlDocument(
       url=url,
       title=title or "",
       lang=lang,
       content=content,
       code_blocks=code_blocks,
       etag=etag,
       last_modified=last_modified,
       fetched_at=fetched_at,
   )
   ```
4. Leave `read_chunk_json` (line 147) and its `ChunkDocument` return untouched.

### Method
Edit the signature, docstring, import, and single return statement; verify with
`rg` that no other reference to the removed placeholder fields remains in this
function.

### Details
The four removed fields (`chunking_strategy="text"`, `chunk_index=0`,
`source_file=""`, `chunk_type=""`, plus `normalized_content=None`) were always
placeholders on a payload with no chunk. Their removal is safe because
`_read_source_data` converts the `CrawlDocument` to a real `ChunkDocument` with
populated chunk-only fields (doc 03) before any chunk processing.

## Compatibility considerations
`read_crawl_json` is consumed only by `chunk_splitter._read_source_data`
(production) and `tests/rag/ingestion/test_pipeline_utils_strict.py` (which
accesses only crawl-DTO fields). The conversion in doc 03 keeps the downstream
`ChunkDocument` contract intact.

## Security considerations
N/A: DTO-shape change only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Unit: `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q`
  asserts `read_crawl_json` returns a `CrawlDocument` with the expected fields and
  no chunk-only fields.

## Completion criteria
`read_crawl_json` returns a `CrawlDocument` and constructs no chunk-only fields;
the strict validator suite passes.

## Out of Scope
Changing `read_chunk_json`, the 16-key payload field set, or any chunk-only reader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change `read_crawl_json` return type to `CrawlDocument` | Completed | 20261120-093650 | 20261120-093650 | — |
| 2 | Update strict tests per Validation plan | Completed | 20261120-093650 | 20261120-093650 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-093650 | 20261120-093650 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-093650 | 20261120-093650 | N/A:no doc change for this file |

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
- **Requirement ID**: `REQ-001` — `read_crawl_json` returns a `CrawlDocument` and constructs no chunk-only fields
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-044650_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-065959
- **Related target files**: `scripts/rag/ingestion/pipeline_utils.py`
