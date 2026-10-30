# Procedure: ADR-014 loop-ownership reword (Decision Details, INV-02, Implementation Notes)

**Doc ID:** 20261030-122302_01
**Target File:** `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
**Change Type:** docs | **Priority:** P1 | **Plan Phase:** 1

## Goal
Reword ADR-014 so the LLM/Tool round-trip loop is described as a three-role model —
logical loop owner (WorkflowEngine side), construction owner (`Orchestrator`), per-turn
delegate (`LLMTurnRunner`) — without method-name dependence, preserving invariant meaning
(constraint C-1, REQ-001/REQ-002, AC-1/AC-2).

## Scope
- Decision Details `LlmTurnExecutor` bullet (:58).
- INV-02 (:129).
- Implementation Notes paragraph (:162-164).
- Automated Tests table INV-02 row description (:135) — text only, coordinated with row 05's test extension.
- Not touched: INV-01, INV-03, headings, IDs, Approval, Related ADRs, Implementation References.

## Assumptions
- A-1 (owner decision, recorded in plan): the WorkflowEngine side is the logical loop
  owner; `Orchestrator` is the construction owner. HEAD re-verified 2026-10-30: sole
  construction site `scripts/agent/orchestrator.py:120`; injection `:150`
  `llm_executor=`; adapter stores it (`workflow_engine_adapter.py:87/:98`) and calls it
  (`:341` `handle_llm_turn`); `llm_turn_executor.py:84` creates a fresh `LLMTurnRunner`
  per turn; the runner is never retained (`self._runner` does not exist).
- `check_adr_preservation.py` compares decision/invariant meaning against the approved
  baseline; the reword must clarify, not invert (Risk row 1).

## Design decisions
- Replace the class-name-dependent phrase "centralized in the component that actually
  drives the loop (currently `LlmTurnExecutor`)" with explicit roles; class names remain
  as parenthetical examples, not contracts.
- The current INV-02 text says creation is centralized "in the one component that
  actually drives" the loop, while the actual sole construction site is `Orchestrator`
  (the driver holds, not constructs). The reword aligns the text with the traced reality
  and with A-1; the prohibition semantics (no unused/duplicate instances) are unchanged.
- Proposed Decision Details bullet (replaces :58):
  `**LlmTurnExecutor** (scripts/agent/llm_turn_executor.py): responsible for the short
  loop between the LLM and Tool Calls (streaming and Tool call round-trips within a
  turn). The logical owner of this loop is the WorkflowEngine side, which runs every
  turn through the single LlmTurnExecutor instance it holds; the Orchestrator is the
  construction owner, creating exactly one instance and injecting it. The per-turn loop
  body is delegated to a LLMTurnRunner (scripts/agent/llm_turn_runner.py) instance
  created fresh for each turn; the runner holds no independent authority and is not
  retained after the turn. No other component holds duplicate unused loop-executing
  instances.`
- Proposed INV-02 (replaces :129):
  `INV-02: LlmTurnExecutor instances are constructed only by the Orchestrator — exactly
  one shared instance, injected into the component that drives the LLM/Tool Call
  round-trip loop. No other component constructs, or holds unused or duplicate,
  LlmTurnExecutor instances; per-turn delegation to a fresh runner created by the
  executor does not create an additional loop authority.`
- Proposed Implementation Notes addition (append sentence to :162 paragraph):
  `Each turn's loop body runs in a fresh LLMTurnRunner instance created by the
  LlmTurnExecutor and discarded at turn end; the runner holds no independent authority.`
- Proposed INV-02 verification-row text (:135): `A regression test that LlmTurnExecutor
  is constructed exactly once by the Orchestrator and no component holds an unused or
  duplicate instance` — lands in the same commit group as row 05's extended guard so the
  row always describes an existing test.

## Alternatives considered
- Keep INV-02 generic ("the component that actually creates and drives"): rejected — it
  is exactly the ambiguity the issue targets (creator vs caller).
- Name `LLMTurnRunner` inside INV-02 as the delegate: rejected — invariants must be
  name-resilient; the runner is cited in Decision Details/Implementation Notes only.

## Implementation
1. Re-run the trace before editing (read-only): `orchestrator.py:120/:150`,
   `workflow_engine_adapter.py:87/:98/:341`, `llm_turn_executor.py:27/:84`,
   `llm_turn_runner.py:40`. If any anchor moved, update only cited line references, not
   the role model.
2. Apply the four text edits above (Decision Details bullet, INV-02, Implementation
   Notes, verification-row description).
3. Diff review: confirm INV-01/INV-03 bytes unchanged and no heading/ID changes
   (`git diff` review against this doc).

## Compatibility considerations
- The reworded invariant text is cited in `docs/10_adr/adr_01_index.md` :146 — row 07
  refreshes that row in the same Phase 1 scope; land 01 before or with 07.
- Other plans' index rows (dbmig001/adrauth001/mcpgate001/adrcov001) do not touch
  :145-147; no landing-order conflict beyond row 07.

## Security considerations
None (documentation wording).

## Rollback considerations
Revert the single ADR file; no code or test depends on the wording at runtime.

## Validation plan
- `uv run python tools/check_adr_preservation.py` and `uv run
  tools/check_adr_structure.py` pass (Phase 1 done gate).
- Before/after text diff reviewed against the issue constraint (Risk mitigation).

## Completion criteria
AC-1: exactly one logical loop owner named, separate construction/delegation roles
explicit, no method-name dependence in INV-02; preservation and structure checkers pass.

## Out of Scope
Merging/restructuring `LlmTurnExecutor`/`LLMTurnRunner`/`ToolExecutor`; tests for INV-01/
INV-03; `scripts/` edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-trace anchors (read-only) | Pending | — | — | |
| 2 | Apply four text edits per Design decisions | Pending | — | — | INV-02 row text lands with row 05 |
| 3 | Diff review + preservation/structure checkers | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Verification-row text (:135) must land in the same commit group as row 05's extended guard | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-122302_05_tests_agent_test_orchestrator.py.md` | 1 (plan Phase 3) | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002; AC-1, AC-2
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-122302
- **Related target files**: `docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md`
