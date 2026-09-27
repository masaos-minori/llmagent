## Goal

Root-cause and fix order/state-dependent flakiness in `tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs`, which passes reliably in isolation but fails intermittently in a full-suite/multi-test context (REQ-002).

## Scope

In scope: this test's isolation for whatever shared state causes the intermittent failure. Out of scope: `tests/eventbus/test_eventbus_publish.py`, `tests/mcp_servers/shell/test_shell_server_endpoints.py` (each covered by its own implementation procedure document from this same Plan — though this test's shared-state cause may turn out to be structurally similar to the shell-server test's, given both are named identically and test the same `TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs` pattern in sibling MCP server modules — confirm independently before assuming identical causes).

## Assumptions

- The failure is a test-isolation gap (shared mutable state across tests), not a genuine timing race in production code — consistent with the confirmed pattern that this test passes reliably alone.

## Design decisions

- Per `skills/python-test-and-fix/SKILL.md` Path D: bisect first, given this test's name/structure closely mirrors the shell-server sibling test — check whether both tests share a common audit-logging helper/mock (e.g. in `scripts/mcp_servers/server.py`, the shared base module both `cicd`/`shell` servers likely use) whose state isn't reset between tests.

## Alternatives considered

- Fixing this test in isolation without checking for a shared cause with the shell-server sibling test: rejected — given both tests are named identically and test the same behavior pattern (`test_dispatches_known_tool_and_audit_logs`) in sibling MCP server modules built on a shared base, a common root cause (e.g. in `scripts/mcp_servers/server.py`'s shared audit-logging path) is plausible and should be checked before assuming two independent causes.

## Implementation

### Target file

`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`

### Procedure

1. Check whether this test and `tests/mcp_servers/shell/test_shell_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs` share a common fixture/base class/audit-logging mock (e.g. via `rg -n "class TestCallToolEndpoint"` in both files and comparing their setup) — if so, investigate and fix the shared cause once, referencing both test files.
2. Bisect within `tests/mcp_servers/`: run this test alongside progressively larger subsets to find the minimal reproducing combination (which other test, run first, triggers the failure).
3. Inspect the identified shared state directly and add the appropriate per-test isolation (a fixture reset, or an equivalent fix).

### Method

Investigative bisection first (per `skills/python-test-and-fix/SKILL.md` Path D), checking for a shared cause with the sibling shell-server test before treating this as fully independent — then a fix scoped to the confirmed mechanism, not a blind retry-based fix.

### Details

- Reproduction baseline already confirmed in this session: 2 reruns of `tests/eventbus/test_eventbus_publish.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs tests/mcp_servers/shell/test_shell_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs` together showed a different one of the 2 mcp_servers tests failing each time (never both, never neither) — this alternating pattern is itself a clue: it may indicate a shared resource both tests compete for (e.g. a shared port, a shared audit-log file path, or a shared mock registry) rather than pure random flakiness.
- If the fix requires modifying production code (e.g. `scripts/mcp_servers/server.py`'s shared base), this is an additional target file discovery — stop and report `Blocked: additional target file discovered — {path}` pending Plan amendment.

## Compatibility considerations

- No production change anticipated (pending investigation); if one is required, compatibility impact TBD.

## Security considerations

N/A: test-reliability fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added isolation fixture.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Integration (repeated-run flaky verification) | `uv run pytest tests/mcp_servers/ -q` (x5 consecutive) | The test passes consistently across all 5 runs |

## Completion criteria

- The test passes consistently across 5 consecutive runs of `uv run pytest tests/mcp_servers/ -q`.
- No `time.sleep()` or blind retry was used as the fix.

## Out of scope

- `tests/eventbus/test_eventbus_publish.py`, `tests/mcp_servers/shell/test_shell_server_endpoints.py` (each covered by its own implementation procedure document from this same Plan) — though investigate for a shared cause per Procedure step 1 before finalizing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check for a shared cause with the sibling shell-server test | Completed | 20260927-151219 | 20260927-152000 | Root cause: `_duplicate_cache` in `dispatch.py` shared between MCP servers; both tests use empty `idempotency_key=""` causing cross-test cache collision |
| 2 | Bisect to find the minimal reproducing test combination | Completed | 20260927-151500 | 20260927-151800 | Confirmed alternating failure pattern: cicd→shell or shell→cicd depending on execution order |
| 3 | Fix the identified shared-state issue and verify consistent passing | Completed | 20260927-152000 | 20260927-152500 | Added unique `x-idempotency-key` headers to both tests; verified 50 consecutive runs pass |

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
- **Requirement ID**: REQ-002: root-cause and fix flakiness in `test_cicd_server_endpoints.py`
- **Source issue**: issues/20260927-075303_test002_flaky-tests-observed-in-full-suite-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093620
- **Related target files**: tests/mcp_servers/cicd/test_cicd_server_endpoints.py
