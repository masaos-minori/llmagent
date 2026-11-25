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
- `ReplayDirective` (new) is a dataclass whose fields are `original_call_id` (new), `task_id`, `tool`,
  `args_hash`, and `consumed`; it stays inside the `agent` layer, so no import-linter boundary changes.
  Validation correction: it is not frozen — `consumed` is set by the matching helper, and a frozen dataclass
  cannot carry one-time consumption without a second holder object.
- Matching, ambiguity, consumption, and the id choice are extracted into one helper that returns the resolved
  call id or the rejection tuple, so `_prepare_one` gains exactly one branch (radon C (16) → C (17)) instead of
  the three branches inline matching would add (`rules/toolchain.md` complexity gate).

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
- Add `_resolve_replay_call_id` (new) that takes the prepared call's tool name and `_canonical_args_hash(args)`
  and returns the resolved logical call id: the single unconsumed directive's original id for the current task
  (marked consumed), a fresh `_logical_call_id()` when nothing matches, or the `_reject` tuple when more than one
  directive matches.
- In `_prepare_one`, after the arguments are validated and before the context is built, consult the helper and
  return its rejection tuple when it is one; otherwise use the returned id as `ToolExecutionContext.call_id`.

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
| 1 | Add `ReplayDirective` (new) and `_match_replay_directive` (new) | Completed | — | 20261125-125350 | ReplayDirective is not frozen (consumed must be mutable); helper named _resolve_replay_call_id returns the resolved id or the _reject tuple |
| 2 | Attach the original id in `_prepare_one`, consume once, fail closed | Completed | 20261125-125350 | 20261125-125350 | ambiguity kind added to _reject's free-string vocabulary; _prepare_one radon C(16) -> C(17), one added branch ambiguity kind added to _reject's free-string vocabulary; _prepare_one radon C(16) -> C(17), one added branch |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-125350 | 2026-11-25 | ruff/mypy/bandit/module-size/lint-imports/mock-patch-targets pass; tests/agent/test_tool_preparation.py 19 passed (existing); new directive tests come from procedure 09 end-of-batch run: full suite 14240 passed, diff-cover 100% on changed lines, pre-commit all hooks pass, cited ADR tests 75 passed |

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