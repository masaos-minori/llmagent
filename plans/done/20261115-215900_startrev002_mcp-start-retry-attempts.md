## Goal
- Make MCP subprocess startup and post-startup health verification attempt each server exactly twice, with the fixed retry delay between the two attempts, as documented ("retries once after a fixed delay").

## Priority
Medium

## Scope
- **In-Scope**: the two retry call sites in `McpServerStarter` (`start_servers`, `verify_health`); a keyword-only `skip_first_attempt` option on `retry_once_with_delay`; tests that count underlying attempts and the gap between them.
- **Out-of-Scope**: which exceptions enter the retry path (decided in `issues/done/20261005-121409_stp001_mcp-server-startup-retry-no-longer-retries-runtimeerror-and-loses-the-fatal-context.md`); the delay value; readiness polling inside `HttpServerLifecycleManager`; reuse of a live process on retry (`issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md`); the `verify_health` degraded-but-live logic (`issues/20261115-214907_startrev007_degraded-live-nondict-body.md`); documentation text (the contract it states is already the intended one).
- **Dependencies**: related, not blocking: `issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md` (re-verify after this lands, because a delayed retry changes when its reuse branch is reached) and `issues/20261115-214907_startrev007_degraded-live-nondict-body.md` (shares `McpServerStarter.verify_health`; implement in sequence to avoid merge conflicts).

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214902_startrev002_mcp-start-retry-attempts.md`).
- `McpServerStarter.start_servers` runs `_start_http_subprocess_once` inline and, on one of a fixed set of exception types, calls `retry_once_with_delay(lambda: self._start_http_subprocess_once(...))`. `retry_once_with_delay` itself begins with `return await fn()` and only sleeps before a second call. `verify_health` has the same shape with `_verify_single_health`.
- Reproduced in Step 2 of this cycle with a lifecycle stub that always raises and `RETRY_DELAY_SEC` set to 0.3 s: three `start_http_subprocess` calls at offsets 0.0 s, 0.0 s and 0.3 s, then `RuntimeError`.
- The contract is documented in `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` and `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` ("retries once after a fixed delay").
- The existing tests do not catch it: `tests/agent/test_startup_mcp_lifecycle.py::test_genuine_runtime_error_still_retries` spies on the helper and asserts it is awaited once; no test counts `start_http_subprocess` calls or measures the gap.
- The only production callers of `retry_once_with_delay` are the two sites in `startup_mcp_starter.py` (checked in Step 3); the rest are tests.

## Problem
A failing server costs three start attempts, each bounded by `startup_timeout_sec`, and the second follows the first with no delay, so the delay protects only the third attempt. The health-verification path gives a transient failure an immediate re-probe before the delay. Startup failure takes about three times as long as intended, and the immediate attempt rarely succeeds where the first failed.

## Reason for Change
The behavior contradicts the documented policy and the intent recorded in the code (`RETRY_DELAY_SEC`, "retry-once-with-delay"), and no test would catch a regression or the current defect. Not time-critical: the failure path is already fail-closed.

## Implementation Intent
Make the retry helper's contract usable by a caller that has already made, and lost, the first attempt: `retry_once_with_delay` gains a keyword-only `skip_first_attempt` option. With it set, the helper does not call `fn` immediately; it checks the shutdown event, waits the interruptible delay, calls `fn` once, and on failure raises the fatal-prefixed, secret-masked rebuilt exception exactly as today. Both call sites pass the option, so each server is attempted twice. The inline first attempt stays where it is, so the exception classes that trigger a retry, the tolerated `None` result of a first attempt, and the exception propagation of every other class are unchanged. The helper's name and default behavior stay, so the ADR and doc statements that name `retry_once_with_delay()` remain correct.

## Requirements
- `REQ-001`: `McpServerStarter.start_servers` attempts a failing server exactly twice, the second attempt no earlier than `RETRY_DELAY_SEC` after the first.
- `REQ-002`: `McpServerStarter.verify_health` attempts a failing server's health probe sequence exactly twice, with the delay between the attempts.
- `REQ-003`: `retry_once_with_delay` supports a caller-made first attempt through a keyword-only option; its default behavior, shutdown race, `StartupInterrupted` propagation, exception-type preservation and masked fatal message are unchanged.
- `REQ-004`: Tests count the underlying attempts and measure the gap between them for the start path, the health path and the helper option.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/shared/retry_helper.py | Provide the retry-only mode | Add keyword-only `skip_first_attempt: bool = False` to `retry_once_with_delay`; when true skip the leading `await fn()` and go straight to the shutdown check, the interruptible delay and the second attempt; update the docstring | REQ-003; AC-3 | `retry_once_with_delay` at lines 18-62: `return await fn()` at line 41 is the unconditional first attempt; radon B (6) (checked in Step 3 and Step 5) | `tests/agent/test_retry_helper.py` | Verified |
| scripts/agent/startup_mcp_starter.py | Use the retry-only mode at both sites | Pass `skip_first_attempt=True` in the `start_servers` call (line 107) and the `verify_health` call (line 171) | REQ-001, REQ-002; AC-1, AC-2 | Both calls follow an inline first attempt (`_start_http_subprocess_once` at line 87, the inline health GET at lines 147-168); reproduction recorded three attempts (checked in Step 2 and Step 3) | `tests/agent/test_startup_mcp_lifecycle.py` | Verified |
| tests/agent/test_startup_mcp_lifecycle.py | Count attempts and the gap | Add start-path and health-path tests that count real attempts with a small `RETRY_DELAY_SEC` patch and assert the gap; keep `test_genuine_runtime_error_still_retries` and `test_startup_interrupted_propagates_without_retry` passing | REQ-004; AC-4 | `TestStartupOrchestratorStartServers` (starts at line 86) mocks `start_http_subprocess`; `TestStartupVerifyMcpHealth` (starts at line 278) patches `httpx.AsyncClient` (checked in Step 3) | tests/agent/test_startup_mcp_lifecycle.py | Verified |
| tests/agent/test_retry_helper.py | Cover the new option | Add tests: with `skip_first_attempt=True` `fn` is called exactly once after the delay; its failure raises the fatal-prefixed masked exception; a set shutdown event raises `StartupInterrupted` without calling `fn`; the default mode is unchanged | REQ-003, REQ-004; AC-3, AC-4 | The file holds the exception-type-preservation tests for the default mode (`test_timeout_error_preserved`, `test_connection_refused_error_preserved`, `test_runtime_error_preserved` and others), using a `call_count` closure (checked in Step 3) | tests/agent/test_retry_helper.py | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md | States the retry-once-after-delay contract that must hold after the change | REQ-001, REQ-002 |
| docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md | Names `retry_once_with_delay()` and the fatal-prefixed second failure; the option must keep both statements true | REQ-003 |
| tests/agent/test_startup_mcp_starter.py | Regression suite for the starter that must keep passing | REQ-001, REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): With a start operation that always fails, the underlying `start_http_subprocess` is called exactly twice and the second call occurs no earlier than `RETRY_DELAY_SEC` after the first.
- AC-2 (REQ-002): With a health probe that always fails, the probe sequence is attempted exactly twice (the inline attempt and one retry) with the delay between them.
- AC-3 (REQ-003): `retry_once_with_delay(..., skip_first_attempt=True)` calls `fn` exactly once, after the delay, raises the masked fatal-prefixed exception on failure and raises `StartupInterrupted` without calling `fn` when the shutdown event is set; with the default the behavior is byte-for-byte as before.
- AC-4 (REQ-004): `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_retry_helper.py tests/agent/test_startup_mcp_starter.py` passes with the new cases, and the new attempt-count tests fail against the pre-change code.
- AC-5 (REQ-001, REQ-002, REQ-003): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py` pass.

## Tests
- REQ-001: start-path test: a lifecycle stub that always raises counts exactly two calls and a gap of at least the patched delay; a stub failing once then returning a process still yields that process (existing test kept).
- REQ-002: health-path test: a patched client that always returns a failing status counts exactly two sequences with the gap; a client failing once then returning 200 passes.
- REQ-003: helper tests for the option (one call after the delay, masked fatal-prefixed failure, shutdown before the delay raises `StartupInterrupted`, shutdown during the delay) and a regression test that the default mode still calls `fn` first.
- REQ-004: the count and gap assertions above are the tests; write them first and confirm they fail on the current code.

## Documentation Impact
N/A: the contract in `docs/22_mcp/mcp_06_03_long-running-http-operation-startup_modesubprocess.md` and `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` already states one retry after a fixed delay and names `retry_once_with_delay()`, which keeps its name and default behavior; no `docs/*.md` change is required (REQ-001 to REQ-003).

## Assumptions
- A keyword-only option on the existing helper is preferred to a second helper function: it keeps the name that the ADR and the doc cite and keeps the tests' patch target (`agent.startup_mcp_starter.retry_once_with_delay`) valid. Falsifiable by the ADR/doc grep recorded in Step 3.
- Keeping the inline first attempt is correct because it preserves the exception filter (only a fixed set of types retried) and the tolerated `None` result, both asserted by existing tests (`test_no_process_returned_does_not_append`, `test_startup_interrupted_propagates_without_retry`).
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports no finding that names this Plan; none of its four target files is a target of another Frozen Plan at the time of freezing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the default (first-attempt-included) mode of `retry_once_with_delay` stays used after this change; it has no production caller afterwards, only tests and the ADR text | Decision on removal vs keeping | Keep it in this Plan; revisit under `rules/coding.md` deprecation policy only if the ADR text changes | False |
| UNK-02 | Re-verification of `issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md` after this lands (open sibling, related, not blocking) | The sibling's reachability after the delayed retry | Re-check when that issue is planned: `issues/20261115-214903_startrev003_retry-reuses-unconfirmed-process.md` | False |
| UNK-03 | Order against `issues/20261115-214907_startrev007_degraded-live-nondict-body.md`, which edits `McpServerStarter.verify_health` (open sibling, related, not blocking) | Merge order of two small edits to one method | Plan 007 will record the overlap; implement in sequence: `issues/20261115-214907_startrev007_degraded-live-nondict-body.md` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/shared/retry_helper.py | Modify | Low: two production call sites, both in `startup_mcp_starter.py`; a new optional keyword | 1 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_mcp_starter.py | Modify | Medium: every agent startup passes through `start_servers` and `verify_health`; behavior changes only on a failing server | 5 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/test_startup_mcp_lifecycle.py | Modify | Low: tests only | 2 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_retry_helper.py | Modify | Low: tests only | 0 | High: one author | not applicable (rsynced): `tests/` is not deployed |

## Design
- **Design decision (retry ownership)**: three options were weighed. (1) Remove the inline first attempt and let the helper own both attempts: rejected, because the helper retries any `Exception` while the inline code retries only a fixed set of types, so a programming error would start being retried, the tolerated `None` first result would be lost, and two existing tests assert the current shape. (2) Add a second helper that only retries: rejected, because the ADR and the doc name `retry_once_with_delay()` as the path and would go stale. (3) Add `skip_first_attempt` to the existing helper: chosen. Compatibility impact: none for the default call; the two call sites change behavior only by dropping the extra immediate attempt.
- **Behavior after the change**: first attempt (inline, caller's exception filter) fails → helper checks the shutdown event, waits the interruptible delay, makes the second attempt → on failure raises the fatal-prefixed masked exception. Total attempts per server: two.
- **Counting contract for tests**: the unit under test counts calls of `lifecycle.start_http_subprocess` and of the health client's `get`, not calls of the helper, because the existing spy-based test cannot see the defect.
- **Architecture analysis**: imports checked with `lint-imports`: 6 contracts kept, 0 broken at this commit; `retry_helper.py` imports only `asyncio` and lazily `agent.startup` and `agent.secrets_masker`; no new import is added (checked in Step 5).
- **Dependency graph**: `retry_once_with_delay` is imported by `startup_mcp_starter.py` and the tests only (checked in Step 3).
- **Historical analysis**: `startup_mcp_starter.py` 5 commits and `retry_helper.py` 1 commit in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: no port or database is touched by this change; no deploy-time lock to check (checked in Step 5).
- **Validation quality baseline**: radon: `start_servers` C (16), `verify_health` C (15), `retry_once_with_delay` B (6), no complexity increase expected; vulture: no findings in the target files (five unrelated findings elsewhere in `scripts/`); bandit (medium and above): no issues in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); the baseline test run was 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind` (unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold).

## Implementation steps
1. **Phase 1: Retry helper option**
   - [ ] Add keyword-only `skip_first_attempt: bool = False` to `retry_once_with_delay` and skip the leading `await fn()` when set; keep the shutdown pre-check, the interruptible delay and the masked fatal rebuild untouched; update the docstring (REQ-003; scripts/agent/shared/retry_helper.py)
   - [ ] Add the helper tests first and confirm the new option tests fail before the change (REQ-003, REQ-004; tests/agent/test_retry_helper.py)
2. **Phase 2: Starter call sites**
   - [ ] Add the start-path attempt-count and gap test and confirm it fails on the current code (REQ-001, REQ-004; tests/agent/test_startup_mcp_lifecycle.py)
   - [ ] Pass `skip_first_attempt=True` in the `start_servers` retry call (REQ-001; scripts/agent/startup_mcp_starter.py)
   - [ ] Add the health-path attempt-count and gap test, then pass `skip_first_attempt=True` in the `verify_health` retry call (REQ-002, REQ-004; tests/agent/test_startup_mcp_lifecycle.py, scripts/agent/startup_mcp_starter.py)
3. **Phase 3: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002, REQ-003; scripts/agent/shared/retry_helper.py, scripts/agent/startup_mcp_starter.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/shared/retry_helper.py | Unit | `uv run pytest tests/agent/test_retry_helper.py -q` | New option tests and all existing helper tests pass |
| scripts/agent/startup_mcp_starter.py | Unit | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_startup_mcp_starter.py -q` | Attempt counts are exactly two; existing starter tests pass |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Reference table and module size | Static | `uv run python tools/generate_reference_table.py --check && uv run python tools/check_module_size.py` | No drift; no module over its limit |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: A caller relying on the immediate second attempt now sees one fewer attempt and a longer gap before the second (likelihood low; the only callers are the two sites in this Plan) → **Mitigation**: the contract and docs already say one retry after a fixed delay; tests assert the new count.
- **Risk**: The option changes a shared helper (likelihood low) → **Mitigation**: the default is unchanged and covered by a regression test; no other production caller exists (checked in Step 3).
- **Risk**: `verify_health` is edited by a sibling issue (likelihood medium) → **Mitigation**: implement in sequence; the one-line call edit is trivial to rebase.
- **Risk**: A gap assertion in a test can be flaky on a loaded host (likelihood low) → **Mitigation**: assert a lower bound only, with a small patched delay, and no upper bound.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retry helper option and its tests (scripts/agent/shared/retry_helper.py, tests/agent/test_retry_helper.py) | Completed | 20261116-131551 | 20261116-131945 |  |
| 2 | Starter call sites and their tests (scripts/agent/startup_mcp_starter.py, tests/agent/test_startup_mcp_lifecycle.py) | Completed | 20261116-142246 | 20261116-142246 |  |
| 3 | Deployment and verification (scripts/agent/shared/retry_helper.py, scripts/agent/startup_mcp_starter.py) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-094712_01_scripts_agent_shared_retry_helper.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261116-094712_02_scripts_agent_startup_mcp_starter.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214902_startrev002_mcp-start-retry-attempts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-215900
- **Related target files**: scripts/agent/shared/retry_helper.py, scripts/agent/startup_mcp_starter.py, tests/agent/test_startup_mcp_lifecycle.py, tests/agent/test_retry_helper.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1); `start_servers` retry call; reproduction of three attempts | scripts/agent/startup_mcp_starter.py | Phase 2 | AC-1 | start-path attempt-count test | Confirmed by repository evidence |
| REQ-001 | Issue Acceptance Criteria (1); Testing Expectations | tests/agent/test_startup_mcp_lifecycle.py | Phase 2 | AC-1, AC-4 | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -q` | Explicit in issue |
| REQ-002 | Issue Required Changes (2); `verify_health` retry call | scripts/agent/startup_mcp_starter.py | Phase 2 | AC-2 | health-path attempt-count test | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria (2) | tests/agent/test_startup_mcp_lifecycle.py | Phase 2 | AC-2, AC-4 | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py -q` | Explicit in issue |
| REQ-003 | Issue Constraints (helper is shared; behavior must not change for other callers); `retry_once_with_delay` line 41 | scripts/agent/shared/retry_helper.py | Phase 1 | AC-3 | helper option tests | Derived from confirmed evidence |
| REQ-003 | Issue Acceptance Criteria (3); Testing Expectations | tests/agent/test_retry_helper.py | Phase 1 | AC-3, AC-4 | `uv run pytest tests/agent/test_retry_helper.py -q` | Explicit in issue |
| REQ-004 | Issue Testing Expectations; existing spy test counts helper awaits only | tests/agent/test_startup_mcp_lifecycle.py | Phase 2 | AC-4 | new tests fail on the pre-change code | Confirmed by repository evidence |
| REQ-004 | Issue Testing Expectations | tests/agent/test_retry_helper.py | Phase 1 | AC-4 | new tests fail on the pre-change code | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-094712 -->