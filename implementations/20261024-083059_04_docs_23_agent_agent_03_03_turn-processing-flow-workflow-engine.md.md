## Goal

Rewrite the two passages of `agent_03_03` that currently state the defective contract, so they describe
the new boundary: the `execute` stage performs only LLM/tool execution, and turn-entry preparation runs
once before the engine runs (`REQ-009`, `AC-9`).

## Scope

- Two sections only: `## Workflow Stages` (the stage table at `:79`) and `## Retry Mechanism`
  (`:82-88`).
- The stage timeout table and `max_attempts` values stay as written.

## Assumptions

- The reader infers from the Plan which effects move out of the `execute` stage; this document only
  restates the resulting contract in the two sections.

## Design decisions

- Remove "Memory injection, mode classification" from the `execute` row's responsibility; those are now
  the once-per-turn entry step, not a stage.
- State explicitly in the Retry Mechanism that a stage retry re-runs only LLM/tool execution and that
  entry preparation is not retried and leaves the stage timeout.

## Alternatives considered

- N/A: documentation-only wording change.

## Implementation

### Target file

`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`

### Procedure

1. `## Workflow Stages` — rewrite the `execute` row (`:79`) so its Responsibility is
   "LLM invocation, tool execution loop" only, and add one sentence after the table: turn-entry
   preparation (clear the previous turn's ephemeral messages, inject memory, classify the turn mode,
   append the user message, compress history) runs once per turn **before** the engine runs; it is not a
   stage and is not retried.
2. `## Retry Mechanism` (`:82-88`) — add one sentence after the retry-policy bullets: a retry of the
   `execute` stage re-runs only LLM/tool execution; turn-entry preparation ran once before the engine
   ran, is not re-run on retry, is not retried itself, and is not bounded by `execute.timeout_sec`
   (memory search and history compression keep their own bounds).

### Method

Before (`:79`):

```
| execute | Memory injection, mode classification, LLM invocation, tool execution loop | Yes |
```

After:

```
| execute | LLM invocation, tool execution loop (per-attempt; retried per the retry policy) | Yes |
```

Add after the table:

> Turn-entry preparation — clearing the previous turn's ephemeral messages, injecting memory,
> classifying the turn mode, appending the user message, and compressing history — runs once per turn
> before the engine runs. It is not a stage and is not re-run when the `execute` stage is retried.

Before (`:84-88`, the retry-policy paragraph and bullets):

```
All `plan`/`execute`/`verify` stages go through the same retry loop function. Stages where `retryable`
is `false` (default: `plan` and `verify`) are executed once and raise an exception immediately upon
failure. For stages where `retryable` is `true` (default: `execute`), retry behavior is determined by
the retry policy:

- `max_attempts`: Maximum number of attempts
- Backoff strategy is currently implemented as "fixed" only
- `backoff_sec`: Delay between retries
```

After — keep everything above and append one paragraph:

> A retry of the `execute` stage re-runs only LLM/tool execution. Turn-entry preparation runs once per
> turn before the engine runs; it is not re-run on a retry, is not retried itself, and is not bounded
> by `execute.timeout_sec`. Memory search and history compression keep their own timeouts.

### Details

- Do not touch the `plan`/`verify` rows, the timeout table, or any section outside these two.
- Wording must stay consistent with `docs/23_agent/agent_03_01_turn-processing-flow-overview.md`
  (Row 5), which restates the same boundary in the overview.

## Compatibility considerations

- N/A: documentation-only wording change.

## Security considerations

- N/A: documentation-only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_content_policy.py`

All three must report no finding (`AC-9`).

## Completion criteria

- `:79` no longer attributes memory injection or mode classification to the `execute` stage; both
  chapters state the once-per-turn entry step; the three docs checkers report no finding (`AC-9`).

## Out of Scope

- `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` — Row 5.
- Any other chapter; `grep` found no stage-retry or user-append claim elsewhere that would drift.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | rewrite :79 and :82-88 |
| 2 | Add or update tests per Validation plan | N/A: documentation-only | — | — | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | docs checkers below |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this file |

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
- **Requirement ID**: `REQ-009` (the two agent turn-processing chapters describe the new once-per-turn / per-attempt boundary)
- **Source issue**: issues/20261021-093421_turn002_execute-stage-retry-duplicates-user-messages.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-102728_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-083059
- **Related target files**: docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md
