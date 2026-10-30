# Procedure: agent_03_01 turn-flow overview alignment

**Doc ID:** 20261030-122302_03
**Target File:** `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`
**Change Type:** docs | **Priority:** P1 | **Plan Phase:** 2

## Goal
Align the ⑤ LLM Turn Processing call-graph block (:62-70) with the three-role model: the
injected single `LlmTurnExecutor` executes the turn; the per-turn loop body is delegated
to a fresh `LLMTurnRunner`.

## Scope
- The ASCII call-graph segment starting at :62 (`→ LlmTurnExecutor.handle_llm_turn(llm_url)`).
- Not touched: the surrounding ①-④/⑥ blocks, stage annotations.

## Assumptions
- The call-graph line itself is factually current (`handle_llm_turn` still exists at
  `llm_turn_executor.py`, called by the adapter at `:341`); the gap is the missing
  per-turn delegation, so the loop body reads as if the executor itself runs it.

## Design decisions
- Add one delegation line under the `handle_llm_turn` entry, keeping the ASCII tree
  alignment: `→ per-turn loop body: fresh LLMTurnRunner (created per turn, not retained)`
  before the existing `├─ LLMClient.stream(...)` branch; the Tool Loop branch stays as
  the runner's body. Wording must mirror rows 01/02.
- Do not add signatures or file paths (docs content policy: responsibility and lifecycle).

## Alternatives considered
- Redrawing the whole diagram: rejected — scope creep; one annotation line carries the
  ownership fact.

## Implementation
1. Row 01 landed; mirror its phrasing.
2. Insert the annotation line in the :62 block; verify the box-drawing alignment renders
   unchanged elsewhere.

## Compatibility considerations
Must not contradict rows 02/04; `check_docs_consistency.py --domain agent` covers drift.

## Security considerations
None.

## Rollback considerations
Revert the file.

## Validation plan
- Phase 2 gate: `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`.

## Completion criteria
REQ-03 for `agent_03_01`: ownership + per-turn lifecycle visible in the call graph.

## Out of Scope
Other sections of the file; generated docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert delegation annotation in the ⑤ block | Pending | — | — | Needs row 01 |
| 2 | Run Phase 2 checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 01 final wording not yet landed at procedure-generation time | No | — |

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
- **Related target files**: `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`
