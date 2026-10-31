# Procedure: mcp_03_01 `_stream_llm` method-owner fix (additional row 08)

**Doc ID:** 20261030-122302_08
**Target File:** `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
**Change Type:** docs | **Priority:** P2 | **Plan Phase:** 2 (additional row)

## Goal
Fix the stale method-owner claim found by doc 02's U-1 sweep: `:82` attributes
`_stream_llm()` to `LlmTurnExecutor`; the method lives on `LLMTurnRunner`.

## Scope
- `:82` sentence: `LlmTurnExecutor._stream_llm()` → `LLMTurnRunner._stream_llm()`; the
  sentence's filtering claim itself stays (verified: the only call site of
  `registry.llm_tool_definitions()` in the turn path is `llm_turn_runner.py:334` inside
  `_stream_llm` (working tree; :292 area at HEAD), with the
  `ctx.cfg.tool.tool_definitions` fallback at `:336`).
- Nothing else in the file.

## Assumptions
- Registered as an additional target row 2026-10-31 with owner confirmation (doc 02
  Blocker Log; plan Implementation Target Files table).
- Row 01 landed (frozen-row dependency mirrors rows 02-04).

## Design decisions
- Minimal owner-name correction; no rewording of the filtering stages.

## Alternatives considered
- Rewording the whole paragraph: rejected — the paragraph is otherwise verified accurate.

## Implementation
1. Apply the `:82` owner-name correction.
2. Confirm the diff touches only that sentence.

## Compatibility considerations
- Phase 2 gate covers `docs/22_mcp` via `check_docs_quality.py` / `check_docs_structure.py`
  / `check_docs_content_policy.py`; `check_docs_consistency.py --domain agent` covers the
  agent-side docs.

## Security considerations
None.

## Rollback considerations
Revert the file.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`.

## Completion criteria
`:82` names `LLMTurnRunner` as the `_stream_llm` owner; diff limited to that sentence.

## Out of Scope
Other `mcp_03_01` content; `scripts/` edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply :82 owner-name correction | Completed | — | 20261031-211703 | Registered 2026-10-31 stale ownership ref fixed: :82 owner attribution corrected (LLMTurnRunner._stream_llm is sole LLM-call path); gates: consistency mcp + quality Pass |
| 2 | Diff review + docs checkers | Completed | — | 20261031-211703 | stale ownership ref fixed: :82 owner attribution corrected (LLMTurnRunner._stream_llm is sole LLM-call path); gates: consistency mcp + quality Pass |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure (additional-row registration)
- **Requirement ID**: U-1 sweep follow-up (doc 02)
- **Source issue**: `issues/20261029-104510_turnadr001_align-adr014-loop-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_turnadr001_align-adr014-loop-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261031-191800 (owner-confirmed registration during doc 02 cycle)
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`