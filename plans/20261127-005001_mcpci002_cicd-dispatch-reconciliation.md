# Plan: Reconcile GitHub Actions workflow dispatch and enforce safe retry behavior

## Goal
- Make `trigger_workflow` report a structured dispatch outcome that is reconciled against the run the dispatch created, so a lost response or a crash after acceptance cannot lead to a duplicate workflow run.

## Priority
High

## Scope
- **In-Scope**: the five dispatch states (`accepted`, `confirmed`, `accepted_unconfirmed`, `outcome_unknown`, `reconciliation_required`); the correlation marker and its fallback correlation; bounded run polling; the pre-dispatch run search for the same logical call; the workflow-dispatch reconciler registration; input-value redaction in previews and recovery output; the affected tests; the CI/CD documentation record.
- **Out-of-Scope**: the credential and configuration contract (mcpci001); log retrieval (mcpci003).
- **Dependencies**: mcpci001 (must be implemented first); mcpdd001, mcpai001, mcpai005, mcpdl004, mcpai006 are closed except for their deploy hand-off rows and are recorded as non-blocking Unknowns.
  - **Depends on**: `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` | phase all | this Plan builds its response models on mcpci001's strict request models and polls through the lifespan-owned shared HTTP client that mcpci001 introduces.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 6). A successful dispatch response confirms acceptance, not run creation. The Issue's backlog claim that the implementation reports immediate success without a run id was verified against current source: `trigger_workflow` returns a success string on HTTP 204 and on any other 2xx, with no run id, no correlation marker, and no polling. `trigger_workflow` is in `CICD_WRITE_TOOLS` (`scripts/shared/tool_constants.py:76`; the Issue cites line 75, which is the corrected position).

## Problem
Response loss or a crash after dispatch can lead to a retry that starts a duplicate workflow, and the result gives no run id to reconcile against. The current contract cannot distinguish "accepted", "the run was created", "no run was found", "several runs match", and "the outcome is unknown".

## Reason for Change
External side-effect safety: the dispatch is an irreversible external write whose result is not observable from the response alone. Token, key, and dry-run contracts must be final first, which is why this Plan is sequenced after mcpci001.

## Implementation Intent
Return structured states instead of an immediate success string. Correlate a dispatch with the run it created through a marker in the workflow inputs when the workflow contract allows it, and through a fallback correlation on workflow identifier, ref, actor, and dispatch time otherwise. Poll for the matching run with bounded timeout and interval. Search for an existing run before any repeat dispatch of the same logical call. Keep `trigger_workflow` explicitly non-retryable until reconciliation is proven.

## Requirements
- `REQ-001`: `trigger_workflow` returns a structured dispatch outcome carrying one of the five states; a 2xx response never becomes `confirmed` without a matched run.
- `REQ-002`: A correlation marker is added to the dispatch inputs when the workflow contract allows it; otherwise the fallback correlation is workflow identifier, ref, actor, and dispatch time.
- `REQ-003`: Run lookup polls with a bounded timeout and interval and returns `confirmed` only on a unique match, with run id, URL, status, workflow, and ref; `accepted_unconfirmed` when none is found, `reconciliation_required` for multiple candidates, `outcome_unknown` for response loss or timeout.
- `REQ-004`: Before any repeat dispatch of the same logical call, the existing run is searched; the fail-closed rule when durable deduplication is unavailable is the shared rule already implemented by the dedup gate.
- `REQ-005`: `trigger_workflow` stays explicitly non-retryable; `accepted_unconfirmed` and `outcome_unknown` are never retried automatically.
- `REQ-006`: Workflow input values are redacted from previews, logs, and recovery output; keys and counts only.
- `REQ-007`: The run lookup implements the shared `Reconciler` contract for workflow dispatch and is registered at the control-API registry seam; evidence is recorded as a non-sensitive digest, never a raw payload.
- `REQ-008`: Documentation records the five states, the correlation and polling strategy, and why automatic retry stays disabled, and removes any statement that a dispatch response proves run creation.

## Implementation Target Files
**Freeze status**: Frozen (Step 8's Implementation Target Files Validation passed:
`tools/audit_plan_target_paths.py` 0 findings, `tools/check_plan_target_overlaps.py`
compatible overlap with the open mcpci001 plan, `tools/check_workitem_structure.py` no findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Add the structured dispatch-outcome model for the five states and the matched-run fields (run id, URL, status, workflow, ref); reuse `outcome_unknown` from the shared write-outcome vocabulary | REQ-001, REQ-003, AC-1, AC-2, AC-5 | Request models at lines 88-140 have no response counterpart; the module defines only `CicdConfig` and the domain exceptions, so no dispatch-outcome model exists (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | `trigger_workflow` returns the structured outcome; add the correlation marker to the dispatch inputs, the bounded polling for the matching run, and the run lookup used by the reconciler | REQ-001, REQ-002, REQ-003, REQ-007, AC-1, AC-2, AC-3 | Lines 102-132 return `f"Workflow dispatched: ..."` on 204 and on any other 2xx, with no run id, no correlation marker, and no polling; `get_workflow_runs` at line 134 is the only run read (checked in Step 2) | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Modify | The delegation carries the structured outcome instead of a string | REQ-001, AC-2 | `trigger_workflow` at line 49 delegates directly to the workflow backend and returns its value unchanged (checked in Step 3) | `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | `handle_trigger_workflow` returns the structured outcome; the dry-run preview emits input keys and counts only | REQ-001, REQ-006, AC-4 | Lines 70-75 build the preview string with `with inputs={req.inputs}`, embedding raw input values (checked in Step 3) | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Register the workflow-dispatch reconciler at the control-API registry seam | REQ-004, REQ-007, AC-3 | No production `register_reconciler` call exists; the control plane is wired by `MCPServer` (`scripts/mcp_servers/server.py:226-228`, `433-439`) and `cicd_server.py` performs no registration (checked in Step 3) | `tests/mcp_servers/test_call_state_api.py` | Verified |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Add the response-model shape tests for the five states and the matched-run fields | REQ-001, REQ-003, AC-2 | Lines 35-54 pin the request schema shape only; no response model is pinned (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Replace the immediate-success tests with the structured-state contract and add the preview-redaction tests | REQ-001, REQ-006, AC-4 | Lines 201-208 assert `result == "dispatched"` from the handler, which pins the current string contract (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Modify | The delegation test returns the structured outcome instead of the string `"dispatched"` | REQ-001, AC-2 | Lines 93-104 pin `composite._workflow.trigger_workflow.return_value = "dispatched"` and `assert result == "dispatched"` (checked in Step 3) | this file | Verified |
| `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Modify | Add the response-loss and multiple-match tests first, and replace the pinned immediate-success assertion | REQ-001, REQ-003, AC-2, AC-3 | Lines 57-73 pin the plain-2xx dispatch message (`assert "dispatched" in result.lower()`) (checked in Step 3) | this file | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Record the five states, the correlation and polling strategy, and why automatic retry stays disabled; correct the statement that the dispatch response returns a confirmation | REQ-008 | Line 73 states postcondition verification is not applicable because the server "returns a confirmation rather than a resulting state to compare" (checked in Step 3) | `uv run python tools/check_docs_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure): one row per file; test, configuration, and
documentation files carry their own rows; `Validation Status` is `Verified` for every row.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob pattern, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/dedup_gate.py` | The shared fail-closed rule and the `reconciliation_required` refusal the run lookup must not bypass | REQ-004 |
| `scripts/shared/mcp_call_state_contract.py` | `Reconciler`, `ReconcileEvidence`, and the closed `RECONCILE_OUTCOMES` vocabulary the run lookup implements | REQ-007 |
| `scripts/shared/write_outcome.py` | `outcome_unknown` and `NO_AUTO_RETRY_OUTCOMES`, the vocabulary REQ-005 reuses | REQ-005 |
| `scripts/shared/tool_constants.py` | `CICD_WRITE_TOOLS` at line 76, the set the Issue cites | REQ-005 |
| `scripts/shared/tool_metadata.py` | The declared `retry_policy` authority that keeps `trigger_workflow` non-retryable | REQ-005 |
| `scripts/shared/execution_snapshot.py` | The snapshot a `Reconciler` receives is component-keyed and carries no call arguments, which fixes how the correlation is recovered | REQ-002, REQ-007 |
| `scripts/mcp_servers/control_api.py` | `register_reconciler`, the registration seam the run lookup is attached to | REQ-007 |
| `scripts/mcp_servers/cicd/cicd_service_defs.py` | `_GITHUB_API_BASE` and `build_auth_headers`, reused by the run lookup | REQ-003 |
| `scripts/mcp_servers/audit.py` | The audit record carries no raw arguments, so redaction applies to previews and recovery output only | REQ-006 |
| `tests/shared/test_tool_constants.py` | Lines 156-164 pin `trigger_workflow` as explicitly non-retryable; the Plan must keep them passing | REQ-005 |
| `tests/mcp_servers/test_mcp_dispatch.py` | Lines 1004, 1044, 1158 already cover the `dedup_store_error` fail-closed path the Issue lists as a test case | REQ-004 |
| `tests/mcp_servers/test_write_dangerous_audit.py` | Line 60 pins the cicd write-tool inventory; the handler is a stubbed success string, so the response-contract change does not reach it | REQ-005 |
| `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` | Pins the cicd tool inventory and schema shape; the inventory is unchanged by this Plan | REQ-005 |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Line 224 pins the dispatch-table wiring for `trigger_workflow` | REQ-001 |
| `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` | Pins the non-2xx fail-fast behavior on the jobs path, which the response-contract change must not alter | REQ-001 |
| `config/cicd_mcp_server.toml` | The `[dedup]` table the fail-closed rule reads; gains a row only if the polling bounds become configuration (UNK-02) | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-003): a confirmed dispatch returns the matching run id and URL.
- `AC-2` (REQ-001, REQ-003): missing, delayed, and ambiguous run creation have distinct outcomes, and a 2xx never becomes `confirmed` without a matched run.
- `AC-3` (REQ-004, REQ-005): response-loss recovery searches for the original run before dispatching again, and ambiguous outcomes are never retried automatically.
- `AC-4` (REQ-006): workflow input values do not appear in previews, logs, or recovery messages.
- `AC-5` (REQ-005): `trigger_workflow` remains declared non-retryable, and the existing pinning test still passes.
- `AC-6` (REQ-008): the CI/CD documentation records the five states, the correlation and polling strategy, and why automatic retry stays disabled, and contains no statement that a dispatch response proves run creation.

## Tests
- `REQ-001`/`REQ-003`: confirmed run creation, creation delay, no run, multiple matching runs, response loss, and server crash after acceptance, in `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` and `tests/mcp_servers/cicd/test_cicd_models.py`.
- `REQ-001`: delegation returns the structured outcome, in `tests/mcp_servers/cicd/test_service_github_actions_composite.py`.
- `REQ-004`: the pre-dispatch run search and the dedup-store failure path; the shared fail-closed cases already exist in `tests/mcp_servers/test_mcp_dispatch.py` and are extended only if a cicd-specific case is missing.
- `REQ-006`: preview redaction — keys and counts only, in `tests/mcp_servers/cicd/test_cicd_mcp_service.py`.
- `REQ-005`: `tests/shared/test_tool_constants.py` must keep reporting `trigger_workflow` as non-retryable.
- Full validation sequence per `rules/toolchain.md`: ruff, mypy, bandit, lint-imports, the full test suite, diff-cover, pre-commit.

## Documentation Impact
Yes. Per `docs/00_index.md`'s "Document References by Task" (MCP server spec domain), the
per-server document `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` is the target row: the
five states, the correlation and polling strategy, and why automatic retry stays disabled;
remove any statement that a dispatch response proves run creation (REQ-008).

## Assumptions
- The polling timeout and interval are module constants in `scripts/mcp_servers/cicd/cicd_models.py`, not configuration; if the answer to UNK-02 is "configurable", the Plan is amended with a `config/cicd_mcp_server.toml` row.
- The handler contract stays `-> str` (the structured outcome is JSON-serialized), so `dispatch_tool` and the audit `outcome` mapping are unchanged.
- The five response states are a cicd-scoped contract; the reconciler keeps the shared closed `RECONCILE_OUTCOMES` vocabulary, so no shared vocabulary module is modified.
- Compatible overlap with mcpci001 on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci001 owns the strict request models, canonicalization, and the lifespan-owned client; this Plan owns the response contract and the run lookup.
- The correlation marker is stored as a digest, never as a raw input value, per `ReconcileEvidence`'s non-sensitive-digest rule.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether target workflows can accept a correlation input | No workflow contract in the repository declares an accepted input key; the allowlisted workflow is external | Decide with the workflow owner; the Issue's fallback correlation (workflow identifier, ref, actor, dispatch time) is the default path | False |
| UNK-02 | Polling timeout and interval values | No existing bound in `scripts/mcp_servers/cicd/` or `config/cicd_mcp_server.toml` | Decide at implementation; recorded as constants unless the owner makes them configuration | False |
| UNK-03 | mcpci001 is open: its plan has no `Completed` row | `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` is `Frozen` with all steps `Pending` | Complete mcpci001 before this Plan is implemented; this Plan's response models and polling client depend on it | True |
| UNK-04 | mcpdd001, mcpai001, mcpai005, mcpai006 each have one `Pending` row, all deploy hand-offs | Deploy has not been performed for those plans | Their code work is complete; the shared rule this Plan reuses is already implemented, so only the deploy decision remains | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Medium — imported by six cicd modules and five test modules, and by the `agent-mcp-config-models` import-linter contract | 1 | 2 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | Medium — imported by the composite backend and two test modules | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Modify | Low — the composite facade and one test module | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Modify | Medium — the dispatch handler reached through the dispatch table and the server endpoint | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Medium — the control-API seam and the audit path | 3 | 3 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Low | 0 | 2 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Modify | Low | 0 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Modify | Low | 0 | 1 | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Low | 3 | 2 | not applicable (rsynced) |

## Design
Path B analysis (four dimensions, `workflow-path-b.md`):

- **Architecture**: the import-linter contracts keep `shared` a leaf and forbid `agent` from
  importing `mcp_servers.cicd.cicd_models` (`agent-mcp-config-models`). The response contract
  therefore stays inside `mcp_servers.cicd`; no shared vocabulary module is changed. The run
  lookup is a `Reconciler` implementation registered at the control-API seam, which is already
  attached for cicd-mcp through `MCPServer` (`scripts/mcp_servers/server.py:226-228`).
- **Dependency graphing**: `cicd_models.py` is the hub (six cicd importers, five test importers);
  `cicd_service_github_actions.py` has two importers (the composite facade and its tests);
  `cicd_service_business.py` is reached only through the dispatch table. Blast radius is Medium
  for the hub and the handler, Low for the facade and tests.
- **Historical**: churn over 30 days is 0-3 commits per target file; bus factor 1-3. The dispatch
  path has not changed recently, so the response-contract change is a fresh contract, not a
  contested one.
- **Operational dependency inspection**: `uv run pip-audit` reports no finding for `httpx` or
  `orjson`, the packages the run lookup uses. Port 8012 has no listener at the time of the check.

Consumer scan (`tools/scan_change_consumers.py --seed trigger_workflow`, candidates only):
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`,
  `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`, `tests/mcp_servers/cicd/test_cicd_models.py`:
  target rows.
- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`,
  `tests/shared/test_tool_constants.py`, `tests/mcp_servers/test_mcp_dispatch.py`,
  `tests/mcp_servers/test_write_dangerous_audit.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`,
  `tests/mcp_servers/test_mcp_tool_validators.py`, `tests/mcp_servers/file/test_mcp_tools_validation.py`,
  `tests/shared/test_route_resolver.py`: reference rows or `not affected` — they pin the tool
  inventory, the routing entry, the non-retryable declaration, or a stubbed handler, none of which
  this Plan changes. `tests/mcp_servers/test_write_dangerous_audit.py` is `not affected: the fake
  handler returns a stubbed success string and the audit record carries no arguments`.
- ADR citations in `docs/10_adr/adr_01_index.md` and `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`:
  `not affected: they cite routing and approval tests, not the dispatch response contract`.

Predictable fallout check:
- Module size: every target file is below the 24576 B gate (largest 10056 B, `cicd_server.py`);
  `not affected: no split row required`.
- Pinned counts: `tests/mcp_servers/cicd/test_cicd_models.py` pins the request schema shape and is
  a target row; `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` pins the tool
  inventory, which is unchanged.
- Tool inventory: no tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected.
- Generated blocks: no generated-reference domain is touched.

Design decisions (Path B):
- **Response-state vocabulary ownership**: keep the five states as a cicd-scoped contract in
  `scripts/mcp_servers/cicd/cicd_models.py` rather than extending `shared.mcp_call_state_contract`'s
  `RECONCILE_OUTCOMES`, because that vocabulary is the closed reconciler-evidence set read by the
  control API and the Agent recovery service. Alternative rejected: adding `accepted` and
  `accepted_unconfirmed` to the shared set, which would change a contract owned by mcpdl004.
- **Correlation recovery**: the `Reconciler` receives the component-keyed execution snapshot, which
  carries no call arguments, so the marker cannot be recovered from the snapshot. Decision: record
  the correlation as a non-sensitive digest in `ReconcileEvidence` at dispatch time and use the
  fallback correlation (workflow identifier, ref, actor, dispatch time) for the run lookup.
  Alternative rejected: reading raw inputs at reconcile time, which violates the no-raw-payload rule.
- **Key independence**: adding a marker to `inputs` changes the args hash, so the same logical call
  with and without the marker produces different dedup keys. The pre-dispatch run search is therefore
  implemented independently of the idempotency key, per REQ-004.

## Implementation steps

1. **Phase 1: Characterization tests first**
   - [ ] Write the response-loss, no-run, delayed-run, and multiple-match tests before any code change (REQ-001, REQ-003; `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`)
   - [ ] Stop and report if a correlation marker cannot be added without changing the workflow contract (REQ-002; per the Issue's AI Implementation Instruction)
2. **Phase 2: Structured outcome model**
   - [ ] Add the dispatch-outcome model with the five states and the matched-run fields, reusing `outcome_unknown` from the shared vocabulary (REQ-001, REQ-003; `scripts/mcp_servers/cicd/cicd_models.py`)
   - [ ] Add the response-model shape tests (REQ-001, REQ-003; `tests/mcp_servers/cicd/test_cicd_models.py`)
3. **Phase 3: Correlation marker and bounded run lookup**
   - [ ] Add the correlation marker to the dispatch inputs when the workflow contract allows it, and the fallback correlation otherwise (REQ-002; `scripts/mcp_servers/cicd/cicd_service_github_actions.py`)
   - [ ] Add bounded polling with the timeout and interval constants, and the pre-dispatch run search for the same logical call (REQ-003, REQ-004; `scripts/mcp_servers/cicd/cicd_service_github_actions.py`)
4. **Phase 4: Handler and delegation contract**
   - [ ] `handle_trigger_workflow` returns the structured outcome and the preview emits input keys and counts only (REQ-001, REQ-006; `scripts/mcp_servers/cicd/cicd_service_business.py`)
   - [ ] The composite delegation carries the structured outcome (REQ-001; `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`)
   - [ ] Replace the immediate-success tests and add the preview-redaction tests (REQ-001, REQ-006; `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`)
5. **Phase 5: Reconciler registration**
   - [ ] Register the workflow-dispatch reconciler at the control-API registry seam, recording evidence as a digest only (REQ-004, REQ-007; `scripts/mcp_servers/cicd/cicd_server.py`)
6. **Phase 6: Documentation**
   - [ ] Record the five states, the correlation and polling strategy, and why automatic retry stays disabled; remove the statement that a dispatch response proves run creation (REQ-008; `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`)
7. **Phase 7: Deployment & Verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md` and hand off to `skills/deploy/SKILL.md`; the prerequisite is that the change is committed and pushed first, and deploying is the user's decision (REQ-001..REQ-008; all target files)

### Release units
**Unit**: structured-state contract | **Phases**: 3, 4 | **Reason**: the backend and handler return-contract change breaks the pinned immediate-success assertions in `tests/mcp_servers/cicd/test_cicd_mcp_service.py` and `tests/mcp_servers/cicd/test_service_github_actions_composite.py` until those tests are replaced in the same commit, so neither phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_models.py` | Unit — response-model shape and state totality | `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` | The five states and the matched-run fields are pinned; no state is produced without a matched run |
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Unit — mocked HTTP, no live GitHub call | `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed, unconfirmed, ambiguous, and unknown outcomes are distinct; polling is bounded |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | Unit — delegation | `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_composite.py` | The structured outcome passes through unchanged |
| `scripts/mcp_servers/cicd/cicd_service_business.py` | Unit — handler and preview redaction | `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Input values are absent from the preview; keys and counts only |
| `scripts/mcp_servers/cicd/cicd_server.py` | Unit — reconciler registration seam | `uv run pytest tests/mcp_servers/test_call_state_api.py` | The registered reconciler answers without re-executing the call |
| `scripts/shared/tool_constants.py` (reference) | Unit — non-retryable declaration | `uv run pytest tests/shared/test_tool_constants.py` | `trigger_workflow` is still explicitly non-retryable |
| All target files | Full sequence | `uv run python tools/run_validation_gates.py` | ruff, mypy, bandit, lint-imports, the full suite, diff-cover ≥ 90%, pre-commit pass |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Structure check | `uv run python tools/check_docs_structure.py` | No findings |

## Risks
- **Risk**: a correlation key added to `inputs` changes the args hash, so the same logical call with and without the marker produces different dedup keys and the gate cannot block a duplicate dispatch → **Mitigation**: the pre-dispatch run search is implemented independently of the idempotency key (REQ-004), and the tool stays non-retryable (REQ-005).
- **Risk**: bounded polling adds latency to a tool call and can exceed the shared HTTP client timeout → **Mitigation**: bounded constants (UNK-02), `outcome_unknown` on timeout, and no automatic retry.
- **Risk**: the target workflow contract may not accept a correlation input → **Mitigation**: the fallback correlation on workflow identifier, ref, actor, and dispatch time; stop and report if neither path works (Phase 1).
- **Risk**: input values can leak through recovery output or the audit `detail` field → **Mitigation**: keys and counts only, and the reconciler records a digest, never a raw payload (REQ-006, REQ-007).
- **Risk**: the response-contract change breaks tests that pin the current string contract in three files → **Mitigation**: the tests are replaced in the same release unit (Phases 3 and 4).
- **Risk**: mcpci001 may not be implemented when this Plan is consumed, so the strict models and the shared client it provides are absent → **Mitigation**: recorded as the blocking dependency UNK-03; implementation stops until it completes.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Characterization tests first (`tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`) | Pending | — | — | — |
| 2 | Structured outcome model (`scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`) | Pending | — | — | — |
| 3 | Correlation marker and bounded run lookup (`scripts/mcp_servers/cicd/cicd_service_github_actions.py`) | Pending | — | — | — |
| 4 | Handler and delegation contract (`scripts/mcp_servers/cicd/cicd_service_business.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`) | Pending | — | — | — |
| 5 | Reconciler registration (`scripts/mcp_servers/cicd/cicd_server.py`) | Pending | — | — | — |
| 6 | Documentation (`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`) | Pending | — | — | — |
| 7 | Deployment & Verification | Pending | — | — | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-005001
- **Evidence revision**: 30c08e72260ab00936fc442cd1646cb12aebb896
- **Related target files**: `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `scripts/mcp_servers/cicd/cicd_service_business.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Implementation Intent | `scripts/mcp_servers/cicd/cicd_models.py` | 2 | AC-1, AC-2, AC-5 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 3 | AC-2 | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent | `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py` | 4 | AC-2 | `tests/mcp_servers/cicd/test_service_github_actions_composite.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent | `scripts/mcp_servers/cicd/cicd_service_business.py` | 4 | AC-2 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes; Unresolved Questions (UNK-01) | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 3 | AC-2 | Phase 1 stop condition | Needs confirmation |
| REQ-003 | Required Changes; Unresolved Questions (UNK-02) | `scripts/mcp_servers/cicd/cicd_models.py` | 2 | AC-1, AC-2 | `tests/mcp_servers/cicd/test_cicd_models.py` | Needs confirmation |
| REQ-003 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 3 | AC-1, AC-2 | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes; Dependencies (mcpai001 shared rule) | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 3 | AC-3 | `tests/mcp_servers/test_mcp_dispatch.py` (reference) | Confirmed by repository evidence |
| REQ-004 | Dependencies (mcpdl004 reconciler contract) | `scripts/mcp_servers/cicd/cicd_server.py` | 5 | AC-3 | `tests/mcp_servers/test_call_state_api.py` | Confirmed by repository evidence |
| REQ-005 | Constraints; AI Implementation Instruction | `scripts/shared/tool_constants.py` (reference) | 4 | AC-5 | `tests/shared/test_tool_constants.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; Acceptance Criteria | `scripts/mcp_servers/cicd/cicd_service_business.py` | 4 | AC-4 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-007 | Dependencies (mcpdl004) | `scripts/mcp_servers/cicd/cicd_server.py` | 5 | AC-3 | `tests/mcp_servers/test_call_state_api.py` | Confirmed by repository evidence |
| REQ-008 | Documentation Impact | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | 6 | AC-6 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
