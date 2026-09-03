## Goal
State `read_crawl_json()` as the canonical crawl-artifact reader used by `ChunkSplitter`
(`REQ-002`), and align this document's field references with the crawl-artifact's
8-required-key classification without duplicating the full contract table (`REQ-006`).

## Scope
- **In scope**: add a short canonical-reader statement (reader, caller,
  `ChunkFormatError` failure mode) to section "2.4 Output JSON Format"; link to the
  canonical crawl/chunk artifact-field contract table instead of restating it.
- **Out of scope**: authoring the full Required/Nullable/Conditional field table
  (belongs to `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` per `REQ-011` —
  see row 2 of this Plan's Implementation Target Files); modifying
  `scripts/rag/ingestion/pipeline_utils.py` or `chunk_splitter.py`; test file changes.

## Assumptions
- The canonical field-contract document is
  `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, per the Plan's Assumptions
  section (`REQ-011`). This document's link target depends on that document's
  implementation adding an addressable section/anchor for the contract table — if that
  section's heading differs from what this document assumes, update the link at
  implementation time to match the actual heading.

## Design decisions
- Extend the existing "2.4 Output JSON Format" section rather than adding a new
  top-level subsection — it is already the section describing the crawler's JSON
  output contract, so this is the natural location for the canonical-reader statement
  (see `skills/python-design/SKILL.md` Avoid implementation-reference duplication:
  state the reader/caller/failure-mode facts here once, link elsewhere for the full
  field table rather than repeating it).

## Alternatives considered
- Duplicate the full 8-key field table locally instead of linking: rejected — conflicts
  with `REQ-011`'s single-canonical-source requirement and creates a second table to
  keep in sync.

## Implementation
### Target file
`docs/03_rag_02_02_ingestion_pipeline-crawler.md`

### Procedure
Extend the "### 2.4 Output JSON Format" section (currently a single link-out line) to
state the canonical reader, its caller, the `ChunkFormatError` failure mode, and a link
to the canonical field-contract table for the full classification.

### Method
Use `Edit` to replace the section body; do not alter the section heading or any other
section.

### Details
Replace:
```
### 2.4 Output JSON Format

See [docs/03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) for details.
```
with:
```
### 2.4 Output JSON Format

`read_crawl_json()` (`scripts/rag/ingestion/pipeline_utils.py:100`) is the canonical
reader for crawl-stage JSON artifacts; `ChunkSplitter`
(`scripts/rag/ingestion/chunk_splitter.py:196`) is its sole caller. A crawl artifact
requires exactly 8 keys (`url`, `content`, `title`, `lang`, `code_blocks`, `etag`,
`last_modified`, `fetched_at`) — a missing key or an invalid field type raises
`ChunkFormatError` (see [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md)).
For the full Required/Nullable/Conditional classification of these fields, see the
canonical crawl/chunk artifact-field contract table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).
See also [docs/03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) for
the `ChunkDocument` DTO this reader returns.
```
Repository evidence for the line numbers cited: `scripts/rag/ingestion/pipeline_utils.py:100`
(`def read_crawl_json`) and `scripts/rag/ingestion/chunk_splitter.py:196`
(`return read_crawl_json(src_path)`) — both confirmed by direct read during this
document's creation.

## Compatibility considerations
N/A: documentation-only; no code or artifact-format change. The added link depends on
row 2's document (`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`) being
implemented with a matching anchor — verify the link resolves after row 2's edit lands,
per this Plan's Validation plan (`check_docs_quality.py` link check).

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan) — expect no structural findings and no broken-link findings once row 2's target
section exists.

## Completion criteria
This document's target section states `read_crawl_json()` as the canonical
crawl-artifact reader, `ChunkSplitter` as its sole caller, the `ChunkFormatError`
failure mode, and links to (without duplicating) the canonical field-contract table.

## Out of scope
- The full Required/Nullable/Conditional field table (row 2's responsibility).
- Any change to `scripts/rag/ingestion/pipeline_utils.py` or `chunk_splitter.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `check_docs_quality.py`, `check_docs_consistency.py --domain rag` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document IS the documentation update |

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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_02_02_ingestion_pipeline-crawler.md
