# Implementation Procedure: docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md (shellprefix001)

## Goal
- Update the `shell_run` row of the Special Risk Overrides table and its note to describe
  the new auto-approval condition (REQ-010: which command shapes are auto-approved and
  why; interpreters/test runners always prompt).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Execute after seq 01/02 are implemented so the documented behavior matches shipped code
  (Plan Phase 5 ordering).
- Doc edit is scoped to the Special Risk Overrides section (table row currently reading
  "`shell_run` and `command` starts with any of `approval_shell_safe_prefixes` → `none`")
  plus at most one short explanatory paragraph; the Risk Escalation section already
  describes the positional-path check and stays unchanged.

## Design decisions
- Describe the rule at policy level (gate list + read-only-by-construction requirement,
  allowed `git` subcommands, interpreter denial) without pasting code or the full shipped
  prefix list — `skills/DESIGN.md` Docs content policy (implementation detail belongs to
  code).

## Alternatives considered
- N/A: wording-level doc edit; no design surface.

## Implementation
### Target file
- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`

### Procedure
1. Replace the `shell_run` `none` row condition with: `shell_run` whose executable is in
   `approval_shell_safe_prefixes` AND whose parsed arguments match the agent's read-only
   safe-shape rule (read-only git subcommands: `log`, `status`, `show`, `diff`, and
   list-only `branch`; `cat`, `echo`, `ls`, `pwd`, `grep`, `find` without denied flags).
2. Extend the section's Note paragraph: auto-approval requires both the config gate and
   the code-side shape rule; interpreters and test runners (`python`, `pytest`, `uv run`)
   always take the approval prompt; any executable without a defined read-only shape is
   `high`.

### Method
- Keep the table structure and surrounding headings byte-identical otherwise.

### Details
- N/A: wording edit only; line anchors shift with the edit, so no line citations.

## Compatibility considerations
- The stale "starts with" wording was already flagged as a shellprefix001 documentation
  matter by `plans/20261101-142514_shellrisk001_...` (Documentation Impact) — this edit
  closes it.

## Security considerations
- N/A: documentation only; accuracy is the value (the doc currently overstates what is
  auto-approved).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`,
  `uv run python tools/check_docs_content_policy.py`, and
  `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
- The `shell_run` override row and note describe the gate-plus-shape-rule condition and
  the interpreter prompt rule (AC-4), and all four docs checkers pass.

## Out of Scope
- `docs/91_security/security_02_high-risk-tool-common-policy.md` — seq 05 document.
- Code and config behavior — seq 01/02.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the `shell_run` override row and Note paragraph | Completed | 20261103-094439 | 20261103-094439 | Execute after seq 01/02 (Plan Phase 5) Changed file: docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md (shell_run override row + Note) |
| 2 | Run the docs checkers (`routing.md` Tools) | Completed | 20261103-094439 | 20261103-094439 | check_docs_quality/structure/content_policy/consistency --domain agent: all pass |

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
- **Requirement ID**: `REQ-010` (document auto-approved shapes and the interpreter prompt
  rule)
- **Source issue**: `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-072856
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`