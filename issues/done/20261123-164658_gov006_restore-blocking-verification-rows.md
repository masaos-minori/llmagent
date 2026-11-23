# Restore the Blocking verification rows of seven ADR invariants with new automated tests

## Priority
Low

## Summary
Eight ADR invariants have a verification row set to Non-Blocking because no automated test verifies them (ledger entries AAL-001 and AAL-031 to AAL-036 in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 5). The maintainer decided to resolve them by adding the missing tests, restoring each row to Blocking, and removing the entry as a reverted change. Five rows can be restored now; ADR-001 INV-02 needs a scope decision (a proposal is given), and ADR-002 INV-04 is blocked on the wording of INV-04 (AAL-030).

## Background
Decision of the maintainer (2026-11-23, in the session that reviewed `issues/20261123-104604_gov005_adr-approval-ledger.md`): the Non-Blocking rows are resolved by adding tests (option B of that issue's review), not by approving the relaxation. Per the ledger rules, an entry is removed once the pending change is reverted; restoring the row to Blocking with a cited, passing test is that revert, and no approver, date, or approval sentence is written.

Findings of a read-only investigation (2026-11-23; every path below is to be re-verified at planning):
- **AAL-035, ADR-003 INV-07** (Circuit-Open keeps LLM visibility): no test covers it. `tests/shared/test_runtime_tool_registry.py:333` covers the startup `unavailable_servers` argument, not a runtime Circuit-Open; `RuntimeToolRegistry.llm_tool_definitions` filters only on `enabled_for_llm`. Small test in `tests/shared/test_tool_executor_routing.py` (new class using `McpServerHealthRegistry(failure_threshold=1)`): the tool list and `enabled_for_llm` do not change after `record_failure` or after the HALF_OPEN transition, the tool still routes, and execution returns the unavailable error without a transport call.
- **AAL-034, ADR-003 INV-04** (no fallback to the static `ToolRegistry`): `tests/shared/test_route_resolver.py::TestRoutingSourceIsolation::test_resolve_rejects_ToolRegistry_fallback_when_runtime_registry_available` is weak because it resolves a name absent from the static registry anyway. Add a test with a name that is in the static registry but not in the runtime registry (expect `ToolRoutingError` kind `unknown_tool`, and `not_ready` for an unwired resolver), and an AST `repo_scan` test that `route_resolver.py`, `runtime_tool_registry.py`, `tool_executor.py`, and `tool_transport_invoker.py` do not import `shared.tool_registry`.
- **AAL-031, ADR-002 INV-03** (an MCP server starts without `agent.toml`): `tests/mcp_servers/test_config_isolation_import.py::test_a_server_module_executes_once_under_python_m` runs the real `run_http()` in a subprocess but points `LLMAGENT_CONFIG_DIR` at a full copy of `config/` that includes `agent.toml`, so a server reading `agent.toml` directly would still pass. Add a parametrized test over the same ten servers with a config directory holding only the server's own file, asserting exit code 0, that `uvicorn.Config` was reached, and that only the own config file was loaded.
- **AAL-033, ADR-003 INV-03** (Routing, approval, and auditing use the same Safety Tier): only per-consumer tests exist (`tests/agent/test_tool_approval_risk.py`, `tests/agent/test_tool_policy_comprehensive.py`, `tests/agent/test_tool_audit.py`). Add `tests/agent/test_safety_tier_single_source.py`: one tool per tier in a `RuntimeToolRegistry`, driven through `run_approval_checks`, asserting that the registry tier, the logged approval risk, the plan-mode block, and the routed server key agree, and that flipping the tiers in the registry flips all consumers together.
- **AAL-036, ADR-012 INV-04** (Git MCP validation does not use Agent-side approval state): `tests/mcp_servers/git/test_git_security_compliance.py::TestLiveCallToolAuthorization` mocks the repository state and the pipeline; `tests/mcp_servers/git/test_repository_state.py` uses a real repository but no approval input; `.importlinter` contract `mcp_servers-no-agent` runs only through `lint-imports`. Add `tests/mcp_servers/git/test_git_approval_independence.py`: a real repository, checkout of a protected branch denied with and without forged approval-shaped headers, a non-protected checkout allowed without approval input, and an AST `repo_scan` that `scripts/mcp_servers/git/` has no `agent` import and no `approv`, `grant`, or `plan_mode` identifier.
- **AAL-001, ADR-001 INV-02** (no external state-change path bypasses the Workflow Engine): only partial tests exist (`tests/agent/test_orchestrator.py::TestWorkflowLoadFailureIsFatal`, `tests/agent/workflow/test_adapter_guards.py`). The code path is `repl_input_loop.py` `handle_turn`, then the orchestrator, then `WorkflowEngineAdapter.execute_turn`, then `engine.run`, then `handle_llm_turn`, `LLMTurnRunner`, `execute_all_tool_calls`, and `ToolExecutor.execute`. Proposal: `tests/agent/workflow/test_no_workflow_bypass.py` with an AST `repo_scan` over explicit call-site allowlists (`handle_llm_turn`, `LLMTurnRunner(`, `execute_all_tool_calls`, `.execute(` on the executor and gateway, `.handle_turn(`) plus a behavioral test that `handle_llm_turn` runs only inside `engine.run`. The scope of "external state-change path" is a maintainer decision: the proposal covers the tool-execution and LLM-turn chain and records slash commands and MCP lifecycle start and stop as an explicit allowlist.
- **AAL-032, ADR-002 INV-04** (the Agent starts without MCP-specific secrets): a test of the current wording would fail on shipped behavior. `config/agent.toml` gives the Agent each server's `auth_token` and an optional `control_auth_token` (`scripts/shared/mcp_config.py`), and an enabled server with an empty token is fatal at startup (`tests/agent/test_startup_validation.py::TestMcpAuthDisabledServers`, `tests/shared/test_mcp_config_validation.py::test_auth_token_empty_string_raises`). The pending amendment AAL-030 words INV-04 as "the only MCP-specific value the Agent is given is each enabled server's connection token", which omits `control_auth_token`. The row can be restored only after the maintainer fixes the INV-04 wording (list both tokens, or drop the control token from `agent.toml`); then `tests/agent/test_mcp_secret_boundary.py` (the Agent config's per-server keys are exactly `auth_token` and `control_auth_token`, each a single `${ENV:NAME}` reference) plus the two existing tests can be cited.
- The ADR text to restore: in each ADR's `## Verification` table the row's `Blocking` value becomes `Yes` and its `Implementation` cell cites the new test; the pending `Current Decision Approval (pending)` bullet and the ledger entry are removed (a revert); other statements that depend on the relaxation (ADR-002 checklist lines about INV-03 and INV-04, ADR-003's manual-review note for INV-03, ADR-012's verification note, and the `adr_01_index.md` matrix row of ADR-012 INV-04 and its citation count) are updated with it.
- Test conventions found: subprocess tests are normally `@pytest.mark.integration`, but `tests/mcp_servers/test_config_isolation_import.py` spawns subprocesses without the marker; whole-repository AST scans take `@pytest.mark.repo_scan`; no shared AST scan helper exists today.

## Problem
Seven invariants are not verified by a Blocking gate while their ADR text is pending approval, and each unverified invariant can regress silently.

## Reason for Change
The maintainer chose to close the Non-Blocking entries through tests instead of approvals; the ledger entries stay open until the rows are restored.

## Implementation Intent
Add one focused automated test per invariant, in the order of smallest and most independent first, then restore each ADR row to Blocking citing the test and remove its pending bullet and ledger entry as a revert. Keep production code unchanged; if a test cannot be written without a production change, stop and report which change is needed instead of weakening the invariant.

## Target Files or Areas
- New or extended tests: `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_route_resolver.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/agent/test_safety_tier_single_source.py` (new), `tests/mcp_servers/git/test_git_approval_independence.py` (new), `tests/agent/workflow/test_no_workflow_bypass.py` (new), and later `tests/agent/test_mcp_secret_boundary.py` (new)
- ADRs: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_01_index.md` (Invariant Verification Matrix and citation count), `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 5 entries)
- Possibly `tests/test_run_cited_adr_tests.py` (the citation-count pin)

## Required Changes
- Add the test for ADR-003 INV-07 (AAL-035), then ADR-003 INV-04 (AAL-034), then ADR-002 INV-03 (AAL-031), then ADR-003 INV-03 (AAL-033), then ADR-012 INV-04 (AAL-036), each as described in Background and re-verified against current source.
- Add the ADR-001 INV-02 test (AAL-001) after the maintainer confirms the scope in Unresolved Questions (or with the proposed scope recorded as an assumption).
- Restore each row to Blocking with the cited test, remove its pending bullet and ledger entry as a revert, and update the dependent statements; keep `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and the citation-count pin passing.
- ADR-002 INV-04 (AAL-032): not in the first batch; plan it only after the maintainer fixes the INV-04 wording (AAL-030) and states whether `control_auth_token` stays in `agent.toml`.

## Constraints
- No approver, date, or approval sentence is written; removing a ledger entry is the revert of the pending Non-Blocking change.
- A test must fail when the invariant is violated; a test that asserts the current state without a failing counterpart does not restore Blocking.
- Production code is unchanged. A required production change is reported, not made here.
- Tests follow the repository conventions found above (markers `integration` and `repo_scan`, existing fixtures); a test that is slow or spawns subprocesses is marked accordingly and still cited by the ADR row only if the cited-test runner executes it (`.github/run_cited_adr_tests.py`).
- ADR text changes are limited to the rows and statements that depend on the relaxation.

## Acceptance Criteria
- [ ] Each of the five rows (AAL-031, 033, 034, 035, 036) has a passing automated test, the ADR row is Blocking and cites it, and its pending bullet and ledger entry are removed.
- [ ] AAL-001 is handled the same way once its scope is confirmed, or stays open with the reason recorded.
- [ ] AAL-032 stays open with its dependency on AAL-030 recorded.
- [ ] `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `.github/run_cited_adr_tests.py`, and the full test suite pass.

## Testing Expectations
- Each new test is run alone and in the full suite; each is mutation-checked once by temporarily breaking the invariant (for example making the router consult the static registry) to confirm it fails, without committing the break.
- `.github/run_cited_adr_tests.py` runs the cited tests; the citation-count pin in `tests/test_run_cited_adr_tests.py` is updated with the matrix.
- ruff and mypy for the new test files.

## Documentation Impact
Yes: the ADR Verification tables, the Invariant Verification Matrix of `adr_01_index.md`, and the governance Part 5 entries; no new documentation files.

## Out of Scope
- Approving any Non-Blocking relaxation; the other ledger entries of gov005; changing any ADR decision beyond restoring the verification rows; production code changes.

## Dependencies
- Related: `issues/20261123-104604_gov005_adr-approval-ledger.md` (the ledger work this issue splits off; its entries AAL-001 and AAL-031 to AAL-036 close here).
- AAL-032 depends on the maintainer's decision on AAL-030 (INV-04 wording and the control token).
- Sibling check (2026-11-23): no other open issue or plan targets these tests or ADR rows; the open plans `plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md` and `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md` do not touch them.

## Unresolved Questions
- `不明`: the scope of "external state-change path" for ADR-001 INV-02 (the proposal is the tool-execution and LLM-turn chain, with slash commands and MCP lifecycle start and stop allowlisted); the maintainer confirms or amends it.
- `不明`: the wording of INV-04 and whether `control_auth_token` stays in `agent.toml` (blocks AAL-032).
- `不明`: how the Part 5 rules want a reverted entry recorded (the rules say removal on revert; confirm no withdrawn-history line is wanted).
- Assumption to confirm at planning: whether the posture gate of each MCP server reads `agent.toml` (it is stubbed in the existing isolation test), which decides whether the AAL-031 test can pass for all ten servers without a production change.

## AI Implementation Instruction
Implement one test per invariant in the order given, verify each by breaking the invariant temporarily, and restore the ADR row only when the test passes. Do not change production code, do not write approval text, and stop and report if an invariant cannot be tested without a decision or a production change (ADR-002 INV-04 is such a case until INV-04 is reworded).

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-164658
- **Related target files**: `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_route_resolver.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/agent/test_safety_tier_single_source.py`, `tests/mcp_servers/git/test_git_approval_independence.py`, `tests/agent/workflow/test_no_workflow_bypass.py`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_01_index.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
