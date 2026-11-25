## Goal
Define the one-time `ReplayDirective` (new) and match a reissued call to it during preparation, reusing the
original logical call id.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The directive's `original id` and `original call id` are the same value after the mcpdl001 id unification;
  both fields are kept as the Issue states.
- Directives are read from `TurnState.replay_directives` (sibling procedure seq 04), populated at turn entry
  by the adapter.

## Design decisions
- `ReplayDirective` (new) is a frozen dataclass whose fields are `original_call_id` (new), `task_id`, `tool`,
  `args_hash`, and `consumed`; it stays inside the `agent` layer, so no import-linter boundary changes.
- Matching is extracted into its own helper so `_prepare_one`, already at radon C rank, does not grow further
  (`rules/toolchain.md` complexity gate).

## Alternatives considered
- Matching inside `_prepare_one` inline — rejected: it adds branches to a C-rank function and mixes id
  assignment with matching.

## Implementation
### Target file
`scripts/agent/tool_preparation.py`

### Procedure
Add the directive dataclass, the matching helper, and the id attachment in `_prepare_one`.

### Method
- Add `ReplayDirective` (new) with the fields above.
- Add `_match_replay_directive` (new) that takes the prepared call's tool name and `_canonical_args_hash(args)`
  and returns the single unconsumed directive for the current task, `None` when nothing matches, and the set of
  matches when more than one matches.
- In `_prepare_one`, after the arguments are validated and before the context is built, consult the helper: on a
  single match, use the directive's original call id as `ToolExecutionContext.call_id` and mark the directive
  consumed; otherwise keep the fresh `_logical_call_id()`.

### Details
- Ambiguity is fail closed: when several directives match, return `_reject(tc_id, name, args, "ambiguity", ...)`
  listing the matching ids, so the call never reaches dispatch. `ambiguity` is a new `kind` value in the existing
  free-string vocabulary of `_reject`.
- Consumption is per directive object: a second call in the same batch that would match the same directive gets
  no directive and proceeds as a new call, because the directive is already consumed.
- A reissue with edited arguments produces a different hash, so no directive matches and the call proceeds as a
  new call — the intended behavior.
- `PreparedToolCall` gains no field; the attachment happens inside the context construction, so consumers listed
  in the Plan's consumer scan (`tool_approval.py`, `tool_run_recorder.py`, `repository_gateway.py`) are unaffected.

## Compatibility considerations
The helper reads directives through `AgentContext`, which is already imported under `TYPE_CHECKING`; no runtime
import is added.

## Security considerations
The id is never taken from LLM text: the LLM-supplied `tc_id` is still validated by `_malformed_id_reason`, and
the id attached to the context comes only from the Agent-side directive.

## Rollback considerations
N/A: revert the commit; the dataclass and the matching helper are used only by this module and the adapter.

## Validation plan
- `uv run pytest tests/agent/test_tool_preparation.py` — match, one-time consumption, ambiguous-match structured
  error (AC-002).
- `uv run python tools/check_module_size.py` — the module stays under the 24576 B gate.
- Full sequence per `rules/toolchain.md`, including `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
A reissued call whose tool name and canonical hash match exactly one directive is prepared with the original id,
a second matching call gets no directive, and an ambiguous match is rejected at preparation without dispatch.

## Out of Scope
No directive persistence, no change to the approval grant or the transport DTO.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `ReplayDirective` (new) and `_match_replay_directive` (new) | Pending | — | — | |
| 2 | Attach the original id in `_prepare_one`, consume once, fail closed | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (directive type and one-time consumption), `REQ-002` (matching and id attachment), `REQ-003` (fail closed on ambiguity)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `scripts/agent/tool_preparation.py`
