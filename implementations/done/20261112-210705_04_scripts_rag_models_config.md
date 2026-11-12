## Goal

Remove the `rag_pipeline_service_url` field from the `RagConfigImpl` dataclass in `scripts/rag/models_config.py` (REQ-002 / AC-2).

## Scope
**Release unit**: rag-config-field-removal

## Assumptions

- `RagConfigImpl` mirrors `RagConfig`; the field is read nowhere in production code.

## Design decisions

- Delete only the field declaration line; keep field order intact.

## Alternatives considered

N/A: single-field deletion in a dataclass; no design trade-off.

## Implementation
### Target file
`scripts/rag/models_config.py`

### Procedure
Delete the field declaration at line 38.

### Method
Edit.

### Details
Remove exactly this line inside the `RagConfigImpl` dataclass:

```
    rag_pipeline_service_url: str | None
```

It sits between `embed_workers: int` and `mqe_prompt_template: str`.

## Compatibility considerations

Test rows of this Plan drop the keyword from every constructor.

## Security considerations

N/A: removing a dead config field.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_config_resolution.py` passes after the fixtures are updated.
- `uv run ruff format` / `ruff check` clean.

## Completion criteria

`scripts/rag/models_config.py` has no `rag_pipeline_service_url` field in `RagConfigImpl`.

## Out of Scope

Consumers passing the keyword — fixed by the test rows of this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 2 | Add or update tests per Validation plan | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261112-215935 | 20261112-215935 | STEP: archived after verifying committed implementation (041a7beb9) |

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
- **Requirement ID**: REQ-002 — remove `rag_pipeline_service_url` field from `RagConfigImpl`
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: scripts/rag/models_config.py
