## Goal

Add `tests/agent/test_tool_preparation.py`, a new test file covering the 8 acceptance
scenarios named in the plan (and the sibling requirement it traces to) for
`scripts/agent/tool_preparation.py::prepare_tool_calls()`: registry `None`, unregistered
name despite a matching stale `ctx.cfg.tool.tool_definitions` entry, malformed JSON,
non-dict decoded JSON value, schema violation, a mixed valid/invalid batch preserving
order, an approval-mock that must never be called for a call that failed preparation,
and a fully-valid call producing a correct `PreparedToolCall`.

## Scope

In scope: one new test file, `tests/agent/test_tool_preparation.py`, exercising only
`prepare_tool_calls()` and `PreparedToolCall` from `scripts/agent/tool_preparation.py`
(see that module's doc in this set for its exact shape/API). No production code change.

Out of scope: `tests/agent/test_tool_runner.py` and `tests/agent/
test_tool_approval_*.py` updates for the *downstream* consumption of `PreparedToolCall`
— separate docs in this set.

## Assumptions

- `prepare_tool_calls(ctx, tool_calls) -> tuple[list[PreparedToolCall], list[tuple]]`
  matches the shape specified in the `tool_preparation.py` doc: the second tuple element
  is a list of 6-tuples in `execute_one_tool_call()`'s existing return shape (`tc_id,
  name, args, text, is_error, llm_text`), letting these tests reuse the same assertion
  style already used in `tests/agent/test_tool_runner.py` for that tuple shape (e.g. its
  `TestExecuteOneToolCallValidation` class, confirmed present at lines 811+ of that
  file).
- This new test file can reuse the existing `_cfg()`/`_make_ctx()`/`_tc()`-style helper
  pattern already established in `tests/agent/test_tool_runner.py` (confirmed: that file
  defines `_cfg(**overrides)` at its top, building an `AgentConfig` via
  `build_agent_config`) — this doc's new file defines its own local equivalents rather
  than importing private helpers cross-file, matching this codebase's existing
  convention of each test file owning its own fixtures (confirmed: none of the five
  `test_tool_approval_*.py` files import fixtures from one another either).

## Design decisions

- **One test class per preparation-error kind, plus one for the happy path and one for
  batch-ordering/approval-isolation**, mirroring the existing `TestExecuteOneToolCall
  Validation` style in `test_tool_runner.py` (one method per scenario, each fully
  self-contained with its own `ctx`/`tc` construction).
- **Assert on the specific error-kind tag**, not just "is_error is True" — since the
  plan introduces five distinct machine-readable kinds (`configuration`, `unknown_tool`,
  `validation`, `schema`, `metadata`), each scenario's test should assert the resulting
  synthetic tuple's `error_type`/kind marker matches the expected kind, not merely that
  an error occurred, so a future regression that returns the wrong kind (e.g.
  `unknown_tool` misclassified as `validation`) is caught.
- **The "unregistered name with matching stale tool_definitions entry" scenario is the
  single most important regression test in this file** — it is the direct behavioral
  reproduction of the vulnerability this plan closes (a tool name absent from the
  registry but present in `ctx.cfg.tool.tool_definitions` must now be rejected, not
  silently accepted).

## Alternatives considered

- Parametrizing all 8 scenarios into one `@pytest.mark.parametrize` table. Considered,
  but rejected in favor of explicit per-scenario test methods: the existing
  `test_tool_runner.py`/`test_tool_approval_*.py` style in this codebase favors explicit,
  named test methods over parametrized tables for behaviorally distinct scenarios
  (confirmed: no `@pytest.mark.parametrize` use found in `test_tool_runner.py`'s
  validation-related classes), and each of these 8 scenarios has a distinct assertion
  shape (different kind tags, different call counts on the approval mock), which a
  shared parametrized body would make harder to read than help.

## Implementation

### Target file

`tests/agent/test_tool_preparation.py` (new file)

### Procedure

1. Module docstring: "Unit tests for tool_preparation.py: the fail-closed
   preparation phase run before approval." Imports: `from __future__ import
   annotations`; `unittest.mock.MagicMock`; `pytest`; `from agent.config_builders
   import build_agent_config`; `from agent.config_dataclasses import AgentConfig`; `from
   agent.tool_preparation import PreparedToolCall, prepare_tool_calls`.
2. Local helpers (mirroring `test_tool_runner.py`'s existing pattern):
   `_cfg(**overrides) -> AgentConfig` (same defaults shape as `test_tool_runner.py`'s
   `_cfg()`, reused/copied since this is a new, independent file); `_make_ctx(cfg)`
   building a mock `AgentContext` with `services_required.runtime_tools` settable per
   test; `_tc(name, args_str, call_id="call_1") -> dict` building a raw tool-call dict
   matching the LLM tool_calls wire shape (`{"id": call_id, "function": {"name": name,
   "arguments": args_str}}}`).
3. `class TestPrepareToolCallsConfigurationErrors:`
   - `test_registry_none_rejects_with_configuration_kind`: `ctx.services_required.
     runtime_tools = None`; call `prepare_tool_calls(ctx, [_tc("read_text_file",
     '{"path": "/tmp/f"}')])`; assert `prepared == []`; assert the one failure tuple's
     `is_error is True` and its reason/kind indicates `configuration`.
4. `class TestPrepareToolCallsUnknownTool:`
   - `test_unregistered_name_rejected_despite_matching_tool_definitions_entry`: this is
     the core regression test — `ctx.cfg.tool.tool_definitions = [{"function": {"name":
     "stale_tool"}}]` (a stale static entry matching the call's name by string), but
     `ctx.services_required.runtime_tools.get.side_effect = KeyError("stale_tool")` (not
     registered). Call `prepare_tool_calls(ctx, [_tc("stale_tool", "{}")])`; assert
     `prepared == []` and the failure's kind is `unknown_tool` — proving the
     `tool_definitions` entry is never consulted as a fallback.
5. `class TestPrepareToolCallsMalformedJson:`
   - `test_malformed_json_rejected_with_validation_kind`: `_tc("read_text_file",
     "{not valid json")`; assert rejection kind `validation`, reason references the
     invalid JSON.
   - `test_non_dict_decoded_value_rejected`: `_tc("read_text_file", "[1, 2, 3]")` (valid
     JSON, but an array, not an object); assert rejection kind `validation`, reason
     states arguments must decode to a JSON object.
6. `class TestPrepareToolCallsSchemaViolation:`
   - `test_schema_violation_rejected_with_schema_kind`: registry returns a
     `runtime_tool` mock with `input_schema` requiring `"path"`; call with
     `'{"unexpected": "field"}'`; assert rejection kind `schema`, reason surfaces the
     validation failure text (mirroring `test_tool_runner.py`'s existing
     `test_validation_failure_returns_error_result` assertion style: `"extra" in
     text`/`"extra" in llm_text` — here, asserting the missing/extra field name appears
     in the reason).
7. `class TestPrepareToolCallsHappyPath:`
   - `test_valid_call_produces_prepared_tool_call`: registry returns a valid
     `runtime_tool`; `registry.tool_spec_for_call.return_value = ToolSpec(call_id=
     "call_1", name="read_text_file", args={"path": "/tmp/f"})`; call `prepare_tool_calls`
     with one valid call; assert `len(prepared) == 1`, `prepared[0].call_id ==
     "call_1"`, `prepared[0].name == "read_text_file"`, `prepared[0].args ==
     {"path": "/tmp/f"}`, `prepared[0].spec is registry.tool_spec_for_call.return_value`,
     `prepared[0].original_call is` the original raw dict; assert `failures == []`.
8. `class TestPrepareToolCallsBatchOrdering:`
   - `test_mixed_valid_invalid_batch_preserves_order`: three calls — valid, invalid
     (unregistered), valid — with distinct `call_id`s; assert `len(prepared) == 2` and
     their `call_id`s match the two valid calls in original relative order; assert
     `len(failures) == 1` and its `tc_id` matches the invalid call's id.
   - `test_approval_never_called_for_failed_prep_call`: construct a batch with one
     failing call (unregistered) and one valid call; patch/mock
     `agent.tool_approval.check_approval` (or, at the integration level, patch
     `run_approval_checks`) and run the full `execute_all_tool_calls()` pipeline (or, if
     this test file should stay unit-scoped to `prepare_tool_calls()` alone per its
     Scope, assert instead that the failed call's id never appears in `prepared` —
     i.e. it structurally cannot reach the approval-gate call site since only
     `prepared` is passed to it. Prefer the structural assertion here, since wiring
     `execute_all_tool_calls()` end-to-end belongs to `test_tool_runner.py`'s own test
     suite, not this file's unit scope).

### Method

New file, written directly against the `prepare_tool_calls()`/`PreparedToolCall` API
specified in the `tool_preparation.py` doc in this set. Mirror existing test-style
conventions from `test_tool_runner.py` (`_cfg`/`_make_ctx`/`_tc` helper shapes,
`MagicMock`-based registry mocking) rather than inventing a new fixture style.

### Details

- `tests/agent/test_tool_runner.py`'s existing `TestExecuteOneToolCallValidation` class
  (lines 811+) already demonstrates the `ctx.services_required.runtime_tools =
  MagicMock(); ...runtime_tools.get.return_value = runtime_tool_mock` /
  `...get.side_effect = KeyError(...)` mocking pattern this new file reuses for
  registry-lookup scenarios — confirmed by direct read of that class's four methods
  (`test_validation_failure_returns_error_result`,
  `test_validation_passes_when_runtime_tools_is_none`,
  `test_validation_passes_for_unknown_tool`, `test_validation_passes_for_empty_schema`).

## Compatibility considerations

N/A — new test file, no existing test is modified by this doc.

## Security considerations

- This file is the acceptance test for the plan's core security fix (closing the
  `tool_definitions`-fallback silent-acceptance gap); its
  `test_unregistered_name_rejected_despite_matching_tool_definitions_entry` scenario is
  the direct regression guard against that gap being silently reintroduced in the
  future.

## Rollback considerations

- Deleting this new file has no effect on any other file; it exists purely to validate
  `tool_preparation.py`, whose own rollback is covered in that module's doc.

## Validation plan

`uv run pytest tests/agent/test_tool_preparation.py -v` — all 8 scenarios (across the 6
classes above) pass.

## Out of scope

- Updating `tests/agent/test_tool_runner.py` for `execute_one_tool_call()`'s new
  `PreparedToolCall`-accepting signature — separate doc.
- Updating `tests/agent/test_tool_approval_preflight.py` for `run_approval_checks()`'s
  new signature — separate doc.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184037_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-235944
- Related target files: test_tool_preparation.py
