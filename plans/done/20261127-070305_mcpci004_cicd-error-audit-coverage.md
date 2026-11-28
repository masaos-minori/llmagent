# Plan: Correct CI/CD error classification and guarantee complete audit coverage

## Goal
- Map GitHub API and transport failures in the CI/CD server to truthful, machine-readable errors, and emit exactly one correlated, redacted audit record for every authenticated CI/CD tool call, including rejected and failed calls.

## Priority
Medium

## Scope
- **In-Scope**: the status-to-exception mapping in the CI/CD GitHub Actions backend (5xx, 429, 409, transport failures); the bounded and redacted upstream error text and the preserved `Retry-After` and reset metadata; the exception-handler registrations and the machine-readable response body; exactly one audit event per authenticated call in `call_tool()`; the normalized target and the stable CI/CD error codes; the duplicate `requested_target` assignment in the shared audit helper; the affected tests; the CI/CD and audit documentation records.
- **Out-of-Scope**: dispatch reconciliation states (mcpci002); log streaming bounds and the per-job result contract (mcpci003); web-search audit behavior (mcpws002); the shared `AuditEmission` class itself, which is already implemented; the jobs-fetch path's own non-2xx mapping, recorded as UNK-03.
- **Dependencies**: mcpci001 (must be implemented first, it provides the normalized `owner/repo` target); mcpdd001, mcpai001, mcpai006, mcpws002, mcpai010 are closed and their helper, audit-record fields, and HTTP-level test fixture are implemented. mcpci002 and mcpci003 can run in parallel.
  - **Depends on**: `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` | phase all | the audit target is the normalized `owner/repo` value mcpci001's shared normalization function produces; this Plan cannot name the normalized target before that function exists.
  - **Depends on**: `plans/done/20261119-141108_mcpws002_websearch-config-audit-redaction.md` | phase all | the shared audit-emission contract and the redaction helpers this Plan reuses; already implemented, so the dependency is satisfied.
  - **Depends on**: `plans/done/20261119-140513_mcpai006_github-write-retry-policy.md` | phase all | the audit-record field order this Plan writes through the shared helper; already implemented, so the dependency is satisfied.
  - **Depends on**: `plans/done/20261119-140517_mcpai010_github-http-contract-tests.md` | phase all | the `http_boundary` fixture the transport-failure tests use; already implemented in `tests/mcp_servers/conftest.py`, so the dependency is satisfied.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 8).

Evidence (`Explicit in code`, verified in Step 2): `scripts/mcp_servers/cicd/cicd_service_github_actions.py::_check_response` maps 404 to `CicdNotFoundError` (line 71), 422 to `CicdValidationError` (lines 73-74), 401/403 to `CicdAuthorizationError` (line 76), and every other non-2xx status — including 5xx — to `CicdNotFoundError` through the catch-all at lines 78-80. `scripts/mcp_servers/cicd/exception_handlers.py:39` maps `CicdNotFoundError` to HTTP 404, so a GitHub 500 surfaces as Not Found. 429 is not a status branch at all: it is a substring test on the response message inside `_raise_auth_error` (lines 82-90), so a genuine 429 status reaches the catch-all. No `CicdConflictError` exists and no `httpx` transport exception is handled in the backend.

`scripts/mcp_servers/cicd/cicd_server.py::call_tool` calls `_audit_log` at line 183, after the dispatch call, so the disabled-tool return (line 173) and the `ExecutionContextError` return (line 178) produce no record, and an exception raised by the handler produces none. The Issue's line citation (177) is off by the current file; the call site is line 183.

The shared audit-emission contract named by the Issue exists: `scripts/mcp_servers/audit.py::AuditEmission` (lines 236-296, the end of the file; re-verified 20261127), used by `scripts/mcp_servers/web_search/web_search_server.py`. The duplicate `requested_target` assignment is confirmed at `scripts/mcp_servers/audit.py` lines 124-125 and 128-129.

## Problem
A GitHub outage is reported as Not Found, which hides the outage and misleads the recovery decision; the agent's transport layer treats tool-level statuses `400/403/404/409/422` as tool results and only `429` and `5xx` as transport faults, so the wrong classification changes both the reported error and the health-registry outcome. Audit coverage is incomplete: a call that is refused before dispatch, or that raises, leaves no record, so incident review cannot tell whether the call happened.

## Reason for Change
Truthful errors and complete audit are needed for recovery decisions and incident review; the final names depend on the credential contract that provides the normalized target.

## Implementation Intent
A status-to-exception table in the backend that names each failure mode, transport failures mapped to the upstream error, bounded and redacted error text with preserved retry metadata, handler registrations for the new exception types, and one `AuditEmission` emitted from a `finally` block in `call_tool()` so every authenticated call produces exactly one record.

## Requirements
- `REQ-001`: the backend maps non-2xx statuses truthfully: 5xx to `CicdUpstreamError`, 429 to a distinct rate-limit error, 409 to a conflict error; 401, 403, 404, and 422 keep their current semantics.
- `REQ-002`: DNS, TLS, connection, and timeout failures map to upstream errors; raw transport exception text never appears in an error.
- `REQ-003`: upstream error text is bounded by a maximum length and redacted; `Retry-After` and the rate-limit reset value are preserved as structured fields on the exception.
- `REQ-004`: the exception handlers register the new exceptions at 409 and 429, keep upstream at 502, and the response body carries the stable error code together with the preserved metadata.
- `REQ-005`: `call_tool()` emits exactly one audit record per authenticated call through `AuditEmission` from a `finally` block, covering success, disabled tool, unknown tool, validation, authorization, upstream, dedup, and unexpected outcomes.
- `REQ-006`: the record carries the normalized `owner/repo` target and a stable CI/CD error code, and never a token, a workflow input value, or raw upstream payload text.
- `REQ-007`: audit-write failure never propagates; `call_tool()` logs the failure and increments `audit_failure_count`, the policy decided by the owner on 20261127 (see Assumptions).
- `REQ-008`: the duplicate `requested_target` assignment in the shared audit helper is removed.
- `REQ-009`: documentation records the CI/CD error mapping table, the exactly-one-event behavior, and the redaction rules.

## Implementation Target Files
**Freeze status**: Frozen (Step 8's Implementation Target Files Validation passed:
`tools/audit_plan_target_paths.py` 0 findings, `tools/check_plan_target_overlaps.py`
compatible overlap with the open mcpci001 plan and the frozen mcpci002 and mcpci003 plans,
`tools/check_workitem_structure.py` no findings).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as the modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | Map non-2xx statuses truthfully (5xx to upstream, 429 to the rate-limit error, 409 to the conflict error); wrap the request so DNS, TLS, connection, and timeout failures become upstream errors; bound and redact the upstream message; carry `Retry-After` and reset metadata on the exception | REQ-001, REQ-002, REQ-003, AC-1, AC-2 | `_check_response` lines 68-80: 404 at line 71, 422 at lines 73-74, 401/403 at line 76, and the catch-all `if not resp.is_success` raising `CicdNotFoundError` at lines 78-80; 429 is only a substring test inside `_raise_auth_error` (lines 82-90); `_parse_error_message` (lines 59-65) returns the upstream `message` verbatim with no length bound; the module handles no `httpx` exception (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Add `CicdConflictError` and `CicdRateLimitError`, the CI/CD error-code vocabulary as a frozenset, the exception-to-code mapping, and the maximum error-text length constant | REQ-001, REQ-003, REQ-004, REQ-006, AC-1, AC-3, AC-5 | The module defines four exceptions and no conflict or rate-limit type, no error-code vocabulary, and no error-text bound; `tests/mcp_servers/cicd/test_cicd_models.py` lines 193-197 pin the existing hierarchy (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_models.py` | Verified |
| `scripts/mcp_servers/cicd/exception_handlers.py` | Modify | Register handlers for the new exceptions at 409 and 429, keep upstream at 502, and render the stable error code and the preserved metadata in the response body | REQ-004, AC-3 | Lines 36-41 register four handlers, `CicdNotFoundError` at 404 (line 39) and `CicdUpstreamError` at 502 (line 41); the body is `{"detail": str(exc)}` built at lines 30-31, with no error code and no metadata (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` | Verified |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | `call_tool()` emits exactly one record through `AuditEmission` from a `finally` block covering success, disabled tool, unknown tool, validation, authorization, upstream, dedup, and unexpected outcomes; classify the outcome (`ok`, `error`, `rejected`), the normalized target, and the stable error code; on audit-write failure log the failure and increment `audit_failure_count` instead of propagating (REQ-007) | REQ-005, REQ-006, REQ-007, AC-4, AC-5 | `call_tool` lines 169-192: the disabled path returns at line 173 and the `ExecutionContextError` path at line 178, both before `_audit_log` at line 183; `target` is the raw requested `repo` at line 188; `outcome` comes from `DispatchResult.outcome`, which yields only `ok` or `error` (`scripts/mcp_servers/dedup_gate.py` lines 71-74); no exception handling around the dispatch call (checked in Step 2) | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/cicd/test_cicd_audit.py` | Verified |
| `scripts/mcp_servers/audit.py` | Modify | Remove the duplicate `requested_target` assignment; record the CI/CD error-code vocabulary in the module docstring's Error Type Vocabulary section | REQ-006, REQ-008, AC-6 | Lines 124-125 and 128-129 assign `record["requested_target"]` twice with the same value; the docstring's vocabulary section (lines 8-20) lists only the `mdq` and `web_search` vocabularies (checked in Step 2) | `tests/mcp_servers/test_audit_redaction.py` | Verified |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Reverse the pinned HTTP 500 to Not Found expectation; add the 401, 403, 404, 409, 422, 429, 500, and 503 cases | REQ-001, AC-1 | `test_500_raises_not_found_error` at line 306 pins the catch-all mapping; the surrounding tests at lines 276-316 pin 404, 422, 401/403, and the 2xx no-raise case (checked in Step 2) | this file | Verified |
| `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Modify | Add the DNS, TLS, connection, and timeout cases and the bounded and redacted error-text cases | REQ-002, REQ-003, AC-2 | Lines 45 and 52 pin the parse-failure fallback; line 60 pins the 2xx pass-through; no transport case exists in the file (re-verified 20261127) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` | Modify | Add the 409 and 429 handler tests and update the exact-body assertions to the machine-readable shape | REQ-004, AC-3 | Lines 54-73 pin four status codes and exact `{"detail": ...}` bodies, the last test in the file (re-verified 20261127, file is 73 lines); no conflict or rate-limit handler test exists | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Add the new exception classes to the pinned hierarchy and the error-code vocabulary tests | REQ-001, REQ-006, AC-1, AC-5 | `test_exception_hierarchy` at lines 193-197 pins four classes only (checked in Step 2) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | Write the exactly-one-record tests for every result category first; update the health-details key pin only if UNK-02 adds the audit-failure counter to `/health` | REQ-005, REQ-007, AC-4 | `test_audit_record_keeps_session_and_request_context_in_order` (line 200) pins `len(records) == 1` at line 245 for the success path only; line 303 pins `set(body["details"]) == {"service", "dedup"}`; the disabled and validation paths carry no audit assertion (checked in Step 2) | this file | Verified |
| `tests/mcp_servers/cicd/test_cicd_audit.py` | Create | Exactly-once emission per category, redaction, absence of tokens and workflow input values, and audit-serialization failure behavior | REQ-005, REQ-006, REQ-007, AC-4, AC-5 | The file does not exist; `tests/mcp_servers/cicd/` has no audit test module, and the exactly-once behavior is pinned only for the helper itself in `tests/mcp_servers/test_audit_redaction.py` lines 40-85 (checked in Step 2) | this file | Verified |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Add the CI/CD error mapping table and correct the audit statement | REQ-009, AC-7 | Line 74 states that a disabled-tool rejection returns before the audit call and writes no record, which this Plan makes false; line 66 records only that records are written via `_audit_log()` with `server_key="cicd"`; the document has no error mapping section (checked in Step 2) | `uv run python tools/check_docs_structure.py` | Verified |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | State the exactly-one-event rule for the CI/CD server, the redaction rules, and the audit-failure policy decided by the owner (never propagate, log and count) | REQ-007, REQ-009, AC-4, AC-7 | Line 30 states the one-record rule for every server that writes the shared log, which the CI/CD server currently violates on the disabled and validation paths; line 58 states the exactly-once rule for web-search-mcp only; the Common Error Formats table (section at line 68) lists "Server error | 500" at line 75 with no per-server mapping (re-verified 20261127) | `uv run python tools/check_docs_structure.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure): one row per file; test and documentation
files carry their own rows; `Validation Status` is `Verified` for every row.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob pattern, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/audit.py` | `AuditEmission` and its `emit()` keyword contract, the record field order, and the redaction helpers; the class itself is not modified | REQ-005, REQ-006 |
| `scripts/mcp_servers/dedup_gate.py` | `DispatchResult` and its error-type taxonomy and `dedup_state` values, which the audit record reports | REQ-005 |
| `scripts/mcp_servers/dispatch.py` | The dispatch categories that produce `error_type` for unknown tool, validation, and dedup refusals | REQ-005, REQ-006 |
| `scripts/mcp_servers/server.py` | `extract_request_context` field order, which the audit correlation depends on | REQ-005 |
| `scripts/mcp_servers/cicd/cicd_service_guards.py` | `_assert_allowed_repo` and `_assert_allowed_workflow`, the authorization-rejection path that must be audited | REQ-005, AC-4 |
| `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` | Its own non-2xx mapping (`CicdUpstreamError` at line 164) and the `httpx.RequestError` catch at lines 93-94; the divergence from the main backend is recorded as UNK-03 | REQ-001, AC-1 |
| `scripts/mcp_servers/web_search/web_search_server.py` | The existing production use of `AuditEmission` from a `finally` block, the pattern this Plan follows | REQ-005 |
| `scripts/mcp_servers/git/git_server.py` | The never-propagate audit-failure pattern and its `audit_failure_count` counter (lines 183-199, 407), the pattern this Plan follows for the CI/CD server per the owner's decision | REQ-007 |
| `scripts/mcp_servers/github/github_service_security.py` | The raise-on-failure pattern (`GitHubAuditError`), the other existing policy | REQ-007 |
| `scripts/shared/write_outcome.py` | The write-outcome vocabulary that names `applied_audit_failed`, the case an audit write failure after an applied dispatch produces | REQ-007 |
| `scripts/shared/mcp_call_state_contract.py` | `CONTROL_ERROR_CODES` and `RECONCILE_OUTCOMES`, which this Plan does not extend | REQ-006 |
| `scripts/mcp_servers/health_response.py` | `make_health_response` and the details shape, only if UNK-02 exposes the audit-failure counter | REQ-007 |
| `tests/mcp_servers/conftest.py` | The `http_boundary` fixture the transport-failure tests use; the committed file at the evidence revision has 195 lines and defines `http_boundary` (re-verified 20261127), so the fixture is available (UNK-06 resolved) | REQ-002 |
| `tests/mcp_servers/test_audit_redaction.py` | The helper's pinned exactly-once and redaction behavior, which the new CI/CD test must not re-implement | REQ-005, REQ-006 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): GitHub 500 and 503 become upstream errors, not 404; 429 is a distinct error; 401, 403, 404, 409, and 422 keep appropriate semantics; DNS, TLS, connection, and timeout failures are upstream errors.
- `AC-2` (REQ-003): error text is within the declared maximum length, contains no token-shaped content, and the preserved `Retry-After` or reset value is present when upstream supplies it.
- `AC-3` (REQ-004): the handlers answer conflict at 409, rate limit at 429, and upstream at 502, and the body carries the stable error code.
- `AC-4` (REQ-005, REQ-007): every authenticated call emits exactly one audit event, including disabled and allowlist-rejected calls and exceptions, and an audit-write failure is logged and counted, not raised.
- `AC-5` (REQ-006): credentials, workflow input values, and raw upstream payloads are absent from audit records and from error text.
- `AC-6` (REQ-008): the duplicate assignment is gone and the record output for the other servers is unchanged.
- `AC-7` (REQ-009): the CI/CD document carries the error mapping table and the corrected audit statement, and the audit document carries the exactly-one-event rule and the redaction rules.

## Tests
- `REQ-001`/`REQ-002`/`REQ-003`: reverse the existing HTTP 500 to Not Found expectation first, then add 401, 403, 404, 409, 422, 429, 500, 503, DNS, TLS, and timeout cases in `tests/mcp_servers/cicd/test_cicd_mcp_service.py` and `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`; the transport cases use the shared `http_boundary` fixture, which is committed at the current evidence revision (UNK-06 resolved).
- `REQ-004`: 409 and 429 handler tests and the machine-readable body shape in `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`.
- `REQ-005`/`REQ-006`/`REQ-007`: exactly one record for every result category — success, disabled, unknown tool, validation, authorization, upstream, dedup, unexpected — plus audit-serialization failure, in `tests/mcp_servers/cicd/test_cicd_audit.py` and `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.
- `REQ-001`/`REQ-006`: exception hierarchy and error-code vocabulary tests in `tests/mcp_servers/cicd/test_cicd_models.py`.
- Full validation sequence per `rules/toolchain.md`: ruff, mypy, bandit, lint-imports, the full test suite, diff-cover, pre-commit.

## Documentation Impact
Yes. Per `docs/00_index.md`'s "Document References by Task" (MCP server spec domain), the
per-server document `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` is the target row for the
CI/CD error mapping table and the corrected audit statement (REQ-009); the audit-domain document
`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` is the target row for the exactly-one-event
rule, the redaction rules, and the audit-failure policy decided by the owner (never propagate,
log and count) (REQ-007, REQ-009).
The Agent-side audit log, the server application log, and the `mcp_tool_exec` event remain three
separate layers named in that document; this Plan does not merge the terms.

## Assumptions
- The CI/CD error-code vocabulary is a CI/CD-scoped frozenset in `scripts/mcp_servers/cicd/cicd_models.py`, following the lowercase-snake style the shared helper recommends for new servers. `scripts/shared/mcp_call_state_contract.py`'s `CONTROL_ERROR_CODES` is not extended, consistent with the decision recorded for mcpci002.
- `AuditEmission` already accepts `target`, `outcome`, `error_type`, and `detail`, so the shared class needs no change; the only shared-helper change is the duplicate assignment removal, which assigns the same value twice and changes no observable output for the other eight servers, so the Issue's stop-and-report condition is not triggered.
- The audit outcome vocabulary already includes `rejected` (`scripts/mcp_servers/audit.py` line 89, also line 156); `DispatchResult.outcome` yields only `ok` or `error`, so `call_tool()` classifies the rejected categories itself.
- The response body shape change (adding the error code and the preserved metadata) is a response-contract change, so the exact-body assertions in `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` are updated in the same release unit.
- The audit-write-failure policy for the CI/CD server is the never-propagate pattern (log the failure and increment `audit_failure_count`), decided by the owner on 20261127, matching `scripts/mcp_servers/git/git_server.py`; the raise-on-failure pattern of `scripts/mcp_servers/github/github_service_security.py` is the rejected alternative.
- The health-details key pin in `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` line 303 changes only if UNK-02 decides that the CI/CD server exposes the audit-failure counter in `/health`.
- Compatible overlap with mcpci001 on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci001 owns the strict request models, the hard maximum constants, the shared `owner/repo` normalization, the lifespan-owned client, and the health credential block; this Plan owns the exception types, the error-code vocabulary, the status mapping, and the audit emission. The health-details key pin in `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` is already being updated by mcpci001, so this Plan's change to that pin (UNK-02) is applied after it.
- Compatible overlap with mcpci002 on `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci002 owns the structured dispatch outcome and the reconciler registration, this Plan owns the error classification and the audit emission; in `cicd_server.py` mcpci002 touches the reconciler registration and this Plan touches `call_tool`.
- Compatible overlap with mcpci003 on `scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, and `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`: mcpci003 owns the log response model and the byte budget, this Plan owns the exception types and the error-code vocabulary; the two touch different symbols in the same files.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The documented audit-failure policy for the CI/CD server | No policy was recorded for cicd-mcp in `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`; the existing servers differ: `scripts/mcp_servers/file/write_server.py` and `scripts/mcp_servers/shell/shell_service.py` never propagate, `scripts/mcp_servers/github/github_service_security.py` raises `GitHubAuditError`, and `scripts/mcp_servers/cicd/cicd_server.py` propagates the failure from `_audit_log` | Resolved by the owner on 20261127: never propagate, log the failure and increment `audit_failure_count`, matching `scripts/mcp_servers/git/git_server.py` | False |
| UNK-02 | Whether the CI/CD `/health` details expose `audit_failure_count` | The pattern exists in `scripts/mcp_servers/git/git_server.py` line 407 and in `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` line 125, but `scripts/mcp_servers/cicd/cicd_server.py` reports only `service` and the dedup block | Decide at implementation; the counter itself exists per UNK-01's decision, so only its exposure in `/health` is open. If it is exposed, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` line 303 is updated in the same unit | False |
| UNK-03 | Whether the jobs-fetch path's non-2xx mapping should converge with the main backend's status mapping | `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` raises `CicdUpstreamError` for every non-2xx, including 404, pinned by `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py` line 14; the main backend answers 404 with `CicdNotFoundError` | Decide whether one mapping is required; if yes, the job backend becomes a target row | False |
| UNK-04 | The maximum length of the bounded upstream error text | No bound exists in `scripts/mcp_servers/cicd/` and no documented ceiling in the audit or MCP error documents | Decide at implementation as a module constant in `scripts/mcp_servers/cicd/cicd_models.py`; the test asserts the bound rather than a specific value | False |
| UNK-05 | mcpci001 is open: its plan has no `Completed` row | `plans/20261126-152931_mcpci001_cicd-credential-config-contract.md` is `Frozen` with all steps `Pending` | Complete mcpci001 before this Plan is implemented; the normalized target in the audit record depends on its normalization function | True |
| UNK-06 | The `http_boundary` fixture was not committed at the original evidence revision | `tests/mcp_servers/conftest.py` at 30c08e72260a had 141 lines and no `http_boundary`; the fixture is present at the current evidence revision (re-verified 20261127, 195 lines) | Resolved by re-verification on 20261127: the fixture is committed, so the transport cases use it | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Modify | Medium — the error mapping is read by the composite facade and by two test modules; the status change alters what the agent transport classifies as a transport fault | 0 | 1 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_models.py` | Modify | Medium — imported by six cicd modules and five test modules, and by the `agent-mcp-config-models` import-linter contract | 1 | 2 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/exception_handlers.py` | Modify | Low — one consumer, the CI/CD app; the body shape is a response-contract change | 0 | 3 | not applicable (rsynced) |
| `scripts/mcp_servers/cicd/cicd_server.py` | Modify | Medium — the endpoint reached by the agent transport and pinned by the endpoint test module | 3 | 3 | not applicable (rsynced) |
| `scripts/mcp_servers/audit.py` | Modify | Medium — imported by nine MCP servers and the agent audit path; the change is a duplicate assignment removal with no observable output change | 5 | 3 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Modify | Low | 0 | 2 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Modify | Low | 0 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` | Modify | Low | 0 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_models.py` | Modify | Low | 1 | 1 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Modify | Low | 5 | 2 | not applicable (rsynced) |
| `tests/mcp_servers/cicd/test_cicd_audit.py` | Create | Low — new file | 0 | N/A: new file | not applicable (rsynced) |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | Modify | Low | 3 | 2 | not applicable (rsynced) |
| `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Modify | Low | 4 | 2 | not applicable (rsynced) |

## Design
Path B analysis (four dimensions, `workflow-path-b.md`):

- **Architecture**: `uv run lint-imports` reports 6 contracts KEPT; `scripts/shared/` stays a leaf
  and no agent module imports MCP server config models, so adding exception types and a
  CI/CD-scoped vocabulary in `scripts/mcp_servers/cicd/cicd_models.py` breaks no contract. The
  import graph shows `scripts/mcp_servers/cicd/cicd_service_github_actions.py` importing
  `scripts.mcp_servers.cicd.cicd_service_defs` and `shared`, `scripts/mcp_servers/cicd/exception_handlers.py`
  importing only `fastapi` and the cicd models, and `scripts/mcp_servers/audit.py` importing only
  standard library plus `shared` — no new cross-layer edge is introduced. No cycle was found among
  the target modules.
- **Dependency graphing**: `scripts/mcp_servers/audit.py` is the widest consumer surface (nine server
  importers plus the agent audit path, 14 files total including tests); `scripts/mcp_servers/cicd/cicd_models.py`
  is the CI/CD hub; `scripts/mcp_servers/cicd/exception_handlers.py` has no production importer
  outside the CI/CD app. `pydeps` on `scripts/mcp_servers/audit.py` reports only `orjson` and
  `shared` as external dependencies. Blast radius is Medium for the shared helper, the backend, the
  models, and the endpoint, Low for the handler and the test modules.
- **Historical**: churn over 30 days is 0-5 commits per target file; bus factor 1-3. `scripts/mcp_servers/audit.py`
  and `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` are the most frequently changed files in
  the set, so the exactly-once rule and the record shape are contested surfaces.
- **Operational dependency inspection**: `uv run pip-audit` reports no finding for `orjson` and
  `httpx`, the packages the audit record and the transport path use. `uv run bandit` reports one
  Low-confidence `B105` at `scripts/mcp_servers/cicd/cicd_server.py` line 202 (`deps["github_token"] = "not_set"`,
  a health-report string, not a credential); `uv run vulture` reports no finding on the target files.
  Radon complexity: `_build_audit_record` C (13), `redact_url` B (10), every target function A.
  Port 8012 has no listener at the time of the check.

Consumer scan (`tools/scan_change_consumers.py --seed _check_response`, candidates only):
- `scripts/mcp_servers/cicd/cicd_service_github_actions.py` (definition and three call sites at lines
  131, 150, 180): target row.
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`:
  target rows.
- `tests/mcp_servers/cicd/test_service_github_actions_composite.py`: `not affected` — it pins delegation
  through the composite facade, not the status mapping.
- `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`: `not affected` — it does not call
  `_check_response`; its own mapping already raises `CicdUpstreamError`, and the remaining 404
  divergence is recorded as UNK-03.
- Consumer scan for `_audit_log` (14 files): nine server importers, the agent `tool_audit` path, and the
  test modules. Only `scripts/mcp_servers/cicd/cicd_server.py` and `scripts/mcp_servers/audit.py` are
  target rows; the other eight servers are `not affected` because the duplicate assignment removal
  changes no output. `scripts/mcp_servers/web_search/web_search_server.py` is `not affected` — it uses
  `AuditEmission` unchanged.

Predictable fallout check:
- Module size: every target file is below the 24576 B gate (largest production target
  `scripts/mcp_servers/audit.py` at 10267 B, largest test target `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
  at 28860 B, which the gate does not apply to); `not affected: no split row required`.
- Pinned counts: `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` pins `len(records) == 1` and the
  health-details key set, both target rows; `tests/mcp_servers/cicd/test_cicd_models.py` pins the exception
  hierarchy, a target row; `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` pins the tool
  inventory and the config shape, which this Plan does not change — `not affected`.
- Tool inventory: no tool is added or removed, so `tools/TOOL_DESCRIPTIONS.md` is not affected.
- Generated blocks: no generated-reference domain is touched.

Design decisions (Path B):
- **Status mapping as a table, not an if-chain**: `_check_response` is currently A(5) complexity and
  will gain three branches. Alternative rejected: adding three more `if` clauses, which pushes the
  function past the complexity convention; a status-to-(exception, error-code) mapping keeps the
  function at the same complexity and makes the table the single source the documentation mirrors.
- **Error-code home**: the CI/CD error codes are a CI/CD-scoped frozenset in
  `scripts/mcp_servers/cicd/cicd_models.py`. Alternative rejected: extending
  `scripts/shared/mcp_call_state_contract.py`'s `CONTROL_ERROR_CODES`, which is the dedup control
  vocabulary and is not an audit error-type vocabulary.
- **Redaction home**: the bounded error text is produced by a helper in the CI/CD backend.
  Alternative rejected: adding a shared text-redaction helper to `scripts/mcp_servers/audit.py`, which
  would change a module shared by nine servers for one server's need and trigger the Issue's
  stop-and-report condition.
- **Rate-limit exception type**: a genuine 429 status raises `CicdRateLimitError` at HTTP 429.
  Alternative rejected: keeping the current substring test inside `_raise_auth_error`, which reports a
  rate limit as 403 when the status is 429 and cannot carry `Retry-After`.
- **Audit emission seam**: one `AuditEmission` created at the start of `call_tool()` and emitted from a
  `finally` block, following `scripts/mcp_servers/web_search/web_search_server.py`. Alternative rejected:
  moving `_audit_log` calls into each early-return branch, which duplicates the record contract and
  cannot cover an exception raised by the handler.
- **Transport consequence**: mapping 5xx to 502 makes the agent transport treat the response as a
  transport fault for side-effecting tools (fail-closed, ADR-004) instead of a tool-level result, which
  is the intended recovery behavior; the rule in `docs/22_mcp/mcp_03_03_transport-and-health.md` is
  unchanged, so that document is not a target row.

## Implementation steps

1. **Phase 1: Error-mapping tests first**
   - [ ] Reverse the pinned HTTP 500 to Not Found expectation and add the 401, 403, 404, 409, 422, 429, 500, 503, DNS, TLS, and timeout cases before any code change (REQ-001, REQ-002; `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`)
   - [ ] Add the 409 and 429 handler tests and the machine-readable body shape (REQ-004; `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`)
2. **Phase 2: Audit-coverage tests first**
   - [ ] Write the exactly-one-record tests for every result category and the audit-serialization failure case (REQ-005, REQ-006, REQ-007; `tests/mcp_servers/cicd/test_cicd_audit.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`)
   - [ ] Write the audit-write-failure test asserting the log-and-count behavior rather than a raised exception (REQ-007; `tests/mcp_servers/cicd/test_cicd_audit.py`)
3. **Phase 3: Error vocabulary and exception types**
   - [ ] Add `CicdConflictError`, `CicdRateLimitError`, the CI/CD error-code frozenset, the exception-to-code mapping, and the maximum error-text constant (REQ-001, REQ-003, REQ-004, REQ-006; `scripts/mcp_servers/cicd/cicd_models.py`)
   - [ ] Add the hierarchy and vocabulary tests (REQ-001, REQ-006; `tests/mcp_servers/cicd/test_cicd_models.py`)
4. **Phase 4: Status and transport mapping in the backend**
   - [ ] Replace the catch-all with the status-to-(exception, error-code) mapping, wrap the request so transport failures become upstream errors, bound and redact the message, and carry `Retry-After` and reset metadata (REQ-001, REQ-002, REQ-003; `scripts/mcp_servers/cicd/cicd_service_github_actions.py`)
5. **Phase 5: Handler mapping**
   - [ ] Register the 409 and 429 handlers and render the error code and the preserved metadata in the body (REQ-004; `scripts/mcp_servers/cicd/exception_handlers.py`)
6. **Phase 6: Exactly-once audit emission and the shared helper fix**
   - [ ] `call_tool()` emits exactly one record through `AuditEmission` from a `finally` block, classifies the outcome, uses the normalized target and the stable error code, and logs an audit-write failure and increments `audit_failure_count` instead of propagating it (REQ-005, REQ-006, REQ-007; `scripts/mcp_servers/cicd/cicd_server.py`)
   - [ ] Remove the duplicate `requested_target` assignment and record the CI/CD vocabulary in the docstring (REQ-006, REQ-008; `scripts/mcp_servers/audit.py`)
7. **Phase 7: Documentation**
   - [ ] Add the CI/CD error mapping table and correct the audit statement (REQ-009; `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`)
   - [ ] State the exactly-one-event rule, the redaction rules, and the audit-failure policy (REQ-007, REQ-009; `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`)
8. **Phase 8: Deployment & Verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md` and hand off to `skills/deploy/SKILL.md`; the prerequisite is that the change is committed and pushed first, and deploying is the user's decision (REQ-001..REQ-009; all target files)

### Release units
**Unit**: error mapping contract | **Phases**: 1, 3, 4, 5 | **Reason**: the reversed 500 expectation and the new status, transport, and handler tests fail until the exception types, the backend mapping, and the handler registrations land in the same commit, so no phase in the set can be validated alone.

**Unit**: exactly-one audit event | **Phases**: 2, 6 | **Reason**: the per-category and serialization-failure tests fail until `call_tool()` emits through `AuditEmission` and the duplicate assignment is removed; the health-details pin changes only if UNK-02 exposes the audit-failure counter.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | Unit — fake transport and the `http_boundary` fixture, no live GitHub call | `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | 500 and 503 raise the upstream error, 429 and 409 raise their own types, transport failures raise the upstream error, error text is within the bound and contains no token-shaped content |
| `scripts/mcp_servers/cicd/cicd_models.py` | Unit — exception hierarchy and error-code vocabulary | `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py` | The new classes and the frozenset are pinned |
| `scripts/mcp_servers/cicd/exception_handlers.py` | Unit — isolated FastAPI app | `uv run pytest tests/mcp_servers/cicd/test_cicd_exception_handlers.py` | 409, 429, and 502 with the machine-readable body |
| `scripts/mcp_servers/cicd/cicd_server.py` | Integration — TestClient over the real app, every result category | `uv run pytest tests/mcp_servers/cicd/test_cicd_audit.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | Exactly one record per authenticated call, including disabled, validation, unknown tool, dedup refusal, and exceptions; no token or workflow input value |
| `scripts/mcp_servers/audit.py` | Unit — shared helper behavior for all servers | `uv run pytest tests/mcp_servers/test_audit_redaction.py` | Exactly-once and redaction behavior unchanged; the record output is identical after the duplicate removal |
| All target files | Full sequence | `uv run python tools/run_validation_gates.py` | ruff, mypy, bandit, lint-imports, the full suite, diff-cover ≥ 90%, pre-commit pass |
| `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | Structure check | `uv run python tools/check_docs_structure.py` | No findings |

## Risks
- **Risk**: the CI/CD audit-failure policy was undecided at the time the Issue was written, so AC-4's failure case had no target behavior → **Mitigation**: decided by the owner on 20261127 as the never-propagate pattern (log and count); the test asserts the log-and-count behavior rather than a raised exception.
- **Risk**: the shared audit helper is imported by nine servers, so a change there can affect unrelated servers → **Mitigation**: the change is limited to a duplicate assignment of the same value, which changes no output; the Issue's stop-and-report condition is checked before any other edit to that file.
- **Risk**: reversing the 500 expectation changes what the agent transport classifies, so side-effecting CI/CD calls become fail-closed transport faults where they previously looked like tool errors → **Mitigation**: this is the intended behavior; the transport rule is unchanged and the health-registry consequence is recorded in the Design section.
- **Risk**: the response body shape change breaks the exact-body assertions in `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` → **Mitigation**: the tests are updated in the same release unit as the handler registration.
- **Risk**: the health-details key pin in `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` line 303 breaks if an audit-failure counter is added → **Mitigation**: the counter is exposed in `/health` only if UNK-02 decides it, and the pin is updated in the same unit.
- **Risk**: the jobs-fetch path keeps its own mapping, so the same status can produce different exception types across the two backends → **Mitigation**: recorded as UNK-03; the existing test pins the current behavior and the divergence is documented rather than silently changed.
- **Risk**: mcpci001 may not be implemented when this Plan is consumed, so the normalized target it provides is absent → **Mitigation**: recorded as the blocking dependency UNK-05; implementation stops until it completes.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Error-mapping tests first (`tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`, `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`) | Completed | 20261128 | 20261128 | procedures 01 and 03; 403 substring pin rewritten |
| 2 | Audit-coverage tests first (`tests/mcp_servers/cicd/test_cicd_audit.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`) | Completed | 20261128 | 20261128 | procedure 04; health-details pins updated for the exposed counter (UNK-02 decided) |
| 3 | Error vocabulary and exception types (`scripts/mcp_servers/cicd/cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_models.py`) | Completed | 20261128 | 20261128 | procedure 02; UNK-04 decided as `MAX_ERROR_TEXT_LENGTH = 500`; `unexpected_error` added for the audit category |
| 4 | Status and transport mapping in the backend (`scripts/mcp_servers/cicd/cicd_service_github_actions.py`) | Completed | 20261128 | 20261128 | procedure 01; transport wrap scoped to `get_workflow_runs` and `get_workflow_status`; UNK-06 fixture `http_boundary` used |
| 5 | Handler mapping (`scripts/mcp_servers/cicd/exception_handlers.py`) | Completed | 20261128 | 20261128 | procedure 03; exact-body assertions moved to the machine-readable shape |
| 6 | Exactly-once audit emission and the shared helper fix (`scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/audit.py`) | Completed | 20261128 | 20261128 | procedures 04 and 05; UNK-05 resolved (mcpci001 landed); never-propagate policy applied |
| 7 | Documentation (`docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`) | Completed | 20261128 | 20261128 | procedures 12 and 13; doc checkers pass |
| 8 | Deployment & Verification | Pending | — | — | not executed: deployment was not requested for this batch |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/done/20261127-152110_01_scripts_mcp_servers_cicd_cicd_service_github_actions.py.md` | 1, 4 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_02_scripts_mcp_servers_cicd_cicd_models.py.md` | 3 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_03_scripts_mcp_servers_cicd_exception_handlers.py.md` | 5 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_04_scripts_mcp_servers_cicd_cicd_server.py.md` | 2, 6 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_05_scripts_mcp_servers_audit.py.md` | 6 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_12_docs_22_mcp_mcp_04_03_rag-pipeline-and-cicd.md.md` | 7 | Procedure | Completed | — | 20261128 |
| `implementations/done/20261127-152110_13_docs_22_mcp_mcp_02_03_audit-logging-and-errors.md.md` | 7 | Procedure | Completed | — | 20261128 |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261127-070305
- **Evidence revision**: 431d80ee328ed91f26c43f27638d21a5b6375d3c
  (re-verified 20261127 at this revision; the 8 files changed since 30c08e72260a were reviewed and
  the row claims were corrected to the current line numbers — `tests/mcp_servers/conftest.py` now has
  195 lines and defines `http_boundary` (UNK-06 resolved), and the audit-document line citations were
  updated. The source issue is archived at `issues/done/`, `TOOL_DESCRIPTIONS.md` has no cicd entry
  change, and the `docs/00_index.md` task mapping still names both documentation rows. The 121 related
  tests pass at HEAD. `check_evidence_freshness.py record` could not write this revision because the
  mcpci001 plan dependency is uncommitted.)
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/exception_handlers.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/audit.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`, `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`, `tests/mcp_servers/cicd/test_cicd_models.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/cicd/test_cicd_audit.py`, `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes; Acceptance Criteria | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 4 | AC-1 | `tests/mcp_servers/cicd/test_cicd_mcp_service.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes | `scripts/mcp_servers/cicd/cicd_models.py` | 3 | AC-1 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 4 | AC-1 | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes; Unresolved Questions (UNK-04) | `scripts/mcp_servers/cicd/cicd_service_github_actions.py` | 4 | AC-2 | `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes | `scripts/mcp_servers/cicd/cicd_models.py` | 3 | AC-2 | `tests/mcp_servers/cicd/test_cicd_models.py` | Needs confirmation |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/exception_handlers.py` | 5 | AC-3 | `tests/mcp_servers/cicd/test_cicd_exception_handlers.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes | `scripts/mcp_servers/cicd/cicd_models.py` | 3 | AC-3 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes; Acceptance Criteria | `scripts/mcp_servers/cicd/cicd_server.py` | 6 | AC-4 | `tests/mcp_servers/cicd/test_cicd_audit.py` | Confirmed by repository evidence |
| REQ-005 | Problem; Testing Expectations | `tests/mcp_servers/cicd/test_cicd_server_endpoints.py` | 2 | AC-4 | this file | Confirmed by repository evidence |
| REQ-006 | Required Changes; Constraints | `scripts/mcp_servers/cicd/cicd_models.py` | 3 | AC-5 | `tests/mcp_servers/cicd/test_cicd_models.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; Dependencies (UNK-05) | `scripts/mcp_servers/cicd/cicd_server.py` | 6 | AC-5 | `tests/mcp_servers/cicd/test_cicd_audit.py` | Needs confirmation |
| REQ-007 | Required Changes; Unresolved Questions (UNK-01, resolved by the owner on 20261127) | `scripts/mcp_servers/cicd/cicd_server.py` | 6 | AC-4 | `tests/mcp_servers/cicd/test_cicd_audit.py` | Explicit in issue |
| REQ-008 | Required Changes | `scripts/mcp_servers/audit.py` | 6 | AC-6 | `tests/mcp_servers/test_audit_redaction.py` | Confirmed by repository evidence |
| REQ-009 | Documentation Impact | `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` | 7 | AC-7 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |
| REQ-009 | Documentation Impact | `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` | 7 | AC-7 | `uv run python tools/check_docs_structure.py` | Confirmed by repository evidence |