## Goal

Add the single `CrawlDocument` -> `ChunkDocument` conversion at the
`process_file` seam (`_read_source_data`) so the rest of the splitter keeps
operating on a `ChunkDocument`, and make `ChunkMetadata` total so a missing key
fails at construction (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `read_crawl_json` now returns a `CrawlDocument` (doc 02); `_read_source_data`
  must convert it before any chunk processing.
- `_extract_chunk_metadata` is the only builder of `ChunkMetadata` and always
  returns all eight keys, so a total contract is safe.
- `ChunkDocument.chunking_strategy` / `chunk_type` are not read downstream; the
  real values flow as parameters to `_extract_chunk_metadata` via
  `_build_chunk_list`. The conversion's values are therefore fillers.

## Design decisions
- Introduce one module-level helper `_crawl_to_chunk_document` (new)
  `(crawl, src_path)` and call it inside `_read_source_data`; everything downstream
  (`_build_chunk_list`, `_is_markdown_source`, `_write_chunk_files`) keeps its
  `ChunkDocument` signature unchanged.
- Fill the four chunk-only fields with real (non-placeholder) values:
  `chunk_index=0`, `source_file=src_path.name`, `chunking_strategy="text"`
  (the splitter's default, matching `_build_text_triples`'s signature default),
  `chunk_type=""`, `normalized_content=None`. These are superseded by the
  per-file `chunking_strategy` computed in `process_file` (line 272).
- Make `ChunkMetadata` total by removing `total=False`; update its docstring,
  which currently claims all fields are optional.

## Alternatives considered
- Replacing `ChunkMetadata` with a frozen dataclass: rejected — removing
  `total=False` is the smaller change and preserves the spread-into-payload
  usage (`_build_chunk_payload`).

## Implementation
### Target file
`scripts/rag/ingestion/chunk_splitter.py`

### Procedure
1. Import `CrawlDocument` alongside `ChunkDocument` at the top of the module
   (confirm the current import line for `models_data`).
2. Add a module-level helper after the DTO imports:
   ```python
   def _crawl_to_chunk_document(
       crawl: CrawlDocument, src_path: Path
   ) -> ChunkDocument:
       """Convert a validated CrawlDocument to a ChunkDocument for the splitter."""
       return ChunkDocument(
           url=crawl.url,
           title=crawl.title,
           lang=crawl.lang,
           content=crawl.content,
           code_blocks=list(crawl.code_blocks),
           etag=crawl.etag,
           last_modified=crawl.last_modified,
           fetched_at=crawl.fetched_at,
           chunking_strategy="text",
           chunk_index=0,
           source_file=src_path.name,
           chunk_type="",
           normalized_content=None,
       )
   ```
3. In `_read_source_data` (line 444), wrap the reader result:
   ```python
       def _read_source_data(self, src_path: Path) -> ChunkDocument | None:
           """Read and parse a JSON crawl file; returns a ChunkDocument or None."""
           try:
               return _crawl_to_chunk_document(read_crawl_json(src_path), src_path)
           except (FileNotFoundError, ChunkFormatError) as e:
               logger.error("skip %s: %s", src_path.name, e)
               return None
   ```
4. Make `ChunkMetadata` total: change line 93 from
   `class ChunkMetadata(TypedDict, total=False):` to
   `class ChunkMetadata(TypedDict):`, and update the docstring below it that
   states "All fields are optional because this dict is spread with ** into the
   output payload" to reflect that all eight keys are now required.

### Method
Two edits: (a) add the helper + rewire `_read_source_data`; (b) drop
`total=False` and fix the docstring. Confirm via `rg` that `_extract_chunk_metadata`
still returns all eight keys and that no other builder exists.

### Details
`process_file` reads `chunk_doc.url` (lines 262, 299) and passes `chunk_doc` to
`_is_markdown_source` (which reads `data.url`, `data.content`) and
`_build_chunk_list` before computing the real `chunking_strategy` (line 272).
Converting inside `_read_source_data` satisfies every call site with a proper
`ChunkDocument`. The 16-key payload contract produced by `_build_chunk_payload`
(line 566) is unchanged because `_extract_chunk_metadata` still emits all eight
metadata keys plus the eight chunk-specific keys.

## Compatibility considerations
Downstream readers (`chunk_grouping`, `embedding`, `file_routing`, `ingester`)
consume `read_chunk_json`, not this path, so they are unaffected. The conversion
preserves the 16-key payload asserted by `TestChunkPayloadKeyContract`.

## Security considerations
N/A: DTO-shape and type-totality change only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Unit: `TestChunkPayloadKeyContract` in
  `tests/rag/ingestion/test_chunk_splitter.py` still asserts the unchanged 16-key
  payload after the conversion and total-metadata change.
- Unit: `ChunkMetadata` construction raises when a key is omitted (type checker;
  runtime is enforced by TypedDict total at construction sites).

## Completion criteria
A single `_crawl_to_chunk_document` (new) conversion builds a `ChunkDocument` from the
`CrawlDocument` at `_read_source_data`; `ChunkMetadata` is total; the 16-key
contract holds.

## Out of Scope
Changing the 16-key payload field set/order, or any chunk-only reader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `CrawlDocument`->`ChunkDocument` conversion; make `ChunkMetadata` total | Pending | — | — | |
| 2 | Update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (conversion), `REQ-003` (total `ChunkMetadata`)
- **Source issue**: `issues/20261119-112020_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-044650_ragcrv008_crawl-chunk-dto-conflation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-065959
- **Related target files**: `scripts/rag/ingestion/chunk_splitter.py`
