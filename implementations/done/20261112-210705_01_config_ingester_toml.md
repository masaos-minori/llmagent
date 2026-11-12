## Goal

Delete the unused `rag_pipeline_service_url` key from `config/ingester.toml` (REQ-002 / AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The deployed `/opt/llm/config/ingester.toml` is out of scope; the ingester never validates this file and reads the key via `cfg.get(..., "")`, so its absence is harmless.
- `ConfigLoader.restrict_to("ingester.toml")` does not require this key; removing it keeps the file loadable.

## Design decisions

- Delete only the key line and its immediately preceding comment line; leave surrounding keys untouched.

## Alternatives considered

N/A: single-key deletion in a config file; no design trade-off.

## Implementation
### Target file
`config/ingester.toml`

### Procedure
Delete the comment at line 27 and the key at line 28.

### Method
Edit.

### Details
Remove exactly these two lines (line 27 comment, line 28 key):

```
# Base URL of the rag-pipeline MCP server for cache invalidation
rag_pipeline_service_url = "http://127.0.0.1:8010"
```

Do not touch the earlier `strict_artifact_validation` NOTE block above.

## Compatibility considerations

None beyond REQ-002: no other file reads this key from the TOML.

## Security considerations

N/A: removing a dead configuration key.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `rg -n "rag_pipeline_service_url" config` returns nothing.
- `uv run pytest tests/rag/ingestion` passes.

## Completion criteria

`config/ingester.toml` contains no `rag_pipeline_service_url` line or its comment.

## Out of Scope

The deployed production copy of `ingester.toml`.

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
- **Requirement ID**: REQ-002 — remove `rag_pipeline_service_url` from `config/ingester.toml`
- **Source issue**: issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-210705
- **Related target files**: config/ingester.toml
