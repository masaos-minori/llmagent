## Goal

Remove the `rag_pipeline_service_url=None,` keyword argument from the `RagConfig(...)` construction in `tests/agent/test_rag_get_cfg.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Design decisions

N/A: delete one keyword argument.

## Implementation
### Target file
`tests/agent/test_rag_get_cfg.py`

### Procedure
Delete the keyword at line 36.

### Method
Edit.

### Details
Remove exactly this line:

```
        rag_pipeline_service_url=None,
```

## Validation plan

- `uv run pytest tests/agent/test_rag_get_cfg.py` passes.

## Completion criteria

The keyword is gone from `tests/agent/test_rag_get_cfg.py`.

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
- **Requirement ID**: REQ-002 — remove the keyword from config construction
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: tests/agent/test_rag_get_cfg.py
