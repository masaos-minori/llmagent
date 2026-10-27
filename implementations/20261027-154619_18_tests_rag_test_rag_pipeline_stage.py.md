# Implementation Procedure: Rename the local stub dataclass field in `tests/rag/test_rag_pipeline_stage.py`

## Goal

Rename the two key occurrences in the stage-level test module's local config stub so the
structural-conformance edge to the renamed `RagConfig` protocol holds (REQ-004, AC-6).

## Scope

- Two occurrences (verified 2026-10-27): the local dataclass field declaration
  `rag_service_url: str = ""` at L33 and the fixture kwarg `rag_service_url=""` at L65.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07), specifically the `RagConfig`
  protocol rename in `scripts/shared/types.py` — the local stub satisfies the protocol
  structurally, so its field name must match the new protocol attribute exactly.

## Design decisions

- Mechanical rename only (Plan Design "mechanical propagation"); mypy validates the structural
  conformance after both rows land.

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/rag/test_rag_pipeline_stage.py`

### Procedure

1. Rename the dataclass field `rag_service_url: str = ""` at L33 (verified) to the new spelling
   `rag_query_service_url` (new), default `""` unchanged.
2. Rename the fixture kwarg `rag_service_url=""` at L65 (verified) to the new spelling.

### Method

Two identifier-token renames.

### Details

- N/A: grep verified exactly two standalone occurrences in this file.

## Compatibility considerations

- Test-only change; stage-level behavior identical (AC-3: `""` still means in-process).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_pipeline_stage.py` — green after Phase 2 rows land.
- `uv run mypy --no-namespace-packages scripts/` plus test-side type checks — stub conforms to
  the renamed protocol.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file.

## Out of Scope

- The `scripts/shared/types.py` protocol rename (own procedure document) and all other rows.

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
- **Related target files**: tests/rag/test_rag_pipeline_stage.py
