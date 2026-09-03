## Goal
Document `chunk_index`'s non-negative-integer constraint with explicit `bool`
rejection (`REQ-005`), and the non-empty requirements for `url`/`content` plus `lang`'s
actual (unenforced) validation scope (`REQ-008`) — none of these are currently in this
constraints table.

## Scope
- **In scope**: add four new rows to the existing "Constraints Reference" table
  (`chunk_index` type constraint, `url` non-empty requirement, `content` non-empty
  requirement with the crawl-only cross-field exception, `lang` validation scope) and
  a corresponding Evidence bullet.
- **Out of scope**: the existing seven constraint rows (language detection threshold,
  chunk size/overlap, embedding dimensions, crawl depth, max crawl pages, replication)
  and their Evidence bullets; modifying `scripts/rag/ingestion/pipeline_utils.py` or
  `scripts/rag/enums.py`.

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Append the four new rows to the existing single Constraints table rather than
  creating a new section — this document's established format is one flat table plus
  an Evidence list, and these four facts are constraints of the same kind (artifact
  field validation rules) as the existing rows.

## Alternatives considered
- Create a separate "Artifact Field Constraints" section: rejected — unnecessary
  structural change; the existing table format already accommodates these rows without
  losing clarity.

## Implementation
### Target file
`docs/03_rag_05_5-constraints-reference.md`

### Procedure
Append four rows to the existing Constraints table and one bullet to the Evidence
list.

### Method
Use `Edit`, anchored on the exact existing table and Evidence-list text shown below.

### Details
**Change 1** — append rows to the table (insert after the `| Replication | ... |` row,
before the closing `|---|---|` block ends — i.e. as the new last rows of the table):
```
| `chunk_index` type constraint | Non-negative `int`; `bool` is explicitly rejected before the `int` check (`_validate_int_non_negative`) — no implicit conversion from strings or booleans |
| `url` non-empty requirement | Required non-empty string for both crawl and chunk artifacts (`_validate_str`); no fallback |
| `content` non-empty requirement | Chunk artifacts: required non-empty string (`_validate_str`), no exception. Crawl artifacts: empty string allowed only when `code_blocks` is non-empty (cross-field rule) |
| `lang` validation scope | Any non-empty string accepted at parse time (`_validate_str`); the `en`/`ja` value set defined by `LanguageCode` (`scripts/rag/enums.py`) is a convention only, not enforced by either reader (Needs confirmation: whether parse-time enforcement is intended) |
```

**Change 2** — append to the "**Evidence:**" bullet list (after the existing "Crawl
depth and max pages: ..." bullet):
```
- `chunk_index`/`url`/`content` validation, `lang` non-enforcement: Explicit in code
  (`scripts/rag/ingestion/pipeline_utils.py:53-97` validator definitions, `:100-233`
  `read_crawl_json()`/`read_chunk_json()` call sites); `LanguageCode`'s `en`/`ja`
  members are defined in `scripts/rag/enums.py` but never referenced by either reader.
```
Repository evidence: `scripts/rag/ingestion/pipeline_utils.py:90-97`
(`_validate_int_non_negative`: `bool` check precedes the `int`/non-negative check);
`:53-58` (`_validate_str`, used for `url` in both readers, `content` in chunk
artifacts); `:61-66` (`_validate_str_or_empty`, used for `content` in crawl artifacts)
and `:141-145` (crawl's cross-field rule: `if not content and not code_blocks: raise
ChunkFormatError(...)`); `scripts/rag/enums.py:11-15` (`LanguageCode` defines `EN`/`JA`
only) — confirmed no reference to `LanguageCode` exists in `read_crawl_json()`'s or
`read_chunk_json()`'s bodies (`lang = _validate_str(data, "lang", ...)` only). All
confirmed by direct read during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code or behavior change.

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
The Constraints table states `chunk_index`'s non-negative-int-with-bool-rejection
rule, `url`/`content`'s non-empty requirements (including the crawl-only cross-field
exception), and `lang`'s actual (unenforced) validation scope, each with a
corresponding Evidence entry.

## Out of scope
- The existing seven constraint rows and their Evidence bullets.
- Any change to `scripts/rag/ingestion/pipeline_utils.py` or `scripts/rag/enums.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Table rows + Evidence bullet |
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
- **Requirement ID**: REQ-005, REQ-008
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_05_5-constraints-reference.md
