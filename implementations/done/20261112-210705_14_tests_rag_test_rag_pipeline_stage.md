## Goal

Remove the `rag_pipeline_service_url` field and keyword argument in `tests/rag/test_rag_pipeline_stage.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Design decisions

N/A: delete one field declaration and one keyword argument.

## Implementation
### Target file
`tests/rag/test_rag_pipeline_stage.py`

### Procedure
Delete the field at line 44 and the keyword argument at line 74.

### Method
Edit.

### Details
1. Remove the field declaration at line 44:

```
    rag_pipeline_service_url: str | None = None
```

2. Remove the keyword argument at line 74:

```
        rag_pipeline_service_url=None,
```

## Validation plan

- `uv run pytest tests/rag` passes.

## Completion criteria

Both the field and the keyword are gone from `tests/rag/test_rag_pipeline_stage.py`.

## Out of Scope

N/A

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |

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
- **Requirement ID**: REQ-002 — remove the field and keyword from the test double
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: tests/rag/test_rag_pipeline_stage.py
