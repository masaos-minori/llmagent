## Goal

Document the tier/rule precedence as implemented, the protected-path scope relative to `allowed_root`,
and the display-only nature of `role` in the approval-configuration guide (REQ-002, REQ-005, REQ-010).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- Existing deny-all statements at `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md:103,127`
  are correct and stay.
- The `role` claim must be confirmed against `scripts/shared/mcp_config.py` (Plan Phase 2 step) and
  recorded here without duplicating `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
  (a reference document this document must link to, not modify).

## Design decisions
- Describe precedence in config terms (what a key does), linking to the canonical approval-flow document
  (row 21) for the algorithm rather than restating it.
- Protected-path scope is stated as the approved DT-06 Option A semantics.

## Alternatives considered
Restating the full `classify_risk()` algorithm here — rejected; it would create a second canonical
source for the same claim (AC-010).

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
### Procedure
1. Add the precedence note: `approval_risk_rules` decide the level when a tool is listed;
   `tool_safety_tiers` is consulted only when no rule matches, and drives plan-mode blocking.
2. Add the protected-path scope note (escalation inside the jail; jail denial outside it).
3. Record the confirmed display-only nature of `role`, linking to the MCP config-field document.
### Method
Three short subsections in the existing configuration-guide structure.
### Details
- Keep the `role` statement non-normative: it describes display, not enforcement.

## Compatibility considerations
Phase 2 (the `role` confirmation) and Phase 5 (approved posture) both touch this file; the regenerated
API reference is unaffected (it renders code docstrings only).

## Security considerations
Must not imply that protected paths discriminate inside the jail or that `role` gates execution.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
Each claim (precedence, protected-path scope, `role`) resolves to exactly one canonical source registered
in row 32 (AC-002, AC-005, AC-010).

## Out of Scope
`scripts/shared/mcp_config.py` and the MCP config-field document (reference only), `config/agent.toml` (row 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the precedence, scope, and `role` notes per Procedure | Completed | 20261119-080149 | 20261119-080149 | Three notes added: precedence paragraph (Risk Rules), protected-path scope bullet (Escalation subsection), `role` display-only paragraph (Agent-side MCP Fields). `role` confirmed display-only against `scripts/shared/mcp_config.py` (consumed only by `cmd_mcp.py` and `services/mcp_status.py`); links to agent_06_02 (canonical order) and mcp_06_02 (field semantics), neither restated |
| 3 | Run the documentation checkers (`routing.md` Tools) | Completed | 20261119-080149 | 20261119-080149 | check_docs_quality / check_docs_structure / check_docs_consistency --domain agent pass; linked mcp_06_02 document exists |

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
- **Requirement ID**: `REQ-002` (evaluation order), `REQ-005` (concurrency posture), `REQ-010` (canonical source)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
