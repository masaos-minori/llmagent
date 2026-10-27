# Implementation Procedure: Rename the `RagConfigImpl` fixture kwarg in `tests/agent/test_rag_get_cfg.py`

## Goal

Rename the key in the agent config-getter test's typed `_RAG_CFG_BASE` fixture so it constructs
the renamed `RagConfigImpl` field with identical semantics (REQ-004, AC-6).

## Scope

- One occurrence (verified 2026-10-27): the keyword `rag_service_url=""` at L26 inside the
  module-level `_RAG_CFG_BASE = RagConfigImpl(...)` construction.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07). This is a typed keyword-argument
  construction of `RagConfigImpl` (not a MagicMock), so a missed rename is a `TypeError` at
  import time once row 02 (`models_config.py`) lands — these rows must land in one sequence.

## Design decisions

- Mechanical rename only (Plan Design "mechanical propagation").

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/agent/test_rag_get_cfg.py`

### Procedure

1. Rename the keyword `rag_service_url=""` at L26 (verified) to the new spelling
   `rag_query_service_url` (new); value `""` unchanged.

### Method

Single keyword rename in the `_RAG_CFG_BASE` construction.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Test-only change; config-construction behavior identical (AC-3: `""` still means in-process).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_rag_get_cfg.py` — green after Phase 2 rows land.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file.

## Out of Scope

- `models_config.py` dataclass rename (own procedure document) and all other rename rows.

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
- **Related target files**: tests/agent/test_rag_get_cfg.py
