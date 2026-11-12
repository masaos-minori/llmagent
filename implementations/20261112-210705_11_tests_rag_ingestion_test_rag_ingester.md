## Goal

Drop the `rag_pipeline_service_url` entry from the test configuration in `tests/rag/ingestion/test_rag_ingester.py` (REQ-002 / AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The entry is a dict literal in a test config; removing it matches the removed `RagConfig` field.

## Design decisions

N/A: delete one dict entry.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
Delete the dict entry at line 78.

### Method
Edit.

### Details
Remove exactly this line inside the test config dict:

```
        "rag_pipeline_service_url": "",
```

## Compatibility considerations

None: the field no longer exists on `RagConfig`.

## Validation plan

- `uv run pytest tests/rag/ingestion` passes.

## Completion criteria

`tests/rag/ingestion/test_rag_ingester.py` carries no `rag_pipeline_service_url` entry.

## Out of Scope

N/A

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: test-only change | — | — | |

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
- **Requirement ID**: REQ-002 — drop the key from the test configuration
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: tests/rag/ingestion/test_rag_ingester.py
