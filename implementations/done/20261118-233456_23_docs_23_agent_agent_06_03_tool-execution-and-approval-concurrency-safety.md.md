## Goal

Name the default per-server concurrency value and the currently unlisted MCP server keys, closing REQ-005
on the documentation side.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md:47` already states that an
  unlisted server is capped at the process default.
- The default is `DEFAULT_PER_SERVER_CONCURRENCY = 8` (`scripts/shared/tool_transport_invoker.py:33`);
  `git` and `mdq` are unlisted in `config/agent.toml:71` (row 08 documents that posture as intentional).

## Design decisions
- Document the fallback rather than add config keys: adding explicit `git`/`mdq` limits would change
  runtime behavior and is out of this decision-set.

## Alternatives considered
Adding `git`/`mdq` entries to `config/agent.toml` (the other half of the Plan's Phase 2 option) —
rejected in favor of the documentation branch (row 08).

## Implementation
### Target file
`docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`
### Procedure
At `:47`, name the default value (8) and the currently unlisted keys (`git`, `mdq`), citing
`scripts/shared/tool_transport_invoker.py` as the implementation.
### Method
One-paragraph edit.
### Details
N/A: nothing beyond naming the value and keys is not inferable from REQ-005.

## Compatibility considerations
Must match the row 08 config comment; no runtime change.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
Every MCP server key in `config/agent.toml` either has an explicit limit or a named default here
(AC-005).

## Out of Scope
Concurrency values in `config/agent.toml` (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Name the default and unlisted keys at :47 | Completed | 20261119-075950 | 20261119-075950 | Fallback bullet now names `DEFAULT_PER_SERVER_CONCURRENCY = 8` and the unlisted shipped keys `git`/`mdq` (verified: 10 `[mcp_servers.*]` keys vs 8 limit entries). Matches the row 08 config comment |
| 3 | Run the documentation checkers (`routing.md` Tools) | Completed | 20261119-075950 | 20261119-075950 | check_docs_quality and check_docs_consistency --domain agent pass |

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
- **Requirement ID**: `REQ-005` (explicit concurrency posture)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/23_agent/agent_06_03_tool-execution-and-approval-concurrency-safety.md`
