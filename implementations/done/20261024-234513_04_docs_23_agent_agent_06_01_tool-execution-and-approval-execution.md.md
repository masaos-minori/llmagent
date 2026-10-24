# Implementation Procedure: docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md

## Goal

State in `Argument Validation` how a call rejected for a missing `id` or missing `function.name` is
answered and that the round still completes in batch order, and record the two pairing limits (id-less
positional pairing; duplicate-real-id collapse `D-3`) in `Known Limitations` (`REQ-008` malformed-call
outcome documented; `AC-9`).

## Scope

- Two additions to `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`: one sentence
  pair after the `Argument Validation` closing paragraph (`:66`), two bullets in `Known Limitations`
  (`:85-87`). No other section changes.

## Assumptions

- The doc already carries the fail-closed preparation contract (`:59-66`) and the per-id answering
  contract (pairing sentence at `:72`); only the outcome and the limits are missing (revalidation
  record).

## Design decisions

- Contract-level prose only: no helper names, no line numbers, no algorithm description —
  `check_docs_content_policy.py --strict` (CI) excludes implementation detail.
- Do not touch the first line of any public docstring in `scripts/agent/` while wording the addition;
  `docs/23_agent/agent_13_reference-api-generated.md` is generated from public top-level symbols
  (ADR-015 guard).

## Alternatives considered

N/A: the target section pair is fixed by the Plan row and `Documentation Impact`.

## Implementation

### Target file

`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure

Append after the paragraph ending `...do not perform their own argument validation or registry
lookups.` (`:66`):

> A preparation rejection is answered, not fatal: the rejected call contributes one `tool` message at
> its batch position carrying the rejection reason (a missing or empty `id` is answered with
> `tool_call_id == ""`), and the round completes for the remaining calls. A malformed provider tool
> call never aborts a turn.

Add to `Known Limitations` (`:87` list):

> - A result whose `tool_call_id` is empty can only be paired positionally: it is matched to the
>   batch entry lacking an id in declared order.
> - Repeated `tool_call_id` values in one assistant message collapse to a single answered row: a
>   second call sharing a real id produces no second result row.

### Method

Direct edits; no restructuring of existing sentences; the pairing sentence at `:72` and the Key
Constraints list stay unchanged.

### Details

N/A: the two insertions above are the whole change.

## Compatibility considerations

N/A: prose-only addition to one doc file already registered in `docs/00_index.md`'s "Agent REPL flow /
tool execution" task scope.

## Security considerations

N/A: documentation text; describes an error-answer contract, no secrets.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_structure.py '23_agent/agent_06_01_*.md'`
- `uv run python tools/check_docs_content_policy.py` (and `--strict`, as CI runs it) → no
  implementation-detail finding in the added text.
- `uv run python tools/check_docs_consistency.py --domain agent` → symbol references consistent.
- `uv run python tools/generate_reference_table.py --check` → no drift (no public docstring touched).

## Completion criteria

- Both insertions present in the named sections; the malformed-call outcome (`AC-1` behavior), the
  positional-pairing limit, and the `D-3` collapse are each stated once; all four checkers pass.

## Out of Scope

- `docs/23_agent/agent_03_01_turn-processing-flow-overview.md` (named by the index row but not the
  changed contract — Plan `Documentation Impact`).
- The pairing sentence at `:72` and the Key Constraints section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the outcome sentences to `Argument Validation` and the two bullets to `Known Limitations` | Completed | 20261025-0100 | 20261025-0100 | land after the code row so the doc describes shipped behavior |
| 2 | Run the docs checkers listed in Validation plan | Completed | 20261025-0100 | 20261025-0100 | Validation glob corrected to `docs/23_agent/agent_06_01_*.md` (glob is repo-root relative) |

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
- **Requirement ID**: `REQ-008` (documentation states the per-call malformed-call outcome)
- **Source issue**: `issues/20261021-093421_tool004-missing-tool-call-id-raises-keyerror.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-023815_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-234513
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`
