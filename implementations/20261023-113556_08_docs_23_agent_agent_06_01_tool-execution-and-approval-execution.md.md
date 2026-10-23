## Goal

State the round pairing invariant this code now guarantees in
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
(`AC-6`): every declared `tool_call_id` that reached the round has exactly one
persisted `role='tool'` row, the two stop reasons a synthesized row can state, and
that a synthesized row does not affect stats or guard state.

## Scope

Documentation update to `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
only. Scope rule: only the `### Result Reflection in History` section (`:68-70`)
plus one `## Key Constraints` bullet for the mid-round stop. `## Known Limitations`
(:82-84) stays accurate. Reference reads: `scripts/agent/tool_runner.py` (row 1),
`scripts/agent/tool_enums.py` (row 3), `docs/23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md`
(row 9).

## Assumptions

- The invariant is real at HEAD-after-implementation: the round owns `collected`,
  records each real result at the production point, and synthesizes one row per
  unanswered declared id on normal or exceptional completion.

## Design decisions

- Extend the existing `### Result Reflection in History` section rather than add a
  new one, so `docs/00_index.md` mapping is unchanged (no new file).

## Alternatives considered

- A new dedicated document — rejected by the scope rule; the invariant belongs to
  tool execution, which this document already covers.

## Implementation

### Target file

`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure

1. Extend `### Result Reflection in History` (`:68-70`) to state:
   - The round answers every declared `tool_call_id` it received: exactly one
     `role='tool'` row exists in history and in `session_messages` when the round
     ends, whether it completed normally or failed by raising.
   - A call the round did not execute is answered by a synthesized row whose text
     states one of two stop reasons: the round stopped by a guard observation, or
     the round did not complete (`ToolCallStopReason`).
   - A synthesized row does not change `ctx.stats`, does not add to
     `out_failed_keys`, and does not feed the empty-result guard.
2. Add one bullet to `## Key Constraints` (:77-80): a mid-round guard stop ends
   the remaining calls of the sequential group and the remaining batches of the
   plan; those ids are answered by the synthesized row.

### Method

- Edit the two sections in place. Do not touch `## Known Limitations` (:82-84).

### Details

- Keep the existing sentence about `append_message()` / `extend_messages()`; add
  the invariant paragraph after it.

## Compatibility considerations

- Documentation only; no code, config, or `docs/00_index.md` change.

## Security considerations

- N/A: documentation only.

## Rollback considerations

- Revert the two-section edit; `git checkout -- docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`.

## Validation plan

- `uv run python tools/check_docs_structure.py`, `uv run python
  tools/check_docs_consistency.py`, `uv run python tools/check_docs_content_policy.py`
  report no finding (`AC-6`).

## Completion criteria

`### Result Reflection in History` states the round invariant, both stop reasons,
and that a synthesized row does not affect stats or guard state; `## Key
Constraints` carries the mid-round-stop bullet; all three docs validators pass.

## Out of Scope

- Correcting `agent_03_02:78` — row 9.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `### Result Reflection in History` with the round invariant, two stop reasons, stats/guard note (AC-6) | Pending | — | — | Phase 3 |
| 2 | Add mid-round-stop bullet to `## Key Constraints` | Pending | — | — | Phase 3 |
| 3 | Run docs validators (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: N/A: documentation section (AC-6)
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
