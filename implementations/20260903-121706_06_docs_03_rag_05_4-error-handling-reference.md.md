## Goal
Document that missing required fields and invalid field types in a crawl or chunk
artifact raise `ChunkFormatError` (exact-key-set check plus per-field type/value
validation), per `REQ-004` — this document currently has no row or section covering
this failure mode for either canonical reader.

## Scope
- **In scope**: add a new section documenting `ChunkFormatError` conditions raised by
  `read_crawl_json()` and `read_chunk_json()`.
- **Out of scope**: the existing `Crawler`, `ChunkSplitter`, `RagIngester`,
  `RagPipeline` tables and `Implementation Notes` (no Requirement in this Plan targets
  their existing content); modifying `scripts/rag/exceptions.py` or
  `scripts/rag/ingestion/pipeline_utils.py`.

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Add a new top-level section, "## Pipeline Utils — Artifact Validation", positioned
  between the existing "## ChunkSplitter" and "## RagIngester" sections — this mirrors
  where the two readers are actually invoked (`read_crawl_json()` inside
  `ChunkSplitter`'s call path; `read_chunk_json()` inside `RagIngester`'s), and keeps
  this shared-validation-layer content out of either module-specific table rather than
  duplicating it into both.
- Document the conditions as a table matching this document's existing per-module
  format (`| Error | Action |`), rather than prose, for consistency with the rest of
  the document.

## Alternatives considered
- Add a `ChunkFormatError` row directly into the existing `ChunkSplitter` and
  `RagIngester` tables (one row each): rejected — the validation logic and raised
  conditions are identical for both readers (shared `pipeline_utils.py` validator
  functions), so a single shared section avoids restating the same conditions twice
  with a risk of drift.

## Implementation
### Target file
`docs/03_rag_05_4-error-handling-reference.md`

### Procedure
Insert a new "## Pipeline Utils — Artifact Validation" section after the existing
"## ChunkSplitter" table and before "## RagIngester".

### Method
Use `Edit`, anchoring on the exact existing "## RagIngester" heading line to insert
immediately before it.

### Details
Insert the following content immediately before the `## RagIngester` heading:
```markdown
## Pipeline Utils — Artifact Validation (`read_crawl_json()` / `read_chunk_json()`)

Both canonical artifact readers (`scripts/rag/ingestion/pipeline_utils.py`) raise
`ChunkFormatError` (`scripts/rag/exceptions.py:27`, a `RagLayerError` and `ValueError`
subclass) on any validation failure — there is no silent-default fallback path in
either reader (contrast with the legacy `read_json_file()`, documented as historical
in [03_rag_02_08_ingestion_pipeline-shared.md](03_rag_02_08_ingestion_pipeline-shared.md)).

| Error | Action |
|---|---|
| File read failure (`OSError`) | `ChunkFormatError` |
| JSON parse failure | `ChunkFormatError` |
| Parsed JSON is not an object | `ChunkFormatError` |
| Missing one or more required keys (exact-key-set check; 8 keys for crawl, 13 for chunk) | `ChunkFormatError` |
| Unknown key present beyond the required 13 (chunk artifacts only; `schema_version`/`artifact_type`/`created_by` are exempted) | `ChunkFormatError` |
| Required-classified field is missing, `null`, or the wrong type (`_validate_str`) | `ChunkFormatError` |
| Conditional-classified field has the wrong type (`_validate_str_or_empty`) | `ChunkFormatError` |
| Nullable-classified field is present but neither `str` nor `null` (`_validate_nullable_str`) | `ChunkFormatError` |
| `chunk_index` is `bool`, non-`int`, or negative (`_validate_int_non_negative`; `bool` explicitly rejected before the `int` check) | `ChunkFormatError` |
| Crawl artifact only: `content` is empty and `code_blocks` is also empty (cross-field rule) | `ChunkFormatError` |

For the full per-field Required/Nullable/Conditional classification referenced above,
see the canonical table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).
```
Repository evidence: `scripts/rag/exceptions.py:27` (`ChunkFormatError` definition);
`scripts/rag/ingestion/pipeline_utils.py:105-145` (`read_crawl_json()` raise sites:
read/parse/type/missing-key/cross-field); `:168-204` (`read_chunk_json()` raise sites:
read/parse/type/missing-key/unknown-key); `:53-97` (validator function definitions) —
all confirmed by direct read during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code or behavior change. The added link depends on row 2's
canonical table existing — verify it resolves after row 2's edit lands (per this
Plan's Validation plan link check).

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
This document contains a section stating that both canonical readers raise
`ChunkFormatError` on the listed conditions (missing keys, invalid types, `chunk_index`
bool/negative rejection, and the crawl-only cross-field rule).

## Out of scope
- The existing `Crawler`, `ChunkSplitter`, `RagIngester`, `RagPipeline` tables and
  `Implementation Notes` section.
- Any change to `scripts/rag/exceptions.py` or `scripts/rag/ingestion/pipeline_utils.py`.

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md
