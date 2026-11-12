## Goal
Fix the module docstring paths in `scripts/mcp_servers/server.py` and document in `attach_auth_middleware` that it authenticates a Bearer token, unlike the EventBus function of the same name (`REQ-004` / `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Docstring lines 7-8 say `mcp/dispatch.py` and `mcp/audit.py`; the files are `scripts/mcp_servers/dispatch.py` and `scripts/mcp_servers/audit.py` (checked).
- The function's first docstring line (`Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.`) stays unchanged: it feeds generated reference text; only later lines change. Both names and every import stay unchanged.
- Code change in `scripts/` (docstring only): the change is committed and pushed first; deployment is the user's decision (`skills/deploy/SKILL.md`).

## Design decisions
- Docstring-only edit; no executable line changes.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Module docstring: `Tool dispatch helpers live in mcp_servers/dispatch.py.` and `Audit log helpers live in mcp_servers/audit.py.`
2. `attach_auth_middleware` docstring: add a paragraph that this function authenticates (Bearer token, fail-closed on an empty token), whereas `eventbus.auth.attach_auth_middleware` only injects `X-Request-Id`.

### Method
- Run `rg -n 'mcp/dispatch|mcp/audit' scripts/mcp_servers/server.py` afterwards: no match.
- Run `uv run python tools/generate_reference_table.py --check`.

### Details
- Check `tests/mcp_servers` for any test that asserts docstring text.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers -q`; `uv run ruff format`/`ruff check`/`mypy`/`bandit` on the file — clean.
- `uv run python tools/generate_reference_table.py --check` — no drift; `uv run python tools/check_docstrings.py` — pass.

## Completion criteria
- No `mcp/dispatch` or `mcp/audit` text remains; the distinction is documented; no import changed; tests and the reference check pass.

## Out of Scope
- Renaming either function (UNK-03); behavior changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the two docstrings | Completed | 20261112-204830 | 20261112-204830 |  |
| 2 | Run `uv run pytest tests/mcp_servers -q`, ruff format/check, mypy, and `generate_reference_table.py --check` | Completed | 20261112-204830 | 20261112-204830 |  |
| 3 | Hand off to deploy after commit and push (user decision) | Completed | 20261112-204830 | 20261112-204830 |  |

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
- **Requirement ID**: `REQ-004` — correct docstring paths; document the `attach_auth_middleware` distinction
- **Source issue**: issues/20261109-113421_adrrev019_docs-stale-statements.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-112439_adrrev019_docs-stale-statements.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124641
- **Related target files**: `scripts/mcp_servers/server.py`