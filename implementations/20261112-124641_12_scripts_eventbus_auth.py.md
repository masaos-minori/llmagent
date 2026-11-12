## Goal
Document in `scripts/eventbus/auth.py` that `attach_auth_middleware` only injects `X-Request-Id`, that authentication happens in endpoint dependencies, and how it differs from the MCP function (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current docstring already says the middleware only injects `X-Request-Id` and delegates authentication to `resolve_principal()` (checked); the missing piece is the distinction from `mcp_servers.server.attach_auth_middleware`.
- Overlap: `plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md` and `plans/20261112-122030_rmcompat007_history-comment-sweep.md` edit comments and other code in this file (including the `Precedent` comment near line 22); this edit changes only this function's docstring after its first line, and must not use the word `Precedent`.
- The first docstring line stays unchanged (generated EventBus reference).
- Code change in `scripts/` (docstring only); deployment is the user's decision.

## Design decisions
- Add one sentence after the existing text; no executable change.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`scripts/eventbus/auth.py`

### Procedure
1. Extend the docstring: `Unlike mcp_servers.server.attach_auth_middleware, which authenticates a Bearer token, this function performs no authentication.`

### Method
- Run `uv run python tools/generate_reference_table.py --check` to confirm the generated reference is stable.

### Details
- `app.py` and the imports stay unchanged.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus -q`; `uv run ruff format`/`ruff check`/`mypy`/`bandit` on the file — clean.
- `uv run python tools/generate_reference_table.py --check` — no drift.

## Completion criteria
- The docstring states the distinction; nothing executable changed; tests and the reference check pass.

## Out of Scope
- Renaming the function; the comment sweep and strict-read changes (rmcompat004, rmcompat007).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the docstring | Pending | — | — | |
| 2 | Run `uv run pytest tests/eventbus -q`, ruff, mypy, and `generate_reference_table.py --check` | Pending | — | — | |
| 3 | Hand off to deploy after commit and push (user decision) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — document that the EventBus `attach_auth_middleware` only injects `X-Request-Id`
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `scripts/eventbus/auth.py`
