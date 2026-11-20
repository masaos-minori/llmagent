## Goal

Confirm `CrawlDocument` in `scripts/rag/models_data.py` carries every field
`ChunkSplitter` reads from the source document, so the single
`CrawlDocument` -> `ChunkDocument` conversion (doc 03) has a complete source DTO.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `CrawlDocument` is a frozen dataclass and stays one; the conversion reads its
  fields only.
- The splitter reads exactly `url`, `title`, `lang`, `fetched_at`, `etag`,
  `last_modified`, `content`, `code_blocks` from the source DTO.

## Design decisions
- No new field is added to `CrawlDocument`: the eight fields `ChunkSplitter`
  reads are already present, so extending it would be a no-op.
- `CrawlDocument` remains the raw-crawl DTO; the chunk-only fields
  (`chunking_strategy`, `chunk_index`, `source_file`, `chunk_type`) stay on
  `ChunkDocument` only, preserving the artifact boundary.

## Alternatives considered
- Adding a synthetic/new DTO: rejected — `CrawlDocument` already exists and
  already holds the required fields (Plan Background).

## Implementation
### Target file
`scripts/rag/models_data.py`

### Procedure
1. Open `class CrawlDocument` (line 41) and list its fields.
2. Cross-check against the fields read by `_build_chunk_list` /
   `_extract_chunk_metadata` in `scripts/rag/ingestion/chunk_splitter.py`.
3. Confirm all eight are present; record the match.

### Method
Field-by-field comparison of `CrawlDocument` against the splitter's source
accesses.

### Details
`CrawlDocument` (line 41) declares `url`, `title`, `lang`, `fetched_at`,
`content`, `code_blocks`, `etag`, `last_modified`. `_build_chunk_list` reads
`data.lang`, `data.content`, `data.code_blocks`; `_extract_chunk_metadata` reads
`data.url`, `data.title`, `data.lang`, `data.fetched_at`, `data.etag`,
`data.last_modified`. All eight fields the splitter needs are present, so **no
edit to `models_data.py` is required**. This row exists to record that the DTO
completeness check passed before the conversion in doc 03 is written.

## Compatibility considerations
`CrawlDocument` is referenced nowhere under `scripts/` or `tests/` today, so
confirming its shape has no external-caller impact.

## Security considerations
N/A: type-shape confirmation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `CrawlDocument` lists all eight fields; the splitter's source accesses
  are a subset.

## Completion criteria
Confirmed `CrawlDocument` carries all eight fields `ChunkSplitter` reads; no
field addition needed.

## Out of Scope
Adding chunk-only fields to `CrawlDocument`; changing `ChunkDocument` or
`ChunkRecord`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm `CrawlDocument` completeness; no edit required | Completed | 20261120-093650 | 20261120-093650 | No edit required: CrawlDocument already declares all 8 fields ChunkSplitter reads (verified) |
| 2 | Add or update tests per Validation plan | Completed | 20261120-093650 | 20261120-093650 | N/A:no code change,no test change |
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
- **Requirement ID**: `REQ-002` — `CrawlDocument` carries every field the splitter reads
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-044650_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-065959
- **Related target files**: `scripts/rag/models_data.py`
