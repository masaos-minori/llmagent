## Goal

Update `tests/agent/test_tool_approval_preflight.py`'s `TestRunApprovalChecks` class
(current lines ~730-831) for `run_approval_checks()`'s new signature (see the
`tool_approval.py` doc in this set): it now takes/returns `list[PreparedToolCall]`
instead of raw `tc: dict`, and no longer has its own lenient JSON-decode fallback.

## Scope

In scope: `tests/agent/test_tool_approval_preflight.py`'s `TestRunApprovalChecks` class
only (5 methods: `test_approved_calls_returned`, `test_denied_calls_collected`,
`test_plan_mode_blocks_configured_tools`,
`test_plan_mode_does_not_block_unlisted_tools`,
`test_invalid_json_arguments_does_not_crash`) and this file's import block.

Out of scope: this file's other classes (confirmed via `grep -n "^class "` that this
class is dedicated to `run_approval_checks()`; every other class in the 831-line file
tests `check_approval()`, `log_approval_decision()`, and preflight policy checks, none
of which change signature in this plan).

## Assumptions

- `PreparedToolCall(call_id, name, args, spec, original_call)` is the shape specified in
  the `tool_preparation.py` doc; these tests construct it directly (not via
  `prepare_tool_calls()`, since these are unit tests of `run_approval_checks()` in
  isolation, not of preparation) with a placeholder `spec` (any `ToolSpec` instance,
  since `run_approval_checks()` never reads `pc.spec` — confirmed by that function's
  body, which only reads `pc.name`/`pc.args`/`pc.call_id`).

## Design decisions

- **Delete `test_invalid_json_arguments_does_not_crash` rather than adapt it.** Its
  premise — that `run_approval_checks()` receives a raw call with malformed JSON and
  must not crash — no longer applies: after this plan, `run_approval_checks()` only ever
  receives `PreparedToolCall`s whose `args` are already a valid, parsed `dict` (malformed
  JSON is rejected earlier, in preparation, and never becomes a `PreparedToolCall` at
  all). Keeping a test that manually constructs a `PreparedToolCall` with a string
  `args` value to simulate this would test an impossible/artificial state, not real
  behavior — removed rather than kept as dead-state coverage. The equivalent
  malformed-JSON-rejection scenario is covered instead in `test_tool_preparation.py` (see
  that file's doc), where it belongs.
- **The remaining four scenarios keep their names and assertions unchanged**, only their
  input construction changes (`tc: dict` → `PreparedToolCall`) and their `approved[0]`
  assertions gain a field-access adaptation (`approved[0].name` instead of
  `approved[0]["function"]["name"]`, where such an assertion exists).

## Alternatives considered

- Keeping `test_invalid_json_arguments_does_not_crash` but changing its intent to assert
  that *preparation* (not `run_approval_checks()`) rejects the malformed call, by
  patching `prepare_tool_calls` inside this test. Rejected: this test file is scoped to
  `run_approval_checks()`/`check_approval()`/preflight behavior specifically (per its own
  module docstring, "Covers ... execute_one_tool_call(), log_approval_decision(), and
  run_approval_checks()"); pulling `prepare_tool_calls()` into scope here would blur that
  file's boundary — better to add the scenario to `test_tool_preparation.py`, which
  already owns it.

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. Update the import block (current lines 14-19 area) to add `from agent.
   tool_preparation import PreparedToolCall` and (if not already present) `from
   shared.tool_spec import ToolSpec`.
2. Add a tiny local helper near the top of the `TestRunApprovalChecks` class or the
   file's shared fixtures section:
   ```python
   def _pc(name: str, args: dict, call_id: str = "call_1") -> PreparedToolCall:
       return PreparedToolCall(
           call_id=call_id,
           name=name,
           args=args,
           spec=ToolSpec(call_id=call_id, name=name, args=args),
           original_call={"id": call_id, "function": {"name": name, "arguments": "{}"}},
       )
   ```
3. `test_approved_calls_returned`: replace the `tool_calls = [{"id": "call_1",
   "function": {"name": "list_directory", "arguments": '{"path": "/tmp"}'}}]` literal
   with `prepared = [_pc("list_directory", {"path": "/tmp"})]`; change the call to
   `approved, denied = await run_approval_checks(ctx, prepared)`; assertions (`len(
   approved) == 1`, `denied == []`) unchanged.
4. `test_denied_calls_collected`: same pattern — `prepared = [_pc("write_file",
   {"path": "/tmp/f"})]`; `await run_approval_checks(ctx, prepared)`; assertions
   unchanged (`approved == []`, `denied == ["call_1"]`).
5. `test_plan_mode_blocks_configured_tools`: same pattern with `write_file`; assertions
   unchanged.
6. `test_plan_mode_does_not_block_unlisted_tools`: same pattern with `list_directory`;
   assertions unchanged.
7. Delete `test_invalid_json_arguments_does_not_crash` in full (current final method in
   this class, ~lines 812-831) — its scenario is ported to `test_tool_preparation.py`
   per the Design decision above.

### Method

Manual, per-method edit — five small, mechanically similar changes plus one deletion;
no codemod needed.

### Details

- Confirmed via direct read of `tests/agent/test_tool_approval_preflight.py` (831
  lines): `TestRunApprovalChecks` starts at the `# ── run_approval_checks() ──` comment
  (~line 730) and contains exactly the 5 methods named above, each constructing a raw
  `tool_calls: list[dict]` literal and calling `await run_approval_checks(ctx,
  tool_calls)`.
- `import run_approval_checks` is already present at line 17 (`from agent.tool_approval
  import check_approval, run_approval_checks`) — no import removal needed, only the two
  additions in step 1.

## Compatibility considerations

- This is the only one of the five `test_tool_approval_*.py` files with any actual
  change required, since it is the only one calling `run_approval_checks()` directly
  (confirmed via `grep -rn "run_approval_checks" tests/agent/test_tool_approval_*.py` —
  see the sibling docs for `paths.py`/`risk.py`/`concurrency.py`/`repos.py`, each
  verified to need no change).

## Security considerations

N/A — test-only file.

## Rollback considerations

- Tied to `tool_approval.py`'s rollback (its sole behavioral dependency); revert
  together.

## Validation plan

`uv run pytest tests/agent/test_tool_approval_preflight.py -v` — all tests pass,
including the 4 retained `TestRunApprovalChecks` methods; confirm
`test_invalid_json_arguments_does_not_crash` no longer exists in this file (`grep -n
"test_invalid_json_arguments_does_not_crash" tests/agent/test_tool_approval_preflight.py`
returns nothing) and its ported equivalent exists in `test_tool_preparation.py`.

## Out of scope

- This file's other classes (preflight policy, `check_approval()`,
  `log_approval_decision()`) — unaffected, no signature change touches them.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184037_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-235949
- Related target files: test_tool_approval_preflight.py
