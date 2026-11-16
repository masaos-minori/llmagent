## Goal
- Make the degraded-but-live check a single typed predicate that returns false, without raising, for any `/health` body that is not a JSON object carrying the boolean `true`, and make every startup path use that one predicate.

## Priority
Medium

## Scope
- **In-Scope**: `HealthChecker.is_degraded_but_live` (defensive parse, object check, strict boolean test, corrected docstring); replacing the inline copy in `McpServerStarter.verify_health` with a call to it; tests for both phases.
- **Out-of-Scope**: the 503 and `liveness` health protocol itself; server-side `/health` output; the retry count and delay (`plans/20261115-215900_startrev002_mcp-start-retry-attempts.md`); the polling loop's other exception handling; documentation text.
- **Dependencies**: related, not blocking: `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md` (it edits the retry call at the end of `McpServerStarter.verify_health`; this Plan replaces the inline degraded block earlier in the same method; implement Plan 002 first, the two edits do not overlap in lines).

## Background
- Found by an adversarial review of the agent startup path at commit `490fccc50` (Issue `issues/20261115-214907_startrev007_degraded-live-nondict-body.md`).
- `HealthChecker.is_degraded_but_live` parses a 503 response and reads `body.get("liveness")`. It catches only `json.JSONDecodeError` and `httpx.DecodingError` around the parse. A JSON array or string body raises `AttributeError` at `body.get`. Reproduced in Step 2 of the review: array body and string body raise `AttributeError`; a `null` body returns false.
- `HealthChecker.poll_until_ready` wraps the call in `except (httpx.HTTPError, OSError)`, so the `AttributeError` escapes the poll loop, and `McpServerStarter.start_servers` retries only `OSError`, `RuntimeError` and related types, so it also escapes there to `StartupOrchestrator.run`'s broad handler, which rolls back and re-raises (Explicit in code, read in Step 3).
- `McpServerStarter.verify_health` carries an inline copy of the check and catches `httpx.DecodingError` around `resp.json()`; `resp.json()` raises `json.JSONDecodeError` (a `ValueError`), so the inline copy survives a malformed body only through the outer `except Exception`.
- Found in Step 2 of this cycle (beyond the Issue): the current test is truthiness, `bool(body.get("liveness", False))`. Reproduced: `{"liveness": "false"}` and `{"liveness": "0"}` are treated as live; `{"liveness": 0}` is not. The only emitter in the repository writes the boolean `True` (`scripts/mcp_servers/health_response.py`), so a strict boolean test is compatible with every server in the repository.
- The docstring of `is_degraded_but_live` says it mirrors `McpServerStartupStarter.verify_health`; that class does not exist (the class is `McpServerStarter`).

## Problem
Two implementations of one rule have diverged. The shared one raises for non-object JSON and accepts truthy non-boolean values as live; the inline one is correct only through a broad outer handler. A booting server answering 503 with a non-object body aborts startup with an `AttributeError` instead of being polled on or retried, and the message names an attribute error, not the server.

## Reason for Change
Startup failure classification should come from typed handling, not from which exception happens to escape; one predicate also keeps the spawn phase and the post-startup phase in agreement about what "live" means, as the predicate's own docstring requires. Medium because it needs an unusual health response and the outcome is a startup abort that rollback already cleans up.

## Implementation Intent
Make `is_degraded_but_live` the only implementation. It parses the body defensively (any `ValueError`, which includes `json.JSONDecodeError`, and `httpx.DecodingError` mean "not degraded-but-live"), requires the parsed value to be a JSON object, and returns true only when `liveness` is the boolean `true`. `McpServerStarter.verify_health` calls it instead of its inline copy and keeps its existing log lines and its outer retry handling. The issue's open question (truthy values) is decided here as "only the boolean `true`", on the evidence that every emitter writes a boolean.

## Requirements
- `REQ-001`: `HealthChecker.is_degraded_but_live` returns false without raising for every body that is not a JSON object (array, string, number, null, malformed JSON, empty body) and returns true only for a 503 JSON object whose `liveness` is the boolean `true`.
- `REQ-002`: `McpServerStarter.verify_health` contains no copy of the degraded-but-live rule and calls `HealthChecker.is_degraded_but_live`; behavior for object bodies is unchanged.
- `REQ-003`: A server answering 503 with a non-object body keeps being polled by the readiness loop until the startup timeout instead of aborting the start.
- `REQ-004`: A 503 object body with `liveness` true stays ready-but-degraded in both phases, and every other non-200 response stays a failure that enters the existing retry path.
- `REQ-005`: Tests cover the predicate over all body shapes, the poll loop with a non-object 503 then 200, and `verify_health` through the retry path.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Own the typed predicate | Rewrite `is_degraded_but_live`: catch `ValueError` and `httpx.DecodingError` around `resp.json()`, return false unless the body is a `dict`, return `body.get("liveness") is True`; correct the docstring's class name; remove the `import json` that becomes unused (found while generating the procedure) | REQ-001, REQ-003, REQ-004; AC-1, AC-3, AC-4 | `is_degraded_but_live` at lines 104-122: `except (json.JSONDecodeError, httpx.DecodingError)` and `return bool(body.get("liveness", False))`; docstring names `McpServerStartupStarter`; reproduction raised `AttributeError` on array and string bodies and returned true for `"false"` (checked in Step 2 and Step 3) | `tests/agent/test_http_lifecycle_health_check.py` | Verified |
| scripts/agent/startup_mcp_starter.py | Remove the inline copy | In `verify_health`, replace the inline 503 JSON parsing (lines 152-166) with `if resp.status_code == 503 and HealthChecker.is_degraded_but_live(resp)`-style delegation, keeping the "degraded but live" info log and the `continue`; leave the outer retry handler as is | REQ-002, REQ-004; AC-2, AC-4 | The inline block reads `resp.json()`, `body.get("liveness", False)` and catches `httpx.DecodingError`; `HealthChecker` is already imported at line 22 and used by `_verify_single_health` (checked in Step 3) | `tests/agent/test_startup_mcp_starter.py` | Verified |
| tests/agent/test_http_lifecycle_health_check.py | Predicate and poll-loop tests | Extend `test_is_degraded_but_live_branches` (line 376) and add cases to `TestHealthPollDegradedTolerance` (line 303): array, string, number, null, malformed and empty bodies; `"false"` and `0` liveness; a poll with a non-object 503 followed by 200 | REQ-001, REQ-003, REQ-005; AC-1, AC-3, AC-5 | `TestHealthPollDegradedTolerance` has `test_tolerates_degraded_but_live` (line 313) and `test_rejects_503_without_liveness_flag` (line 345) using `mgr` and httpx responses (checked in Step 3) | tests/agent/test_http_lifecycle_health_check.py | Verified |
| tests/agent/test_startup_mcp_starter.py | `verify_health` tests | Add httpx-based cases: a 503 object body with `liveness` true continues without retry; a 503 non-object body goes through the retry path and ends in the existing fatal error; no inline copy remains (behavioral) | REQ-002, REQ-004, REQ-005; AC-2, AC-4, AC-5 | The file holds `test_verify_single_health_degraded_but_live_does_not_raise` (line 143) and a `verify_health` test with `route.call_count == 1` (line 124) built on a respx-style router (checked in Step 3) | tests/agent/test_startup_mcp_starter.py | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/health_response.py | The emitter of the `/health` body; it writes the boolean `liveness: True`, which justifies the strict test | REQ-001 |
| tests/agent/test_startup_mcp_lifecycle.py | Its `TestStartupVerifyMcpHealth` builds 503 responses as `MagicMock`; the new delegation must keep those tests passing | REQ-002 |
| scripts/agent/shared/retry_helper.py | `verify_health` retries through it; the retry path must stay as is | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `is_degraded_but_live` returns false, without raising, for array, string, number, null, malformed and empty 503 bodies and for `liveness` values that are not the boolean `true` (`"false"`, `"0"`, `0`, `null`); it returns true only for a 503 JSON object with `liveness` true.
- AC-2 (REQ-002): `McpServerStarter.verify_health` contains no `body.get`, `resp.json()` or JSON-parsing code of its own and delegates to `HealthChecker.is_degraded_but_live`.
- AC-3 (REQ-003): A poll test with a fake server answering 503 with a non-object body and then 200 ends ready, and one that never recovers ends with the existing timeout `HttpStartupError`, not with an `AttributeError`.
- AC-4 (REQ-004): A 503 object body with `liveness` true is accepted in both phases; any other non-200 response still enters the existing retry path and ends in the fatal error after the retry.
- AC-5 (REQ-005): `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_mcp_lifecycle.py` passes with the new cases, and the non-object-body tests fail against the pre-change code.
- AC-6 (REQ-001, REQ-002): `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass; `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check` pass.

## Tests
- REQ-001: parametrized predicate tests over body shapes and `liveness` values, with real `httpx.Response` objects.
- REQ-003: poll-loop tests using the existing `mgr` fixture: non-object 503 then 200 becomes ready; a permanent non-object 503 times out with `HttpStartupError`.
- REQ-002, REQ-004: `verify_health` tests with httpx-level responses for the object, non-object and non-503 cases; the existing `MagicMock`-based tests in `tests/agent/test_startup_mcp_lifecycle.py` must keep passing unchanged.
- REQ-005: write the non-object-body and `"false"` tests first and confirm they fail on the current code.

## Documentation Impact
N/A: no `docs/*.md` change is required. The startup health text states that a 503 with a liveness flag counts as degraded-but-live and does not name the body-shape handling; re-read it after the change and correct a statement only if the final behavior contradicts it (REQ-001, REQ-004).

## Assumptions
- Only the boolean `true` counts as live: every emitter in the repository writes a boolean (`scripts/mcp_servers/health_response.py`) and the eventbus health route builds `liveness` from a boolean expression; falsifiable by a repository search for other `/health` producers (done in Step 3: none found).
- Delegating to the shared predicate keeps the `MagicMock` 503 tests green: a `MagicMock` response has a status of 503, its `headers.get(...)` returns a mock for which `"application/json" in ...` is false, so the predicate returns false and the path ends in the existing failure (checked in Step 3).
- Overlap judgment (Step 8b): `tools/check_plan_target_overlaps.py` reports one finding naming this Plan: `scripts/agent/startup_mcp_starter.py`, also targeted by `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md`. Judged compatible with a sequencing preference: Plan 002 changes the retry call at the end of `verify_health` and the one in `start_servers`; this Plan replaces the inline degraded block earlier in `verify_health`; neither changes what the other asserts. Implement Plan 002 first. Recorded in Scope Dependencies as a sequencing note.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Order against `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md`, which edits `McpServerStarter.verify_health` (open sibling Plan, related, not blocking) | Merge order of two edits to one method | Implement Plan 002 first; the edits touch different lines: `plans/20261115-215900_startrev002_mcp-start-retry-attempts.md` | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Modify | Medium: the predicate gates every subprocess MCP server's startup readiness poll and `verify_health`; behavior changes only for non-object bodies and non-boolean liveness | 4 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| scripts/agent/startup_mcp_starter.py | Modify | Medium: every agent startup passes through `verify_health`; behavior changes only on a 503 response | 5 | High: one author | not applicable (rsynced): `deploy/deploy.sh` rsyncs `scripts/` |
| tests/agent/test_http_lifecycle_health_check.py | Modify | Low: tests only | 2 | High: one author | not applicable (rsynced): `tests/` is not deployed |
| tests/agent/test_startup_mcp_starter.py | Modify | Low: tests only | 3 | High: one author | not applicable (rsynced): `tests/` is not deployed |

## Design
- **Design decision (strictness)**: options weighed for `liveness`. (1) Keep truthiness: rejected, `"false"` and `"0"` count as live, which is wrong for a health signal. (2) Accept the boolean `true` only: chosen, compatible with every emitter in the repository. (3) Also accept the strings `"true"`/`"1"`: rejected as speculative. Compatibility impact: a server that sent a non-boolean truthy value would stop counting as degraded-but-live; none exists in the repository.
- **Design decision (single implementation)**: the rule lives only in `HealthChecker.is_degraded_but_live`; `verify_health` delegates. The outer `except Exception` in `verify_health` stays because it also covers connection errors, and its retry path is unchanged.
- **Architecture analysis**: `lint-imports` reports 6 contracts kept, 0 broken at this commit; `startup_mcp_starter.py` already imports `HealthChecker`; no new import (checked in Step 5).
- **Dependency graph**: `is_degraded_but_live` is called by `HealthChecker.poll_until_ready` and `McpServerStarter._verify_single_health`; the inline copy is only in `verify_health` (checked in Step 3).
- **Historical analysis**: `http_lifecycle_health_checker.py` 4 commits and `startup_mcp_starter.py` 5 commits in the last 30 days; one contributor (two spellings of one name) in the last 90 days (checked in Step 5).
- **Operational dependency inspection**: no port, database or service is touched (checked in Step 5).
- **Validation quality baseline**: radon: `start_servers` C (16) and `verify_health` C (15) today, and the change removes branches from `verify_health`; vulture and bandit: no finding in the target files; diff-cover baseline: the working tree equals `master`, so the diff has no coverage lines (no current number); baseline test run 12261 passed, 2 failed, 7 skipped, the two failures being the pre-existing posture tests `tests/mcp_servers/test_posture_gate_start_path.py::test_running_the_mdq_entry_module_goes_through_real_run_http` and `tests/mcp_servers/mdq/test_mdq_health_posture.py::TestBindGate::test_validated_posture_does_not_block_bind`, unrelated to this Plan; the Plan must raise diff coverage to the `rules/toolchain.md` threshold.

## Implementation steps
1. **Phase 1: Shared predicate**
   - [ ] Write the predicate and poll-loop tests first and confirm the non-object-body and `"false"` cases fail on the current code (REQ-001, REQ-003, REQ-005; tests/agent/test_http_lifecycle_health_check.py)
   - [ ] Rewrite `is_degraded_but_live` and correct its docstring (REQ-001, REQ-003, REQ-004; scripts/agent/http_lifecycle_health_checker.py)
2. **Phase 2: Remove the inline copy**
   - [ ] Add the `verify_health` tests with httpx-level responses (REQ-002, REQ-004, REQ-005; tests/agent/test_startup_mcp_starter.py)
   - [ ] Replace the inline degraded block in `verify_health` with a call to the shared predicate (REQ-002, REQ-004; scripts/agent/startup_mcp_starter.py)
3. **Phase 3: Deployment & verification**
   - [ ] Run the validation plan; hand off to `skills/deploy/SKILL.md` only after the change is committed and pushed, and deploying is the user's decision (REQ-001, REQ-002; scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Unit | `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q` | New predicate and poll cases pass; existing cases pass |
| scripts/agent/startup_mcp_starter.py | Unit | `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_mcp_lifecycle.py -q` | New `verify_health` cases pass; the `MagicMock` 503 tests pass unchanged |
| Changed Python files | Static | `uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && PYTHONPATH=scripts uv run lint-imports` | No findings; 6 contracts kept |
| Module size and reference table | Static | `uv run python tools/check_module_size.py && uv run python tools/generate_reference_table.py --check` | No module over its limit; no drift |
| Diff coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At or above the threshold in `rules/toolchain.md` |

## Risks
- **Risk**: A server that sends a non-boolean truthy `liveness` stops counting as degraded-but-live and fails startup (likelihood low; none exists in the repository) → **Mitigation**: the emitter inventory in Step 3; the strictness decision is recorded in Design and the assumption is falsifiable.
- **Risk**: The `MagicMock`-based 503 tests behave differently once `verify_health` delegates (likelihood low) → **Mitigation**: analysed in Step 3 and listed as a validation command; run them before and after.
- **Risk**: Both this Plan and Plan 002 edit `McpServerStarter.verify_health` (likelihood medium) → **Mitigation**: implement Plan 002 first; the edits are on different lines.
- **Risk**: A defensive `ValueError` catch could hide a future bug in the parser (likelihood low) → **Mitigation**: the predicate returns false only, and the outer retry path still ends in the fatal error with the HTTP status.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Shared predicate and its tests (scripts/agent/http_lifecycle_health_checker.py, tests/agent/test_http_lifecycle_health_check.py) | Completed | — | 20261116-134510 |  |
| 2 | Remove the inline copy and add `verify_health` tests (scripts/agent/startup_mcp_starter.py, tests/agent/test_startup_mcp_starter.py) | Completed | — | 20261116-140914 |  |
| 3 | Deployment and verification (scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py) | Completed | — | 20261116-185552 | Deployed HEAD bddab31ce. All 11 binaries rebuilt (max-arity fix efd6c5cae; agent rebuilt again after REQ-006 merge). Schema-drift audit: rag/eventbus/session/workflow DBs recreated, old files archived as *.pre-deploy-20261116.bak (session kept 6 sessions/500 memories per operator decision), mdq OK untouched. Event Bus restarted healthy (direct documented launch, setup_services.sh gate blocked by remote agent-llm host 192.168.11.197 down, out of repo scope). cicd orphan test process killed, port 8012 free for on-demand binary start. DEPLOYED_REV and agent sha256 verified. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261116-095125_01_scripts_agent_http_lifecycle_health_checker.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261116-095125_02_scripts_agent_startup_mcp_starter.py.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261115-214907_startrev007_degraded-live-nondict-body.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-220700
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py, scripts/agent/startup_mcp_starter.py, tests/agent/test_http_lifecycle_health_check.py, tests/agent/test_startup_mcp_starter.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (1); reproduction of `AttributeError`; truthiness reproduction in Step 2 | scripts/agent/http_lifecycle_health_checker.py | Phase 1 | AC-1 | predicate tests | Confirmed by repository evidence |
| REQ-003 | Issue Acceptance Criteria (3); `poll_until_ready` exception tuple | scripts/agent/http_lifecycle_health_checker.py | Phase 1 | AC-3 | poll-loop tests | Confirmed by repository evidence |
| REQ-004 | Issue Constraints (object body with liveness true stays ready in both phases) | scripts/agent/http_lifecycle_health_checker.py | Phase 1 | AC-4 | existing tolerance tests plus new cases | Explicit in issue |
| REQ-002 | Issue Required Changes (2); inline block in `verify_health` | scripts/agent/startup_mcp_starter.py | Phase 2 | AC-2 | `verify_health` tests | Confirmed by repository evidence |
| REQ-004 | Issue Constraints (any other non-200 enters the existing retry path) | scripts/agent/startup_mcp_starter.py | Phase 2 | AC-4 | `verify_health` retry-path test | Explicit in issue |
| REQ-001 | Issue Required Changes (3); Testing Expectations | tests/agent/test_http_lifecycle_health_check.py | Phase 1 | AC-1, AC-5 | `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q` | Explicit in issue |
| REQ-003 | Issue Testing Expectations (poll-loop test with a fake server) | tests/agent/test_http_lifecycle_health_check.py | Phase 1 | AC-3, AC-5 | poll-loop tests | Explicit in issue |
| REQ-005 | Issue Testing Expectations | tests/agent/test_http_lifecycle_health_check.py | Phase 1 | AC-5 | new tests fail on the pre-change code | Explicit in issue |
| REQ-002 | Issue Testing Expectations (`verify_health` test through the retry path) | tests/agent/test_startup_mcp_starter.py | Phase 2 | AC-2, AC-5 | `uv run pytest tests/agent/test_startup_mcp_starter.py -q` | Explicit in issue |
| REQ-004 | Issue Testing Expectations | tests/agent/test_startup_mcp_starter.py | Phase 2 | AC-4, AC-5 | `verify_health` retry-path test | Explicit in issue |
| REQ-005 | Issue Testing Expectations | tests/agent/test_startup_mcp_starter.py | Phase 2 | AC-5 | new tests fail on the pre-change code | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261116-095125 -->