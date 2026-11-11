## Goal
Make every WRITE_DANGEROUS MCP tool leave a server-side audit record (closing the one verified gap, `rag_delete_document` in rag-pipeline-mcp) and define MCP authentication once in a new ADR that ADR-007 links to and that every MCP document agrees with.

## Priority
High

## Scope
- **In-Scope**: rag-pipeline-mcp emits the shared `mcp_tool_exec` audit record from its `call_tool` handler (success and failure); a parametrized test proves an audit record for every WRITE_DANGEROUS tool on every hosting server; a new ADR (ADR-017) for MCP authentication, registered in the ADR index, the ADR document guide, and the authority model; ADR-007 links to it; `mcp_02_02`, `mcp_06_14`, `mcp_02_03`, `mcp_06_05`, and `mcp_04_03` are corrected to agree with the code and the ADR.
- **Out-of-Scope**: removing `accept_all_for_tests` (already merged, `cad5e91ea`); adding a `principal` field or any other change to the audit record format; changing the Bearer-token mechanism; authentication for non-MCP components (EventBus is ADR-013); writing approval statements for a maintainer; the `governance_03` ledger entries (ledger plan `plans/20261111-095703_adrrev012_adr-approval-ledger.md`); the duplicated `requested_target` row in `mcp_02_03` and the duplicated `requested_target` assignment in `scripts/mcp_servers/audit.py` (observed, unrelated).
- **Dependencies**: The issue's dependency `issues/20261109-112640_adrrev004_non-strict-bypass-removal.md` is closed (archived; `accept_all_for_tests` no longer appears under `scripts/`, `config/`, `tests/`, or `docs/`), so no `Depends on` entry is recorded. Sequencing: this Plan should land before the ledger Plan so the ledger does not record an empty-token documentation conflict that this Plan closes.

## Background
`config/agent.toml` `[tool_safety_tiers]` marks 13 tools WRITE_DANGEROUS: `delete_file`, `delete_directory` (file-delete-mcp); six `github_*` write tools (github-mcp); `rag_delete_document` (rag-pipeline-mcp); `trigger_workflow` (cicd-mcp); `git_checkout`, `git_pull`, `git_push` (git-mcp). Verification against current source found that every hosting server except rag-pipeline-mcp calls `_audit_log()` from its `call_tool` handler; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` `call_tool` discards `session_id` and `request_id` and writes nothing. The documents `mcp_02_03`, `mcp_06_05`, and `mcp_04_03` state this gap.

On authentication, the memo's claim that only four servers refuse an empty token is stale: `require_auth_token()` is used by every server module, `attach_auth_middleware()` is fail-closed for an empty token, and ADR-007 Decision 9 and INV-09 already state the all-servers rule. What remains is (a) ADR-007's out-of-scope line "Detailed implementation of security authentication (handled by a separate ADR)" with no such ADR, and (b) two sentences that contradict the code: `mcp_06_14` troubleshooting "Missing secrets via environment variables" (Symptom "The server starts, but health checks fail") and the last Bearer bullet of `mcp_02_02` ("Empty server-side token ... `attach_auth_middleware()` skips the authentication check").

## Problem
- A destructive RAG operation leaves a record only on the Agent side; if the Agent log is lost or a caller other than the Agent reaches the server, a deletion leaves no trace.
- MCP authentication rules live in reference documents and in ADR-007's decision text, while ADR-007 defers the details to an ADR that does not exist, and two reference sentences contradict the implemented fail-closed behavior.

## Reason for Change
Server-side audit of destructive writes is a security-sensitive gap, and authentication rules that point at a non-existent ADR cannot be reviewed. The test-only bypass is already removed, so the new ADR can state "no bypass".

## Implementation Intent
Reuse the shared audit helper exactly as cicd-mcp and github-mcp do (one `mcp_tool_exec` record per executed `call_tool`, `outcome` taken from `DispatchResult`), with no new field and no second format. Write the authentication ADR from the already-implemented behavior (one `MCP_<SERVER_KEY>_AUTH_TOKEN` variable per server resolved on both sides, an empty token aborts server startup and Agent startup, no bypass, changes take effect only on restart), narrow ADR-007's authentication coverage to a link, and bring the five MCP documents into agreement.

## Requirements
- `REQ-001`: rag-pipeline-mcp `call_tool` emits one shared audit record per executed call through `mcp_servers.audit._audit_log()` for both `ok` and `error` outcomes, with `server_key="rag_pipeline"`, `session_id`/`request_id` from `extract_request_context()`, and `target` set to the document URL truncated to 80 characters for `rag_delete_document` and empty for the other tools. A call rejected before dispatch because the tool is disabled writes no record (same as cicd-mcp and github-mcp).
- `REQ-002`: A parametrized test asserts an audit record for every WRITE_DANGEROUS tool on its hosting server (success path and, where the server can fail without external services, an error path), and a completeness test asserts the parametrization equals the WRITE_DANGEROUS set derived from `config/agent.toml` `[tool_safety_tiers]`.
- `REQ-003`: A new ADR-017 defines MCP authentication once: one shared variable per server resolved on both the Agent side and the server side, an empty token aborts startup on both sides, no bypass, changes apply only on restart, with failure behavior and an Approval section carrying a pending maintainer statement (not an invented approval).
- `REQ-004`: ADR-007 links to ADR-017 and drops its "handled by a separate ADR" out-of-scope line; ADR-017 is registered in `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, and `config/adr_authority.toml` (decision target, narrowed ADR-007 limit, typed edge), and `check_adr_authority.py` passes.
- `REQ-005`: `mcp_02_02` and `mcp_06_14` no longer contain a sentence that contradicts ADR-017 or the code, and defer to ADR-017 instead of restating the rules.
- `REQ-006`: `mcp_02_03`, `mcp_06_05`, and `mcp_04_03` no longer say rag-pipeline-mcp writes no audit log; the list of audit-writing servers, the audit layers, and the "servers without audit logging" section name only file-read-mcp.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Emit the shared audit record from `call_tool` (it currently discards `session_id`/`request_id` at `_, _, idempotency_key = extract_request_context(request)`). 15792 bytes, far below the 24576-byte module-size gate | REQ-001 / AC-1 | `call_tool` at line 336 returns `_to_call_tool_response(r)` with no audit call; `cicd_server.py:168-186` and `github_server.py:229-246` show the pattern (checked in Step 3) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, `tests/mcp_servers/test_write_dangerous_audit.py` | Verified |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Modify | Add success and failure audit-emission tests for rag-pipeline-mcp (module already tests `POST /v1/call_tool` with a `_FakeService`) | REQ-001 / AC-1 | Existing `_FakeService` fixture and `/v1/call_tool` tests in the file (checked in Step 3) | itself | Verified |
| `tests/mcp_servers/test_write_dangerous_audit.py` | Create | New parametrized cross-server test plus completeness check against `config/agent.toml` tiers. New file; `tests/mcp_servers/` exists | REQ-002 / AC-2 | `tests/mcp_servers/file/test_file_server_audit_records.py` (file-write/delete) and `tests/mcp_servers/cicd/test_cicd_server_endpoints.py:144-190` show per-server audit capture; no cross-server test exists (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Create | New ADR for MCP authentication; New file; `docs/10_adr/` exists; number 017 is free (`adr_00_document-guide.md` records ADR-011 as unassigned, files stop at 016) | REQ-003 / AC-3 | `ls docs/10_adr/` shows adr_02_03_007 and adr_02_03_012 as the only MCP-group ADRs (checked in Step 3) | `tools/check_adr_structure.py`, `tools/check_adr_authority.py` | Verified |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Link to ADR-017 from Decision 9 and replace the out-of-scope line "Detailed implementation of security authentication (handled by a separate ADR)" at line 92 | REQ-004 / AC-4 | Line 92 out-of-scope entry; Decision 9 at line 77 (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `docs/10_adr/adr_01_index.md` | Modify | Add the ADR-017 row to the ADR List and regenerate the guarded authority sections | REQ-004 / AC-4 | ADR List rows ADR-001 to ADR-016 at lines 45-63; guarded sections are produced by `tools/generate_adr_authority.py` (checked in Step 3) | `uv run python tools/generate_adr_authority.py --check` | Verified |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Add ADR-017 to the document guide's ADR enumeration | REQ-004 / AC-4 | Line 61 states ADR-011 is unassigned and enumerates the ADR list (checked in Step 3) | `tools/check_docs_structure.py` | Verified |
| `config/adr_authority.toml` | Modify | Add a decision target for MCP authentication (primary ADR-017) and narrow the ADR-007 supplemental limit under `mcp.technical-safety` ("transport, authentication, and health-check responsibilities") plus typed ADR edges | REQ-004 / AC-4 | `mcp.technical-safety` entry with the ADR-007 limit; `mcp.transport` primary ADR-007 (checked in Step 3) | `tools/check_adr_authority.py`, `tests/tools/test_adr_authority.py` | Verified |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | Replace the last Bearer bullet (line 83: "Empty server-side token (a standalone test run only): `attach_auth_middleware()` skips the authentication check ...") with a pointer to ADR-017 consistent with the fail-closed middleware | REQ-005 / AC-5 | `attach_auth_middleware()` in `scripts/mcp_servers/server.py:95-131` returns 401 for every request when the token is empty (checked in Step 2) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` | Modify | Correct the troubleshooting entry "Missing secrets via environment variables" (line 53: "The server starts, but health checks fail") and defer the rules to ADR-017 | REQ-005 / AC-5 | `require_auth_token()` raises `RuntimeError` for an empty token (`server.py:134-144`), so the server does not start (checked in Step 2) | `tools/check_docs_consistency.py --domain mcp` | Verified |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Add rag-pipeline-mcp to the audit-writing servers (line 22) and fix the Note (line 44) | REQ-006 / AC-6 | Lines 22 and 44 state rag-pipeline-mcp writes no audit log (checked in Step 2) | `tools/check_docs_quality.py` | Verified |
| `docs/22_mcp/mcp_06_05_reading-audit-logs.md` | Modify | Fix Layer 2 (line 56) and the "MCP Servers without Audit Logging" section (line 65) so only file-read-mcp is listed | REQ-006 / AC-6 | Lines 56 and 65 (checked in Step 2) | `tools/check_docs_quality.py` | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Replace line 46 "Audit: Layer1 `tool_exec` only; no shared or dedicated audit log" | REQ-006 / AC-6 | Line 46 (checked in Step 2) | `tools/check_docs_quality.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/audit.py` | The shared helper (`_audit_log`, `AuditRecord`) that REQ-001 reuses; confirms there is no `principal` field and that `outcome` is `ok`, `error`, or `rejected` | REQ-001 |
| `scripts/mcp_servers/dispatch.py` | `DispatchResult.outcome` and `_to_call_tool_response` that the new audit call reads | REQ-001 |
| `scripts/mcp_servers/server.py` | `extract_request_context`, `attach_auth_middleware`, `require_auth_token`: the behavior ADR-017 documents | REQ-001, REQ-003, REQ-005 |
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` | `fmt_delete_document` returns "Deleted: {url}" or "Not found: {url}" with outcome `ok` either way; it fixes the audit semantics for a missing document | REQ-001 |
| `scripts/mcp_servers/cicd/cicd_server.py` | Reference pattern for the audit call in `call_tool` | REQ-001 |
| `scripts/mcp_servers/github/github_server.py` | Reference pattern for the audit call in `call_tool` | REQ-001 |
| `scripts/mcp_servers/git/git_server.py` | Audit emission for git_checkout, git_pull, git_push (`_audit_log_safe`, outcome `rejected` paths) | REQ-002 |
| `scripts/mcp_servers/file/delete_server.py` | Audit emission for delete_file and delete_directory | REQ-002 |
| `config/agent.toml` | `[tool_safety_tiers]` is the source of the WRITE_DANGEROUS set for the completeness test | REQ-002 |
| `config/mcp_dedup.toml` | `rag_delete_document = "retryable"` shows the dedup overlay: a replayed call must still be audited once per request | REQ-001 |
| `tests/mcp_servers/_auth_headers.py` | Existing helper for authenticated TestClient calls | REQ-002 |
| `tests/mcp_servers/file/test_file_server_audit_records.py` | Existing audit-capture pattern for the file servers | REQ-002 |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Existing audit-capture pattern for cicd-mcp | REQ-002 |
| `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md` | Template and wording precedent for an MCP-group ADR | REQ-003 |
| `docs/10_adr/adr_02_07_016_adr-authority-model.md` | Authority model rules the new ADR must satisfy | REQ-003, REQ-004 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR process and approval evidence standard; approval records come from a maintainer | REQ-003 |
| `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` | Requires a new approval record in the same change for an ADR edit that changes a decision (ADR-007) | REQ-003, REQ-004 |
| `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md` | Referenced by `mcp_02_02` and `mcp_06_14` for the mdq-mcp authentication rule | REQ-005 |

## Acceptance Criteria
- AC-1: A `rag_delete_document` call through rag-pipeline-mcp `POST /v1/call_tool` writes exactly one `mcp_tool_exec` record with `tool`, `target`, `outcome`, `session_id`, `request_id`, and `server_key="rag_pipeline"` for success and for failure, and contains no document content (`REQ-001`).
- AC-2: The parametrized test fails if any of the 13 WRITE_DANGEROUS tools lacks an audit record on its hosting server, and the completeness test fails if the parametrization drifts from `config/agent.toml` (`REQ-002`).
- AC-3: ADR-017 states the authentication rules and failure behavior, passes `check_adr_structure.py`, and its Approval section holds a clearly marked pending maintainer statement (`REQ-003`).
- AC-4: ADR-007 links to ADR-017; ADR-017 appears in the index, the document guide, and `config/adr_authority.toml`; `check_adr_authority.py` and `generate_adr_authority.py --check` pass (`REQ-004`).
- AC-5: No sentence in `mcp_02_02` or `mcp_06_14` contradicts ADR-017 or the fail-closed code (`REQ-005`).
- AC-6: No document under `docs/22_mcp/` says rag-pipeline-mcp writes no audit log (`REQ-006`).
- AC-7: `check_docs_consistency.py --domain mcp`, `check_docs_content_policy.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_japanese.py`, and `check_adr_preservation.py` (no ERROR other than the intended ADR-007 text change) pass; `uv run pytest tests/mcp_servers -v` and the `rules/toolchain.md` sequence pass.

## Tests
- `REQ-001`: in `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, an audit record is captured for `rag_delete_document` success, for "Not found" (outcome `ok`), and for a handler error (outcome `error`); no record when the tool is disabled; the record carries no document content.
- `REQ-002`: `tests/mcp_servers/test_write_dangerous_audit.py` parametrizes over (server, tool) for the 13 tools and over the completeness set derived from `config/agent.toml`.

## Documentation Impact
Update the MCP domain documents and the ADR set (`docs/00_index.md` "Document References by Task", MCP and governance areas): the new ADR-017, ADR-007, the ADR index and document guide, `mcp_02_02`, `mcp_02_03`, `mcp_04_03`, `mcp_06_05`, `mcp_06_14` (REQ-003 to REQ-006). Describe intent, rules, and failure behavior; do not copy environment-variable values or tokens. Write in English.

## Assumptions
- A tool disabled at the availability gate writes no audit record, matching the comment in `github_server.py` ("disabled-tool rejection is not misclassified into the audit log's error-type taxonomy") and `cicd_server.py`.
- `target` for rag-pipeline-mcp carries the document URL (truncated to 80 characters like the file servers) only for `rag_delete_document`, and is empty for query tools, because query text may carry user content (REQ-001).
- The principal is represented by `session_id` and `request_id` (the Bearer token is one shared secret per server); the audit format is not extended (Constraint "keep the audit format stable").
- "Not found" is audited with outcome `ok` because the tool handler reports it as a normal result; no service change is made.
- The new ADR number is 017 and the file name follows the existing `adr_<group>_<NNN>_<slug>.md` convention with group `03` (mcp).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the audit record must carry a principal | No decision in the issue, ADR, or code; the format has no field for it | Maintainer decision; if required, a separate issue changes the format and `mcp_06_05` consumers | False |
| UNK-02 | The authority split for ADR-017: a new decision target (name) and the exact narrowed ADR-007 limit | `config/adr_authority.toml` has `mcp.technical-safety` (primary ADR-012, ADR-007 limit "transport, authentication, and health-check responsibilities") but no authentication target | Draft in Phase 3 and confirm with `check_adr_authority.py`; the maintainer confirms the split at approval | False |
| UNK-03 | Maintainer approval statements for ADR-017 and for the ADR-007 decision change (approver, date, scope) | Approvals are maintainer statements and may not be written by the implementer | Write a marked pending record; report it; the maintainer supplies the statement (ledger plan tracks it) | False |
| UNK-04 | Whether one cross-server test module can build the five server apps (shell is ADMIN not WRITE_DANGEROUS, so file-delete, github, rag-pipeline, cicd, git) with their services stubbed | Per-server fixtures exist but no cross-server test does; import-time side effects of five server modules are unchecked | Spike in Phase 2: if one module is not feasible, keep the parametrization per server directory and keep only the completeness test in `tests/mcp_servers/test_write_dangerous_audit.py` | False |
| UNK-05 | Whether any test or inventory enumerates ADR files and would need an update for ADR-017 | `tests/tools/test_adr_authority.py` references ADR-016 but was not read in full | Run `uv run pytest tests/tools -q` and the ADR checkers in Phase 3; add any failing inventory as a plan amendment (`tools/amend_plan.py`, fallout class) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Modify | Low (one module-local handler; importers are its package `__init__`, health probe, and tests) | 6 | N/A | Requires deploy of `scripts/` (rag-pipeline-mcp restart) |
| `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Modify | Low | 3 | N/A | not applicable (tests are not deployed) |
| `tests/mcp_servers/test_write_dangerous_audit.py` | Create | Low | N/A | N/A | not applicable (tests are not deployed) |
| `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Create | Medium (ADR graph and index consumers) | N/A | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Modify | Medium | 2 | N/A | not applicable (docs) |
| `docs/10_adr/adr_01_index.md` | Modify | Medium (generated sections, high churn) | 29 | N/A | not applicable (docs) |
| `docs/10_adr/adr_00_document-guide.md` | Modify | Low | 9 | N/A | not applicable (docs) |
| `config/adr_authority.toml` | Modify | Medium (read by `check_adr_authority.py`, `generate_adr_authority.py`, CI lint) | 2 | N/A | not applicable (not deployed to `/opt/llm`) |
| `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Modify | Low | 11 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` | Modify | Low | 7 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Low | 7 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_06_05_reading-audit-logs.md` | Modify | Low | 5 | N/A | not applicable (docs) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Low | 9 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files, new test module, new ADR). Analysis recorded from Step 3 and the Path B inspection:
- Architecture: `rag_pipeline_server` imports `mcp_servers.dispatch` and `mcp_servers.server`; adding `from mcp_servers.audit import _audit_log` follows the same dependency direction as `cicd_server.py` and `github_server.py`. No new import cycle (`audit.py` imports only `shared.logger` and `orjson`).
- Dependency graph: importers of `rag_pipeline_server` are `rag_pipeline/__init__.py`, `rag_pipeline_health_probe.py`, and seven test modules; none changes behavior.
- Historical analysis: churn figures in `Affected areas` come from `git log --since=30.days`; bus factor is `N/A` (git-fame not installed).
- Operational: rag-pipeline-mcp listens on port 8010 and is Agent-managed; no database or lock is touched, and the change takes effect on restart through the deploy hand-off.
- Persisted schema: not applicable. Consumer scan (`tools/scan_change_consumers.py`): no persisted schema, public API, or shared constant changes; the audit record format is unchanged, `not affected: mcp_06_05 log-reading procedures (no field added)`.
- Audit semantics (REQ-001): call `_audit_log(logger, session_id=..., request_id=..., action=req.name, target=..., outcome=r.outcome, server_key="rag_pipeline")` after dispatch. `error_type` is left at its default because `DispatchResult` carries its own taxonomy for dispatch failures; set it only if `DispatchResult` exposes one (verified at implementation). The server's existing `logger` is the shared `Logger` writing `rag-mcp.log`; the record lands there like cicd-mcp's lands in its application log (`mcp_06_05` "Layer 2").
- Alternative rejected: emitting the record from `dispatch_tool` in `scripts/mcp_servers/dispatch.py` would audit every server, but changes servers that already audit (duplicate records) and widens the blast radius.
- ADR-017 shape: Context, Decision (one variable per server on both sides, empty token aborts server startup and Agent startup, no bypass, restart required), Alternatives (shared token across servers; per-environment profile switch), Consequences, Invariants with test citations (reuse the existing `tests/mcp_servers/test_require_auth_token.py` and per-server auth tests), Approval with a marked pending statement. Wording is drawn from ADR-007 Decision 9, `mcp_06_14`, and the code, without copying token values.
- ADR-007 change is a decision-scope reduction (authentication detail moves out), so it needs a maintainer approval record in the same change (`governance_05`); the pending record is written as ADR-010 does for its withdrawal.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: rag-pipeline-mcp audit emission** (REQ-001; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`)
   - [ ] Write the failing audit tests first (success, not found, handler error, disabled tool, no content in the record).
   - [ ] Read `session_id`/`request_id` from `extract_request_context()` and call `_audit_log` after dispatch in `call_tool`.
   - [ ] Run `uv run pytest tests/mcp_servers/rag_pipeline -v`.
2. **Phase 2: WRITE_DANGEROUS audit coverage** (REQ-002; `tests/mcp_servers/test_write_dangerous_audit.py`)
   - [ ] Spike UNK-04: build the (server, tool) parametrization for the five hosting servers with services stubbed.
   - [ ] Add the completeness test that derives the WRITE_DANGEROUS set from `config/agent.toml` `[tool_safety_tiers]`.
   - [ ] Run `uv run pytest tests/mcp_servers -v`.
3. **Phase 3: Authentication ADR and authority registration** (REQ-003, REQ-004; `docs/10_adr/adr_02_03_017_mcp-authentication.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `config/adr_authority.toml`)
   - [ ] Draft ADR-017 with a pending maintainer approval record (never an invented approver or date).
   - [ ] Link ADR-007 to ADR-017 and replace its out-of-scope line; add its pending approval record.
   - [ ] Add the authority entry and edges to `config/adr_authority.toml`; add the index and document-guide rows; run `uv run python tools/generate_adr_authority.py`, then `--check`.
4. **Phase 4: Align the MCP documents** (REQ-005, REQ-006; `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_06_05_reading-audit-logs.md`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`)
   - [ ] Fix the two contradicting authentication sentences and point to ADR-017.
   - [ ] Update the audit-writing server list, Note, audit layers, and "servers without audit logging" section; fix `mcp_04_03` line 46.
5. **Phase 5: Deployment & Verification** (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` and the documents above)
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence (format, lint, type, architecture, security, test, coverage).
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); rag-pipeline-mcp restarts on deploy.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Unit (endpoint audit capture) | `uv run pytest tests/mcp_servers/rag_pipeline -v` | Pass |
| `tests/mcp_servers/test_write_dangerous_audit.py` | Unit (parametrized, 13 tools) | `uv run pytest tests/mcp_servers -v` | Pass |
| Python targets | Format, lint, type, security | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy <files>`, `uv run bandit -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` | Clean |
| Module size | Size gate | `uv run python tools/check_module_size.py` | Pass |
| Coverage | Changed lines | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |
| `docs/10_adr/*`, `docs/22_mcp/*` | Documentation structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| `docs/22_mcp/*` | Doc claims against code and config | `uv run python tools/check_docs_consistency.py --domain mcp` | Pass |
| `docs/10_adr/*`, `config/adr_authority.toml` | ADR structure, authority, graph drift, preservation | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `generate_adr_authority.py --check`, `check_adr_preservation.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py` | Pass (preservation: only the intended ADR-007 text change reported) |
| ADR-017 | Needs Confirmation and Known Deviation inventories | `uv run python tools/check_needs_confirmation_inventory.py`, `check_known_deviation_sync.py` | Pass |
| `tests/tools/test_adr_authority.py` | Authority unit tests | `uv run pytest tests/tools -q` | Pass |

Validation quality baseline: `radon` and `vulture` are not installed on this host (Tool availability guard, lightweight alternative: the cyclomatic and dead-code checks are covered by ruff in the toolchain run); `bandit -q -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` exited 0 with no finding on the scanned path.

## Risks
- **Risk**: A replayed idempotent call (`rag_delete_document` is `retryable` in `config/mcp_dedup.toml`) is audited twice or not at all. → **Mitigation**: The audit call sits after `dispatch_tool`, so each request is audited once with its own `request_id`; Phase 1 includes a replay test case.
- **Risk**: The audit record leaks content or a secret. → **Mitigation**: `target` is the URL truncated to 80 characters, nothing else from the arguments or result is recorded, and the test asserts the record contains no document content.
- **Risk**: The cross-server test is brittle because five server modules import with side effects. → **Mitigation**: UNK-04 spike with a per-server fallback; the completeness test alone still guards the set.
- **Risk**: A new ADR enlarges the authority graph and breaks `check_adr_authority.py` or CI lint. → **Mitigation**: Add the entry and edges together, run the checkers in the same phase, and keep ADR-007 supplemental with a narrowed limit rather than removing it.
- **Risk**: Editing ADR-007 is a decision change and the approval record is missing. → **Mitigation**: Write a clearly marked pending record and report it; do not fabricate an approval (UNK-03).
- **Risk**: High-churn `docs/10_adr/adr_01_index.md` conflicts with sibling Plans that edit it. → **Mitigation**: Regenerate guarded sections with the tool and rerun `tools/check_plan_target_overlaps.py`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | rag-pipeline-mcp audit emission (REQ-001) | In Progress | — | — |  |
| 2 | WRITE_DANGEROUS audit coverage test (REQ-002) | In Progress | — | — |  |
| 3 | Authentication ADR and authority registration (REQ-003, REQ-004) | In Progress | — | — |  |
| 4 | Align the MCP documents (REQ-005, REQ-006) | In Progress | — | — |  |
| 5 | Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261111-231122_01_scripts_mcp_servers_rag_pipeline_rag_pipeline_server.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261111-231122_03_tests_mcp_servers_test_write_dangerous_audit.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261111-231122_04_docs_10_adr_adr_02_03_017_mcp-authentication.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-231122_05_docs_10_adr_adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-231122_06_docs_10_adr_adr_01_index.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-231122_07_docs_10_adr_adr_00_document-guide.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-231122_08_config_adr_authority.toml.md` | 3 | Procedure | Pending | — | — |
| `implementations/20261111-231122_09_docs_22_mcp_mcp_02_02_startup-modes-and-health.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-231122_10_docs_22_mcp_mcp_06_14_mcp-authentication-setup.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-231122_11_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-231122_12_docs_22_mcp_mcp_06_05_reading-audit-logs.md` | 4 | Procedure | Pending | — | — |
| `implementations/20261111-231122_13_docs_22_mcp_mcp_04_03_rag-pipeline-and-cicd.md` | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-095422
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`, `tests/mcp_servers/test_write_dangerous_audit.py`, `docs/10_adr/adr_02_03_017_mcp-authentication.md`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_01_index.md`, `docs/10_adr/adr_00_document-guide.md`, `config/adr_authority.toml`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_06_05_reading-audit-logs.md`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: emit audit in rag-pipeline-mcp; verification: `rag_pipeline_server.py` `call_tool` writes none | `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` | Step 1 | AC-1 | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations: unit tests for rag-pipeline-mcp audit emission (success and failure) | `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py` | Step 1 | AC-1 | `uv run pytest tests/mcp_servers/rag_pipeline -v` | Explicit in issue |
| REQ-002 | Required Changes: audit-line test for every WRITE_DANGEROUS tool; verification: 13 tools in `[tool_safety_tiers]` | `tests/mcp_servers/test_write_dangerous_audit.py` | Step 2 | AC-2 | `uv run pytest tests/mcp_servers -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes: new ADR for MCP authentication; Problem: ADR-007 defers to a non-existent ADR | `docs/10_adr/adr_02_03_017_mcp-authentication.md` | Step 3 | AC-3 | `check_adr_structure.py`, `check_adr_authority.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: link from ADR-007, register in index and authority model | `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Step 3 | AC-4 | `check_adr_preservation.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: register in the index and authority model | `docs/10_adr/adr_01_index.md` | Step 3 | AC-4 | `generate_adr_authority.py --check` | Explicit in issue |
| REQ-004 | Target Files: ADR set; verification: document guide enumerates ADRs and ADR-011 is unassigned | `docs/10_adr/adr_00_document-guide.md` | Step 3 | AC-4 | `check_docs_structure.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes: register in the authority model | `config/adr_authority.toml` | Step 3 | AC-4 | `check_adr_authority.py` | Explicit in issue |
| REQ-005 | Required Changes: re-check `mcp_02_02`; verification: line 83 contradicts fail-closed middleware | `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` | Step 4 | AC-5 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-005 | Required Changes: re-check `mcp_06_14`; verification: troubleshooting "The server starts" contradicts `require_auth_token()` | `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` | Step 4 | AC-5 | `check_docs_consistency.py --domain mcp` | Confirmed by repository evidence |
| REQ-006 | Required Changes: update `mcp_02_03` so it no longer says rag-pipeline-mcp writes no audit log | `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Step 4 | AC-6 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes: update `mcp_06_05` | `docs/22_mcp/mcp_06_05_reading-audit-logs.md` | Step 4 | AC-6 | `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-006 | Verification: `mcp_04_03` line 46 states no audit log and was missing from the issue | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Step 4 | AC-6 | `check_docs_quality.py` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261111-231122 -->