## Goal

Record which DTO each of `read_chunk_json` / `read_crawl_json` returns in
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`, so the doc matches the
artifact boundary now expressed in the type system (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The doc currently names neither reader (`rg read_crawl_json|read_chunk_json`
  over the doc returns no matches), so this adds a new section rather than
  editing an existing one.
- `read_crawl_json` returns `CrawlDocument` and `read_chunk_json` returns
  `ChunkDocument` (docs 02/03); the doc should state exactly that.

## Design decisions
- Add a short "Pipeline Utils Readers" subsection under the existing
  ingestion-pipeline structure naming each function, its source file, and the
  DTO it returns, plus the artifact each represents ("raw crawl payload" vs
  "chunk-ready document").
- Keep it prose-level (a few bullets); this is a documentation update, not an
  architecture treatise.

## Alternatives considered
- Editing the `pipeline-utils` tag block only: rejected — the tag lists the
  module but never names the readers; a dedicated subsection records the DTO-per
  reader fact that REQ-005 requires.

## Implementation
### Target file
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`

### Procedure
1. Insert a new subsection after section 7 (Chunk Utils) and before
   `## Keywords`, e.g. `## 8. Pipeline Utils Readers
   (scripts/rag/ingestion/pipeline_utils.py)`.
2. Record:
   - `read_crawl_json(path)` validates a raw crawl JSON file and returns a
     `CrawlDocument` (the raw-crawl DTO, no chunk-only fields).
   - `read_chunk_json(path)` validates a chunk JSON file and returns a
     `ChunkDocument` (the chunk-ready DTO).
   - The boundary between them is expressed in the type system; the splitter
     converts the `CrawlDocument` to a `ChunkDocument` at the single
     `process_file` seam.
3. Verify the two reader names now appear in the doc.

### Method
Add one subsection with two bullet points naming each reader and its return
DTO; confirm the names are present via `rg`.

### Details
The doc's front matter tags include `pipeline-utils` but its body documents
crawler utils, the English/Japanese chunk mixins, and `chunk_utils` only. No
section describes the strict validator pair in `pipeline_utils.py`. Adding the
subsection records the DTO-per-reader contract that the code now enforces.

## Compatibility considerations
A documentation addition has no runtime impact; it must not contradict the code
(docs 02/03).

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Static: `rg -n "read_crawl_json|read_chunk_json"` over the doc returns the new
  subsection; each reader is paired with its correct DTO.

## Completion criteria
The doc states that `read_crawl_json` returns a `CrawlDocument` and
`read_chunk_json` returns a `ChunkDocument`.

## Out of Scope
Documenting the conversion detail beyond the DTO-per-reader fact; rewriting the
existing sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add a Pipeline Utils Readers subsection naming each reader's DTO | Completed | 20261120-093650 | 20261120-093650 | — |
| 2 | Add or update tests per Validation plan | Completed | 20261120-093650 | 20261120-093650 | N/A:documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120-093650 | 20261120-093650 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261120-093650 | 20261120-093650 | This row |

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
- **Requirement ID**: `REQ-005` — the doc records which DTO each of `read_chunk_json` / `read_crawl_json` returns
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-044650_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-065959
- **Related target files**: `docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`
