# Implementation Procedure — scripts/mcp_servers/cicd/cicd_server.py

## Goal

Emit exactly one correlated audit record for every authenticated CI/CD tool call from a `finally` block,
classify the outcome, use the normalized target and the stable error code, and log an audit-write failure
and count it instead of propagating it.

## Scope
**Release unit**: exactly-one audit event

Requirements implemented: REQ-005 (one record per authenticated call through `AuditEmission`), REQ-006
(normalized target and stable error code, no token or workflow input value), REQ-007 (audit-write failure
never propagates). Acceptance criteria: AC-4, AC-5.

## Assumptions
- The audit-failure policy is the never-propagate pattern, decided by the owner on 20261127: log the
  failure and increment `audit_failure_count`, matching `scripts/mcp_servers/git/git_server.py`
  (Plan Assumption, UNK-01 resolved). The raise-on-failure pattern of
  `scripts/mcp_servers/github/github_service_security.py` is the rejected alternative.
- `AuditEmission` already accepts `target`, `outcome`, `error_type`, and `detail`, so the shared class is
  not changed here (Plan Assumption).
- The normalized `owner/repo` target is the value mcpci001's shared normalization function produces;
  implementation stops until that plan completes (blocking dependency UNK-05).
- The outcome vocabulary already includes rejected (`scripts/mcp_servers/audit.py` line 89), while
  `DispatchResult.outcome` yields only ok or error, so `call_tool()` classifies the rejected categories
  itself (Plan Assumption).
- The health-details key pin in the companion test file changes only if UNK-02 decides that the CI/CD
  server exposes `audit_failure_count` in `/health`; the counter itself exists per UNK-01. Decided at
  implementation: the counter is exposed, matching the pattern the owner's decision referenced.

## Design decisions
- **Audit emission seam**: one `AuditEmission` created at the start of `call_tool()` and emitted from a
  `finally` block, following `scripts/mcp_servers/web_search/web_search_server.py` (Plan Design decision).
- The error code is the CI/CD vocabulary value from the models row, not `type(exc).__name__` (Plan
  Design decision, Error-code home).

## Alternatives considered
- Moving `_audit_log` calls into each early-return branch: rejected — it duplicates the record contract
  and cannot cover an exception raised by the handler (Plan Design decision).
- Propagating an audit-write failure: rejected — the owner's decision is the never-propagate pattern, so
  incident review keeps the record path alive.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_server.py`

### Procedure
- Create one `AuditEmission` at the start of `call_tool()` (lines 169-192) and emit from a `finally`
  block so the disabled path (line 173), the `ExecutionContextError` path (line 178), and an exception
  raised by the handler each produce exactly one record.
- Classify the outcome as ok, error, or rejected from the dispatch category, and carry the stable error
  code from the models row.
- Use the normalized `owner/repo` target instead of the raw requested `repo` at line 188.
- On audit-write failure, log the failure and increment `audit_failure_count`; do not raise (REQ-007).

### Method
- Lines 169-192 re-verified at revision 431d80ee328ed91f26c43f27638d21a5b6375d3c: `_audit_log` is called
  after the dispatch at line 183 with no exception handling around the dispatch call, so the `finally`
  block replaces that single call rather than adding a second record path.
- Step 3b correction: at revision da8097e74 `call_tool()` is at lines 286-315 and `/health` at line 317;
  the 169-192 citation belongs to the older revision. The `finally` block replaces the single `_audit_log`
  call at line 304.
- Step 3b correction, outcome classification: `DispatchResult.outcome` yields only `ok` or `error`, so the
  server classifies the result itself. The categories that are a failure during the tool's work are
  `upstream_error`, `unexpected_error`, and `dedup_store_error`; every other error result is a refusal made
  before the tool's work and is `rejected`. The set is a module-level frozenset in this file.
- Step 3b correction, target: `canonical_repo_key()` from `scripts/shared/repo_identity.py` (mcpci001,
  UNK-05 resolved). A slug that cannot be normalized is reported as requested, never rewritten, and a call
  refused before its arguments are read has no target and reports `"-"`.
- Step 3b correction, counter: `_audit_failure_count` is module-level and guarded by a `threading.Lock`
  around the read-modify-write, the same narrow scope `scripts/mcp_servers/git/git_server.py` uses.
- `extract_request_context` field order is read from `scripts/mcp_servers/server.py` (reference) and stays
  the correlation source.

### Details
- The record never carries a token, a workflow input value, or raw upstream payload text (REQ-006, AC-5).
- The dispatch categories for unknown tool, validation, and dedup refusals come from
  `scripts/mcp_servers/dispatch.py` and `scripts/mcp_servers/dedup_gate.py` (reference); the
  authorization-rejection path is `scripts/mcp_servers/cicd/cicd_service_guards.py` (reference).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`
  - Procedure: write the exactly-one-record tests for every result category first (Phase 2); today only
    the success path is pinned (`len(records) == 1` at line 245 inside the test starting at line 200).
    Update the health-details key pin at line 303 only if UNK-02 exposes the counter.
  - Step 3b correction: the pin is at lines 292 and 335 at revision da8097e74, not 303. UNK-02 is decided
    at implementation: the counter is exposed in `/health` details, following the pattern the owner's
    never-propagate decision referenced, so both pins are updated in the same unit. The value is
    process-global, so the pin asserts the key and its type rather than a fixed count.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.
- `tests/mcp_servers/cicd/test_cicd_audit.py` (new)
  - Procedure: exactly-once emission per category, redaction, absence of tokens and workflow input values,
    and the audit-serialization failure case asserting the log-and-count behavior rather than a raised
    exception. Do not re-implement the helper's pinned behavior in
    `tests/mcp_servers/test_audit_redaction.py` lines 40-85 (reference).
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_audit.py`.

## Compatibility considerations
- The response shape of `call_tool()` is unchanged; only the audit record gains the normalized target and
  the error code, so the endpoint contract pins stay (Plan Assumption).

## Security considerations
- No credential and no workflow input value in the record (REQ-006, AC-5).

## Rollback considerations
- N/A: revert the commit (release unit: validated with the shared helper row).

## Validation plan
- Integration: TestClient over the real app, every result category —
  `uv run pytest tests/mcp_servers/cicd/test_cicd_audit.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Every authenticated call emits exactly one audit event, including disabled and allowlist-rejected calls
  and exceptions, and an audit-write failure is logged and counted rather than raised (AC-4); credentials,
  workflow input values, and raw upstream payloads are absent (AC-5).

## Out of Scope
- The duplicate `requested_target` assignment and the docstring vocabulary
  (`scripts/mcp_servers/audit.py` row); the error-code vocabulary (`scripts/mcp_servers/cicd/cicd_models.py`
  row); the reconciler registration in this file, which is mcpci002's work.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `AuditEmission` emitted from `finally`; outcome classified by `_FAILURE_CATEGORIES`; target from `canonical_repo_key()`; never-propagate counter `_audit_failure_count` under a lock; `/health` details expose the counter (UNK-02) |
| 2 | Add or update tests per Validation plan (companion test files) | Completed | 20261128 | 20261128 | `test_cicd_audit.py` (new): one record per category, normalized target, unresolvable slug reported as requested, no token and no workflow input value, audit-write failure logged and counted; `test_cicd_server_endpoints.py`: disabled-path and validation-path emission tests plus the two health-details pins updated |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128 | 20261128 | `uv run pytest tests/mcp_servers/cicd/test_cicd_audit.py tests/mcp_servers/cicd/test_cicd_server_endpoints.py` passes (58 with the reference file); gates all Pass; diff coverage 100% for this file |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

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
- **Requirement ID**: REQ-005, REQ-006, REQ-007 (exactly-once audit emission, normalized target, never-propagate policy)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `scripts/mcp_servers/cicd/cicd_server.py`, `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/cicd/test_cicd_audit.py`
