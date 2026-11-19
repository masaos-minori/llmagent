# Update MCP design documentation after implementation contracts are finalized

## Priority
Low

## Summary
Remove obsolete design statements and document the final idempotency, replay, audit, file protection, Git postcondition, and GitHub security contracts after the implementation issues are complete.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 12). The design document location is `Unknown` and must be identified when this issue is planned.

## Problem
The combined design document is said to contain pre-fix and post-fix descriptions that contradict each other, and comments describe the Agent logical key and the transport key as separate values and imply that the LLM controls replay identity (`Needs confirmation`).

## Reason for Change
Documenting before implementation is complete risks another round of drift, so this is last in order; no urgency otherwise.

## Implementation Intent
Produce one implementation-aligned description in which every security or reliability claim names the enforcement point, failure behavior, and proving test. Follow `skills/DESIGN.md` (no implementation-reference duplication, only unresolved limitations).

## Target Files or Areas
- MCP server design documentation under `docs/` (exact files `Unknown`)
- Agent workflow and audit comments
- File write and delete, Git, and GitHub design sections

## Required Changes
- Define workflow, task, turn, call, session, request ids and the idempotency key in one table; document Agent-managed replay and the final dedup ownership and lease state machine.
- Correct file-write and file-delete statements; name audit log types and authoritative locations consistently; describe Git postconditions per operation; describe GitHub read authorization, search scope, file-read controls, timeout outcomes, and retry policy.
- List only unresolved limitations; reference the proving test and verified revision for each claim.

## Constraints
- Do not merge before the behavior it documents. ADR content changes need an approval record (governance_01, governance_05), never a simulated one.

## Acceptance Criteria
- [ ] No section contradicts the implementation, and no comment claims that session, tool, and arguments identify a logical call.
- [ ] Replay is described as Agent-managed; audit and recovery outcomes are defined consistently.
- [ ] Known limitations include only unresolved behavior.

## Testing Expectations
- Documentation consistency checks used by the repository (docs checkers, reference table checks); run them on the changed files.

## Documentation Impact
This issue is the documentation change: intent, boundaries, failure behavior, and Known Issues.

## Out of Scope
- Any behavior change.

## Dependencies
- Depends on `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md`, `issues/20261119-140509_mcpai002_github-read-security-boundary.md`, `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`, `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`, `issues/20261119-140512_mcpai005_structured-execution-context.md`, `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140514_mcpai007_dedup-audit-observability.md`, `issues/20261119-140515_mcpai008_git-postcondition-lifecycle.md`, `issues/20261119-140516_mcpai009_file-mcp-hardening.md`, `issues/20261119-140517_mcpai010_github-http-contract-tests.md`, and `issues/20261119-140518_mcpai011_round-recording-accuracy.md`.

## Unresolved Questions
- `不明`: the exact documents to update.

## AI Implementation Instruction
Edit documentation and comments only; verify each claim against current source and the named test before writing it.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140519
- **Related target files**: N/A: not yet confirmed
