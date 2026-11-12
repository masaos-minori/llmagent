## Goal

Remove `rag_pipeline_service_url` from the key list `_ALL_FIELDS` and the default table `_DEFAULTS_FOR_ALL` in `scripts/rag/config_resolution.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Assumptions

- `_ALL_FIELDS` enumerates known fields; `_DEFAULTS_FOR_ALL` supplies defaults. Dropping the key from both keeps resolution consistent with the removed `RagConfig`/`RagConfigImpl` fields.

## Design decisions

- Remove the string literal from the set and the entry from the defaults dict; keep ordering and surrounding keys intact.

## Alternatives considered

N/A: removing one key from two literals; no design trade-off.

## Implementation
### Target file
`scripts/rag/config_resolution.py`

### Procedure
Delete the key from `_ALL_FIELDS` (line 46) and from `_DEFAULTS_FOR_ALL` (line 76).

### Method
Edit.

### Details
In `_ALL_FIELDS`, remove:

```
        "rag_pipeline_service_url",
```

In `_DEFAULTS_FOR_ALL`, remove:

```
    "rag_pipeline_service_url": None,
```

## Compatibility considerations

Consumers that passed the keyword are fixed by the test rows of this Plan.

## Security considerations

N/A: removing a dead config key.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_config_resolution.py` passes after the fixtures are updated.
- `uv run ruff format` / `ruff check` clean.

## Completion criteria

`scripts/rag/config_resolution.py` lists no `rag_pipeline_service_url` in either literal.

## Out of Scope

Consumers passing the keyword — fixed by the test rows of this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | covered by companion test rows |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002 — remove `rag_pipeline_service_url` from `_ALL_FIELDS` and `_DEFAULTS_FOR_ALL`
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: scripts/rag/config_resolution.py
