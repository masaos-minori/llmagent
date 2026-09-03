## Goal
State `read_chunk_json()` as the canonical reader for chunk artifacts used by
`RagIngester` (`REQ-003`), and document that a missing required field or invalid type
raises `ChunkFormatError`, correcting this document's existing inaccurate description
of that failure mode (`REQ-004`).

## Scope
- **In scope**: add a canonical-reader statement (reader, caller, method) to section
  "4.1 Class Overview" or "4.2 Detailed Behavior"; correct the existing "4.6 Error
  Handling" table's "Artifact validation failure" row, which currently misdescribes the
  failure as "skips the chunk as an embedding failure" — actual behavior is a
  whole-URL-group failure via `IngestUrlResult.validation_failure()`.
- **Out of scope**: the full field-contract table (row 2's responsibility, this
  document links to it); modifying `scripts/rag/ingestion/ingester.py`; the pre-existing
  duplicate section-header structure in this document (sections 4, 4a, 4c repeat the
  same heading text — not in this Plan's scope).

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Add the canonical-reader statement to "4.1 Class Overview" (the class-level summary),
  since `_read_chunk_json()`/`read_chunk_json()` is a `RagIngester`-level fact, not a
  detail specific to any one behavior bullet in 4.2.
- Correct rather than merely append to the existing 4.6 table row, per adversarial
  verification during this document's creation: `scripts/rag/ingestion/ingester.py:207-224,242`
  shows `ingest_url_group()` catches `ChunkFormatError` from `_read_chunk_json()` and
  returns `IngestUrlResult.validation_failure(url, chunk_files)` — which fails the
  **entire URL's chunk group** (`n_failed=len(chunk_files)`, `n_success=0`), not a
  single chunk, and does **not** increment `n_embed_failed` (so it is not "an embedding
  failure"); no `logger.warning` call exists on this path (confirmed by reading
  `ingest_url_group()` in full — the only nearby `logger.warning`/`logger.exception`
  calls in this file are for a post-ingestion consistency check and for exceptions
  escaping `ingest_url_group()` entirely, a different path). The existing row's "Logs a
  WARNING; skips the chunk as an embedding failure" wording is stale and must be
  corrected, not left standing alongside the new REQ-004 statement.

## Alternatives considered
- Leave the existing 4.6 row unchanged and only add a new row/sentence for REQ-004:
  rejected — the existing row already claims to describe artifact-validation-failure
  behavior, so leaving it as-is would create two contradictory descriptions of the same
  event in the same document.

## Implementation
### Target file
`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure
1. Extend "### 4.1 Class Overview" with a canonical-reader statement.
2. Replace the "Artifact validation failure" row in the first "### 4.6 Error Handling"
   table (the duplicate 4.6 tables under sections 4a/4c are out of scope — see Out of
   scope) with an accurate description and a link to the field-contract table.

### Method
Use `Edit` for each of the two changes, anchored on the exact existing text shown below.

### Details
**Change 1** — append to the end of the "### 4.1 Class Overview" paragraph (after "For
a complete list of dataclasses and public methods, see
`scripts/rag/ingestion/ingester.py`."):
```
`read_chunk_json()` (`scripts/rag/ingestion/pipeline_utils.py:163`) is the canonical
reader for chunk-stage JSON artifacts; `RagIngester._read_chunk_json()`
(`scripts/rag/ingestion/ingester.py:344`, calling `read_chunk_json()` at line 346) is
its wrapper, used at `ingester.py:222,240`. A missing required key or invalid field
type raises `ChunkFormatError` — see [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md)
and the canonical field-contract table in
[03_rag_02_03_ingestion_pipeline-chunksplitter.md](03_rag_02_03_ingestion_pipeline-chunksplitter.md).
```

**Change 2** — in the first "### 4.6 Error Handling" table (the one immediately under
section "## 4. RagIngester", not the duplicate tables under "## 4a."/"## 4c."), replace
the row:
```
| Artifact validation failure | Logs a `WARNING`; skips the chunk as an embedding failure |
```
with:
```
| Artifact validation failure (`ChunkFormatError` from `read_chunk_json()`) | The entire URL's chunk group is marked failed via `IngestUrlResult.validation_failure()` (`n_failed = len(chunk_files)`, `n_success = 0`); not counted as an embedding failure (`n_embed_failed` unchanged); no `WARNING` is logged at this layer |
```
Repository evidence: `scripts/rag/ingestion/ingester.py:207-224` (`ingest_url_group()`
catching `ChunkFormatError` at the first-chunk read and returning
`IngestUrlResult.validation_failure`), `:238-242` (same catch for every subsequent
chunk in the group), `:58-62` (`IngestUrlResult.validation_failure()` definition:
`n_failed=len(chunk_files)`, `n_success=0`, `n_embed_failed` defaults to `0`) — all
confirmed by direct read during this document's creation; no `logger.warning`/
`logger.exception` call found between lines 207-265 of `ingester.py` (the file's only
other `logger.warning`/`logger.exception` calls, at lines 195, 197, and 384, are for an
unrelated post-ingestion consistency check and for exceptions escaping
`ingest_url_group()` entirely — a different path from a caught `ChunkFormatError`).

## Compatibility considerations
N/A: documentation-only; no code or behavior change. This is a factual correction to an
existing table row, not new content contradicting a design decision — no other
document depends on the corrected wording.

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
"4.1 Class Overview" states `read_chunk_json()` as canonical chunk-artifact reader and
`RagIngester` as its caller; the first "4.6 Error Handling" table's "Artifact
validation failure" row accurately reflects `IngestUrlResult.validation_failure()`
behavior instead of the prior "skips the chunk as an embedding failure" claim.

## Out of scope
- The full field-contract table (row 2's responsibility).
- The duplicate "4.6 Error Handling" tables under this document's "## 4a." and "## 4c."
  sections, and this document's pre-existing duplicate-header structure generally.
- Any change to `scripts/rag/ingestion/ingester.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-172900 | 20260903-172900 | Adversarially re-verified all cited line numbers/behavior against current `ingester.py` (`IngestUrlResult.validation_failure()`, `n_embed_failed` default, logger call locations) — exact match. Both duplicate "4.1"/"4.6" sections exist as described (pre-existing, out of scope); edited only the first occurrence of each via precise line-targeted replacement (Edit's string match was ambiguous across the two identical duplicate blocks) |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-172900 | 20260903-172900 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: pre-existing "3 H1 headings" finding confirmed via stash-diff to predate this edit (out of scope). `check_docs_consistency.py --domain rag`: no findings for this file |
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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20260902-143328_ragcontract_align_rag_artifact_contract_with_strict_reader_behavior.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085152_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-121706
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
