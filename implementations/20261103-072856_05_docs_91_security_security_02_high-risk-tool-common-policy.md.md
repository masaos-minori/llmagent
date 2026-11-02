# Implementation Procedure: docs/91_security/security_02_high-risk-tool-common-policy.md (shellprefix001)

## Goal
- Update the Shell MCP bullet in the tool-deviations examples to state the intent and
  boundaries of `shell_run` auto-approval (REQ-010: intent and boundaries only, not the
  full prefix list).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Execute after seq 01/02 are implemented (Plan Phase 5 ordering).
- Edit is scoped to the "**Shell MCP**" bullet in the deviations examples list; the common
  baseline policy body and the other bullets are unchanged.

## Design decisions
- Keep the bullet at intent level: auto-approval exists only for command shapes that are
  read-only by construction (config gates the executable, an agent-side rule decides
  subcommand/flag acceptability, deny-by-default otherwise); interpreters and test runners
  always prompt. No enumeration of the shipped prefix list (Plan REQ-010 wording, docs
  content policy).

## Alternatives considered
- N/A: wording-level doc edit.

## Implementation
### Target file
- `docs/91_security/security_02_high-risk-tool-common-policy.md`

### Procedure
1. Rewrite the "**Shell MCP**" bullet: `approval_shell_safe_prefixes` auto-approves only
   read-only-by-construction `shell_run` command shapes; the config gates the executable
   and the agent-side safe-shape rule decides subcommand/flag acceptability (deny by
   default); interpreters and test runners always take the approval prompt. Keep the
   reference to `mcp_04_02_file-write-file-delete-shell.md`.

### Method
- One bullet replacement; surrounding list formatting byte-identical.

### Details
- N/A: wording edit only.

## Compatibility considerations
- The bullet currently reads "allows auto-approval for safe prefixes" — the current wording
  understates the boundary; the rewrite aligns it with the corrected agent doc (seq 04).

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py docs/91_security/security_02_high-risk-tool-common-policy.md`,
  `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The Shell MCP bullet states intent + boundaries + interpreter prompt rule (AC-4), and
  all three docs checkers pass.

## Out of Scope
- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` — seq 04 document.
- The referenced `mcp_04_02` shell-server doc (server-side allowlist; out of this Plan's
  target rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the Shell MCP deviations bullet | Pending | — | — | Execute after seq 01/02 (Plan Phase 5) |
| 2 | Run the docs checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (document auto-approval intent and boundaries)
- **Source issue**: `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-072856
- **Related target files**: `docs/91_security/security_02_high-risk-tool-common-policy.md`
