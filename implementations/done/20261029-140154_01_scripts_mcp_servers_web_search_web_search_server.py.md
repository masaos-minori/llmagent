## Goal

Rewrite the false sentences in the `_build_security_posture()` docstring so they state
the real import-time behavior: an empty `auth_token` refuses the module import via
`require_auth_token` — a failure, not a warning (REQ-001, REQ-002).

## Scope

- Docstring-only edit: `scripts/mcp_servers/web_search/web_search_server.py:69-71`
  (the "Unlike Shell ... warning rather than a failure" sentence). No executable line
  changes (REQ-003).

## Assumptions

- Verified import ordering (Plan Design, re-confirmed against current source): posture is
  built at `web_search_server.py:83`; the module-scope
  `attach_auth_middleware(..., require_auth_token(...))` at lines 101-104 then raises
  `RuntimeError` (`scripts/mcp_servers/server.py:142-146`) on an empty token.
- `run_startup_validation` still "never raises, never binds HTTP"
  (`scripts/shared/security/startup_flow.py:186`), so the preserved sentence stays true.

## Design decisions

- Replace the presence/absence Shell contrast with a mechanism contrast: Shell guards
  with a module-level `if not _cfg.auth_token: raise RuntimeError(...)`
  (`scripts/mcp_servers/shell/shell_server.py:120-124`); web_search refuses via the
  middleware helper call.
- Keep the accurate sentences untouched: the flow-never-raises statement, the
  server-security-stage-only statement, and the fingerprint-view sentence.

## Alternatives considered

- N/A: docstring-only correction; no code alternatives apply.

## Implementation
### Target file

`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure

Replace the last sentence block of the docstring (`web_search_server.py:69-71`) with the
verified ordering text; leave every other line byte-identical.

### Method

New closing sentences (replacing "Unlike Shell, this module has no import-time refusal
for an empty token, so the posture is where an empty auth_token first becomes visible,
as a warning rather than a failure."):

```
Unlike Shell's module-level guard, this module refuses an empty token through the
middleware helper: the posture (with its auth-token warning) is built first, then the
module-scope attach_auth_middleware(..., require_auth_token(...)) call raises
RuntimeError and the import fails — a failure, not a degraded-warn mode.
```

### Details

- Match the actual sentence flow and line wrapping of the surrounding docstring when
  applying the text; the block above is the required content, not literal formatting.
- `git diff` must show only docstring lines (AC-3).

## Compatibility considerations

- N/A: docstring text only; no call site, signature, or import changes.

## Security considerations

- The rewrite removes a claim that could have led an operator to believe an empty token
  degrades to a warning; no runtime security behavior changes.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- T1 consistency check: compare each rewritten sentence against
  `scripts/mcp_servers/server.py:137-148`, `web_search_server.py:83,101-104`, and
  `scripts/shared/security/startup_flow.py:186`.
- `uv run pytest tests/mcp_servers/web_search` — suite green, unchanged results.
- `uv run ruff check scripts/mcp_servers/web_search`;
  `uv run mypy --no-namespace-packages scripts/mcp_servers/web_search`; `git diff` review
  confirms a docstring-only diff.
- `PYTHONPATH=scripts uv run lint-imports` — unchanged imports, no violations.

## Completion criteria

- The docstring contains no "no import-time refusal" or "warning rather than a failure"
  claim (AC-1) and accurately describes refusal ordering and the Shell mechanism
  difference (AC-2).
- `web_search_server.py`'s diff touches only docstring lines and the web_search suite is
  unchanged green (AC-3).

## Out of Scope

- All executable code in `web_search_server.py`; `require_auth_token` /
  `attach_auth_middleware` semantics (`scripts/mcp_servers/server.py`).
- `tests/mcp_servers/web_search/test_web_search_health_posture.py:8-9` stale test-module
  docstring — report-only flag per the Plan; needs its own Issue.
- All `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the docstring sentences per Method/Details | Completed | 20261029-145130 | 20261029-145139 | REQ-001, REQ-002 |
| 2 | Run the T1 consistency check and the validation gates (docs checkers, `rules/toolchain.md`) | Completed | 20261029-145139 | 20261029-150113 | REQ-003; no new tests in scope Full-suite+diff-cover gate batched with the sibling docstring-only procedure |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (docstring states import-time refusal), REQ-002 (accurate
  Shell comparison and flow-never-raises statements preserved), REQ-003 (docstring-only
  diff)
- **Source issue**: issues/20261029-012525_ebrev002_websearch-import-refusal-doc-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-075747_ebrev002_websearch-import-refusal-doc-mismatch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-140154
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py