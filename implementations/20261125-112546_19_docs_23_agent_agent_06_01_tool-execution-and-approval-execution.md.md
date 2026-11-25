## Goal
Document the Agent-managed replay directive in one place, next to the identifier definitions.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The identifier definitions are in the section around line 81 of this document; the new text goes in the same
  section, not in a new one.

## Design decisions
- One paragraph, per `docs/00_index.md` "Document References by Task" (Agent spec scope): the replay directive is
  described where the logical call id is defined, so there is a single normative statement of the claim.

## Alternatives considered
- Documenting it in `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — rejected: that
  document's stale composed-key claim is owned by the mcpai012 final sweep, not by this Plan.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
Add the replay-directive paragraph to the identifier-definition section.

### Method
State that a reissued call is matched by tool name plus canonical argument hash against Agent-held directives,
each directive is consumed at most once, an ambiguous match is rejected at preparation, and the logical call id
never appears in the LLM-facing control text.

### Details
- Keep the existing sentence about the row key being byte-identical to the transport key; the new paragraph adds
  only the recovery path.
- No code identifiers beyond the ones already named in the section.

## Compatibility considerations
N/A: documentation-only change.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria
The document states the matching, one-time consumption, fail-closed behavior, and the no-id constraint in one
place, and the docs gates pass.

## Out of Scope
No change to the MCP design-document sweep (mcpai012).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the replay-directive paragraph | Pending | — | — | |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (Agent-managed matching), `REQ-005` (control text carries no id)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
