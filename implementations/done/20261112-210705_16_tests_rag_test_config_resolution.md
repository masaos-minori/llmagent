## Goal

Remove `rag_pipeline_service_url` from the fixtures in `tests/rag/test_config_resolution.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Design decisions

N/A: delete one dict entry and two keyword arguments.

## Implementation
### Target file
`tests/rag/test_config_resolution.py`

### Procedure
Delete the dict entry at line 44 and the keyword arguments at lines 90 and 216.

### Method
Edit.

### Details
1. Remove the dict entry at line 44:

```
        "rag_pipeline_service_url": None,
```

2. Remove the keyword argument at line 90:

```
        rag_pipeline_service_url=None,
```

3. Remove the keyword argument at line 216:

```
        rag_pipeline_service_url=None,
```

## Validation plan

- `uv run pytest tests/rag/test_config_resolution.py` passes.

## Completion criteria

The entry and both keywords are gone from `tests/rag/test_config_resolution.py`.

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
- **Requirement ID**: REQ-002 — remove the key from the resolution-test fixtures
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: tests/rag/test_config_resolution.py
