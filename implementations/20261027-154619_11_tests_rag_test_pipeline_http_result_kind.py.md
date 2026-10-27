# Implementation Procedure: Rename the fixture helper and docstring in `tests/rag/test_pipeline_http_result_kind.py`

## Goal

Rename all four key occurrences in the result-kind regression file so `http_result_kind`
classification tests run against the renamed field with identical logic (REQ-004, AC-6).

## Scope

- Four occurrences (verified 2026-10-27): helper parameter at L18, assignment at L21, the
  docstring mention at L160 ("No rag_service_url -> http_result_kind=None."), and the call
  `rag_service_url=""` at L161.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07).
- This file's `test_no_http_mode` is referenced by `adr_02_06_010_rag-fallback.md` as a test
  evidence row; the function name itself does not contain the key, so the ADR link survives
  the rename untouched.

## Design decisions

- The docstring occurrence renames alongside the code (AC-1 covers every token, including
  comments/docstrings in tests).

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/rag/test_pipeline_http_result_kind.py`

### Procedure

1. Rename the helper parameter `rag_service_url` (L18, verified) to the new spelling
   `rag_query_service_url` (new), default `"http://rag.local"` unchanged.
2. Rename both tokens on L21 (verified).
3. Rename the key named in the L160 docstring (verified).
4. Rename the `rag_service_url=""` keyword at L161 (verified).

### Method

Mechanical token renames; helper defaults and all result-kind assertions unchanged.

### Details

- Grep the file after the edits to confirm zero standalone occurrences remain (the Plan counts
  4 occurrences; verification found exactly these four lines).

## Compatibility considerations

- Test-only change; result-kind semantics identical (AC-3).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_pipeline_http_result_kind.py` — green after Phase 2 rows land.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: zero standalone old-spelling tokens in this file; AC-3: in-process mode
  (`http_result_kind=None` when the key is empty) regression passes.

## Out of Scope

- The HTTP-mode fixture rename (own procedure document) and ADR test-link text (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 row; land after Phase 2 rows 01-07 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: rename only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: tests/rag/test_pipeline_http_result_kind.py
