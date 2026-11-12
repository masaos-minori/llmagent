## Goal

Remove the `rag_pipeline_service_url` field from the `RagConfig` dataclass in `scripts/shared/types.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Assumptions

- `RagConfig` is a frozen-ish dataclass consumed by resolution and models; dropping one field breaks every constructor that passes it as a keyword — those are fixed in the companion test rows of this Plan.

## Design decisions

- Delete only the field declaration line; keep field order and the rest of the dataclass intact.

## Alternatives considered

N/A: single-field deletion in a dataclass; no design trade-off.

## Implementation
### Target file
`scripts/shared/types.py`

### Procedure
Delete the field declaration at line 109.

### Method
Edit.

### Details
Remove exactly this line inside the `RagConfig` dataclass:

```
    rag_pipeline_service_url: str | None
```

It sits between `embed_workers: int` and `mqe_prompt_template: str`.

## Compatibility considerations

Every test that builds `RagConfig(**{...})` with this keyword must drop it (this Plan's test rows).

## Security considerations

N/A: removing a dead config field.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_config_resolution.py` passes after the test fixtures are updated.
- `uv run ruff format` / `ruff check` clean on `scripts/shared/types.py`.

## Completion criteria

`scripts/shared/types.py` has no `rag_pipeline_service_url` field in `RagConfig`.

## Out of Scope

Any consumer that still passes the keyword — fixed by the test rows of this Plan.

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
- **Requirement ID**: REQ-002 — remove `rag_pipeline_service_url` field from `RagConfig`
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: scripts/shared/types.py
