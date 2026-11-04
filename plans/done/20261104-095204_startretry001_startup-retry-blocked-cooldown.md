## Goal
- Make the documented retry-once of an MCP subprocess startup a genuine second launch attempt: after a first start failure the second call must reach the subprocess layer instead of being vetoed by the runtime failure cooldown, a suppressed start must be a typed signal that can never be read as success, and the first failure must stay visible as the cause of a final failure.

## Priority
High

## Scope
- **In-Scope**:
  - `_ServerLifecycleRouter.start_http_subprocess` no longer consults the failure cooldown; it remains the explicit startup/start entry point.
  - The shutdown-suppression branch of the same method raises a typed error instead of returning `None`; `McpServerStarter` maps it to `StartupInterrupted`.
  - The first failure (server key and masked reason) is logged and stays reachable from the final error through exception chaining.
  - Integration-style tests with the real router and real starter, only the subprocess layer faked; update the two characterization tests that pin the old `None` returns.
  - Documentation wording for the startup retry and the shutdown guard.
- **Out-of-Scope**:
  - Changing `RETRY_DELAY_SEC` or the cooldown window.
  - Orphan handling of a process that fails its readiness poll (tracked by `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md`).
  - The post-startup health-check retry in `verify_health`.
  - Any change to `retry_once_with_delay` (its exception-type preservation and secret masking contract stays as is).
  - Runtime `ensure_ready` and `restart` behavior, including their cooldown checks.
- **Dependencies**: Related to `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md` (already planned separately): a "shutdown requested" `HttpStartupError` flows into this retry path today. Either can be fixed first; after both, an interrupted start surfaces as `StartupInterrupted`. The other Plan lists this one as its prerequisite, so no `Depends on` line points back at it (sequencing only, not blocking). `issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md` changes the masker used by `retry_once_with_delay` and is independent.

## Background
`McpServerStarter.start_servers` retries a failed subprocess start once through `retry_once_with_delay`. `issues/done/20261005-121409_stp001_...` restored that retry for `RuntimeError`/`HttpStartupError`. The failure cooldown (`_failed_starts`, a fixed window far longer than `RETRY_DELAY_SEC`) was introduced when the lifecycle router was split out of the factory. Existing starter and startup tests mock the lifecycle manager, so the router/starter interaction is untested.

## Problem
For a server whose first start raises `HttpStartupError` (checked in Step 2):
1. `_run_lifecycle_transition` records the failure time, sets state `FAILED`, and re-raises.
2. `start_servers` catches the `RuntimeError` and calls `retry_once_with_delay`, whose first action is the same start call.
3. `_ServerLifecycleRouter.start_http_subprocess` sees `_in_cooldown` and returns `None` without starting or raising.
4. The helper treats `None` as success; `start_servers` then raises the generic "failed to start after retry". A transient failure is always fatal and the real reason is only in an INFO log line.

Related ambiguity: `_start_http_subprocess_once` returns `None` both for "suppressed" and "no process started"; the first attempt treats `None` as success and the retry treats it as failure.

Verification corrections to the Issue: (a) `start_http_subprocess` of the router has exactly one non-test caller, `McpServerStarter._start_http_subprocess_once`; `ensure_ready` and `restart` reach the subprocess manager directly and apply the cooldown themselves, so removing the cooldown from the start entry point does not touch runtime behavior (this answers the Issue's second unresolved question). (b) A successful real start always records the `Popen` in `_http_procs`, so after this change a `None` result cannot come from the real router for any reason other than a mocked layer. (c) The Issue lists `retry_helper.py` and `test_startup_mcp_lifecycle.py` as areas; neither needs modification (see Design).

## Reason for Change
The documented retry-once behavior does not exist at runtime, so startup is less robust than documented, and the operator-facing error hides the actual cause.

## Implementation Intent
Treat the cooldown as a runtime throttle for automatic restarts only. The router's `start_http_subprocess` is the explicit start entry, so it ignores the cooldown; the shutdown guard stays but signals with a typed error. The starter converts that signal to `StartupInterrupted`, which already propagates through the retry helper without a retry.

## Requirements
- `REQ-001`: After a first start failure, the second startup attempt MUST reach the subprocess layer; `_ServerLifecycleRouter.start_http_subprocess` MUST NOT return early because of the failure cooldown.
- `REQ-002`: A suppressed start (router shutting down) MUST be signaled by a typed error rather than `None`, and `McpServerStarter` MUST map it to `StartupInterrupted` so it is never treated as a successful start or a completed retry.
- `REQ-003`: When both attempts fail, the final error MUST name the server and carry the last failure reason, and the first failure (server key, masked reason) MUST remain visible via a log record at warning level and exception chaining.
- `REQ-004`: Runtime cooldown behavior of `ensure_ready` and `restart` MUST be unchanged; `retry_once_with_delay` MUST keep preserving the original exception type and secret masking; shutdown during the retry delay MUST still raise `StartupInterrupted`.
- `REQ-005`: Add integration-style tests using the real `_ServerLifecycleRouter` and `McpServerStarter` with only the subprocess layer faked: fail-then-succeed, fail-then-fail, and shutdown-suppressed start. They MUST fail on the pre-change code and pass after it.
- `REQ-006`: The two characterization tests pinning `None` for cooldown and shutdown MUST be rewritten to the new contract, and the contract text of `start_http_subprocess` in `LifecycleManagerProtocol` MUST describe the raise.
- `REQ-007`: Documentation MUST state that the runtime restart cooldown does not apply to the startup retry and that the shutdown guard of `start_http_subprocess` signals instead of silently returning.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed: every row `Verified` — exists, requires modification, supporting evidence, linked to a Plan requirement; no path appears in both tables; no directory, glob, or vague row).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/lifecycle_router.py` | Router start entry and shutdown signal | Remove the `_in_cooldown` early return from `_ServerLifecycleRouter.start_http_subprocess`; raise a new typed `StartSuppressedError` instead of returning `None` when `_shutting_down` (checked in Step 2) | REQ-001, REQ-002, REQ-004; AC-1, AC-3, AC-4 | `start_http_subprocess` returns `None` on `_shutting_down` and on `_in_cooldown`; `ensure_ready` and `restart` keep their own `_in_cooldown` checks and call `_subprocess_mgr` directly (checked in Step 2) | `tests/agent/test_lifecycle.py`, `tests/agent/test_startup_mcp_starter.py` | Verified |
| `scripts/agent/startup_mcp_starter.py` | Starter mapping and first-failure visibility | Map `StartSuppressedError` to `StartupInterrupted` in `_start_http_subprocess_once`; log the first failure at warning level with server key and masked reason; keep retry wiring (checked in Step 2) | REQ-002, REQ-003; AC-2, AC-3 | `start_servers` logs the first failure at INFO only; `_start_http_subprocess_once` returns `None` when no `Popen` comes back; `from agent.startup import StartupInterrupted` is already imported lazily in this module (checked in Step 2) | `tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_startup_mcp_lifecycle.py` | Verified |
| `scripts/agent/lifecycle_protocol.py` | Contract text | `start_http_subprocess` docstring in `LifecycleManagerProtocol` describes the typed error instead of "or None" semantics for suppression (checked in Step 3) | REQ-006; AC-3 | Docstring reads "returns the Popen object or None"; the signature is shared by the router and `_SubprocessLifecycleManager` (checked in Step 3) | `tests/agent/test_lifecycle.py` | Verified |
| `tests/agent/test_startup_mcp_starter.py` | New integration-style tests | Add a test class with the real router and starter, faking only the `HttpServerLifecycleManager` start; cover fail-then-succeed, fail-then-fail, and shutdown-suppressed start (checked in Step 2) | REQ-005; AC-1, AC-2, AC-3, AC-5 | File exists and has no cooldown or `_ServerLifecycleRouter` reference (rg, checked in Step 2) | `tests/agent/test_startup_mcp_starter.py` | Verified |
| `tests/agent/test_lifecycle.py` | Characterization update | Replace `test_start_http_subprocess_returns_none_in_cooldown` with a test that the start entry ignores the cooldown while `ensure_ready` and `restart` still honor it (checked in Step 2) | REQ-004, REQ-006; AC-4 | `TestCooldownCharacterization` pins `None` in cooldown and keeps the `ensure_ready` and `restart` cooldown tests (checked in Step 2) | `tests/agent/test_lifecycle.py` | Verified |
| `tests/agent/test_agent_factory.py` | Characterization update | Replace `test_start_http_subprocess_returns_none_after_shutdown_all` with an assertion that `StartSuppressedError` is raised and the subprocess layer is not called (checked in Step 2) | REQ-002, REQ-006; AC-3 | `TestRouterPostShutdownGuards` asserts `result is None` and `start.assert_not_called()` (checked in Step 2) | `tests/agent/test_agent_factory.py` | Verified |
| `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` | Startup retry wording | State that the runtime restart cooldown does not apply to the startup retry; keep the retry-once-then-`[fatal]` description; no concrete timing values (checked in Step 2) | REQ-007; AC-6 | Paragraph on retry after a fixed delay and `[fatal]` error exists and does not mention the cooldown (rg, checked in Step 2) | N/A: documentation | Verified |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Shutdown guard wording | The sentence that `start_http_subprocess()` "return[s] immediately after logging a line" under shutdown becomes: it raises the typed suppression error (checked in Step 2) | REQ-007; AC-6 | Sentence listing `ensure_ready()`, `start_http_subprocess()`, `restart()`, `shutdown_idle()` as returning immediately (checked in Step 2) | N/A: documentation | Verified |
| `docs/23_agent/agent_02_runtime-architecture.md` | Shutdown guard wording | The line "guarded against being ignored once shutdown has started" no longer fits the raise for `start_http_subprocess` (checked in Step 2) | REQ-007; AC-6 | The line names `ensure_ready`/`start_http_subprocess`/`restart` together (checked in Step 2) | N/A: documentation | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/shared/retry_helper.py` | `retry_once_with_delay` contract: catches `Exception` only, so `StartupInterrupted` (a `BaseException`) propagates without retry; re-raise keeps `__cause__` and the first error as `__context__` (probe run in Step 3) | REQ-003, REQ-004 |
| `scripts/agent/http_lifecycle_errors.py` | `HttpStartupError` carries `StartupFailure` (server key, reason, stderr tail) and builds its message from it | REQ-003 |
| `scripts/agent/http_lifecycle.py` | `HttpServerLifecycleManager.start` is idempotent and a successful start always records the `Popen` in `_http_procs` | REQ-001, REQ-005 |
| `scripts/agent/lifecycle.py` | `FAILED -> STARTING` is a valid transition, so the second start's state change is not rejected | REQ-001 |
| `scripts/agent/startup.py` | Defines `StartupInterrupted(BaseException)` and the lazy-import pattern used by the starter | REQ-002 |
| `tests/agent/test_startup_mcp_lifecycle.py` | Existing mock-based retry tests (`test_genuine_runtime_error_still_retries`, `test_no_process_returned_does_not_append`) must keep passing unchanged | REQ-004, REQ-005 |
| `tests/agent/test_retry_helper.py` | Pins the retry helper contract that must not change | REQ-004 |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Cites the retry-once then `[fatal]` behavior and `McpServerStarter`; wording must remain true after the change (no ADR edit) | REQ-007 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-005): a first-attempt `HttpStartupError` followed by a successful second attempt starts the server, appends the `Popen`, and startup continues; the fake subprocess layer is called twice.
- AC-2 (REQ-003, REQ-005): two consecutive failures abort startup with an error naming the server and carrying the last failure reason; the first failure appears in a warning log record and in the exception chain.
- AC-3 (REQ-002, REQ-006): a start suppressed by shutdown is never treated as success: `start_http_subprocess` raises the typed error and `start_servers` raises `StartupInterrupted`.
- AC-4 (REQ-004, REQ-006): `ensure_ready` and `restart` still refuse inside the cooldown window; the existing cooldown tests for them pass unchanged.
- AC-5 (REQ-005): the new integration-style tests fail on the pre-change code and pass after the change.
- AC-6 (REQ-007): the three documents match the behavior, the docs checkers report no findings, and no concrete timing values are added.

## Tests
- `REQ-005`: new class in `tests/agent/test_startup_mcp_starter.py` using the real `_ServerLifecycleRouter` and `McpServerStarter`, faking `router._subprocess_mgr._http_mgr` so that `start` raises `HttpStartupError` once and then succeeds (and a variant that raises twice); assert the number of calls reaching the fake, the returned `Popen` list, the final exception type and text, and the router state.
- `REQ-005`: a test where the router is already shutting down; assert `StartupInterrupted` and no subprocess call. The fail-then-fail test patches `agent.startup_mcp_starter.RETRY_DELAY_SEC` to a negligible value so it does not sleep, and asserts the first-failure warning by patching the module's `logger` (see Assumptions).
- `REQ-004`, `REQ-006`: rewrite the two characterization tests; keep `test_ensure_ready_raises_cooldown_error`, `test_restart_skips_when_in_cooldown`, and the retry-helper tests unchanged.
- Regression: `tests/agent/test_startup_mcp_starter.py`, `tests/agent/test_startup_mcp_lifecycle.py`, `tests/agent/test_startup.py`, `tests/agent/test_retry_helper.py`, `tests/agent/test_lifecycle.py`, `tests/agent/test_agent_factory.py`, `tests/agent/test_startup_rollback.py`.

## Documentation Impact
Yes. REQ-007 drives updates to the MCP subprocess startup document, the MCP lifecycle document, and the agent runtime-architecture document (targets in the table above, located through `docs/00_index.md` "Document References by Task"). Wording only; no concrete values.

## Assumptions
- A successful real start always tracks a `Popen`, so `None` from the real router cannot occur after this change; the first-attempt `None` handling in `start_servers` is left as pinned by `test_no_process_returned_does_not_append` (evidence: `http_lifecycle_subprocess_launcher.py` records the process, checked in Step 3).
- The retry-helper exception chain (final error `__cause__` is the second failure, whose `__context__` is the first) is sufficient for "carry the first failure"; it was confirmed with a probe run in Step 3.
- No caller of `start_http_subprocess` exists outside `scripts/agent/` (rg over `scripts/`, Step 3), so the Issue's stop condition does not trigger.
- Overlap with other Frozen Plans is judged by `tools/check_plan_target_overlaps.py` in Step 8b; none is recorded here unless the tool reports one.
- `tests/agent/test_agent_factory.py` is covered by its own row and procedure, not as a companion: the plan-coverage check counts the companions of every procedure in the repository, and a past procedure of another Plan lists that file as a companion, so naming it in the router row's `Related Tests` as well produced a false `companion-multi-row` finding. It was removed from the router row's `Related Tests` with the owner's approval; the router procedure's Validation plan still runs that test file (Step 3a of `plan-to-implementation-procedure`).
- The starter module's `logger` is a `shared.logger.Logger` wrapper whose underlying logger has `propagate = False`, so pytest's `caplog` cannot capture its records; tests assert the first-failure warning by patching the module-level `logger` in `agent.startup_mcp_starter` (checked in Step 3a of `plan-to-implementation-procedure`).
- `tests/agent/test_startup_mcp_starter.py` already mixes routing-drift tests with `McpServerStarter` health tests that build a real starter around a `MagicMock` context; the new class follows the second style (checked in Step 3a).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the final error text should also embed the first failure's reason, beyond the log record and exception chain. | No stated operator requirement; `HttpStartupError` rebuilds from its payload, so a message suffix would not appear for that type. | Implementer keeps the chain and log; the owner may request a message suffix as a follow-up. | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/lifecycle_router.py` | Modify | Medium: one non-test caller of `start_http_subprocess`; shared by `factory.py` | 2 | N/A | not applicable (rsynced) |
| `scripts/agent/startup_mcp_starter.py` | Modify | Medium: startup path of every subprocess MCP server | 7 | N/A | not applicable (rsynced) |
| `scripts/agent/lifecycle_protocol.py` | Modify | Low: docstring only | 2 | N/A | not applicable (rsynced) |
| `tests/agent/test_startup_mcp_starter.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_lifecycle.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/agent/test_agent_factory.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/23_agent/agent_02_runtime-architecture.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Decision 1, how the startup retry avoids the cooldown. Alternatives: (a) a bypass flag on `start_http_subprocess`; (b) a separate startup entry on the router; (c) drop the cooldown check from `start_http_subprocess`. Chosen: (c). The cooldown protects automatic restarts, which reach the subprocess manager through `ensure_ready` and `restart`, both of which keep their checks; the only caller of `start_http_subprocess` is the explicit startup path. Compatibility: the shared `LifecycleManagerProtocol` signature is unchanged, so `_SubprocessLifecycleManager` and mocks need no signature change.

Decision 2, the suppression signal. Alternatives: a result object, or a typed error. Chosen: a typed `StartSuppressedError` defined in `lifecycle_router.py`, raised only for the shutdown guard. The starter converts it to `StartupInterrupted` (a `BaseException`) before it can enter the retry path, so it is neither retried nor read as success. Compatibility: the only behavior change is for callers that relied on `None` after shutdown; the only such production caller is the starter.

Decision 3, first-failure visibility. The starter logs the first failure at warning level with key and masked reason. The retry helper already raises the second failure `from` itself with the first as context; no helper change.

Consumer scan (`uv run python tools/scan_change_consumers.py --seed start_http_subprocess`, run in Step 3; testmon state stale, so candidates only): the targets above cover `scripts/agent/lifecycle_protocol.py`, `scripts/agent/lifecycle_router.py`, `scripts/agent/startup_mcp_starter.py`, and the three documents. Remaining candidates: `tests/agent/test_startup_mcp_lifecycle.py` and `tests/agent/test_startup_rollback.py` (`not affected`: they replace `start_http_subprocess` with `AsyncMock`); `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` lines on subprocess retry (`not affected`: they state retry once then `[fatal]`, which stays true; the ADR is cited as a reference only); the many `tests/agent/test_lifecycle.py` cases that call the router's `start_http_subprocess` on a first, successful start (`not affected` by the cooldown removal: none pre-seeds `_failed_starts` except `TestCooldownCharacterization`, to be confirmed by running the file in Phase 4).

Complexity note: `McpServerStarter.start_servers` is already grade C (16) by radon; this change adds no branch to it (the mapping lives in `_start_http_subprocess_once`).

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add the integration-style test class (REQ-005; `tests/agent/test_startup_mcp_starter.py`) and record that it fails on the current code.
2. **Phase 2: Router and contract**
   - [ ] Remove the cooldown early return and raise `StartSuppressedError` on shutdown (REQ-001, REQ-002; `scripts/agent/lifecycle_router.py`).
   - [ ] Update the protocol docstring (REQ-006; `scripts/agent/lifecycle_protocol.py`).
3. **Phase 3: Starter mapping and first-failure log**
   - [ ] Map the typed error to `StartupInterrupted` and log the first failure at warning level (REQ-002, REQ-003; `scripts/agent/startup_mcp_starter.py`).
4. **Phase 4: Characterization tests**
   - [ ] Rewrite the cooldown and shutdown characterization tests (REQ-004, REQ-006; `tests/agent/test_lifecycle.py`, `tests/agent/test_agent_factory.py`).
5. **Phase 5: Documentation**
   - [ ] Update the three documents and run the docs checkers (REQ-007; `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md`, `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`, `docs/23_agent/agent_02_runtime-architecture.md`).
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` for `scripts/` changes; prerequisite: the change is committed and pushed first, and deploying is the user's decision (approval gate). Run `uv run python tools/generate_reference_table.py --check` (REQ-001; `scripts/agent/lifecycle_router.py`, `scripts/agent/startup_mcp_starter.py`).

### Release units
**Unit**: startup-start-contract | **Phases**: 2, 3, 4 | **Reason**: removing the `None` return breaks the old characterization tests and the starter's shutdown handling until the router, starter, and tests land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/lifecycle_router.py`, `scripts/agent/startup_mcp_starter.py` | Integration-style (real router and starter) | `uv run pytest tests/agent/test_startup_mcp_starter.py -v` | New tests fail before Phase 2-3, pass after |
| Router and starter regression | Unit | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup.py tests/agent/test_retry_helper.py tests/agent/test_lifecycle.py tests/agent/test_agent_factory.py tests/agent/test_startup_rollback.py -v` | All pass |
| Touched Python files | Static | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean, no new errors |
| `scripts/agent/` | Security / architecture | `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` | No new findings |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent |
| Reference tables | Generated-doc drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Three documents | Docs checkers | `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain mcp`, `--domain agent` | No findings |

Baseline (Step 5): `radon cc` reports `McpServerStarter.start_servers` C (16) and `verify_health` C (15), none in the router; `vulture` shows no finding in the target files; `bandit` shows no medium or high severity finding in them; the diff-cover number is recorded at implementation time.

## Risks
- **Risk**: A runtime caller outside the starter starts depending on the router's `start_http_subprocess` cooldown, or on `None` after shutdown → **Mitigation**: caller search shows only the starter; the stop condition of the Issue is kept (stop if a caller outside `scripts/agent/` appears).
- **Risk**: Removing the cooldown from the start entry lets a rapid external loop restart a failing server → **Mitigation**: the entry is used only by the startup path, whose retry count is bounded to one by the helper; runtime paths keep the cooldown.
- **Risk**: `StartSuppressedError` is a `RuntimeError` subclass and would be retried if it escaped the starter mapping → **Mitigation**: convert it inside `_start_http_subprocess_once` and add the shutdown-suppressed test.
- **Risk**: `tests/agent/test_lifecycle.py` has many cases that call the router's `start_http_subprocess` and could depend on cooldown state left by an earlier call in the same test → **Mitigation**: the scan shows only `TestCooldownCharacterization` pre-seeds `_failed_starts`; Phase 4 runs the whole file and any other dependent case is reported as an Additional target file discovery via `tools/amend_plan.py`.
- **Risk**: Test blast radius of the router change → **Mitigation**: `rg -l '\bstart_http_subprocess\b' tests/` showed the affected files above; two characterization tests change, the rest are mock-based and unaffected.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add failing integration-style tests | In Progress | — | — |  |
| 2 | Phase 2: router start entry and protocol contract | In Progress | — | — |  |
| 3 | Phase 3: starter mapping and first-failure log | In Progress | — | — |  |
| 4 | Phase 4: rewrite characterization tests | In Progress | — | — |  |
| 5 | Phase 5: documentation updates | In Progress | — | — |  |
| 6 | Phase 6: deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261104-140850_01_scripts_agent_lifecycle_router.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261104-140850_02_scripts_agent_startup_mcp_starter.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261104-140850_03_scripts_agent_lifecycle_protocol.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261104-140850_04_tests_agent_test_startup_mcp_starter.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261104-140850_05_tests_agent_test_lifecycle.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261104-140850_06_tests_agent_test_agent_factory.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261104-140850_07_docs_22_mcp_mcp_06_03_long-running-http-operation-startup_modesubprocess.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261104-140850_08_docs_22_mcp_mcp_03_04_tool-call-tracing-and-lifecycle.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261104-140850_09_docs_23_agent_agent_02_runtime-architecture.md.md | 5 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-095204
- **Related target files**: scripts/agent/lifecycle_router.py, scripts/agent/startup_mcp_starter.py, scripts/agent/lifecycle_protocol.py, tests/agent/test_startup_mcp_starter.py, tests/agent/test_lifecycle.py, tests/agent/test_agent_factory.py, docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md, docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md, docs/23_agent/agent_02_runtime-architecture.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1; router `start_http_subprocess` cooldown early return | scripts/agent/lifecycle_router.py | 2 | AC-1 | New fail-then-succeed test | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; `None` returns in the router | scripts/agent/lifecycle_router.py | 2 | AC-3 | Shutdown-suppressed test; rewritten shutdown characterization test | Confirmed by repository evidence |
| REQ-002 | Required Changes bullet 2; `_start_http_subprocess_once` | scripts/agent/startup_mcp_starter.py | 3 | AC-3 | Shutdown-suppressed test | Derived from confirmed evidence |
| REQ-003 | Required Changes bullet 3; probe of exception chain | scripts/agent/startup_mcp_starter.py | 3 | AC-2 | New fail-then-fail test | Derived from confirmed evidence |
| REQ-004 | Constraints; cooldown checks in `ensure_ready` and `restart` | scripts/agent/lifecycle_router.py | 2 | AC-4 | Existing `ensure_ready` and `restart` cooldown tests | Explicit in issue |
| REQ-004 | Constraints; `test_retry_helper.py` | scripts/agent/startup_mcp_starter.py | 3 | AC-4 | `tests/agent/test_retry_helper.py`, retry-delay shutdown test | Explicit in issue |
| REQ-004 | Constraints; cooldown characterization tests | tests/agent/test_lifecycle.py | 4 | AC-4 | `tests/agent/test_lifecycle.py` | Explicit in issue |
| REQ-005 | Required Changes bullet 4; Acceptance Criteria | tests/agent/test_startup_mcp_starter.py | 1 | AC-1, AC-2, AC-5 | New integration-style class | Explicit in issue |
| REQ-006 | Derived: characterization tests pin `None` | tests/agent/test_lifecycle.py | 4 | AC-4 | Rewritten cooldown test | Derived from confirmed evidence |
| REQ-006 | Derived: characterization tests pin `None` | tests/agent/test_agent_factory.py | 4 | AC-3 | Rewritten shutdown test | Derived from confirmed evidence |
| REQ-006 | Derived: protocol docstring says "or None" | scripts/agent/lifecycle_protocol.py | 2 | AC-3 | `uv run mypy --no-namespace-packages scripts/` | Derived from confirmed evidence |
| REQ-007 | Documentation Impact | docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md | 5 | AC-6 | `tools/check_docs_*` | Explicit in issue |
| REQ-007 | Derived: shutdown-guard wording | docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md | 5 | AC-6 | `tools/check_docs_*` | Derived from confirmed evidence |
| REQ-007 | Derived: shutdown-guard wording | docs/23_agent/agent_02_runtime-architecture.md | 5 | AC-6 | `tools/check_docs_*` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261104-140850 -->