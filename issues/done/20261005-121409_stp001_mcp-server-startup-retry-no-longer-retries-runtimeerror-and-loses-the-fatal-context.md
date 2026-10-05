# MCP server startup retry no longer retries RuntimeError and loses the fatal context

## Priority
High

## Summary
Two changes in commit 10308ed7f altered MCP subprocess startup failure handling. (a) `McpServerStarter.start_servers()` no longer enters the retry path for `RuntimeError`/`HttpStartupError`, so the most common startup failure is not retried. (b) `retry_once_with_delay()` now re-raises the original exception, so the `[fatal] MCP subprocess '<key>' ...` text (and the secrets-masked message) only reaches the log, not the raised exception. Six tests in tests/agent/test_startup_approval_recovery.py fail.

## Background
- Plan `plans/done/20261004-182808_plan.md` ("Preserve original exception type through retry") and procedures `implementations/20261004-194143_01_scripts_agent_shared_retry_helper_py.md`, `_02_scripts_agent_startup_mcp_starter_py.md`, `_03_tests_agent_test_retry_helper_py.md` were applied in commit 10308ed7f.
- In `scripts/agent/shared/retry_helper.py`, `retry_once_with_delay` second-failure path changed from `raise RuntimeError(masked_msg) from retry_err` to `raise retry_err` (plan REQ-001, "preserve exception type"). The masked message is still computed and logged with `logger.error`.
- In `scripts/agent/startup_mcp_starter.py`, `McpServerStarter.start_servers()` first-attempt handler changed from `except (OSError, RuntimeError)` to `except (OSError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)`.
- `HttpStartupError` subclasses `RuntimeError` (scripts/agent/http_lifecycle_errors.py) and is the main failure raised when an HTTP subprocess fails to start; `TimeoutError`, `ConnectionRefusedError` etc. are already OSError subclasses in Python 3.13, so the new tuple effectively only drops `RuntimeError`.
- The plan's test list (`uv run pytest tests/agent/test_retry_helper.py`, `tests/agent/test_startup_mcp_starter.py`) omitted tests/agent/test_startup_approval_recovery.py, which exercises `StartupOrchestrator._start_servers()` / `_verify_mcp_health()`. The plan's own risk note ("callers that rely on RuntimeError may break; audit all callers") was not carried out for these tests.
- Adversarial verification (re-checked against source, `git show 10308ed7f`, tests and docs on 2026-10-05):
  - Confirmed: the before/after of the except tuple in `McpServerStarter.start_servers` (`(OSError, RuntimeError)` -> `(OSError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)`) and of `retry_once_with_delay` (`raise RuntimeError(masked_msg) from retry_err` -> `raise retry_err`) match the commit diff exactly; the masked message is still logged.
  - Confirmed: `HttpStartupError(RuntimeError)`. In `scripts/agent/http_lifecycle.py` the start path raises it for empty command, command validation failure, stderr log open failure (`http_lifecycle_stderr_log_manager.py`), "exited early", "shutdown requested" and "did not become healthy within Ns" (`_raise_startup_failure`). Only `Popen` failures and `getpgid` OSError escape as OSError. No retry or conversion exists in lifecycle or `StartupOrchestrator`; `McpServerStarter.start_servers` is the only retry layer. So in production the real startup failures (early exit, health timeout) now skip the retry; only spawn-level OSError and its subclasses are still retried.
  - Corrected: 7 tests fail in tests/agent/test_startup_approval_recovery.py; the seventh (`TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_warns_on_pending_approval_task_id_overwrite`) belongs to apr001, not this issue. The six listed here are all attributable to this commit.
  - Corrected: restoring the wrapper (option ii) breaks 2 of the 3 tests in tests/agent/test_retry_helper.py, not 3 (`test_timeout_error_preserved`, `test_connection_refused_error_preserved`); `test_runtime_error_preserved` still passes because `match="Second attempt runtime error"` is a regex search that hits inside `"FATAL Second attempt runtime error"` and the type is `RuntimeError`.
  - Confirmed: with pytest 9.0.3 `pytest.raises(RuntimeError, match=r"\[fatal\]")` matches `add_note` text, `str(exc)` does not contain the note, and `exc.__notes__` does; an `OSError` with a note still fails `pytest.raises(RuntimeError)`, so `add_note` cannot fix test_production_failure_message_contains_server_key.
  - Corrected (consumer impact): the only startup-error consumer is `scripts/agent/repl.py` (around line 126), which does `self._view.write_fatal(f"Startup failed: {e}")`; `str(e)` excludes notes, so under option (i) the operator console still shows only the raw message (for example "HTTP 503") without the server key or `[fatal]`; the note is visible only in tracebacks. Under option (ii) the console shows the masked `[fatal] MCP subprocess ...` text. `StartupOrchestrator.run()` re-raises the same exception after rollback.
  - Secret masking risk (new): since commit 10308ed7f the propagated exception text is not masked by `retry_once_with_delay`, and `repl.py` prints it through `write_fatal` (no masking was found in `CLIView.write_fatal`; the port implementation was not inspected: unknown). `HttpStartupError.__str__` masks only the stderr tail, not `reason`/server key; arbitrary `OSError`/`RuntimeError` text (for example paths or health-check bodies) is unmasked. Option (i) adds only masked text (note), so it adds no leak but does not remove the existing one; option (ii) is the only option that masks the console message. Option (iii) keeps the leak unless `write_fatal`/`repl.py` masks.
  - Plan/procedure check (non-canonical per docs/00_governance/governance_01): plans/done/20261004-182808_plan.md and implementations/20261004-194143_01/_02 asked to "broaden" the handlers for callers that catch `RuntimeError`, not to drop `RuntimeError`; procedure 02 nevertheless replaced the tuple and dropped it, and the plan's REQ-004 caller audit checkboxes stayed unchecked. The plan also stated "No documentation updates required" although docs/22_mcp/mcp_06_05 describes the `RuntimeError` + `[fatal]` contract. Neither document requires dropping `RuntimeError`.
- docs/22_mcp/mcp_06_05_long-running-http-operation-startup_modesubprocess.md states: on failure `McpServerStarter` retries once after `RETRY_DELAY_SEC`; if the second attempt also fails "a `RuntimeError` with the `[fatal]` prefix is raised and startup is aborted".

## Problem
Evidence (re-verified by running the tests and reading source):
- Running `.venv/bin/python -m pytest tests/agent/test_startup_approval_recovery.py -q -p no:cacheprovider -p no:randomly` fails these six tests (all with the exception type or message of the raw error):
  - TestStartupOrchestratorStartServers::test_http_subprocess_failure_raises_in_production (raw `RuntimeError: port busy`, regex `\[fatal\]` not matched)
  - TestStartupOrchestratorStartServers::test_production_profile_raises_on_start_failure (same)
  - TestStartupOrchestratorStartServers::test_production_failure_message_contains_server_key (side effect is `OSError("no such file")`; the retry runs, but the raised exception is the raw `OSError`, not the expected `RuntimeError`)
  - TestStartupOrchestratorStartServers::test_retry_success_appends_to_spawned_subprocesses (first attempt `RuntimeError("port busy")` is not caught, so no retry happens and the error propagates)
  - TestStartupOrchestratorStartServers::test_shutdown_event_during_retry_delay_raises_promptly (`RuntimeError` propagates immediately instead of `StartupInterrupted` during the retry delay)
  - TestStartupVerifyMcpHealth::test_health_check_failure_production_raises (raw `RuntimeError: HTTP 503`; the captured log shows `[fatal] MCP subprocess 'web' failed post-startup health check: HTTP 503`, so the context is only logged)
- Cause attribution (derived from source and the failure output):
  - Change (a) alone explains test_retry_success_appends_to_spawned_subprocesses (retry never happens, error propagates) and test_shutdown_event_during_retry_delay_raises_promptly (the `RuntimeError` is not caught, so the retry delay and `StartupInterrupted` are never reached): both use a `RuntimeError` first-attempt failure that must enter the retry path. Restoring (a) also re-enables the retry for the first two tests, but those additionally assert `[fatal]`, so they need (b) too (with (a) only, they would still fail with raw `RuntimeError: port busy`).
  - Change (b) explains the assertions on `[fatal]` and on the server key (tests 1, 2, 3 and the health check test). `verify_health()` catches `Exception` and always retries, so it is affected only by (b).
  - Test 3 expects `RuntimeError` for an `OSError` side effect (the OSError is still retried, so (a) is not the cause; (b) is), so only a wrapper (or a test update) satisfies it; adding a note to the original exception does not (verified with a scratch test).
- Verified experiment (scratch test, not in repo): with pytest 9.0.3 `pytest.raises(RuntimeError, match=r"\[fatal\]")` matches text added via `BaseException.add_note()`, so option (i) below would satisfy the `[fatal]` assertions for RuntimeError-typed failures.
- tests/agent/test_retry_helper.py (3 tests added by the plan; currently passing) require the raw type to be preserved (`TimeoutError`, `ConnectionRefusedError`, `RuntimeError` with `match` on the second attempt's message). Only the first two would fail if the wrapper were restored (verified by simulation: `RuntimeError("FATAL ...")` is not a `TimeoutError`/`ConnectionRefusedError`; the `RuntimeError` test still matches).
- Side effect of (b): the exception that propagates now carries the unmasked `str(retry_err)`; masking is applied only to the log line. `scripts/agent/repl.py` prints it via `write_fatal(f"Startup failed: {e}")` (see Background, Adversarial verification). Whether the `write_fatal` port implementation masks: unknown.

## Reason for Change
- Correctness: a transient `HttpStartupError`/`RuntimeError` on first start is no longer retried although docs/22_mcp/mcp_06_05 and the comment "First attempt failure — use retry helper" describe a retry; startup becomes less robust.
- Diagnosability: the fatal message with server key is lost from the exception that aborts startup; operators and callers see only e.g. "HTTP 503".
- Six tests fail on master, and the plan's verification omitted the test module that covers the affected callers.

## Implementation Intent
Part (a), required in all options: restore `RuntimeError` in the `start_servers()` except tuple (for example `(OSError, RuntimeError)`; the explicit OSError subclasses are redundant). Keep `StartupInterrupted` behavior as is.

Part (b), lost fatal context. Options:
- Option (i): keep the raised exception type (plan REQ-001) and attach the masked context with `retry_err.add_note(masked_msg)` before `raise`. Pros: preserves the plan intent and tests/agent/test_retry_helper.py; the context travels with the exception; pytest 9 matches notes, so tests 1, 2 and the health test would pass. Cons: notes appear only in the traceback rendering, not in `str(exc)`, so the `repl.py` console message ("Startup failed: ...") still lacks the server key and `[fatal]` text; test_production_failure_message_contains_server_key (expects `RuntimeError` for an `OSError`) would still need a test update; the raw message remains unmasked in `str(exc)`.
- Option (ii): restore `raise RuntimeError(masked_msg) from retry_err`. Pros: matches the documented behavior (docs/22_mcp/mcp_06_05), masks secrets in the propagated message, makes all six tests pass without test edits. Cons: reverts plan REQ-001; two tests in tests/agent/test_retry_helper.py (`test_timeout_error_preserved`, `test_connection_refused_error_preserved`) would fail and need updating; the original type is available only as `__cause__`.
- Option (iii): keep the new contract and update the six tests (and the doc statement) to expect the original exception type. Cons: loses the `[fatal]` text from `str(exc)` and is a contract change that must be accepted by the owner.

Recommendation: (a) plus option (i), with the one remaining test (test_production_failure_message_contains_server_key) updated by the owner to the new type contract, because it keeps the intentional type-preservation decision (and its three tests), keeps the fatal context attached and minimally changes behavior. Trade-off (survived adversarial verification, but with a caveat): the recommendation is safe (the note is masked, no new leak, the three tests keep passing), yet it does not restore operator-console diagnosability or masking of the propagated message, because `repl.py` prints `str(e)`; diagnosability through `str(exc)` is weaker than option (ii); if the owner values the documented "`RuntimeError` with `[fatal]`" contract and masked messages more than type preservation, choose option (ii) and update tests/agent/test_retry_helper.py. The owner decides.

## Target Files or Areas
- scripts/agent/startup_mcp_starter.py (`McpServerStarter.start_servers`, `verify_health`)
- scripts/agent/shared/retry_helper.py (`retry_once_with_delay`)
- scripts/agent/http_lifecycle_errors.py (`HttpStartupError`; read-only reference)
- scripts/agent/repl.py (read-only reference: prints `Startup failed: {e}`)
- tests/agent/test_startup_approval_recovery.py, tests/agent/test_retry_helper.py (only if the owner chooses option (ii) or (iii), or for the single test noted under (i))
- docs/22_mcp/mcp_06_05_long-running-http-operation-startup_modesubprocess.md (read-only here; see Documentation Impact)

## Required Changes
- Restore `RuntimeError` in the first-attempt except tuple of `McpServerStarter.start_servers()`.
- Apply the chosen option for the fatal context in `retry_once_with_delay` (recommended: `add_note` with the masked message, then re-raise the original exception).
- Update only the tests that conflict with the chosen contract, with owner approval (recommended: test_production_failure_message_contains_server_key).
- Optionally (owner decision) mask or enrich the message printed at `scripts/agent/repl.py` (`write_fatal(f"Startup failed: {e}")`) if the unmasked propagated text is not acceptable.
- Make `retry_once_with_delay`'s docstring match the chosen contract (it currently says it raises RuntimeError with `fatal_prefix`).

## Constraints
- Secrets must stay masked in any added context (use the existing `_mask_secrets`); do not attach `str(retry_err)` unmasked to a note or message.
- `StartupInterrupted` semantics during the retry delay must not change.
- Retry count stays at one retry with `RETRY_DELAY_SEC`.

## Acceptance Criteria
- All six tests listed in Problem pass, or, where the owner changed the contract, the updated tests pass and the owner-approved contract is documented.
- tests/agent/test_retry_helper.py passes (option (i)) or is updated consistently (options (ii)/(iii)).
- A first-attempt `RuntimeError`/`HttpStartupError` from `start_http_subprocess` triggers exactly one retry.
- `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` shows no failures related to this issue.

## Testing Expectations
- Run `.venv/bin/python -m pytest tests/agent/test_startup_approval_recovery.py tests/agent/test_retry_helper.py -q -p no:cacheprovider -p no:randomly`, then the regression command above.
- Add a test that `HttpStartupError` on the first attempt is retried (the plan's test list lacked this) and, for option (i), a test that the note carries the masked `[fatal]` message (`__notes__`) and that a secret-like string in the error text is masked in it.
- test_startup_recovery_warns_on_pending_approval_task_id_overwrite also fails in the same module but belongs to apr001; exclude it from this issue's pass criteria.
- Run ruff and mypy on the changed files.

## Documentation Impact
- docs/22_mcp/mcp_06_05_long-running-http-operation-startup_modesubprocess.md currently says a `RuntimeError` with the `[fatal]` prefix is raised after the second failure. It is accurate under option (ii); under options (i) and (iii) it must describe the final contract (original exception type, fatal text logged and attached as a note). Do not edit docs in this issue's filing; update during implementation if the contract changes.

## Out of Scope
- Retry count, delay, or backoff changes.
- Changes to `HttpStartupError` or http_lifecycle.py.
- Masking policy changes in agent/secrets_masker.py.

## Dependencies
N/A: none (independent of trn001 and apr001; tests share the module tests/agent/test_startup_approval_recovery.py with apr001).

## Unresolved Questions
- Which contract does the owner want: preserved exception type (plan REQ-001) or the documented `RuntimeError` with `[fatal]`? Recommendation: (a) + option (i).
- Is the unmasked `str(retry_err)` in the propagated exception acceptable (where is the startup error printed)? Unknown.
- Does `CLIView.write_fatal` / the underlying port mask secrets in the message printed by `repl.py`? Unknown (the port implementation was not inspected).
- Is the console message ("Startup failed: ...") expected to contain the server key and `[fatal]` text (which option (i) does not provide)? Unknown; owner decision.
- Whether any other code path relied on `RuntimeError` from `retry_once_with_delay`: only the two call sites in scripts/agent/startup_mcp_starter.py were found by `rg`.

## AI Implementation Instruction
Restore `RuntimeError` retry first, then apply only the owner-chosen option for the fatal context. Do not edit tests unless the chosen option requires it and the owner approved. Do not change unrelated startup code. Report results of the six tests and the regression run.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261004-182808_plan.md (originating change; this issue is a follow-up)
- **Source implementation procedure**: implementations/20261004-194143_01_scripts_agent_shared_retry_helper_py.md, implementations/20261004-194143_02_scripts_agent_startup_mcp_starter_py.md (originating changes)
- **Generated at**: 20261005-121409
- **Related target files**: scripts/agent/startup_mcp_starter.py, scripts/agent/shared/retry_helper.py, tests/agent/test_startup_approval_recovery.py, tests/agent/test_retry_helper.py
