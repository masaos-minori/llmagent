# Plan: Align ADR-014 Control-Plane Loop Ownership Wording

**Plan ID:** 20261030-001153-turnadr001
**Source Issue:** `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md` (SHA256: 1d5a3f07194670e3b19c04386f5b741d47a3391060240d10f2d94e738c535c75)
**Task Classification:** Path A (small; documentation wording + guard-test adjustment, no code behavior change)
**Status:** Draft

## Goal
Restate ADR-014's ownership of the LLM/tool round-trip loop so it matches the shipped
structure — construction by `Orchestrator`, single owned `LlmTurnExecutor`, per-turn
execution delegated to `LLMTurnRunner` — describing logical ownership and instance
lifecycle instead of names that may move, and strengthen the existing guard test.

## Priority
Low (P3). Documentation/guard-test consistency issue; no behavior defect today. Not
time-sensitive (issue Reason for Change).

## Scope
**In-Scope**:
- ADR-014 Decision Details loop wording, Implementation Notes, and INV-02 phrasing
  (meaning preserved; ownership vs delegation distinguished).
- Agent flow documents: `agent_03_02_turn-processing-flow-llm-tool-loop.md`,
  `agent_03_01_turn-processing-flow-overview.md`, `agent_02_runtime-architecture.md`
  stale method/class references.
- `tests/agent/test_orchestrator.py`: extend the existing
  `TestSingleLlmTurnExecutorOwnership` guard; `tests/agent/test_llm_turn_runner.py`
  adjustment if needed.
- `docs/10_adr/adr_01_index.md` invariant matrix row refresh if the wording change
  alters the cited verification text.

**Out-of-Scope**:
- Merging/restructuring `LlmTurnExecutor` / `LLMTurnRunner` / `ToolExecutor` (issue Out
  of Scope; ADR-014 lists it as out of scope).
- ADR-001 mandatoriness / persistent-state rules.
- Production `scripts/` edits unless the trace reveals a real defect (it does not — see
  Background).
- Hand-editing generated reference documents (regenerate instead).

**Dependencies**: none (issue Dependencies section; re-verified: no other in-flight plan
targets these files except the shared `adr_01_index.md` note in Risks).

## Background
### Codebase Context (directly verified 2026-10-30, HEAD `c5a8285dd` + staged plans)
Production call path traced (issue Required Change 1 — done at plan time):
- `scripts/agent/orchestrator.py:120` constructs exactly one `LlmTurnExecutor`
  (`self._llm_executor`); `:150` injects it into `WorkflowEngineAdapter` via
  `llm_executor=`.
- `scripts/agent/workflow_engine_adapter.py:87` (constructor parameter), `:98`
  (`self._llm_executor = llm_executor` — stored, never constructed), `:341` calls
  `self._llm_executor.handle_llm_turn(...)`.
- `scripts/agent/llm_turn_executor.py:27` `class LlmTurnExecutor`; `:84` creates a fresh
  `LLMTurnRunner` per turn.
- `scripts/agent/llm_turn_runner.py:40` `class LLMTurnRunner` — the per-turn loop body.
- Only one `LlmTurnExecutor` construction site under `scripts/` (verified via grep; the
  issue's :120/:150 anchors confirmed).

Existing guard test (resolves the issue's second unresolved question):
- `tests/agent/test_orchestrator.py:2933` `class TestSingleLlmTurnExecutorOwnership`,
  docstring "INV-02 regression (ADR-014): the Orchestrator centralizes LlmTurnExecutor
  creation — exactly one shared instance, held by no other component"; method
  `test_orchestrator_creates_single_shared_llm_executor` asserts `orch._llm_executor`
  identity and adapter sharing.

ADR-014 current text:
- :58 assigns "the short loop between the LLM and Tool Calls" to `LlmTurnExecutor` and
  says creating/holding the loop is "centralized in the component that actually drives
  the loop (currently `LlmTurnExecutor`)".
- :127-129 INV-01/02/03 (no owner column by design; INV-02 quoted verbatim in the issue).
- Verification table :135-138: INV-02 row cites `tests/agent/test_orchestrator.py`;
  INV-01 and INV-03 stay Manual (index matrix :145/:147) — this plan does not add tests
  for them.

### Corrections to Issue Claims
1. Unresolved question "whether any existing test already asserts no duplicate/unused
   executor" — CONFIRMED: `TestSingleLlmTurnExecutorOwnership` (added earlier,
   `INV-02 regression`) already covers single-instance sharing. The plan adjusts/extends
   it rather than creating a duplicate guard.
2. `LLMTurnRunner` lives at `scripts/agent/llm_turn_runner.py` (issue anchor :40 verified).

### Historical Context
- The adapter/executor split predates the issue; the ADR wording "currently
  `LlmTurnExecutor`" already hedges with "currently", which is exactly the class-name
  dependence the issue wants removed.

## Problem
ADR-014 equates the loop with `LlmTurnExecutor`, while the loop body lives in
`LLMTurnRunner` and the construction site is `Orchestrator`. INV-02's "the one component
that actually drives" is ambiguous between creator and caller; stale wording can invite
a second loop owner or misplaced responsibility in future changes.

## Reason for Change
Contract clarity for the control plane (ADR-014 is cited by the mcpgate001 and
adrcov001 work). No behavior defect; low priority, do now as part of the ADR-consistency
workstream.

## Implementation Intent
Reword ADR-014 so three distinct roles are explicit and name-resilient: (a) logical loop
owner — the WorkflowEngine side (per owner decision), which runs the turn through the
single `LlmTurnExecutor` it holds; (b) construction owner — `Orchestrator`, which creates
exactly one instance and injects it; (c) per-turn runner lifecycle — `LLMTurnRunner` is
created per turn by the executor and holds no independent authority. Extend the existing
guard test to fail on a second or retained-unused executor (factory-count approach per
the issue's testing expectation). Update the three Agent flow docs. Preserve invariant
meaning (`tools/check_adr_preservation.py`).

## Requirements
- `REQ-001`: ADR-014 Decision Details + INV-02 wording distinguish ownership from
  delegation and do not depend on method names; meaning unchanged (constraint C-1).
- `REQ-002`: Exactly one logical loop owner in the text; delegation to `LLMTurnRunner`
  does not create a second authority (issue AC-2).
- `REQ-003`: Flow documents `agent_02`, `agent_03_01`, `agent_03_02` carry the same
  ownership/lifecycle description; stale references replaced; generated reference docs
  regenerated, not hand-edited.
- `REQ-004`: Guard test fails if `Orchestrator` or another component retains an unused
  duplicate executor (issue AC-3; factory-patched construction counting).
- `REQ-005`: Persistent workflow-state responsibility stays outside both turn classes
  (INV-01 unchanged; verification-only).

## Implementation Target Files
**Freeze status**: Frozen (Step 8 Implementation Target Files Validation passed on
2026-10-30: every row exists-or-is-new-with-evidence, is linked to a Plan requirement,
and is `Verified` against `HEAD c5a8285dd` — the call path re-traced by direct read
(`orchestrator.py:120` single `LlmTurnExecutor`, `:145` `WorkflowEngineAdapter`, `:150`
`llm_executor=` injection; adapter `:87/:98/:341`; `llm_turn_executor.py:27/:84`
per-turn `LLMTurnRunner`) and the existing `TestSingleLlmTurnExecutorOwnership` guard
test confirmed present; `check_workitem_structure.py` reports no findings; cross-plan
pairs reported by `check_plan_target_overlaps.py` are recorded sequenced in
Dependencies.)

| File Path | Change Type | Notes | Priority | Dependencies | Estimated Complexity |
|---|---|---|---|---|---|
| docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | docs | :58 Decision Details, Implementation Notes, INV-02 reword (meaning preserved) | P1 | owner decision (recorded) | Low |
| docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md | docs | loop ownership/lifecycle wording alignment | P1 | ADR-014 edit | Low |
| docs/23_agent/agent_03_01_turn-processing-flow-overview.md | docs | same | P1 | ADR-014 edit | Low |
| docs/23_agent/agent_02_runtime-architecture.md | docs | same | P1 | ADR-014 edit | Low |
| tests/agent/test_orchestrator.py | test | extend `TestSingleLlmTurnExecutorOwnership` with factory-count / unused-retention detection | P1 | - | Medium |
| tests/agent/test_llm_turn_runner.py | test | per-turn lifecycle assertion only if the trace requires it (runner holds no authority) | P2 | - | Low |
| docs/10_adr/adr_01_index.md | docs | refresh ADR-014 invariant matrix rows (:145-147) if cited verification text changes | P2 | ADR-014 edit | Low |

Explicitly excluded from target files:
- `scripts/agent/orchestrator.py`, `workflow_engine_adapter.py`, `llm_turn_executor.py`,
  `llm_turn_runner.py` — trace found no defect (issue: edit only if the trace shows one);
  read-only for the implementation phase re-check.

## Reference Files
- docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md — INV-01 boundary context
- tools/check_adr_preservation.py — invariant-preservation gate
- tools/check_adr_structure.py — heading-order/ID rules for ADR edits
- docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md — adjacent flow doc to check for stale wording (issue Unresolved #3)

## Acceptance Criteria
- AC-1: ADR-014 names exactly one logical loop owner and separate construction/delegation
  roles; no method-name dependence in INV-02.
- AC-2: `tools/check_adr_preservation.py` passes — rewording changes no decision or
  invariant meaning.
- AC-3: New/extended test fails on a fabricated second retained executor (demonstrated
  with a temporary fixture, then reverted).
- AC-4: The three flow documents match the traced production call path;
  `check_docs_consistency.py --domain agent` passes.
- AC-5: Generated reference documents refreshed via `generate_reference_table.py`, not
  hand-edited (ADR-015 INV-01).

## Tests
### New
- Factory-count regression in `TestSingleLlmTurnExecutorOwnership` (patch
  `LlmTurnExecutor` construction; assert exactly one construction per Orchestrator run
  and no unused instance retained by adapter or runner paths).
### Modified
- `tests/agent/test_llm_turn_runner.py`: only if a runner-side lifecycle gap is found.
### Regression
- Existing single-instance identity assertions run unchanged.

## Documentation Impact
Yes: ADR-014 + three flow docs + (possibly) the index matrix row. Per `skills/DESIGN.md`
Docs content policy: responsibility and lifecycle, not implementation locations or
signatures. Generated reference blocks regenerated. `docs/00_index.md` task-scope mapping
applies at implementation time.

## Assumptions
- A-1: INV-02's intended owner is the WorkflowEngine side (owner decision recorded
  2026-10-30); `Orchestrator` is documented as construction owner, not loop owner.
- A-2: No production defect exists (trace verified at plan time); script files stay
  untouched.

## Unknowns
- U-1: Which additional flow/reference docs beyond the three named carry stale wording
  (issue Unresolved #3) — resolved by a `rg` sweep of `LlmTurnExecutor|LLMTurnRunner`
  across `docs/` at implementation start; generated docs are regenerated rather than
  swept.

## Affected areas
- docs/10_adr (1-2 files), docs/23_agent (3 files), tests/agent (1-2 files)

## Design
### Current Architecture
ADR prose ties the loop to a class name; the guard test guards single-instance sharing;
the invariant-matrix row cites the test file generically.

### Target Architecture
ADR text expresses a three-role ownership model (owner / constructor / per-turn delegate)
with names as examples, not contracts; the guard test counts constructions via a patched
factory so future renames do not blind it.

### Key Components
1. ADR-014 reworded Decision Details + INV-02.
2. Extended `TestSingleLlmTurnExecutorOwnership` (factory-count variant).

## Implementation steps
### Phase 1: Re-trace and reword (documentation)
- Re-run the trace against current HEAD (anchors above), reword ADR-014 Decision
  Details, Implementation Notes, INV-02; refresh index matrix rows if cited text changed.
- Done when: `check_adr_preservation.py` and `check_adr_structure.py` pass.
### Phase 2: Flow docs
- Sweep stale references (`rg 'LlmTurnExecutor|LLMTurnRunner' docs/`), update the three
  flow docs, regenerate reference tables.
- Done when: `check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` pass.
### Phase 3: Guard-test extension
- Factory-count test + unused-retention fixture proof.
- Done when: AC-3 demonstrated with fail-before evidence on a reverted fixture.

## Validation plan
- Issue-specified: `uv run pytest tests/agent/test_orchestrator.py
  tests/agent/test_llm_turn_runner.py`, `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_adr_preservation.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`.
- `uv run mypy scripts` / `uv run ruff check tests` unchanged (no scripts edits expected).
- No full-suite requirement beyond `tests/agent` (documentation-scale change).

## Risks
| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| INV-02 reword accidentally changes invariant meaning | Medium | Medium | Preservation checker + before/after text diff reviewed against issue constraint |
| Index matrix text drift after reword (ADR-014 rows) | Low | Medium | Include adr_01_index.md refresh in Phase 1 scope |
| Factory-count test overfits current construction sites | Low | Medium | Count via patched class, not call-site strings |

## Dependencies
- No open plan targets these files (issue claim re-verified; the only shared file is
  `docs/10_adr/adr_01_index.md`, already sequenced across dbmig001/adrauth001/mcpgate001 —
  this plan edits only the ADR-014 rows, which none of those plans touch).

## Execution Status
| Phase | Status | Procedure Docs |
|---|---|---|
| Phase 1 | procedure generated | 20261030-122302_01 (ADR-014 reword), 20261030-122302_07 (index refresh) |
| Phase 2 | procedure generated | 20261030-122302_02, _03, _04 (flow docs) |
| Phase 3 | procedure generated | 20261030-122302_05, _06 (guard tests) |

## Blocker Log
| Item | Detail | Status |
|---|---|---|
| Frozen-table gap (U-1 sweep) | Verified-stale references outside the frozen table: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:82` (`_stream_llm` lives on `LLMTurnRunner`) and `docs/23_agent/agent_12_reference-api.md:101/:114`. Registered as Needs-Confirmation additional target rows in doc 02; not edited by this batch | open — Needs Confirmation before implementation |
| Commit-group ordering | Doc 01's INV-02 verification-row text (:135) must land in the same commit group as doc 05's new test; doc 07 (index refresh) must land after doc 05 so the Confirmed-cell citation matches the landed test | recorded in docs 01/05/07 |

## Work Items Created
| Item ID | Target File | Phase |
|---|---|---|
| 20261030-122302_01_docs_10_adr_adr_02_02_014_agent-control-plane-responsibility-boundaries.md.md | docs/10_adr/adr_02_02_014_agent-control-plane-responsibility-boundaries.md | Phase 1 |
| 20261030-122302_02_docs_23_agent_agent_03_02_turn-processing-flow-llm-tool-loop.md.md | docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md | Phase 2 |
| 20261030-122302_03_docs_23_agent_agent_03_01_turn-processing-flow-overview.md.md | docs/23_agent/agent_03_01_turn-processing-flow-overview.md | Phase 2 |
| 20261030-122302_04_docs_23_agent_agent_02_runtime-architecture.md.md | docs/23_agent/agent_02_runtime-architecture.md | Phase 2 |
| 20261030-122302_05_tests_agent_test_orchestrator.py.md | tests/agent/test_orchestrator.py | Phase 3 |
| 20261030-122302_06_tests_agent_test_llm_turn_runner.py.md | tests/agent/test_llm_turn_runner.py | Phase 3 |
| 20261030-122302_07_docs_10_adr_adr_01_index.md.md | docs/10_adr/adr_01_index.md | Phase 1 |

## Traceability
- Issue source: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`

## Requirement Traceability
- Issue Required Change 1 (trace call path) → Background trace (completed at plan time).
- Issue Required Change 2 (ADR-014 wording) → REQ-001/002, AC-1/2 → Phase 1.
- Issue Required Change 3 (flow docs) → REQ-003, AC-4 → Phase 2.
- Issue Required Change 4 (regression test for duplicate/unused executor) → REQ-004, AC-3 → Phase 3.
- Issue Required Change 5 (persistent state outside turn classes) → REQ-005 → verification-only in Phase 1.
- Issue Unresolved #1 → resolved by owner decision (A-1). #2 → resolved (guard test exists). #3 → U-1.
