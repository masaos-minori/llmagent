# Procedure: agent_02 runtime-architecture alignment

**Doc ID:** 20261030-122302_04
**Target File:** `docs/23_agent/agent_02_runtime-architecture.md`
**Change Type:** docs | **Priority:** P1 | **Plan Phase:** 2

## Goal
Confirm and, where needed, extend the dependency/ownership statements so `agent_02`
carries the same three-role description as rows 01-03.

## Scope
- :29 Allowed Dependency Direction: "Orchestrator depends on LlmTurnExecutor" — verified
  accurate (construction + injection at `orchestrator.py:120/:150`); keep.
- :30 Reason for Process Separation: "decoupling Orchestrator from LlmTurnExecutor
  separates turn-level coordination from LLM streaming and tool loop execution" — keep.
- :101 Orchestrator section bullet "Delegates LLM streaming and the tool loop to
  `LlmTurnExecutor`" — extend with the per-turn lifecycle sentence.

## Assumptions
- `agent_02` has no standalone `LlmTurnExecutor` component section (verified: only the
  three references above), so the lifecycle fact belongs in the Orchestrator bullet.

## Design decisions
- :101 replacement: `Delegates LLM streaming and the tool loop to the single
  LlmTurnExecutor instance it constructs and injects; each turn's loop body runs in a
  fresh per-turn runner created by that executor and not retained afterwards.` Mirrors
  rows 01-03 wording; no new names beyond the existing runner concept.

## Alternatives considered
- Adding a dedicated component section for the runner: rejected — ADR-014 lists the
  runner as an implementation example; a component section would imply a new boundary.

## Implementation
1. Row 01 landed; mirror its phrasing.
2. Apply the :101 bullet edit; leave :29/:30 unchanged after re-verification.

## Compatibility considerations
Consistency checkers cover cross-doc drift with rows 02/03.

## Security considerations
None.

## Rollback considerations
Revert the file.

## Validation plan
- Phase 2 gate: `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`.

## Completion criteria
REQ-03 for `agent_02`: construction ownership and per-turn lifecycle stated once,
consistent with the traced call path.

## Out of Scope
Dependency-direction rules; other component sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify :29/:30 accuracy against HEAD | Pending | — | — | Read-only |
| 2 | Apply :101 bullet edit | Pending | — | — | Needs row 01 |
| 3 | Run Phase 2 checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Row 01 final wording not yet landed at procedure-generation time | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003; AC-4
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-122302
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
