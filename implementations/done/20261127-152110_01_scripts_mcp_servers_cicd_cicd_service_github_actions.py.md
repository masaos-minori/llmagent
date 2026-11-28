# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_github_actions.py

## Goal

Replace the catch-all status mapping with a status-to-(exception, error-code) table, make transport
failures upstream errors, and bound and redact the upstream error text while preserving `Retry-After`
and the rate-limit reset value as structured fields.

## Scope
**Release unit**: error mapping contract

Requirements implemented: REQ-001 (truthful non-2xx mapping), REQ-002 (transport failures as upstream
errors), REQ-003 (bounded, redacted error text with preserved metadata). Acceptance criteria: AC-1, AC-2.

## Assumptions
- The exception types, the error-code vocabulary, and the maximum error-text length are defined by the
  `scripts/mcp_servers/cicd/cicd_models.py` row and imported here; this document does not define them.
- The maximum length is the module constant decided at implementation (UNK-04); the test asserts the
  bound rather than a specific value.
- The jobs-fetch path keeps its own mapping, where every non-2xx raises `CicdUpstreamError` including 404
  (`scripts/mcp_servers/cicd/cicd_service_github_actions_job.py` line 305, reference at the current
  revision); the divergence is recorded as UNK-03 and is not changed here.
- The transport cases use the shared `http_boundary` fixture in `tests/mcp_servers/conftest.py`
  (reference), which is committed at the evidence revision (UNK-06 resolved).

## Design decisions
- Status mapping as a table, not an if-chain (Plan Design decision): `_check_response` is A(5) today and
  gains three branches, so the table keeps the complexity convention and becomes the single source the
  documentation mirrors.
- Redaction home: the bounded error text is produced by a helper in this module (Plan Design decision);
  no shared text-redaction helper is added to `scripts/mcp_servers/audit.py`.
- 429 becomes a status branch. The preserved metadata is exception fields, not text inside the message.

## Alternatives considered
- Adding three more `if` clauses to `_check_response`: rejected — it pushes the function past the
  complexity convention and leaves no table for the documentation to mirror.
- Keeping the substring test inside `_raise_auth_error` as the rate-limit path: rejected — it reports a
  genuine 429 status as 403 and cannot carry `Retry-After`.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_github_actions.py`

### Procedure
- Replace the catch-all at lines 172-176 with the status-to-(exception, error-code) mapping: 5xx to
  `CicdUpstreamError`, 429 to `CicdRateLimitError` (new), 409 to `CicdConflictError` (new). Keep the
  existing 404, 422, and 401/403 branches at lines 165-166, 167-169, and 170-171 unchanged. The remaining
  non-2xx statuses (e.g. 400) fall through the table to `CicdUpstreamError` rather than the current
  `CicdNotFoundError` catch-all, which is the truthful mapping REQ-001 asks for; no test pins those
  statuses today.
- Wrap the request so DNS, TLS, connection, and timeout failures raise `CicdUpstreamError` (REQ-002) at
  the two call sites that propagate raw transport exceptions today (`get_workflow_runs` line 362,
  `get_workflow_status` line 392); raw transport exception text never appears in the error. The dispatch
  POST and `_search_runs` keep their existing pinned behaviors (see Method).
- Bound the message returned by `_parse_error_message` (lines 154-161, which returns the upstream value
  verbatim) at the models row's maximum (`MAX_ERROR_TEXT_LENGTH`), and redact token-shaped content.
- Carry `Retry-After` and `X-RateLimit-Reset` as structured fields on the raised exception.

### Method
- Re-verified at revision da8097e74: `_check_response` is at lines 163-176 and `_parse_error_message` at
  lines 154-161. The module already handles `httpx.HTTPError` at two call sites — the dispatch POST
  (line 259, returns `DispatchOutcome(state=OUTCOME_UNKNOWN)`, pinned by
  `test_response_loss_returns_outcome_unknown` in the companion test file) and `_search_runs` (line 309,
  returns `None`) — and those behaviors are mcpci002's work, out of this Plan's scope. The transport wrap
  that raises `CicdUpstreamError` is therefore added only at the two call sites that propagate raw
  transport exceptions today: `get_workflow_runs` (line 362) and `get_workflow_status` (line 392), not
  inside `_check_response` and not at the dispatch or `_search_runs` sites.
- `_raise_auth_error` keeps its 401/403 behavior; only the rate-limit substring test is retired as the
  classification source.

### Details
- The error code carried by the mapping is the models row's vocabulary value for the raised type
  (REQ-004), so the handler row can render it without re-deriving the status.

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
  - Procedure: reverse `test_500_raises_not_found_error` at line 602 first (Phase 1), then add the 401,
    403, 404, 409, 422, 429, 500, and 503 cases. Keep the 2xx pass-through pin at line 609.
    `test_403_rate_limit_includes_reset_time` at lines 575-585 pins the substring classification that is
    retired as the classification source: the 403 path becomes the plain `Access denied: <message>` form,
    so this test is updated in the same cycle to assert that form, and the reset-metadata assertion moves
    to the 429 status branch as structured fields.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.
- `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`
  - Procedure: add the DNS, TLS, connection, and timeout cases for the two wrapped call sites, which the
    file has none of today, and the bounded and redacted error-text cases asserting the bound rather than
    a specific value. Keep the parse-failure fallback pins at lines 122 and 129 and the dispatch
    response-loss pin at line 167 (`test_response_loss_returns_outcome_unknown`), which the wrap must not
    change.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`.

## Compatibility considerations
- Mapping 5xx to 502 makes the agent transport treat the response as a transport fault for
  side-effecting tools (fail-closed, ADR-004) instead of a tool-level result; the transport rule in
  `docs/22_mcp/mcp_03_03_transport-and-health.md` is unchanged (Plan Design decision).

## Security considerations
- Error text contains no token-shaped content (REQ-003, AC-5); no credential is added to the message.

## Rollback considerations
- N/A: revert the commit (release unit: validated with the models and handler rows).

## Validation plan
- Unit: fake transport and the `http_boundary` fixture, no live GitHub call —
  `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- GitHub 500 and 503 raise the upstream error rather than `CicdNotFoundError`, 429 and 409 raise their own
  types, transport failures raise the upstream error, and the error text is within the bound with the
  preserved metadata present when upstream supplies it (AC-1, AC-2).

## Out of Scope
- The exception types and the error-code vocabulary (`scripts/mcp_servers/cicd/cicd_models.py` row); the
  handler registrations (`scripts/mcp_servers/cicd/exception_handlers.py` row); the jobs-fetch mapping
  (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | companion tests are written first (Plan Phase 1); Step 3b correction: line citations updated to revision da8097e74, transport wrap scoped to the two call sites that propagate raw transport exceptions (dispatch POST and `_search_runs` keep their pinned behaviors), remaining non-2xx statuses map to `CicdUpstreamError`, `test_403_rate_limit_includes_reset_time` pin updated |
| 2 | Add or update tests per Validation plan (companion test files) | Completed | 20261128 | 20261128 | `test_cicd_mcp_service.py`: 500/503 reversed to `CicdUpstreamError`, 401/409/429 structured-field cases added, 403 pin rewritten as `test_403_rate_limit_message_raises_plain_auth_error`; `test_service_github_actions_error_edges.py`: transport-failure cases for the two wrapped call sites plus bounded and redacted cases asserting the bound |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128 | 20261128 | `run_validation_gates.py` all Pass; mypy clean (632 files); bandit shows only the pre-existing Low B105 at `cicd_server.py`; lint-imports 6 contracts kept; diff coverage 100% for the unit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs rows |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Allowed red state (release unit, batch mode): targeted tests fail at collection with `ImportError: MAX_ERROR_TEXT_LENGTH` / `CicdConflictError` / `CicdRateLimitError`, attributed to symbols the models row (member seq 02) creates | Yes — resolved when member 02 lands | 20261128 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (status and transport mapping, bounded error text)
- **Source issue**: issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-070305_mcpci004_cicd-error-audit-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-152110
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`, `tests/mcp_servers/cicd/test_service_github_actions_error_edges.py`