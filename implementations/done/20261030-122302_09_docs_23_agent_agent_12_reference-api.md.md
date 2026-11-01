# Procedure: agent_12 caller fixes (:101/:114) (additional row 09)

**Doc ID:** 20261030-122302_09
**Target File:** `docs/23_agent/agent_12_reference-api.md`
**Change Type:** docs | **Priority:** P2 | **Plan Phase:** 2 (additional row)

## Goal
Fix the stale caller claims found by doc 02's U-1 sweep: `:101` (LLMClient) and `:114`
(ToolExecutor) cite `LlmTurnExecutor` as caller; the actual turn-path caller is
`LLMTurnRunner`.

## Scope
- `:101` Caller line (LLMClient section): `LlmTurnExecutor`, `SessionTitleService` →
  `LLMTurnRunner` (per-turn instance created by `LlmTurnExecutor`), `SessionTitleService`.
  Verified: `ctx.services_required.llm.stream` is called only from `llm_turn_runner.py`
  (:284/:343 working tree) plus `SessionTitleService` (`scripts/agent/services/session_title.py`).
- `:114` Caller line (ToolExecutor section): `LlmTurnExecutor` (via `execute_all_tool_calls`)
  → `LLMTurnRunner` (via `execute_all_tool_calls`). Verified: the only production call of
  `execute_all_tool_calls` is `llm_turn_runner.py:158` (working tree; :116 at HEAD).
- Nothing else in the file; `agent_12` is hand-maintained (agent_13 is the generated twin).

## Assumptions
- Registered as an additional target row 2026-10-31 with owner confirmation (doc 02
  Blocker Log; plan Implementation Target Files table).

## Design decisions
- Keep the `SessionTitleService` citation (verified accurate); replace only the executor
  name with the runner, adding the per-turn-instance parenthetical once (docs content
  policy: no signatures/paths).

## Alternatives considered
- Removing the sections' Caller lines: rejected — the fix is a name correction, not a
  schema change.

## Implementation
1. Apply the :101 and :114 corrections.
2. Confirm the diff touches only those two lines.

## Compatibility considerations
- `agent_13_reference-api-generated.md` regeneration (doc 02 Step 4) is separate; this row
  edits only the hand-maintained file.

## Security considerations
None.

## Rollback considerations
Revert the file.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`.

## Completion criteria
:101/:114 name `LLMTurnRunner` as caller; diff limited to those lines.

## Out of Scope
`agent_13` regeneration (doc 02 owns it); other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply :101/:114 caller corrections | Completed | — | 20261031-211706 | Registered 2026-10-31 verification: :101 stale (LLMClient persistent instance from factory, called by LLMTurnRunner._stream_llm via ctx.services_required.llm) fixed; :114 accurate (chain LLMTurnRunner -> tool_runner.execute_all_tool_calls -> ToolExecutor) unchanged; agent_13 regenerated (1-line diff); gates: consistency agent + quality Pass |
| 2 | Diff review + docs checkers | Completed | — | 20261031-211706 | verification: :101 stale (LLMClient persistent instance from factory, called by LLMTurnRunner._stream_llm via ctx.services_required.llm) fixed; :114 accurate (chain LLMTurnRunner -> tool_runner.execute_all_tool_calls -> ToolExecutor) unchanged; agent_13 regenerated (1-line diff); gates: consistency agent + quality Pass |

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
- **Related target files**: `docs/23_agent/agent_12_reference-api.md`