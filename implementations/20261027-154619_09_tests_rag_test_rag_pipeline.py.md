# Implementation Procedure: Rename the two fixture occurrences in `tests/rag/test_rag_pipeline.py`

## Goal

Rename the fixture key spellings in `tests/rag/test_rag_pipeline.py` so the pipeline regression
suite runs against the renamed config field with identical logic (REQ-004, AC-6).

## Scope

- Two occurrences (verified 2026-10-27): `rag_service_url=""` kwargs at L186 and L262.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07).
- Overlap risk recorded in the Plan Risks: this file is also edited by a rag001 Plan procedure
  (appended tests); the fixture-key rename at L186/L262 is disjoint from appended test
  functions; second implementer rebases.

## Design decisions

- Mechanical rename only (Plan Design "mechanical propagation"): keyword arguments bind to the
  renamed `RagConfigImpl` field.

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/rag/test_rag_pipeline.py`

### Procedure

1. Rename the `rag_service_url=""` keyword at L186 (verified) to
   `rag_query_service_url` (new).
2. Rename the `rag_service_url=""` keyword at L262 (verified) to the new spelling.

### Method

Two keyword-token renames; empty-string values unchanged.

### Details

- N/A: both occurrences are fixture-construction kwargs; nothing else in the file references
  the key (grep verified 2026-10-27).

## Compatibility considerations

- Test-only change; behavior identical with renamed fixtures (AC-3, AC-6).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_pipeline.py` — green after Phase 2 rows land.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file; AC-6: suite logic
  unchanged.

## Out of Scope

- Any test additions from the rag001 Plan (separate procedures) and all other rename rows.

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
- **Related target files**: tests/rag/test_rag_pipeline.py
