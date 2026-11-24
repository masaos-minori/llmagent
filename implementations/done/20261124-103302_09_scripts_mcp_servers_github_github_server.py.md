## Goal

Make the audit record use the same repository identity the guard uses (REQ-002: one canonical `owner/repo` key used by the guard, the API slug, the error text, and the audit record), so a mixed-case caller no longer produces an audit key that differs from the boundary decision.

## Scope
**Release unit**: boundary tests (Phase 3, the same unit as the guard row whose behavior the HTTP test asserts)

## Assumptions

- `normalize_repo_key` (new) is defined by `implementations/20261124-103302_01_scripts_shared_repo_identity.py.md`; this document imports it through `shared.` and adds no policy of its own.
- For calls with no `owner`/`repo` arguments the audit target keeps its current form (`repo=/`), so search-only and non-repository calls are unaffected.
- The audit record's field order is characterized by `tests/mcp_servers/github/test_github_server_endpoints.py` and must not change (Plan Reference Files).

## Design decisions

- Normalize at the API entry, only when both parts are present and non-empty, rather than normalizing inside `_audit_log()` — the audit helper takes a pre-built target string and is shared with the write path, which already goes through the canonical key at `_get_repo()` (Plan D-3).
- The change is scoped to the target string only; the response shape, the outcome taxonomy, and the disabled-tool gate are untouched.

## Alternatives considered

- Recording the caller's casing in the audit record while comparing a normalized key in the guard — rejected by Plan D-3: that is the inconsistency this row exists to remove.

## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`

### Procedure
1. In the `/v1/call_tool` handler's audit call, build the target from the canonical key when `req.args` carries a usable `owner` and `repo` (`f"repo={normalize_repo_key(owner, repo)}"` at line 244); otherwise keep the existing empty-value form.
2. Add the `shared.repo_identity` import; change nothing else in the file.

### Method
- The audit target is the repository identity only; operation-specific identifiers stay as they are. No value other than the casing changes.

### Details
- The disabled-tool gate must stay before the dispatch and before the audit call, so a disabled-tool rejection is not classified into the audit error taxonomy (existing comment at lines 231-233).
- `shared/` imports nothing from `mcp_servers/`, so the import direction stays inside the existing contract (`uv run lint-imports`: 6 contracts kept, 0 broken).

### Companion test files
- `tests/mcp_servers/github/test_github_server_endpoints.py`
  - Procedure: add the HTTP `/v1/call_tool` case for an out-of-allowlist repository read (403, no client request) and the audit-record case showing `target` carries the canonical key for a mixed-case call; keep the existing audit field-order and `request.state`-vs-header cases green.
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` (AC-1, AC-2); the 403 case is written before Phase 3 lands, per the release unit.

## Compatibility considerations

- The recorded key form changes for mixed-case callers (Plan Risks); log consumers that match the literal `owner/repo` string must use the canonical form. No response model carries the key, so API responses are unchanged.

## Security considerations

- The audit record is the evidence trail for the approval decision; a key that differs from the one the guard enforced makes the trail unreadable. This row makes the recorded identity the identity that was enforced.

## Rollback considerations

- High: one-line revert restores the current target string.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/mcp_servers/github/github_server.py` | HTTP-level | `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` | Out-of-allowlist read returns 403; the audit `target` carries the canonical key; audit field order unchanged |
| Same file | Quality gates | `uv run ruff check scripts/mcp_servers/github/github_server.py`, `uv run mypy scripts/mcp_servers/github/github_server.py`, `uv run bandit scripts/mcp_servers/github/github_server.py` | No finding |

## Completion criteria

- For a repository-scoped call, the guard, the API slug, the error text, and the audit record show the same key (AC-2).

## Out of Scope

- Retry, timeout, and audit behavior of GitHub writes (mcpai006).
- The canonical-key definition itself (row 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261124-152854 | 20261124-152854 |  |
| 2 | Add or update tests per Validation plan (companion `tests/mcp_servers/github/test_github_server_endpoints.py`) | Completed | 20261124-152854 | 20261124-152854 | Written in Phase 2, before Phase 3 lands 403 out-of-allowlist case and canonical audit-target case added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261124-152854 | 20261124-152854 |  |

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
- **Requirement ID**: REQ-002 (canonical key recorded at the API entry in the audit record)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/mcp_servers/github/github_server.py`, `tests/mcp_servers/github/test_github_server_endpoints.py`