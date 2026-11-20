## Goal
- Delete the removed-key NOTE block from `config/rag_pipeline_mcp_server.toml`, keeping every configuration value byte-identical (Plan REQ-004: delete the NOTE block; keep all values).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Re-run the Plan AC-1 history search on this file immediately before editing; if the block is already gone, skip it and record the evidence (source issue AI Implementation Instruction). Verified present on 20261120 (NOTE block at lines 24-30).

## Design decisions
- Delete the block outright: the guardrail against re-adding `host` / `port` / `http_timeout` lives in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py` and the server's config loading, not in this comment (Plan Risks mitigation).

## Alternatives considered
- Keep a one-line "removed keys" pointer — rejected: the Current-Specification-Only policy bars removal history in active config; git and the plans hold the record.

## Implementation
### Target file
- `config/rag_pipeline_mcp_server.toml`

### Procedure
- Delete the full NOTE block anchored at `# NOTE: host, port, and http_timeout were removed` (all comment lines through the "Re-add only alongside an implementation that actually reads them." line), leaving exactly one blank line between `sqlite_busy_timeout_ms = 30000` and the following `# auth_token:` comment.

### Method
- Locate the block at edit time with `rg -n "NOTE:" config/rag_pipeline_mcp_server.toml`; do not renumber by stale line numbers.
- Do not touch any `key = value` line, the `# auth_token:` comment, or any `[mcp_servers.*]` section.

### Details
- Every value must remain byte-identical; confirm with `git diff -- config/rag_pipeline_mcp_server.toml` that the diff is comment-only.

## Compatibility considerations
- Comment-only edit; the server loads this file via `RAG_PIPELINE_OWN_CONFIG_FILE` in `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, which parses values only. `docs/21_rag/rag_05_01-configuration-reference.md` (Plan Reference Files) carries the canonical key descriptions and does not depend on the NOTE text.

## Security considerations
- N/A: no value, token, or endpoint change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `git diff -- config/rag_pipeline_mcp_server.toml` comment-only review (Plan Validation plan).
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_removed_config_keys_rejected.py tests/mcp_servers/rag_pipeline/test_rag_pipeline_models.py` (Plan AC-5).
- History search re-run on this file returns no hit for the Plan AC-1 pattern.

## Completion criteria
- No removed-key note, removal date, or re-add instruction remains in this file; every value is byte-identical to before; the removed-key rejection and model tests pass unchanged.

## Out of Scope
- Any value change or key addition; any other config file; the `auth_token` comment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120-205834 | 20261120-205907 | changed config/rag_pipeline_mcp_server.toml (NOTE block removed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) with the diff review and pytest set named in the Validation plan | Completed | 20261120-205907 | 20261120-210852 | stale-detector clean; git diff comment-only; pytest rag_pipeline removed-keys + models 19 passed; history re-search no hit; full-suite pending batch end |

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
- **Requirement ID**: `REQ-004` (delete the rag_pipeline_mcp_server.toml removed-key NOTE block; keep all values)
- **Source issue**: issues/20261117-123022_adrchk022_history-comment-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-201816_adrchk022_history-comment-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-202848
- **Related target files**: `config/rag_pipeline_mcp_server.toml`