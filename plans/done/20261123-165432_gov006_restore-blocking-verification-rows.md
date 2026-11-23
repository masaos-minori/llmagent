## Goal
- Add one automated test for each of six ADR invariants whose verification row is Non-Blocking only because no test exists (ADR-003 INV-07, INV-04, INV-03; ADR-002 INV-03; ADR-012 INV-04; ADR-001 INV-02), then restore each row to Blocking citing the new test and remove its pending ledger entry as a revert, without writing any approval text.

## Priority
Low

## Scope
- **In-Scope**: tests for ADR-003 INV-07 (AAL-035), ADR-003 INV-04 (AAL-034), ADR-002 INV-03 (AAL-031), ADR-003 INV-03 (AAL-033), ADR-012 INV-04 (AAL-036), and ADR-001 INV-02 (AAL-001, proposed scope recorded as an assumption); restoring each ADR Verification row to Blocking with the cited test; removing the pending bullets and the ledger entries AAL-001, AAL-031, AAL-033, AAL-034, AAL-035, AAL-036 as a revert; updating the dependent statements (ADR-002 checklist line for INV-03, ADR-003 manual-review note, `adr_01_index.md` matrix rows and pipeline summary, the citation-count pin).
- **Out-of-Scope**: approving any Non-Blocking relaxation; the other gov005 ledger entries; ADR-002 INV-04 (AAL-032), which stays pending until the INV-04 wording (AAL-030) is decided; any production code change under `scripts/` or `config/` (a required production change is reported and stops the step); a test for the scope of ADR-001 INV-02 beyond the proposed one.
- **Dependencies**: related to the gov005 ADR approval ledger issue (its entries AAL-001 and AAL-031 to AAL-036 close here; AAL-032 and the rest stay there); AAL-032 depends on the maintainer's decision on AAL-030. No ordering dependency on another Plan or Issue.

## Background
The ADR Approval Ledger (governance_03 Part 5) holds 37 pending entries, none with a recorded approver or date. Eight of them set a verification row to Non-Blocking because no automated test verifies the invariant. The maintainer decided on 2026-11-23 to resolve these by adding tests instead of approving the relaxation. Removing an entry is allowed when the pending change is reverted; restoring a row to Blocking with a passing cited test is that revert.

## Problem
Seven invariants (and ADR-001 INV-02, which is excluded from the index matrix) are verified by no Blocking gate, so each can regress silently while its ADR text still awaits approval.

## Reason for Change
Each unverified invariant is a standing gap, and the ledger entries stay open until the rows are restored. Tests make the rows Blocking and let the entries close without a maintainer approval.

## Implementation Intent
Add one focused test per invariant, smallest and most independent first, mutation-check each (break the invariant temporarily, confirm the test fails, revert the break), then in one documentation phase restore every row to Blocking citing its test and remove the pending bullets and ledger entries. Production code stays unchanged; if a test cannot be written without a production change, stop and report which change is needed.

## Requirements
- `REQ-001`: Test that tools of a Circuit-Open MCP server stay in `llm_tool_definitions()` and keep `enabled_for_llm` (ADR-003 INV-07, AAL-035).
- `REQ-002`: Test that routing never falls back to the static `ToolRegistry`, with a name present in the static registry but absent from the runtime registry, plus an import scan of the four routing modules (ADR-003 INV-04, AAL-034).
- `REQ-003`: Test that each of the ten MCP servers starts with a config directory holding only its own file and loads only that file (ADR-002 INV-03, AAL-031).
- `REQ-004`: Test that routing, approval, and auditing read the same Safety Tier from one `RuntimeTool`, and that changing the registry tier changes all of them together (ADR-003 INV-03, AAL-033).
- `REQ-005`: Test that Git MCP validation neither assumes nor requires Agent-side approval state: real-repository protected-branch checks give the same result with and without approval-shaped input, and the Git server package has no Agent approval dependency (ADR-012 INV-04, AAL-036).
- `REQ-006`: Test that the tool-execution and LLM-turn chain is reachable only through the Workflow Engine, with the call-site allowlist of the proposed scope (ADR-001 INV-02, AAL-001).
- `REQ-007`: Restore the Verification rows of the six invariants to Blocking citing the new tests; remove the pending bullets and the ledger entries AAL-001, AAL-031, AAL-033, AAL-034, AAL-035, AAL-036; update dependent statements, the index matrix rows and pipeline summary, and the citation-count pin; write no approval text.
- `REQ-008`: Production code and configuration stay unchanged, and every new test is shown to fail when its invariant is broken.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/shared/test_tool_executor_routing.py` | Modify: add a Circuit-Open visibility test class | Add the INV-07 test using `McpServerHealthRegistry(failure_threshold=1)` | REQ-001; AC-001 | File exists (44064 B); imports `McpServerHealthRegistry`, `RuntimeToolRegistry`, `ToolExecutor`; `llm_tool_definitions` at `scripts/shared/runtime_tool_registry.py:152` filters only on `enabled_for_llm` (checked in Step 3) | itself | Verified |
| `tests/shared/test_route_resolver.py` | Modify: add a static-registry fallback test and an import scan | Add the INV-04 tests; the existing `TestRoutingSourceIsolation` resolves a name absent from the static registry anyway | REQ-002; AC-002 | File exists (12940 B); `TestRoutingSourceIsolation` at line 183; no `tool_registry` import in `route_resolver.py`, `tool_executor.py`, `tool_transport_invoker.py` or `runtime_tool_registry.py` (rg, checked in Step 3) | itself | Verified |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify: add a parametrized test with a config directory holding only the own file | Add the INV-03 test over `_ONCE_SERVERS` beside `test_a_server_module_executes_once_under_python_m` | REQ-003; AC-003 | File exists (11451 B); `_ONCE_SERVERS` lists the ten servers; the existing test runs `run_http()` with the stubbed `uvicorn.Config` and `isolated_subprocess_env` (`tests/conftest.py:440`) (checked in Step 3) | itself | Verified |
| `tests/agent/test_safety_tier_single_source.py` | Create: new test module | New file for the INV-03 single-source test; one tool per tier driven through `run_approval_checks` | REQ-004; AC-004 | New file; containing directory `tests/agent/` exists; `run_approval_checks` at `scripts/agent/tool_approval.py:336` (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/git/test_git_approval_independence.py` | Create: new test module | New file for the ADR-012 INV-04 tests on a real repository and an AST scan | REQ-005; AC-005 | New file; containing directory `tests/mcp_servers/git/` exists; server package `scripts/mcp_servers/git/` has `git_security.py`, `repository_state.py`, `write_protection_pipeline.py` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_no_workflow_bypass.py` | Create: new test module | New file for the ADR-001 INV-02 AST scan with call-site allowlists and a behavioral test | REQ-006; AC-006 | New file; containing directory `tests/agent/workflow/` exists; chain symbols `handle_llm_turn` (`scripts/agent/llm_turn_executor.py:71`), `execute_all_tool_calls` (`scripts/agent/tool_runner.py:559`), `WorkflowEngineAdapter.execute_turn` (`scripts/agent/workflow_engine_adapter.py:115`), `Orchestrator.handle_turn` (`scripts/agent/orchestrator.py:163`) (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify: rows to Blocking, pending bullets removed, manual-review note updated | Restore INV-03, INV-04, INV-07 rows (lines 254, 256, 259), remove the bullets at lines 338-340, update the note at line 280 | REQ-007; AC-007 | Rows and bullets read in Step 3: `Blocking` is `No` and the evidence `Not verified` at lines 254, 256, 259 (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify: INV-03 row to Blocking, pending bullet removed, checklist lines updated | Restore the INV-03 row (line 231), remove the bullet at line 298, update checklist lines 341-342 to name only INV-04 | REQ-007; AC-007 | Row at line 231 and bullet at line 298 read in Step 3; INV-04 bullet at line 299 stays for AAL-032 (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify: INV-04 row to Blocking, pending bullet removed | Restore the INV-04 row (line 170) and remove the bullet at line 204 | REQ-007; AC-007 | Row at line 170 and bullet at line 204 read in Step 3 (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify: INV-02 row to Blocking, pending bullet removed | Restore the INV-02 row (line 185) and remove the bullet at line 263 | REQ-007; AC-007 | Row at line 185 and bullet at line 263 read in Step 3 (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify: matrix rows, "stay out of this matrix" sentence, pipeline summary | Add matrix rows for ADR-001 INV-02, ADR-002 INV-03, ADR-003 INV-04 and INV-07; make ADR-003 INV-03 and ADR-012 INV-04 Confirmed and Blocking; update line 178 and the summary at lines 231-232 | REQ-007; AC-007 | Rows at lines 189 (Partial) and 211 (Non-Blocking); line 178 names ADR-001 INV-02 as excluded; summary rows at 231-232 read in Step 3 (checked in Step 3) | `tests/test_run_cited_adr_tests.py` | Verified |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify: remove six ledger entries | Remove AAL-001 (line 366) and AAL-031, AAL-033 to AAL-036 (lines 627-680) as a revert | REQ-007; AC-007 | Entries read in Step 3; only AAL-032 in that range stays (checked in Step 3) | `tests/tools/test_check_adr_structure.py` | Verified |
| `tests/test_run_cited_adr_tests.py` | Modify: update the citation-count pin | The pinned unique citation count (`== 70` at line 148) changes with the new matrix rows | REQ-007; AC-007 | `test_matrix_has_expected_unique_citation_count` at line 134 pins 70 (checked in Step 3) | itself | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/runtime_tool_registry.py` | `llm_tool_definitions` and `enabled_for_llm` behavior | REQ-001, REQ-004 |
| `scripts/shared/mcp_health.py` | `McpServerHealthRegistry` states and `record_failure` | REQ-001 |
| `scripts/shared/route_resolver.py` | Routing source and failure kinds | REQ-002 |
| `scripts/shared/tool_executor.py` | Executor routing and health gate | REQ-001, REQ-002 |
| `scripts/shared/tool_transport_invoker.py` | Fourth routing module in the import scan | REQ-002 |
| `scripts/agent/tool_approval.py` | `run_approval_checks` and the logged approval risk | REQ-004 |
| `scripts/agent/orchestrator.py` | Entry of the turn chain | REQ-006 |
| `scripts/agent/workflow_engine_adapter.py` | `execute_turn` and the engine call | REQ-006 |
| `scripts/agent/llm_turn_executor.py` | `handle_llm_turn` | REQ-006 |
| `scripts/agent/tool_runner.py` | `execute_all_tool_calls` | REQ-006 |
| `scripts/mcp_servers/git/repository_state.py` | Protected-branch state for the ADR-012 test | REQ-005 |
| `scripts/mcp_servers/git/write_protection_pipeline.py` | Git validation pipeline | REQ-005 |
| `tests/conftest.py` | `isolated_subprocess_env` fixture | REQ-003 |
| `.github/run_cited_adr_tests.py` | How cited node ids are extracted and run | REQ-007 |
| `tools/check_adr_structure.py` | Pending-bullet and ledger-entry consistency rules | REQ-007 |
| `tools/check_adr_invariant_matrix.py` | Matrix and body agreement rules | REQ-007 |
| `issues/20261123-104604_gov005_adr-approval-ledger.md` | Ledger scope that this Plan splits off | REQ-007 |

## Acceptance Criteria
- `AC-001` (REQ-001): the INV-07 test passes on current code and fails when the tool list or `enabled_for_llm` is changed by a Circuit-Open transition.
- `AC-002` (REQ-002): the INV-04 tests pass and fail when the resolver consults the static `ToolRegistry` or a routing module imports it.
- `AC-003` (REQ-003): the INV-03 test passes for all ten servers with only the own config file present, and fails when a server reads another config file.
- `AC-004` (REQ-004): the single-source test passes and fails when any one consumer reads a tier other than the registry's.
- `AC-005` (REQ-005): the ADR-012 test passes and fails when the Git package imports Agent approval state or its result depends on approval-shaped input.
- `AC-006` (REQ-006): the bypass test passes and fails when a new call site reaches the chain outside the Workflow Engine allowlist.
- `AC-007` (REQ-007): each restored row is `Blocking` and cites its test, the six pending bullets and ledger entries are gone, no approver, date, or approval sentence was written, and `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `.github/run_cited_adr_tests.py`, and the full suite pass.
- `AC-008` (REQ-008): `git diff --stat` shows no change under `scripts/` or `config/`, and each new test's mutation check is recorded in its procedure.

## Tests
- `REQ-001` to `REQ-006`: the new tests themselves, each run alone and in the full suite; `integration` and `repo_scan` markers per the repository conventions.
- `REQ-007`: `tests/test_run_cited_adr_tests.py` (count pin), `tests/tools/test_check_adr_structure.py`, `tests/tools/test_check_adr_invariant_matrix.py`, and the checker tools themselves.
- `REQ-008`: one temporary break per test (not committed), then the test fails and the break is reverted.

## Documentation Impact
Yes (REQ-007): the four ADR Verification tables, the Invariant Verification Matrix of the ADR index, and the governance Part 5 ledger; located via `docs/00_index.md` (ADR and governance documents). No new documentation files.

## Assumptions
- ADR-001 INV-02 scope: the tool-execution and LLM-turn chain (`handle_turn`, adapter, engine, `handle_llm_turn`, `LLMTurnRunner`, `execute_all_tool_calls`, `ToolExecutor.execute`) is "the external state-change path"; slash commands and MCP lifecycle start and stop are an explicit allowlist. The maintainer may amend this (UNK-01).
- Removing a ledger entry on revert needs no withdrawn-history line, as the Part 5 rules state removal (UNK-03 records the confirmation).
- The other 30 ledger entries and `tests/tools/test_check_adr_structure.py` fixtures are unaffected; the fixture ids there are test data, not pins on the live ledger (checked in Step 3).
- Overlap with the mcpdl005 retention-capacity-monitoring Plan on `tests/mcp_servers/test_config_isolation_import.py` is compatible (Step 8b): that Plan edits the per-file `[dedup]` key-set assertions, while this Plan appends a new parametrized test; the two do not touch the same test function, and either order works.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Scope of "external state-change path" for ADR-001 INV-02 | Maintainer statement | The Plan implements the proposed scope; the maintainer confirms or amends it, and the allowlist in the test changes accordingly | False |
| UNK-02 | Whether each MCP server's posture gate or startup reads a config file other than its own, which decides whether the AAL-031 test passes without a production change | Run of the new test against all ten servers | Implementation: if a server fails, stop and report the production change needed; do not weaken the invariant | False |
| UNK-03 | Whether the Part 5 rules want a withdrawn-history line when an entry is removed on revert | Maintainer statement | Follow the Part 5 text (remove the entry); confirm in review | False |
| UNK-04 | ADR-002 INV-04 (AAL-032): the INV-04 wording (AAL-030) and whether `control_auth_token` stays in `agent.toml` | Maintainer decision | Out of this Plan; tracked by the gov005 issue; a later `tests/agent/test_mcp_secret_boundary.py` plan follows the decision | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/shared/test_tool_executor_routing.py` | Modify | Low | 6 | N/A: git-fame not run | None: tests are not deployed |
| `tests/shared/test_route_resolver.py` | Modify | Low | 3 | N/A: git-fame not run | None: tests are not deployed |
| `tests/mcp_servers/test_config_isolation_import.py` | Modify | Low | 4 | N/A: git-fame not run | None: tests are not deployed |
| `tests/agent/test_safety_tier_single_source.py` | Create | Low | 0 | N/A: new file | None: tests are not deployed |
| `tests/mcp_servers/git/test_git_approval_independence.py` | Create | Low | 0 | N/A: new file | None: tests are not deployed |
| `tests/agent/workflow/test_no_workflow_bypass.py` | Create | Low | 0 | N/A: new file | None: tests are not deployed |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Modify | Medium | 11 | N/A: git-fame not run | None: documentation |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Medium | 9 | N/A: git-fame not run | None: documentation |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Modify | Medium | 7 | N/A: git-fame not run | None: documentation |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium | 10 | N/A: git-fame not run | None: documentation |
| `docs/10_adr/adr_01_index.md` | Modify | Medium | 23 | N/A: git-fame not run | None: documentation |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Modify | Medium | 22 | N/A: git-fame not run | None: documentation |
| `tests/test_run_cited_adr_tests.py` | Modify | Low | 8 | N/A: git-fame not run | None: tests are not deployed |

## Design
- Path B (more than 3 target files). Architecture, dependency, and historical analysis ran once (checked in Step 3): the four routing modules import nothing from `shared.tool_registry`; the Git server package lives under `scripts/mcp_servers/git/`; churn of the ADR index and ledger files is high (22 and 23 commits in 30 days), so the documentation phase is one commit and rebases onto the latest `master` first. Operational dependency inspection is N/A: no process or database is touched.
- No production code, configuration, or deployment change, so there is no deploy step.
- Test designs: INV-07 uses `McpServerHealthRegistry(failure_threshold=1)`, asserts tool list and `enabled_for_llm` unchanged after `record_failure` and after the HALF_OPEN transition, that the tool still routes, and that execution returns the unavailable error without a transport call. INV-04 adds a name present in the static registry and absent from the runtime registry (expect `ToolRoutingError` kind `unknown_tool`, `not_ready` for an unwired resolver) and an AST import scan of the four modules, marked `repo_scan`. ADR-002 INV-03 parametrizes over `_ONCE_SERVERS` with a config directory holding only the server's own file. ADR-003 INV-03 registers one tool per tier and asserts that routing, the logged approval risk, the plan-mode block, and the routed server key agree, then flips the registry tiers and asserts all consumers flip. ADR-012 INV-04 runs a protected-branch checkout on a real repository with and without approval-shaped input, and scans `scripts/mcp_servers/git/` for an `agent` import and for `approv`, `grant`, `plan_mode` identifiers. ADR-001 INV-02 scans call sites of the chain symbols against explicit allowlists and checks that `handle_llm_turn` runs only inside `engine.run`.
- Consumer scan (`tools/scan_change_consumers.py`) is not applicable: no schema, public API, or shared constant changes.
- Predictable fallout check: module size gate not applicable (no `scripts/` or `tools/` file gains code); pinned counts: `tests/test_run_cited_adr_tests.py` pins the matrix citation count and is a target row; tool inventory: no tool added; generated blocks: the ADR index generated sections (`generate_adr_authority.py --check`) do not cover the matrix rows, and the check runs in Phase 7 to confirm; `tests/tools/test_check_adr_structure.py` ledger ids are fixtures, not affected.
- Validation quality baseline: `N/A: no Python target under scripts/ or tools/` (radon, vulture, bandit not run); diff-cover is not needed because the diff has no `scripts/` change.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: ADR-003 INV-07 test**
   - [x] Add the Circuit-Open visibility test class and mutation-check it (REQ-001, REQ-008; `tests/shared/test_tool_executor_routing.py`)
2. **Phase 2: ADR-003 INV-04 tests**
   - [x] Add the static-registry fallback test and the import scan, and mutation-check both (REQ-002, REQ-008; `tests/shared/test_route_resolver.py`)
3. **Phase 3: ADR-002 INV-03 test**
   - [x] Add the only-own-config parametrized test and mutation-check it; stop and report if a server needs a production change (REQ-003, REQ-008; `tests/mcp_servers/test_config_isolation_import.py`)
4. **Phase 4: ADR-003 INV-03 test**
   - [x] Create the single-source Safety Tier test and mutation-check it (REQ-004, REQ-008; `tests/agent/test_safety_tier_single_source.py`)
5. **Phase 5: ADR-012 INV-04 test**
   - [x] Create the Git approval-independence test and mutation-check it (REQ-005, REQ-008; `tests/mcp_servers/git/test_git_approval_independence.py`)
6. **Phase 6: ADR-001 INV-02 test**
   - [x] Create the no-bypass test with the proposed scope and mutation-check it (REQ-006, REQ-008; `tests/agent/workflow/test_no_workflow_bypass.py`)
7. **Phase 7: Restore the rows and close the ledger entries**
   - [x] Restore the Verification rows to Blocking citing the new tests, remove the pending bullets, update dependent statements (REQ-007; `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`)
   - [x] Add and update the matrix rows and pipeline summary in `docs/10_adr/adr_01_index.md`, remove the six ledger entries in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, and update the pin in `tests/test_run_cited_adr_tests.py` (REQ-007)
   - [x] Run `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `.github/run_cited_adr_tests.py`, `generate_adr_authority.py --check`, and the full suite (REQ-007, REQ-008)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_tool_executor_routing.py` | Unit | `uv run pytest tests/shared/test_tool_executor_routing.py -q` | New class passes; fails under the temporary break |
| `tests/shared/test_route_resolver.py` | Unit, repo_scan | `uv run pytest tests/shared/test_route_resolver.py -q` | New tests pass; fail under the temporary break |
| `tests/mcp_servers/test_config_isolation_import.py` | Integration (subprocess) | `uv run pytest tests/mcp_servers/test_config_isolation_import.py -q` | Ten parametrized cases pass; fail when a server reads another config |
| `tests/agent/test_safety_tier_single_source.py` | Integration | `uv run pytest tests/agent/test_safety_tier_single_source.py -q` | Passes; fails when one consumer reads another tier |
| `tests/mcp_servers/git/test_git_approval_independence.py` | Integration, repo_scan | `uv run pytest tests/mcp_servers/git/test_git_approval_independence.py -q` | Passes; fails on an Agent approval dependency |
| `tests/agent/workflow/test_no_workflow_bypass.py` | Regression, repo_scan | `uv run pytest tests/agent/workflow/test_no_workflow_bypass.py -q` | Passes; fails on a call site outside the allowlist |
| ADR rows, index, ledger, pin | Static and unit | `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py`; `uv run python .github/run_cited_adr_tests.py`; `uv run pytest tests/test_run_cited_adr_tests.py tests/tools -q` | No findings; cited nodes pass; pin matches |
| Whole change | Full suite | `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` on the new tests, then `uv run pytest -q` | All pass; `tests/db/test_schema_validation_per_database.py` mcp_dedup failures from the concurrent mcpdl004 work are recorded if they persist |

## Risks
- **Risk**: A server fails the only-own-config test because its startup reads another file (UNK-02) → **Mitigation**: stop at Phase 3, report the production change needed, and leave AAL-031 open rather than weakening the invariant.
- **Risk**: The ADR-001 INV-02 scope (UNK-01) is narrower or wider than the maintainer intends → **Mitigation**: the allowlist is data in the test, the scope is recorded as an assumption, and the maintainer can amend it without changing the structure.
- **Risk**: A scan-based test passes vacuously (an allowlist or pattern that matches nothing) → **Mitigation**: each scan test asserts that its pattern finds at least one expected site, and each test is mutation-checked.
- **Risk**: The ADR index and ledger change concurrently in other sessions (22 and 23 commits in 30 days) → **Mitigation**: Phase 7 is one commit, rebased onto the latest `master` before the checks run.
- **Risk**: The citation-count pin and matrix rows drift apart → **Mitigation**: Phase 7 runs the pin test, the matrix checker, and the cited-test runner together.
- **Risk**: A restored row is read as an approval → **Mitigation**: no approver, date, or approval sentence is written; the entries are removed as a revert, and AC-007 checks it.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | ADR-003 INV-07 test in `tests/shared/test_tool_executor_routing.py` | Completed | — | 20261123-190750 |  |
| 2 | ADR-003 INV-04 tests in `tests/shared/test_route_resolver.py` | Completed | — | 20261123-190750 |  |
| 3 | ADR-002 INV-03 test in `tests/mcp_servers/test_config_isolation_import.py` | Completed | — | 20261123-190750 |  |
| 4 | ADR-003 INV-03 test in `tests/agent/test_safety_tier_single_source.py` | Completed | — | 20261123-190750 |  |
| 5 | ADR-012 INV-04 test in `tests/mcp_servers/git/test_git_approval_independence.py` | Completed | — | 20261123-190750 |  |
| 6 | ADR-001 INV-02 test in `tests/agent/workflow/test_no_workflow_bypass.py` | Completed | — | 20261123-190750 |  |
| 7 | Restore rows and close ledger entries in the four ADRs, `docs/10_adr/adr_01_index.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `tests/test_run_cited_adr_tests.py` | Completed | — | 20261123-190750 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261123-165833_01_tests_shared_test_tool_executor_routing.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261123-165833_02_tests_shared_test_route_resolver.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261123-165833_03_tests_mcp_servers_test_config_isolation_import.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261123-165833_04_tests_agent_test_safety_tier_single_source.py.md | 4 | Procedure | Completed | — | — |
| implementations/20261123-165833_05_tests_mcp_servers_git_test_git_approval_independence.py.md | 5 | Procedure | Completed | — | — |
| implementations/20261123-165833_06_tests_agent_workflow_test_no_workflow_bypass.py.md | 6 | Procedure | Completed | — | — |
| implementations/20261123-165833_07_docs_10_adr_adr_02_02_003_agent-runtime-tool-registry-routing-authority.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261123-165833_08_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261123-165833_09_docs_10_adr_adr_02_03_012_mcp-git-server-side-write-enforcement.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261123-165833_10_docs_10_adr_adr_02_02_001_agent-workflow-engine-mandatory.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261123-165833_11_docs_10_adr_adr_01_index.md.md | 7 | Procedure | Completed | — | — |
| implementations/20261123-165833_12_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md | 7 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261123-164658_gov006_restore-blocking-verification-rows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261123-165432
- **Related target files**: `tests/shared/test_tool_executor_routing.py`, `tests/shared/test_route_resolver.py`, `tests/mcp_servers/test_config_isolation_import.py`, `tests/agent/test_safety_tier_single_source.py`, `tests/mcp_servers/git/test_git_approval_independence.py`, `tests/agent/workflow/test_no_workflow_bypass.py`, `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/10_adr/adr_01_index.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `tests/test_run_cited_adr_tests.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Background, AAL-035 finding | `tests/shared/test_tool_executor_routing.py` | Phase 1 | AC-001 | new Circuit-Open class | Confirmed by repository evidence |
| REQ-002 | Background, AAL-034 finding | `tests/shared/test_route_resolver.py` | Phase 2 | AC-002 | new fallback and import-scan tests | Confirmed by repository evidence |
| REQ-003 | Background, AAL-031 finding | `tests/mcp_servers/test_config_isolation_import.py` | Phase 3 | AC-003 | parametrized only-own-config test | Confirmed by repository evidence |
| REQ-004 | Background, AAL-033 finding | `tests/agent/test_safety_tier_single_source.py` | Phase 4 | AC-004 | single-source test | Confirmed by repository evidence |
| REQ-005 | Background, AAL-036 finding | `tests/mcp_servers/git/test_git_approval_independence.py` | Phase 5 | AC-005 | approval-independence tests | Confirmed by repository evidence |
| REQ-006 | Background, AAL-001 finding; Unresolved Questions | `tests/agent/workflow/test_no_workflow_bypass.py` | Phase 6 | AC-006 | scan and behavioral tests | Derived from confirmed evidence |
| REQ-007 | Background, ADR text to restore; Required Changes | `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Phase 7 | AC-007 | ADR checkers and cited-test runner | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Required Changes | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 7 | AC-007 | ADR checkers and cited-test runner | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Required Changes | `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Phase 7 | AC-007 | ADR checkers and cited-test runner | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Required Changes | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 7 | AC-007 | ADR checkers and cited-test runner | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Required Changes | `docs/10_adr/adr_01_index.md` | Phase 7 | AC-007 | matrix checker and cited-test runner | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Constraints | `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Phase 7 | AC-007 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-007 | Background, ADR text to restore; Testing Expectations | `tests/test_run_cited_adr_tests.py` | Phase 7 | AC-007 | the pin test itself | Confirmed by repository evidence |
| REQ-008 | Constraints; Testing Expectations | `tests/shared/test_tool_executor_routing.py` | Phase 1 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |
| REQ-008 | Constraints; Testing Expectations | `tests/shared/test_route_resolver.py` | Phase 2 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |
| REQ-008 | Constraints; Testing Expectations | `tests/mcp_servers/test_config_isolation_import.py` | Phase 3 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |
| REQ-008 | Constraints; Testing Expectations | `tests/agent/test_safety_tier_single_source.py` | Phase 4 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |
| REQ-008 | Constraints; Testing Expectations | `tests/mcp_servers/git/test_git_approval_independence.py` | Phase 5 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |
| REQ-008 | Constraints; Testing Expectations | `tests/agent/workflow/test_no_workflow_bypass.py` | Phase 6 | AC-008 | mutation check and `git diff --stat` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261123-165833 -->
