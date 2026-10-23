# Implementation Procedure: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

## Goal

State what a failed call contributes to a round and that a round is total, in the tool-execution document. Implements `REQ-001` (every started call contributes one persisted row), `REQ-007` (a failure does not stop later calls or later batches), and `REQ-009` (an all-failing round is counted by the turn-level guard and can stop the turn).

## Scope

Extend exactly two regions of `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`:
- **"Result Reflection in History"** (`:68-70`) — add what the model sees for a failed call (the `[Tool execution failed: ...]` marker, that completed siblings are still recorded, and that side effects are not undone).
- **"Key Constraints"** (`:77-80`) — add one bullet for the batch-total rule.

Do NOT restate "Parallel vs Sequential Execution" (`:35-38`). Do NOT restate or edit the round-pairing invariant owned by `plans/20261022-105432_plan.md`. Do NOT touch "Known Limitations" (`:82-84`).

## Assumptions

- The production change lives in `scripts/agent/tool_runner.py` (row 1) and the failure-text builder in `scripts/agent/tool_result_formatter.py` (row 2); this document only describes their observable behavior.
- The same section (`:68-70`) and same "Key Constraints" region are extended by `plans/20261022-105432_plan.md` Phase 2; this Plan's row states only the per-call failure semantics and must not restate the pairing invariant.

## Design decisions

- **Two targeted edits, not a rewrite.** The failure semantics are a property of result reflection, so they belong in "Result Reflection in History"; the invariant that a round is total is a constraint, so it belongs in "Key Constraints". This matches where the surrounding claims already live.

## Alternatives considered

- **Adding a new subsection.** Rejected: the section anchors ("Result Reflection in History", "Key Constraints") are the ones the plan cites and the docs checkers key on; a new heading would fragment the topic and is not what the evidence points to.

## Implementation

### Target file

`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure

1. **Extend "Result Reflection in History"** (`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md:68-70`). After the existing sentence, add a paragraph stating that a round is total: every call the round starts contributes exactly one `tool` row, including a call whose execution raised. That row carries the fixed `[Tool execution failed: <Class>: <message>]` marker (built in `scripts/agent/tool_result_formatter.py`) with `is_error` semantics, so the model sees the failure; calls that completed alongside it are still recorded; and tool side effects are not undone. Keep it to a few sentences in the document's existing style.

2. **Add one "Key Constraints" bullet** (`:77-80`). Append a bullet: a tool round is total — a single call raising does not drop the results of its siblings, of later groups in the same batch, or of later batches, and does not stop later calls in the same group; an all-failing round is counted by the turn-level error guard (`scripts/agent/tool_loop_guard.py:392-405`) and can stop the turn at `tool_error_max_consecutive` (`config/agent.toml:59`).

3. **Leave "Known Limitations" (`:82-84`) untouched.** The claim there that `_check_type_validation()` does not catch `jsonschema.SchemaError` is stale at HEAD but belongs to the preparation phase, not this round-failure topic; correcting it is out of scope (`UNK-03`). Do not fold it into this row.

### Method

Edit in place: one edit to "Result Reflection in History", one edit to "Key Constraints". Verify with `git diff` that only those two regions changed and that `:35-38`, `:82-84`, and the round-pairing language are byte-identical to HEAD.

## Compatibility considerations

N/A: this extends an existing user-facing doc; the four docs checkers (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain agent`) validate the result.

## Security considerations

N/A: documentation text only; no code or secrets.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py` — no structural warning.
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` — structure valid.
- `uv run python tools/check_docs_content_policy.py` — no content-policy finding.
- `uv run check-agent-docs` — clean.
- `uv run python tools/check_docs_consistency.py --domain agent` — no claim drift against `config/agent.toml` or `scripts/` (e.g. the `tool_error_max_consecutive` reference must match `config/agent.toml:59`).

## Completion criteria

- "Result Reflection in History" states that a failed call contributes one `tool` row with the execution-failure marker and that completed siblings are still recorded.
- "Key Constraints" carries the batch-total bullet.
- All four docs checkers pass with no new finding; `:35-38` and `:82-84` unchanged.

## Out of Scope

- The production wrapper in `scripts/agent/tool_runner.py` (row 1).
- The round-pairing invariant owned by `plans/20261022-105432_plan.md` (not restated here).
- The stale `_check_type_validation()` claim at `:84` (`UNK-03`) — separate documentation issue, out of scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document per-call failure semantics in "Result Reflection in History" + batch-total "Key Constraints" bullet | Pending | — | — | Extend `:68-70` and `:77-80`; do not restate the pairing invariant |
| 2 | Run the four docs checkers (`routing.md` Tools) | Pending | — | — | No new finding; `:82-84` left untouched |

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
- **Requirement ID**: `REQ-001`, `REQ-007`, `REQ-009`
- **Source issue**: issues/20261021-093421_tool003-gather-without-return-exceptions-drops-sibling-results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-004538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-115145
- **Related target files**: docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md
