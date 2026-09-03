## Goal
Create `tests/integration/test_production_security_regression.py`: a new
process/integration-level regression suite proving, through real Agent
startup and real spawned MCP server subprocesses (not synthetic config
objects), that the system runs one Production-grade policy (`REQ-001`,
`REQ-002`), exposes MCP servers only through loopback with actual socket
inspection (`REQ-003`), fails startup correctly for required/optional MCP
components (`REQ-004`), enforces MCP authentication with token redaction in
logs (`REQ-005`), and is unreachable from outside the loopback interface
(`REQ-006`, with a documented fallback when true network-namespace isolation
is unavailable).

## Scope
- **In-Scope**: this one new file only —
  `tests/integration/test_production_security_regression.py`, covering
  `REQ-001` through `REQ-006`.
- **Out-of-Scope**: `localremoval`'s, `loopbackonly`'s, and `mcpauth`'s own
  runtime implementations and unit tests (`REQ-011`/`REQ-005`/`REQ-007` in
  their respective Plans — this file tests the behavior those Plans
  introduce, one layer up, without duplicating their per-file unit
  assertions); deployment-manifest lint (`REQ-007`, no file — confirmed not
  applicable, see Assumptions); the documentation update (`REQ-008`, owned by
  this Plan's other target row, `docs/05_agent_10_04_...md`).

## Assumptions
- `localremoval` (`plans/20260903-091417_plan.md`), `loopbackonly`
  (`plans/20260903-091921_plan.md`), and `mcpauth`
  (`plans/20260903-092407_plan.md`) remain unimplemented as of 2026-09-03 —
  re-confirmed: all three are still under `plans/`. This suite's tests are
  expected to **fail or be skipped**, not pass, until those three land — the
  correctness criterion for this cycle is that the tests are written,
  collected, and run (per the module docstring convention below), not that
  they pass prematurely.
- `tests/integration/test_agent_mcp_integration.py` and
  `tests/integration/test_mcp_transport_crash.py` (re-confirmed to exist)
  establish this repository's existing process-level test patterns (subprocess
  spawning, fixture structure) — reuse their conventions rather than inventing
  a new pattern.
- No `unshare`/`netns`/network-namespace test pattern exists anywhere in
  `tests/` yet (re-confirmed via `grep -rl "unshare\|netns\|network.namespace" tests/`
  — zero matches) — `REQ-006` introduces the first one in this repository.
- The network-namespace-isolation mechanism for `REQ-006` may be unavailable
  in this environment (e.g. `unshare --net` requiring an ungranted
  capability); the test must probe for it at runtime and fall back to the
  documented manual-equivalent check (binding a probe socket to a
  non-loopback interface and confirming connection refusal) rather than
  failing the whole suite on an environment limitation unrelated to the
  behavior under test (per `UNK-01`).

## Design decisions
- One new file, not scattered assertions in the three dependency Plans' own
  unit-test files — keeps "layer" (unit vs. process/integration) as the
  scope boundary, per the source Plan's Design section and the source
  Issue's Constraint ("Do not replace focused unit tests with only a large
  end-to-end test") applied in the opposite direction.
- Frame "collected and run" (not "passing") as this cycle's success
  criterion in the module's own docstring, so a future reader does not
  mistake expected pending-dependency failures for a broken test file (per
  source Plan's Risks).
- Runtime-probe the `unshare --net` capability inside the `REQ-006` test
  itself (e.g. via a guarded subprocess call) rather than a static
  environment-variable flag — keeps the fallback decision self-contained and
  accurate to the actual execution environment.

## Alternatives considered
- Adding these assertions directly into `tests/agent/`, `tests/mcp_servers/`,
  or `tests/eventbus/`'s existing unit-test files — rejected: would blur the
  unit vs. process/integration layering boundary this Plan and the source
  Issue's Constraint both establish.
- Skipping `REQ-006` entirely absent guaranteed `unshare` availability —
  rejected: the source Plan requires a documented, tested manual-fallback
  path instead, so coverage is not silently reduced without visibility.

## Implementation
### Target file
`tests/integration/test_production_security_regression.py`

### Procedure
1. Create the file with a module docstring explaining: this suite exercises
   process-level Production-only/authentication/loopback behavior introduced
   by `localremoval`/`loopbackonly`/`mcpauth`; tests are expected to fail or
   skip until those three Plans land; "collected and run" is this cycle's
   success criterion, not "passing" (REQ-001 through REQ-006).
2. Add startup-policy tests (REQ-001): spawn/import the actual Agent startup
   path against a copied, disposable `config/agent.toml`, asserting a
   Local-mode or retired-key configuration fails startup once
   `localremoval` lands.
3. Add strict-configuration tests (REQ-002): exercise tool-tier, ownership,
   routing, workflow-definition, and database-schema validation through the
   real startup path (not a synthetic config object).
4. Add a socket-inspection test (REQ-003): spawn an MCP server subprocess,
   call `socket.getsockname()` against its actual bound address, asserting
   `127.0.0.1` is accepted and a private-LAN/wildcard bind attempt is
   rejected once `loopbackonly` lands.
5. Add MCP startup-failure and tool-visibility tests (REQ-004): a
   required-component startup failure aborts Agent startup; an
   optional-component failure disables only that tool and excludes it from
   LLM-visible tool definitions.
6. Add MCP authentication tests (REQ-005): missing/invalid/valid Bearer
   token against a spawned MCP server subprocess, plus a log-capture
   assertion confirming the token is redacted in actual emitted log output.
7. Add the external-unreachability test (REQ-006): attempt `unshare --net`
   (or equivalent) isolation at runtime; if available, confirm the loopback
   service is unreachable from the isolated namespace; if unavailable, fall
   back to the documented manual-equivalent (bind a probe socket to a
   non-loopback interface, confirm connection refusal), logging clearly
   which path was taken (per `UNK-01`).
8. Do not add a deployment-manifest lint test (REQ-007) — confirmed not
   applicable (no Docker/systemd/nginx/Kubernetes manifest exists in this
   repository, re-confirmed via `plans/done/20260903-092746_plan.md`'s own
   Step 3 inspection).

### Method
New file created via `Write`; follows `tests/integration/test_agent_mcp_integration.py`'s
and `tests/integration/test_mcp_transport_crash.py`'s existing subprocess-spawning
and fixture conventions (re-confirmed present in both files).

### Details
- Test function naming: one test function (or a small parametrized group) per
  Requirement — `test_production_only_rejects_local_mode` (REQ-001),
  `test_strict_configuration_validation_via_real_startup` (REQ-002),
  `test_mcp_server_socket_is_loopback_only` (REQ-003),
  `test_required_mcp_failure_aborts_startup` /
  `test_optional_mcp_failure_disables_only_that_tool` (REQ-004),
  `test_mcp_auth_missing_invalid_valid_token` /
  `test_mcp_auth_token_redacted_in_logs` (REQ-005),
  `test_external_unreachability_or_manual_fallback` (REQ-006).
- Each test that depends on `localremoval`/`loopbackonly`/`mcpauth` behavior
  not yet landed should use a clear `pytest.mark.xfail(reason=...)` or an
  explicit assertion-failure message naming the pending dependency Plan —
  not a silent `pytest.skip()` — so the pending-dependency state remains
  visible in test output (supports the source Plan's Risks mitigation).
- `REQ-006`'s runtime capability probe must emit a log line stating which
  path was taken (namespace isolation vs. manual fallback) — required by
  `UNK-01`'s resolution path.

## Compatibility considerations
N/A: new test file, no existing code or test is modified or removed.

## Security considerations
This suite tests security-relevant behavior (authentication, network
isolation) but does not itself introduce any security-sensitive code — it
only asserts against behavior `localremoval`/`loopbackonly`/`mcpauth`
introduce. Token values used in the authentication tests (REQ-005) must be
test-only placeholder values, never real credentials.

## Rollback considerations
New file under version control; revert via `git revert` if needed. No other
file depends on this new file's existence.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/integration/test_production_security_regression.py` | Integration/process | `uv run pytest tests/integration/test_production_security_regression.py -v` | Tests are collected and run; expected to fail/xfail until `localremoval`/`loopbackonly`/`mcpauth` land, then pass once they do |
| Cross-check vs. dependency Plans' unit tests | Manual | Manual review: confirm no assertion here duplicates a unit-level assertion already specified in `localremoval`/`loopbackonly`/`mcpauth`'s own test Requirements | No duplicated test coverage across layers |

## Completion criteria
- The file exists, is collected by `pytest`, and contains one test (or
  parametrized group) per `REQ-001` through `REQ-006`.
- Tests currently fail/xfail (not pass) since their dependency Plans are
  unimplemented — this is the expected, correct state for this cycle.
- `REQ-006`'s test logs which isolation path (namespace vs. manual fallback)
  it took.
- No assertion duplicates a unit-level test already specified in
  `localremoval`/`loopbackonly`/`mcpauth`'s own Plans.

## Out of scope
`REQ-007` (deployment-manifest lint — confirmed not applicable, no file);
`REQ-008` (documentation update — owned by this Plan's other target row);
`localremoval`'s/`loopbackonly`'s/`mcpauth`'s own runtime implementations and
unit tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the new test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests are expected to fail/xfail, not pass, until dependency Plans land |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation update is owned by this Plan's other target row (seq 02) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/done/20260902-143337_prodregression_add_production_auth_network_isolation_regression_coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-093012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-171258
- **Related target files**: tests/integration/test_production_security_regression.py
