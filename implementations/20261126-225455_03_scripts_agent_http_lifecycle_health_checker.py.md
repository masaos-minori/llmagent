## Goal

Redact URLs before they are logged by the health checker, and redact before truncating
(REQ-003 — internal logs pass the common masker, no credential-bearing URLs).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The three debug call sites that log `target_url` (lines 296, 298-302, 305) are the only URL
  emissions in this module.
- No overlap with a sibling Plan on this file.

## Design decisions

- Use `redact_url` from `scripts/agent/secrets_masker.py` (document 01) at the logging boundary
  rather than changing `target_url` itself, so the request still uses the full URL.

## Alternatives considered

- Redacting inside `httpx` request construction — rejected: the request needs the real URL, only
  the log line must be safe.

## Implementation
### Target file
`scripts/agent/http_lifecycle_health_checker.py`
### Procedure
- Wrap each logged URL with `redact_url` (new helper, document 01) in the three debug statements.
- Apply redaction before any truncation of the logged value.
### Method
- Introduce one local `logged_url = redact_url(target_url)` used by the pass, status, and failure
  log lines, so the request path is untouched.
### Details
- `bandit` already reports a pre-existing Low `B404` (subprocess import) in this module; no new
  finding is expected.

### Companion test files
- `tests/agent/test_http_lifecycle_health_check.py`
  - Procedure: assert the captured log records contain no userinfo, query, or fragment.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_health_check.py`.

## Compatibility considerations

- Log text changes only; no public contract change.

## Security considerations

- Internal logs are the disclosure surface for REQ-003 (AC-2).

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit: redacted log records — `uv run pytest tests/agent/test_http_lifecycle_health_check.py`.
- Sequence: format → lint → type → arch → security.

## Completion criteria

- Logged URLs carry no userinfo, query, or fragment while the health request still uses the
  configured endpoint.

## Out of Scope

- Health capability semantics (issue cliplc008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion `tests/agent/test_http_lifecycle_health_check.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (internal logs pass the common secret masker)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`, `tests/agent/test_http_lifecycle_health_check.py`
