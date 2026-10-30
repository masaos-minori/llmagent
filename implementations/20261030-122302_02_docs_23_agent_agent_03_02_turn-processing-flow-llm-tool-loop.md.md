# Procedure: agent_03_02 loop-ownership wording alignment (Phase 2 sweep owner)

**Doc ID:** 20261030-122302_02
**Target File:** `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
**Change Type:** docs | **Priority:** P1 | **Plan Phase:** 2

## Goal
Align the flow document's loop description with the ADR-014 three-role model (row 01),
and own the U-1 stale-reference sweep for the whole `docs/` tree.

## Scope
- `agent_03_02` :56 heading paragraph "`LlmTurnExecutor.handle_llm_turn(llm_url)`
  manages the internal loop" — restate ownership/delegation.
- U-1 sweep (this doc owns it): `rg 'LlmTurnExecutor|LLMTurnRunner' docs/ --include '*.md'`.
- Generated docs are regenerated via `generate_reference_table.py`, never hand-edited
  (AC-5, ADR-015 INV-01).

## Assumptions
- Sweep result at procedure-generation time (2026-10-30, HEAD `124e340b4`): hits beyond
  the three flow docs are `overview_01_02-arch-pipelines.md` (:60/:73),
  `mcp_03_01_dispatch-and-routing.md` (:82), `agent_12_reference-api.md` (:76/:101/:114),
  `agent_13_reference-api-generated.md` (generated), `agent_06_03_tool-execution-and-approval-concurrency-safety.md` (:41).
- Verified stale: `mcp_03_01` :82 cites `LlmTurnExecutor._stream_llm()` but `_stream_llm`
  lives on `LLMTurnRunner` (`llm_turn_runner.py:278`); `agent_12` :101/:114 cite
  `LlmTurnExecutor` as caller where the actual caller is `LLMTurnRunner`
  (`llm_turn_runner.py:116` `execute_all_tool_calls`). Verified accurate (no edit):
  `overview_01_02` layer-level statements, `agent_06_03` :41 (`ToolLoopGuard` is
  constructed in `LlmTurnExecutor.execute_turn` at `llm_turn_executor.py:83` and passed
  to the runner — the statement holds at the executor level).

## Design decisions
- `agent_03_02` :56 replacement: `The single LlmTurnExecutor instance (created once by
  the Orchestrator and held by the WorkflowEngine side) executes each turn; its
  handle_llm_turn entry point delegates the loop body to a fresh LLMTurnRunner instance
  created per turn. The runner holds no independent authority and is not retained after
  the turn.` Keep the existing bullet list (payload/streaming/tool-round-trip) as the
  runner's loop body unchanged.
- Stale sweep follow-ups are **additional-target-file discoveries** (frozen-table gap,
  same pattern as mcpgate001 row 8): register `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
  (:82 method-owner fix) and `docs/23_agent/agent_12_reference-api.md` (:101/:114
  caller fix) as additional target rows before implementing them. **Needs Confirmation**
  from the plan owner; do not edit them under this doc.
- `agent_13_reference-api-generated.md` is regenerated, not registered.

## Alternatives considered
- Editing `mcp_03_01`/`agent_12` here without registering rows: rejected — frozen target
  table contract (same rule as mcpgate001 checker-test gap).

## Implementation
1. Row 01 (ADR-014) landed first: re-read the final ADR wording and mirror it here
   (dependency "ADR-014 edit").
2. Replace the :56 paragraph per Design decisions; keep the loop-body bullets.
3. Run the sweep; confirm the hit inventory above; hand off stale hits only through the
   registered additional rows.
4. Regenerate generated reference docs (`uv run python tools/generate_reference_table.py`).

## Compatibility considerations
- Wording must match `agent_03_01` (row 03) and `agent_02` (row 04) — same three-role
  phrasing, checked by `check_docs_consistency.py --domain agent`.

## Security considerations
None.

## Rollback considerations
Revert the doc file; re-run the consistency checkers.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent` (Phase 2 gate).

## Completion criteria
REQ-03: this doc matches the traced production call path and the reworded ADR-014; sweep
inventory recorded; additional-row registrations confirmed or explicitly declined by the owner.

## Out of Scope
Editing `mcp_03_01`, `agent_12`, `overview_01_02`, `agent_06_03` (handled via registered
additional rows or verified accurate); `scripts/` edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Mirror final ADR-014 wording into :56 paragraph | Pending | — | — | Needs row 01 landed |
| 2 | Re-run sweep; confirm hit inventory | Pending | — | — | U-1 resolution |
| 3 | Register `mcp_03_01` and `agent_12` additional rows | Pending | — | — | Needs Confirmation |
| 4 | Regenerate reference tables | Pending | — | — | AC-5 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` and `docs/23_agent/agent_12_reference-api.md` verified stale but absent from the frozen target table — additional-target-file discovery to register before editing | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| additional row (pending registration): `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | 2 | Doc-fix | Needs Confirmation | — | — |
| additional row (pending registration): `docs/23_agent/agent_12_reference-api.md` | 2 | Doc-fix | Needs Confirmation | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003; AC-4, AC-5; U-1 owner
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-122302
- **Related target files**: `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
