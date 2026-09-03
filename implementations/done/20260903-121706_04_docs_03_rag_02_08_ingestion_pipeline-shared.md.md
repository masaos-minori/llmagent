## Goal
Remove the description presenting `read_json_file()`'s lenient fallback behavior as a
supported production reader, relocating it to a clearly marked historical/Migration
section, per `REQ-001`.

## Scope
- **In scope**: mark the existing "Field Mapping for `read_json_file`" table and its
  surrounding description as historical (superseded); correct the "Public Functions"
  table's `read_json_file` row to state it is unused by any current pipeline path; add
  a pointer to the canonical strict readers.
- **Out of scope**: removing `read_json_file()` from
  `scripts/rag/ingestion/pipeline_utils.py` (Plan's explicit Out-of-Scope); the full
  field-contract table (row 2's responsibility, linked here); any other section of
  this document (Chunk Japanese Mixin, Shared Utilities, FTS5 notes).

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Mark the existing "Field Mapping for `read_json_file`" subsection historical **in
  place** (rename its heading and add an explanatory lead-in) rather than physically
  relocating it to the end of the document — `REQ-001` requires the description to
  appear in "a clearly marked historical/Migration section," which a heading + lead-in
  change satisfies without the added risk of a large content move in a document that
  also covers unrelated sections (Chunk Japanese Mixin, Shared Utilities, FTS5 notes).
- Confirmed via `grep -rn "read_json_file" scripts/ tests/ --include=*.py` (excluding
  its own definition in `pipeline_utils.py`) that no current code path calls
  `read_json_file()` — it is dead code from the pipeline's perspective, retained only
  because removing it is explicitly out of this Plan's scope. State this "no current
  caller" fact directly, rather than only "superseded," since it is a stronger and
  independently verified claim.

## Alternatives considered
- Physically move the table to a new section at the end of the file: rejected per
  Design decisions above (unnecessary churn risk for a document with unrelated
  sections; a heading/lead-in change satisfies `REQ-001`'s "clearly marked" requirement).
- Delete the field-mapping table entirely instead of marking it historical: rejected —
  `REQ-001` requires relocating the description, not deleting it; the function still
  exists in code (Plan's Out-of-Scope), so a historical record of its behavior remains
  useful.

## Implementation
### Target file
`docs/03_rag_02_08_ingestion_pipeline-shared.md`

### Procedure
1. Replace the "Public Functions" table's `read_json_file` row.
2. Replace the "**Field Mapping for `read_json_file`**" heading and table with a
   clearly marked historical subsection, adding a canonical-reader pointer.

### Method
Use `Edit` for each of the two changes, anchored on the exact existing text shown
below.

### Details
**Change 1** — in the "Public Functions" table, replace the row:
```
| `read_json_file` | `(path: Path) -> ChunkDocument` | Reads and parses a JSON file, converting it to a `ChunkDocument`; raises `ChunkFormatError` on failure |
```
with:
```
| `read_json_file` | `(path: Path) -> ChunkDocument` | **Legacy fallback reader, not called by any current pipeline path** (confirmed via repository-wide search) — see "Historical: `read_json_file()` Legacy Fallback Reader" below. Current production readers are `read_crawl_json()` / `read_chunk_json()`, documented canonically in [03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md). |
```

**Change 2** — replace:
```
**Field Mapping for `read_json_file`**

| JSON Field | ChunkDocument Field | Fallback |
|---|---|---|
| `url` | `url` | (Required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (Required, no fallback) |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |
```
with:
```
**Historical: `read_json_file()` Legacy Fallback Reader (superseded)**

The following field-mapping table describes `read_json_file()`'s lenient fallback
behavior, retained for historical reference only. This function is **not** used by any
current pipeline code path (verified: no caller exists outside its own definition in
`pipeline_utils.py`) — it predates the strict-reader migration
(`read_crawl_json()`/`read_chunk_json()`, both raising `ChunkFormatError` on
missing/invalid fields instead of silently substituting a default). It remains in
source only because removing it is out of scope for the strict-reader documentation
alignment (see this document's `Source plan`). Do not rely on this fallback behavior
for any new artifact producer — use the canonical readers documented in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md)
instead.

| JSON Field | ChunkDocument Field | Fallback |
|---|---|---|
| `url` | `url` | (Required, no fallback) |
| `title` | `title` | `""` |
| `lang` | `lang` | `"en"` |
| `content` | `content` | (Required, no fallback) |
| `code_blocks` | `code_blocks` | `[]` |
| `etag` | `etag` | `None` |
| `last_modified` | `last_modified` | `None` |
| `chunking_strategy` | `chunking_strategy` | `"text"` |
| `normalized_content` | `normalized_content` | `None` |
| `chunk_index` | `chunk_index` | `0` |
| `source_file` | `source_file` | `""` |
| `chunk_type` | `chunk_type` | `""` |
```
Repository evidence: `scripts/rag/ingestion/pipeline_utils.py:289-321` (`read_json_file`
body, confirming each fallback value cited above); `grep -rn "read_json_file" scripts/
tests/ --include=*.py` excluding `pipeline_utils.py` itself returns no matches
(confirmed during this document's creation — no current caller exists).

## Compatibility considerations
N/A: documentation-only; no code or artifact-format change. `read_json_file()` remains
callable in code (Plan Out-of-Scope) — this change only corrects how it is described,
not its availability.

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan).

## Completion criteria
No section of this document presents `read_json_file()` as a currently-relevant
production reader; its fallback-behavior table appears only under a heading explicitly
marked "Historical," with a stated superseding relationship to the canonical strict
readers.

## Out of scope
- Removing `read_json_file()` from `scripts/rag/ingestion/pipeline_utils.py`.
- The full field-contract table for `read_crawl_json()`/`read_chunk_json()` (row 2).
- This document's Chunk Japanese Mixin, Shared Utilities, and FTS5 sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-173100 | 20260903-173100 | Adversarially re-verified `read_json_file()`'s actual fallback logic (lines 289-321) against every table value, and re-ran the caller-search grep — zero external callers confirmed, exact match to the document's claims |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-173100 | 20260903-173100 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: all checks passed. `check_docs_consistency.py --domain rag`: 2 pre-existing `normalized_form()` warnings, both outside this edit's diff scope (lines 133/139 vs. edit at 59-94) |
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_02_08_ingestion_pipeline-shared.md
