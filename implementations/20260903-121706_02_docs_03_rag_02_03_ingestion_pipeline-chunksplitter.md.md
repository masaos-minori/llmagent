## Goal
Establish this document as the single canonical location for the complete crawl/chunk
artifact-field contract (`REQ-011`), classifying every field as Required, Nullable, or
Conditional, consistently and separately per artifact type (`REQ-006`), and
distinguishing missing keys from explicit `null` and empty-string values (`REQ-007`).

## Scope
- **In scope**: add a new subsection containing the full field-contract table for both
  crawl artifacts (`read_crawl_json()`, 8 required keys) and chunk artifacts
  (`read_chunk_json()`, 13 required keys), with per-field Required/Nullable/Conditional
  classification and the validator each field is checked against.
- **Out of scope**: modifying `scripts/rag/ingestion/pipeline_utils.py`; modifying the
  chunking-algorithm sections (3.1–3.3, 3.5–3.7) of this document; adding the
  canonical-reader cross-link statements in the other seven target documents (each of
  those is its own row in this Plan's Implementation Target Files).

## Assumptions
- This document is the Plan's chosen canonical location (per the Plan's Assumptions
  section) — the other six affected `docs/03_rag_*.md` documents (rows 1, 3–7 of this
  Plan) link here rather than duplicating this table.

## Design decisions
- Insert the contract table as a new "### 3.4a" subsection immediately after the
  existing "### 3.4 Output JSON Format" section and before "### 3.5 Error Handling" —
  this keeps the new content adjacent to the existing chunk-output-format example
  without restructuring this document's pre-existing (and independently
  out-of-scope) duplicate-header structure (sections 3, 3a, 3b repeat the same
  heading text; not touched by this change).
- Classify strictly by which `pipeline_utils.py` validator function is applied to each
  field — `_validate_str` → Required, `_validate_str_or_empty` → Conditional,
  `_validate_nullable_str` → Nullable, `_validate_list_of_str`/`_validate_int_non_negative`
  → Required — rather than inventing a separate classification rubric, so the table
  stays directly traceable to code (see `skills/DESIGN.md` Evidence labels: mark as
  Explicit in code).

## Alternatives considered
- Keep per-document field tables (status quo): rejected — this is exactly the
  duplication `REQ-011` requires eliminating.
- Classify fields by DTO type hints in `scripts/rag/models_data.py::ChunkDocument`
  alone (e.g. `str | None` → Nullable) instead of by validator function: rejected —
  the DTO's own type hints do not distinguish the `Conditional` (empty-string-allowed)
  case from `Required`, since both are typed `str`; the validator function is the only
  source that distinguishes all three classifications.

## Implementation
### Target file
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
Insert a new "### 3.4a Canonical Artifact-Field Contract" subsection after the existing
"### 3.4 Output JSON Format" section (ends before the current "### 3.5 Error Handling"
heading).

### Method
Use `Edit`, anchoring on the exact text of the current "### 3.5 Error Handling" heading
line to insert immediately before it, so the existing "### 3.4 Output JSON Format"
content is left untouched.

### Details
Insert the following content immediately before the `### 3.5 Error Handling` heading:

```markdown
### 3.4a Canonical Artifact-Field Contract

This is the canonical field-contract table for both artifact types in the RAG
ingestion pipeline — other `docs/03_rag_*.md` documents link here instead of
duplicating this table. Classification is derived directly from the validator each
field is checked against in `scripts/rag/ingestion/pipeline_utils.py`
(`read_crawl_json()` / `read_chunk_json()`); both raise `ChunkFormatError` (see
[03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md))
on a missing required key or an invalid field type.

**Missing key vs. `null` vs. empty string**: a key absent from the JSON payload is
always rejected by an exact-key-set check, regardless of classification below —
`null`/empty-string tolerance applies only once the key is present. `null` is accepted
only for `Nullable` fields; empty string is accepted only for `Conditional` fields;
`Required` fields accept neither.

#### Crawl artifacts (8 required keys) — reader: `read_crawl_json()`

| Field | Classification | Validator | Notes |
|---|---|---|---|
| `url` | Required | `_validate_str` | non-empty string |
| `content` | Conditional | `_validate_str_or_empty` | empty string allowed only when `code_blocks` is non-empty (cross-field rule) |
| `title` | Nullable | `_validate_nullable_str` | defaults to `""` when `null` |
| `lang` | Required | `_validate_str` | any non-empty string accepted; the `en`/`ja` value set (`LanguageCode`) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended) |
| `code_blocks` | Required | `_validate_list_of_str` | list of `str`; may be an empty list |
| `etag` | Nullable | `_validate_nullable_str` | optional upstream metadata, not always available at crawl time |
| `last_modified` | Nullable | `_validate_nullable_str` | optional upstream metadata, not always available at crawl time |
| `fetched_at` | Required | `_validate_str` | non-empty string |

Crawl artifacts do not carry `normalized_content` / `chunk_index` / `source_file` /
`chunk_type` / `chunking_strategy` as input keys — `read_crawl_json()` sets these
internally rather than reading them: `chunking_strategy="text"`,
`normalized_content=None`, `chunk_index=0`, `source_file=""`, `chunk_type=""` (these
crawl-stage values do not exist yet).

#### Chunk artifacts (13 required keys) — reader: `read_chunk_json()`

| Field | Classification | Validator | Notes |
|---|---|---|---|
| `url` | Required | `_validate_str` | non-empty string |
| `content` | Required | `_validate_str` | non-empty string — no cross-field exception here, unlike crawl artifacts |
| `title` | Nullable | `_validate_nullable_str` | defaults to `""` when `null` |
| `lang` | Required | `_validate_str` | same non-enforcement note as crawl artifacts |
| `code_blocks` | Required | `_validate_list_of_str` | list of `str`; may be an empty list |
| `etag` | Nullable | `_validate_nullable_str` | optional upstream metadata |
| `last_modified` | Nullable | `_validate_nullable_str` | optional upstream metadata |
| `normalized_content` | Nullable | `_validate_nullable_str` | Japanese-only Sudachi normalization; `null` for English/code chunks |
| `chunk_index` | Required | `_validate_int_non_negative` | non-negative int; `bool` is explicitly rejected before the `int` check |
| `source_file` | Conditional | `_validate_str_or_empty` | empty string allowed unconditionally; otherwise the crawler output filename stem without `.json` |
| `chunk_type` | Conditional | `_validate_str_or_empty` | `"text"` or `"code"` by convention; empty string allowed unconditionally; no enum enforced in code |
| `chunking_strategy` | Required | `_validate_str` | `"text"` or `"heading"` by convention; no enum enforced in code (Needs confirmation: whether a closed value set is intended) |
| `fetched_at` | Required | `_validate_str` | non-empty string |

`read_chunk_json()` additionally rejects any key beyond these 13, except
`schema_version`, `artifact_type`, and `created_by`, which are accepted but not
validated or mapped onto `ChunkDocument`'s own fields.
```

Repository evidence for this table: `scripts/rag/ingestion/pipeline_utils.py:100-160`
(`read_crawl_json`), `:163-233` (`read_chunk_json`), `:53-97` (validator definitions),
confirmed by direct read during this document's creation; `scripts/rag/models_data.py:31-47`
(`ChunkDocument` field set, confirming `str | None` type hints align with the Nullable
classification above).

## Compatibility considerations
N/A: documentation-only; no code or artifact-format change. Once this section exists,
rows 1, 3–7 of this Plan link to it — sequencing note: if those rows' edits land before
this row's, their links will be temporarily broken until this row's edit completes;
`check_docs_quality.py`'s link check (Plan Validation plan) catches any resulting
broken-link finding.

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved. Reverting this row's addition would break the links added by
rows 1, 3–7 — coordinate any rollback across all eight documents in this Plan.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan); additionally, manually grep for the Required/Nullable/Conditional table across
all 8 target documents to confirm this is the only one containing the full table (per
Plan Validation plan's manual cross-check row).

## Completion criteria
This document contains exactly one full crawl-artifact table (8 rows) and one full
chunk-artifact table (13 rows), each field classified Required/Nullable/Conditional per
its `pipeline_utils.py` validator, with the missing-key/null/empty-string distinction
stated explicitly, and no other target document in this Plan duplicates this table.

## Out of scope
- Any change to `scripts/rag/ingestion/pipeline_utils.py`, `chunk_splitter.py`, or
  `scripts/rag/models_data.py`.
- Restructuring this document's pre-existing duplicate section headers (sections 3,
  3a, 3b) — out of this Plan's scope.
- The canonical-reader cross-link statements added to the other seven documents
  (their own rows in this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-172700 | 20260903-172700 | Adversarially re-verified every field/classification/validator against current `pipeline_utils.py` (`read_crawl_json`, `read_chunk_json`, all 5 validator functions) and `models_data.py::ChunkDocument` — exact match, no drift |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-172700 | 20260903-172700 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: pre-existing "3 H1 headings" finding confirmed via stash-diff to predate this edit (out of scope, per this document's own Design decisions). `check_docs_consistency.py --domain rag`: 2 pre-existing warnings, both outside this edit's diff scope. Manual cross-check: `grep` confirms this is the only `docs/03_rag_*.md` file containing the full field-contract table |
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
- **Requirement ID**: REQ-006, REQ-007, REQ-011
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md
