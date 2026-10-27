# Implementation Procedure: Rename the delegation check in `RagPipeline`

## Goal

Rename the reader that selects HTTP-delegation vs in-process mode in `scripts/rag/pipeline.py`
to the new key spelling, with behavior unchanged (REQ-002, REQ-006).

## Scope

- Two occurrences in `scripts/rag/pipeline.py` (verified): the comment at L241 and the
  delegation check `if rag_url := self._cfg.rag_service_url:` at L243.
- No logic, fallback, or result-kind handling change.

## Assumptions

- Part of the single mass rename of this Plan; the check must reference the renamed protocol
  attribute from `scripts/shared/types.py` (sibling row) in the same implementation sequence.
- Semantics preserved: empty/absent value still means "no HTTP delegation, run in-process"
  (REQ-006, AC-3).

## Design decisions

- Comment rename keeps the existing wording pattern ("HTTP mode: delegate to external RAG
  service when <key> is configured") — pure token substitution (Plan Design: mechanical
  propagation).

## Alternatives considered

- N/A: reader rename fixed by REQ-002.

## Implementation
### Target file

`scripts/rag/pipeline.py`

### Procedure

1. Rename `self._cfg.rag_service_url` in the delegation check (L243, verified) to the new
   spelling `rag_query_service_url` (new).
2. Rename the key named in the L241 comment.

### Method

Two identifier/token renames; the walrus binding `rag_url` and all downstream delegation and
fallback code stay untouched.

### Details

- `call_rag_service()` and `_REQUEST_TIMEOUT_SECONDS` semantics are unchanged by this row
  (they belong to no rename row; REQ-003 boundary).

## Compatibility considerations

- N/A: private attribute access; behavior identical with renamed fixtures (AC-3).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_http_mode.py tests/rag/test_pipeline_http_result_kind.py`
  — HTTP-mode and result-kind regression green after the test rename rows land.
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence in this file; AC-3: in-process mode preserved
  when the renamed key is empty/absent.

## Out of Scope

- Test fixture renames (own procedure documents) and `call_rag_service` semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: regression tests only |
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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: scripts/rag/pipeline.py
