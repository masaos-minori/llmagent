# Implementation Procedure: Rename the SimpleNamespace fixture key in `tests/agent/commands/test_agent_rag.py`

## Goal

Rename the fixture config key in the agent RAG-command test so the SimpleNamespace cfg feeds
the renamed delegation attribute in `RagPipeline` with identical semantics (REQ-004, AC-6).

## Scope

- One occurrence (verified 2026-10-27): the `_make_cfg` defaults dict entry
  `"rag_service_url": "http://127.0.0.1:8010"` at L21.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07). The cfg is a `SimpleNamespace`
  consumed attribute-by-attribute by `RagPipeline`; after the `pipeline.py` delegation-check
  rename (row 04), the pipeline reads the new attribute name, so a missed rename here is an
  `AttributeError` at runtime — this file must rename in the same sequence.
- The non-empty URL value keeps the delegation-mode semantics the test asserts (AC-3 pinned
  via existing assertions, unchanged).

## Design decisions

- Mechanical rename only (Plan Design "mechanical propagation").

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/agent/commands/test_agent_rag.py`

### Procedure

1. Rename the dict key `"rag_service_url"` at L21 (verified) to the new spelling
   `rag_query_service_url` (new); value `"http://127.0.0.1:8010"` unchanged.

### Method

Single dict-key rename in the `_make_cfg` defaults.

### Details

- N/A: grep verified exactly one standalone occurrence in this file.

## Compatibility considerations

- Test-only change; agent RAG-command behavior identical.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_rag.py` — green after Phase 2 rows land.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file.

## Out of Scope

- `pipeline.py` delegation-check rename (own procedure document) and all other rename rows.

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
- **Related target files**: tests/agent/commands/test_agent_rag.py
