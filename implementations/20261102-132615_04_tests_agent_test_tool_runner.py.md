# Tool-call log and REPL-emit scrub tests

## Goal

Add tests to `tests/agent/test_tool_runner.py` proving the "Tool call" log line and the REPL
tool-call emit carry scrubbed arguments — the two sinks `mask_args` feeds through
`_log_and_emit_tool_call` (Plan REQ-004 / AC-4).

## Scope

- New class `TestToolCallSinkScrub` (new) appended to the module.
- No changes to existing classes or helpers (`_pc`, `_runtime_tools` are reused read-only); every
  pre-existing test is the AC-6 regression.

## Assumptions

- Verified 20261102: `_log_and_emit_tool_call` (`tool_runner.py:349-352`) logs
  `logger.info("Tool call (turn %s): %s(%s)", ...)` on logger `agent.tool_runner` and calls
  `emit_tool_call(name, _json_dumps(masked))` (`agent.tool_output`); the sink pair runs from
  `_collect_tool_result_msgs` (:317-318) after `mask_args(args, ctx.cfg.tool.masked_fields)`.
- Existing caplog tests in this module already use `caplog.at_level(logging.INFO,
  logger="agent.tool_runner")` — reuse that pattern.
- Red-first (Plan Phase 1): the secret survives both sinks until row 01 lands.

## Design decisions

- Exercise the sinks through the existing `_execute_with_dag` → `_collect_tool_result_msgs` path
  with a stub registry (the `TestExecuteWithDag` pattern) rather than calling the private helper
  directly: the Plan's claim is about the real pipeline's sinks, not the helper in isolation.
- Capture the emit side by monkeypatching `agent.tool_runner.emit_tool_call` with a recording
  mock — the REPL boundary is that function; asserting its argument pins the emitted payload.

## Alternatives considered

- Call `_collect_tool_result_msgs` directly — rejected: private-signature coupling makes the test
  brittle against unrelated refactors; the DAG path is this module's established harness.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
Append `TestToolCallSinkScrub` (new) at the end of the module.

### Method
- `test_log_line_scrubs_free_form_secret` (new): run one tool call whose args are
  `{"command": "export API_KEY=abcd12345678 && true"}` through the DAG harness with `ctx` config
  `masked_fields=[]`; `caplog.at_level(logging.INFO, logger="agent.tool_runner")`; assert a record
  whose message starts `"Tool call ("` exists and no record contains `abcd12345678`.
- `test_emit_payload_scrubs_free_form_secret` (new): same run with
  `monkeypatch.setattr("agent.tool_runner.emit_tool_call", recorder)`; assert the recorded JSON
  argument contains no `abcd12345678` and still contains the tool name.
- `test_masked_fields_still_star_in_log` (new): `masked_fields=["content"]` case keeps `"***"` in
  the log line (REQ-002 at this sink).

### Details
- Build the stub with the module's existing `_pc` (PreparedToolCall) and `_runtime_tools` helpers,
  matching `TestExecuteWithDag`'s ctx/config fixture style.

## Compatibility considerations

- `tests/agent/test_tool_output.py` (the emit boundary's own tests) must pass unchanged.
- This file is shared by four Frozen plans in the batch; only this plan appends here now (recorded
  adjudication D5 — append-only, later plans add their own classes).

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py` — red for the new class until row 01 lands.
- `uv run pytest tests/agent/test_tool_output.py` unchanged.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- Both sinks show scrubbed arguments for the secret-bearing call; all pre-existing tests pass
  unchanged.

## Out of Scope

- `mask_args` unit behavior (row 02); audit writers (row 03); approval preview (unchanged by design).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestToolCallSinkScrub` (new) tests (red before row 01 lands) | Pending | — | — | Plan Phase 1 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (runner log line and REPL emit scrubbed)
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: tests/agent/test_tool_runner.py
