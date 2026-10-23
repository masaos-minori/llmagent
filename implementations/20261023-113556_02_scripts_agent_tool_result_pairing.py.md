## Goal

Provide the round's result synthesis: given the declared ids, the already-answered
ids, the ids whose results were collected, and a closed stop reason, return one
synthesized `(LLMMessage, tool_row)` pair per still-unanswered declared id, in
declared order (`REQ-001`, `REQ-004`). This is the pure core that lets
`scripts/agent/tool_runner.py` answer every declared id when a round fails by
raising (`REQ-010`).

## Scope

New pure module `scripts/agent/tool_result_pairing.py`. No I/O, no agent, shared,
services, or workflow_engine import (`REQ-013`, `DR-003`). Reference reads:
`scripts/agent/tool_enums.py` (`ToolCallStopReason`, this row does not create),
`scripts/agent/tool_runner.py::_build_denied_messages` (the pair shape this row
mirrors), `scripts/agent/tool_result_formatter.py::format_error_payload` (the
payload this row must NOT imitate). Dependent test:
`tests/agent/test_tool_result_pairing.py`.

## Assumptions

- The set of ids that already have a row is exactly `{collected keys} ∪
  prep-failure ids ∪ denied ids` (`ASSUM-03`); anything declared but absent from
  that union was never answered and must be synthesized.
- A call that never ran did not fail, so its synthesized row must not read as an
  error result and must not be mistaken by the empty-result guard (`ASSUM-04`,
  `REQ-005`); the payload names a stop reason from a closed two-member set instead.
- `LLMMessage` and the tool-row tuple shape are imported from `shared.types` /
  reused from `tool_runner.py`'s convention; importing `LLMMessage` from
  `shared.types` is not an `agent.*` layer violation.

## Design decisions

- **The synthesis is a pure function.** `pair_round_results(declared, answered,
  collected, stop_reason)` takes ordered declared ids, the set of already-answered
  ids, the collected map (for its keys), and a `ToolCallStopReason`, and returns
  `[(LLMMessage, tool_row), ...]` for `declared − answered − collected.keys()`.
  Pure = testable without a session fixture and immune to side effects
  (`DR-003`, `REQ-013`).
- **One payload text per stop-reason member.** Each member of
  `ToolCallStopReason` has one module-level constant string, shaped like
  `_build_denied_messages`' fixed text (`tool_runner.py:416`), not a copy of
  `format_error_payload()` output (`REQ-004`).

## Alternatives considered

- Inline in `tool_runner.py` (15526 B, no baseline, needs a session fixture to
  test) or inline in `tool_loop_guard.py` (wrong owner) — rejected by `DR-003`.
- Reusing `format_error_payload()` or `_reject()` — a call that never ran did not
  fail, and conflating the two would make the error counts and error-limit guard
  read calls that never happened as errors (`DR-003`).

## Implementation

### Target file

`scripts/agent/tool_result_pairing.py` (new)

### Procedure

Create the file with these contents:

1. Module docstring stating it is pure logic for round result pairing and carries
   no I/O.
2. Import `LLMMessage` from `shared.types` (the message type `tool_runner.py`
   already builds) and `ToolCallStopReason` from `agent.tool_enums`. Do not import
   any other `agent.*`, `shared.*` beyond `shared.types.LLMMessage`, `services.*`,
   or `workflow_engine.*` (`REQ-013`).
3. Define one payload-text constant per member of `ToolCallStopReason`, e.g.
   `_GUARD_STOP_TEXT` and `_ROUND_NOT_COMPLETED_TEXT`. Each states the call was not
   executed; neither equals `format_error_payload()` output nor the
   `"Tool execution denied by user."` literal (`REQ-004`).
4. Define `pair_round_results(declared, answered, collected, stop_reason)`:
   - Compute `missing = [d for d in declared if d not in answered and d not in collected]`,
     preserving declared order (`REQ-009`).
   - For each missing id, build `msg = LLMMessage(role="tool", tool_call_id=id,
     content=payload[stop_reason])` and `row = ("tool", payload[stop_reason], None,
     id)`, mirroring `_build_denied_messages` (`tool_runner.py:419-427`).
   - Return `[(msg, row) for id in missing]`.
5. Add the file's test `tests/agent/test_tool_result_pairing.py` and run
   `uv run python tools/check_docstrings.py` plus
   `uv run python tools/check_module_size.py` (`REQ-013`, AC-8).

### Method

- Function-only module; no class, no `__init__`, no module-level state.
- `answered` is accepted as an iterable/set of ids; `collected` is accepted as the
  map (only its keys are used). Keep the signature positional and small so the
  pure test constructs arguments directly.

### Details

- Declared order is preserved even when `collected` was filled out of order (the
  DAG sort at `tool_runner.py:330-332` and `:383-385` is the behavior preserved,
  `REQ-009`).
- A duplicated declared id yields one row (list comprehension over `declared`,
  not over a set).
- An empty declaration yields no rows.
- The payload is one constant per enum member; an unknown reason cannot be
  constructed because the enum has exactly two members (`REQ-004`).

## Compatibility considerations

- Pure function; no caller contract beyond its parameters. `tool_runner.py`
  imports it and merges its output into the existing `save_many()` batch.

## Security considerations

- N/A: pure logic, no auth, secret, permission, or policy path.

## Rollback considerations

- Delete the new file; nothing else references it until `tool_runner.py` imports
  it. Reversible; no config or DB.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_pairing.py -q --timeout=120` —
  missing ids synthesized; already-answered, preparation-failure, and denial ids
  not; duplicated declared id yields one row; empty declaration yields none; each
  stop reason yields its own distinct text; output order equals declared order;
  each synthesized message passes `validate_message()` with `role='tool'` and
  `tool_call_id` set.
- `uv run python tools/check_docstrings.py` and `uv run python
  tools/check_module_size.py` report no finding.
- `PYTHONPATH=scripts uv run lint-imports` and `uv run python
  tools/check_imports.py` confirm no cycle and no layer violation (`REQ-013`).

## Completion criteria

`pair_round_results` returns one correctly-shaped `(LLMMessage, tool_row)` pair
per declared id not already answered, in declared order, with a payload drawn from
the closed two-member stop-reason set; the module imports no forbidden package
and passes docstring and module-size checks.

## Out of Scope

- Defining `ToolCallStopReason` — row 3.
- Consuming the pairs — `tool_runner.py` (row 1).
- `GuardDecisionType` is not extended: a synthesized row is a result, not a guard
  decision.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create pure module with `pair_round_results` and one payload per `ToolCallStopReason` (REQ-001, REQ-004) | Pending | — | — | Phase 1 |
| 2 | Add pure-function test file; run docstring + module-size checks (REQ-013) | Pending | — | — | Phase 1 |

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
- **Requirement ID**: REQ-001, REQ-004, REQ-010, REQ-013
- **Source issue**: `issues/20261021-093421_tool002-tool-call-persisted-without-tool-results.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-105432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-113556
- **Related target files**: `scripts/agent/tool_result_pairing.py`
