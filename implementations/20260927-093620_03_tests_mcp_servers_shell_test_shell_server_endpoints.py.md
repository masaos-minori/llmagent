## Goal

Root-cause and fix order/state-dependent flakiness in `tests/mcp_servers/shell/test_shell_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs`, which passes reliably in isolation but fails intermittently in a full-suite/multi-test context (REQ-003).

## Scope

In scope: this test's isolation for whatever shared state causes the intermittent failure. Out of scope: `tests/eventbus/test_eventbus_publish.py` (a distinct file/cause). This test shares an identical name/structure with `tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs` (covered by its own implementation procedure document from this same Plan) — coordinate the investigation per that document's Procedure step 1 rather than duplicating it independently here.

## Assumptions

- The failure is a test-isolation gap (shared mutable state across tests), not a genuine timing race in production code — confirmed via this session's own recheck: this exact test passed reliably (`1 passed`) when run in complete isolation.

## Design decisions

- Coordinate with the `test_cicd_server_endpoints.py` implementation procedure document (same Plan): if that document's investigation (Procedure step 1) finds a shared cause between the two sibling tests, apply the fix once (in whichever file/shared-base module the root cause actually lives) and reference both test files' Traceability sections to this shared finding, rather than duplicating the investigation independently.

## Alternatives considered

- Investigating this test in full isolation from the `cicd` sibling: rejected — given the identical test name/structure across two sibling MCP server modules, checking for a shared cause first is more efficient and more likely to reveal the true mechanism than two independent investigations that might each land on a different (possibly incomplete) explanation.

## Implementation

### Target file

`tests/mcp_servers/shell/test_shell_server_endpoints.py`

### Procedure

1. Check the `test_cicd_server_endpoints.py` implementation procedure document's (same Plan) Procedure step 1 finding first — if it already identified a shared cause (e.g. in `scripts/mcp_servers/server.py`'s shared base), apply the same fix here (or confirm it already covers this file, if the fix lives in shared production code) rather than re-investigating from scratch.
2. If no shared cause was found (the two tests' failures are confirmed independent), bisect within `tests/mcp_servers/` for this test specifically: run it alongside progressively larger subsets to find the minimal reproducing combination.
3. Inspect the identified shared state directly and add the appropriate per-test isolation.

### Method

Coordinated investigation with the `cicd` sibling test's implementation procedure first (per Design decisions), falling back to independent bisection only if no shared cause is found — then a fix scoped to the confirmed mechanism, not a blind retry-based fix.

### Details

- Reproduction baseline already confirmed in this session: this test passed reliably in isolation (`1 passed`) but failed in 1 of 2 reruns when run alongside `tests/eventbus/test_eventbus_publish.py`/`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.
- If the fix requires modifying production code (e.g. `scripts/mcp_servers/server.py`'s shared base), this is an additional target file discovery — stop and report `Blocked: additional target file discovered — {path}` pending Plan amendment, per `rules/workflow-lifecycle.md`. If the `cicd` sibling document's cycle already reported and resolved this same discovery, reference that resolution here instead of re-reporting it.

## Compatibility considerations

- No production change anticipated (pending investigation); if one is required (possibly shared with the `cicd` sibling test's fix), compatibility impact TBD.

## Security considerations

N/A: test-reliability fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added isolation fixture.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/mcp_servers/shell/test_shell_server_endpoints.py` | Integration (repeated-run flaky verification) | `uv run pytest tests/mcp_servers/ -q` (x5 consecutive) | The test passes consistently across all 5 runs |

## Completion criteria

- The test passes consistently across 5 consecutive runs of `uv run pytest tests/mcp_servers/ -q`.
- No `time.sleep()` or blind retry was used as the fix.

## Out of scope

- `tests/eventbus/test_eventbus_publish.py` (distinct file/cause, its own implementation procedure document).
- Duplicating the `cicd` sibling test's investigation if it already found and fixed a shared cause.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Check the `cicd` sibling document's finding for a shared cause | Pending | — | — | |
| 2 | Bisect independently if no shared cause was found | Pending | — | — | |
| 3 | Fix the identified shared-state issue and verify consistent passing | Pending | — | — | |

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
- **Requirement ID**: REQ-003: root-cause and fix flakiness in `test_shell_server_endpoints.py`
- **Source issue**: issues/20260927-075303_test002_flaky-tests-observed-in-full-suite-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093620
- **Related target files**: tests/mcp_servers/shell/test_shell_server_endpoints.py
