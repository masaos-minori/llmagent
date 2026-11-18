## Goal

Fix the Tool Call State Recording paragraph in
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`: the recorded
`retry_class` is attributed to `shared/mcp_dedup.py::retry_class` (owned by the toml),
but the Agent path resolves it from `RETRYABLE_TOOLS`. (`REQ-007` guide names the
wrong source)

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3 docs update)

## Assumptions

- Evidence for the correct claim: `scripts/agent/tool_runner.py:163-172,188` uses
  `RETRYABLE_TOOLS` membership (config isolation — the Agent never reads
  `mcp_dedup.toml`).
- Lands after procedure 01 in `seq` order so the wording matches the fixed
  `tool_constants.py` comments.

## Design decisions

- One sentence edit at `:81`; describe the mechanism (owner constant, load-validated
  toml mirror on the dispatcher side) without per-tool values.

## Alternatives considered

- N/A: single-sentence claim fix.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
1. In "Tool Call State Recording" (`:81`), replace "The recorded `retry_class` comes
   from `shared/mcp_dedup.py::retry_class` (owned by `config/mcp_dedup.toml`)" with a
   statement that the recorded `retry_class` comes from `RETRYABLE_TOOLS` membership in
   `shared/tool_constants.py`, noting `config/mcp_dedup.toml [retry_class]` is the
   dispatcher-side mirror validated against the constant at load.

### Method
Keep the surrounding sentences (idempotency-key derivation, best-effort recorder)
untouched.

### Details
Do not name `tool_runner.py` line numbers in the guide (docs content policy: canonical
symbols, not implementation detail).

## Compatibility considerations

- N/A: docs-only change.

## Security considerations

- N/A: docs-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` (routing.md Tools: docs scope) — all clean.

## Completion criteria

- The guide attributes the Agent-side recorded `retry_class` to `RETRYABLE_TOOLS` and
  describes the toml as the load-validated mirror (AC-6).

## Out of Scope

- `docs/41_db/db_03_07_...` (covered by procedure 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the source-attribution sentence | Pending | — | — | |
| 2 | Run the docs checkers (routing.md Tools, docs scope) | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (Agent guide names the correct retry_class source)
- **Source issue**: issues/20261117-123018_adrchk018_mcp-retry-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-153543_adrchk018_mcp-retry-classes.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162033
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
