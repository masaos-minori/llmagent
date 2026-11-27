# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_github_actions_job.py

## Goal

Fetch each job log through the shared bounded streaming helper under independent raw and
decompressed limits, enforce one exact final-output byte budget, truncate at UTF-8 character
boundaries, and report per-job status instead of failure text embedded in the output.

## Scope
**Release unit**: structured log result contract

Requirements implemented: REQ-001 (the shared helper with the trusted-host policy and the redirect
maximum), REQ-002 (independent raw and decompressed bounds before full buffering), REQ-003 (exact
final byte budget including headers and markers, UTF-8-safe truncation), REQ-004 (per-job status,
included bytes, error code, truncation state), REQ-005 (totals), REQ-006 (output never exceeds the
budget, no raw upstream text). Acceptance criteria: AC-1, AC-2, AC-3, AC-4.

## Assumptions
- The response model and the limit constants are defined by the `cicd_models.py` row and imported
  here; this document does not define them.
- The helper owns its own short-lived client per call; only the jobs API call keeps the injected
  client from mcpci001 (Plan Design decision, Client seam). The shared client's private transport is
  not reached.
- `text/plain` is the only allowed content type for the job log endpoint (Plan Assumption).
- The trusted GitHub log host list and the redirect maximum are decided from GitHub documentation or
  observed behavior; if the list cannot be determined, stop and report (UNK-01, Phase 1).

## Design decisions
- `FetchLimits.returned_bytes` is carried by the helper and not enforced there, so the exact
  final-output budget — headers, log bytes, and the truncation marker — is enforced here (Plan Design
  decision, Byte-budget ownership).
- Per-job failure is an error code in the response model, not text appended to the output (Plan Design
  decision, Error carrier).
- Truncation cuts at a character boundary of the bounded decoder output, not a byte slice decoded with
  `errors="replace"` (Plan Design decision, UTF-8 boundary).

## Alternatives considered
- Relying on the helper's `returned_bytes` limit: rejected — it would leave the header and the marker
  outside the budget and keep the current overrun.
- Keeping the string form of failure: rejected — it cannot be distinguished from log content and leaks
  raw transport exception text.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`

### Procedure
- Replace the `self._http.get(..., follow_redirects=True)` call at lines 82-86 with
  `fetch_bounded` from `scripts/mcp_servers/bounded_fetch.py`, passing `FetchLimits` built from the raw
  and decompressed constants, the trusted-host policy, and the redirect maximum.
- Apply the host policy through `resolve_public_addresses` from `scripts/mcp_servers/address_policy.py`
  (reference); `AddressRejectedError` becomes a per-job error code, not output text.
- Enforce the exact final byte budget in `_append_job_output` (lines 169-181): a job is not appended
  when its header does not fit; the marker bytes are counted inside the budget.
- Replace the `errors="replace"` truncation at lines 117-127 with UTF-8 character-boundary truncation.
- Record per-job status, included bytes, error code, and truncation state in the response model; remove
  the `(log fetch failed: HTTP {status})` and `(log fetch error: {e})` output text at lines 91 and 102.
- Build the totals: jobs, included jobs, failed jobs, downloaded bytes, visible bytes, truncation reason.

### Method
- Lines 82-104 currently download the full response and embed failure text (re-verified 20261127); the
  jobs API call keeps using the injected client, only the log download changes to the helper.
- Reuse `_GITHUB_API_BASE`, `_MAX_JOBS_FOR_LOGS`, and `build_auth_headers` from
  `scripts/mcp_servers/cicd/cicd_service_defs.py` (reference).

### Details
- Raw transport exception text never appears in the result (REQ-004); the warning log keeps the job id
  and the error code, not the token.

### Companion test files
- `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`
  - Procedure: write the byte-budget, header-only exhaustion, untrusted-redirect, compressed and
    chunked, and UTF-8-boundary tests before any code change (Phase 1); then replace the pins at lines
    48 and 72 (embedded failure strings) and line 103 (`result_bytes >= max_bytes`, which allows
    overrun) with the exact-budget contract. Keep the non-2xx fail-fast pins on the jobs path.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`.

## Compatibility considerations
- The handler contract stays `-> str` (the result is JSON-serialized), so `dispatch_tool` and the audit
  `outcome` mapping are unchanged (Plan Assumption).

## Security considerations
- No token and no raw upstream text in the result (REQ-006); redirects outside the trusted hosts are
  rejected (AC-3).

## Rollback considerations
- N/A: revert the commit; the release unit is validated with the Protocol, facade, and handler rows.

## Validation plan
- Unit: fake transport and resolver, no live GitHub call —
  `uv run pytest tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Raw and decompressed bytes are bounded before buffering (AC-1); the final output never exceeds the
  budget and no replacement characters appear (AC-2); untrusted redirects are rejected (AC-3);
  complete, partial, and total failure are machine-distinguishable (AC-4).

## Out of Scope
- The response model and constants (`cicd_models.py` row); the helper itself, already implemented by
  mcpws001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | characterization tests first (Plan Phase 1) |
| 2 | Add or update tests per Validation plan (companion test file) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs row |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006 (bounded streaming, exact budget, per-job status, totals)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions_job.py`, `tests/mcp_servers/cicd/test_mcp_cicd_edge_cases.py`
