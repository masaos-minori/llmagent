## Goal

Remove the opt-in loopback `/health` admission from the shared Bearer-auth
middleware in `scripts/mcp_servers/server.py` so that every route, including
`/health`, requires the server's token again (`REQ-001`, `REQ-002`; AC-1, AC-2).

## Scope

Only `scripts/mcp_servers/server.py`: delete the `exempt_health_on_loopback`
parameter, the exemption expression in the middleware closure, the `_is_loopback_client`
helper, the now-unused `ipaddress` import, and the docstring paragraph describing the
admission. No other file is modified by this document.

## Assumptions

- `web_search_server.py` is the only caller that passed the keyword; git, rag-pipeline,
  cicd, mdq, and eventbus call `attach_auth_middleware` with no keyword (verified by `rg`).
- The agent's startup poll sends the server's shared `auth_token` (`scripts/agent/http_lifecycle.py`),
  so it still authenticates once the admission is gone.
- The launcher's `port_is_responding` treats any response below 500 (a 401 included) as
  "responding", so a now-401 `/health` is harmless at startup.

## Design decisions

- Delete the parameter entirely rather than leaving `exempt_health_on_loopback=False`:
  the plan mandates complete removal, not a disabled switch, and returns the signature to
  its pre-mcp004 two-argument form `attach_auth_middleware(app, token)`.
- Delete `_is_loopback_client` and the `health_exempt` local so the closure performs a
  single `_is_authorized` check, restoring one rule for every route.

## Alternatives considered

Keeping a disabled `exempt_health_on_loopback=False` keyword: rejected — the plan removes
the capability, not disables it, and a dead parameter is a future correctness trap.

## Implementation

### Target file

`scripts/mcp_servers/server.py`

### Procedure

1. Delete the `_is_loopback_client` function defined directly above
   `attach_auth_middleware` (current lines ~96-107).
2. Remove `*, exempt_health_on_loopback: bool = False,` from the
   `attach_auth_middleware` signature (current line ~114).
3. Delete the docstring paragraph beginning `When exempt_health_on_loopback is true, ...`
   (current lines ~129-135); the docstring then describes only the token / empty-token
   behavior.
4. In the `_auth_middleware` closure, delete the `health_exempt = (...)` block
   (current lines ~154-158) and change the guard to
   `if not _is_authorized(request, token):` returning the 401.
5. Remove `import ipaddress` (current line 15) after confirming nothing else in the module
   references `ipaddress.`.

### Method

Apply the five edits, then verify with `rg -n "exempt_health_on_loopback|_is_loopback_client"`
against `scripts/` (expect no match) and run the middleware unit tests.

### Details

- Signature (current lines 110-115):
  `def attach_auth_middleware(app, token, *, exempt_health_on_loopback: bool = False) -> None:`.
- Exemption (current lines 154-160):
  `health_exempt = (exempt_health_on_loopback and request.url.path == "/health" and _is_loopback_client(request))`
  followed by `if not health_exempt and not _is_authorized(request, token):`.
- `_is_loopback_client` (current lines 96-107) is the only place `ipaddress.ip_address(...)`
  is used in the module; removing it makes `import ipaddress` unused.
- Callers confirmed by `rg`: `git/git_server.py`, `rag_pipeline/rag_pipeline_server.py`,
  `cicd/cicd_server.py`, `mdq/mdq_server.py`, `eventbus/app.py` pass no keyword; only
  `web_search/web_search_server.py` passed it (removed by its own procedure).

## Compatibility considerations

Removing the keyword-only parameter changes the public signature. Every existing caller
already omits it except web-search (handled by its own procedure), so no caller breaks.
`/health` now requires the same token as every other route; the agent poll still sends the
shared token and the launcher's port probe still accepts a 401.

## Security considerations

This tightens authentication: `/health` loses its one unauthenticated path and is guarded
by the Bearer check like all other routes. Confirm the `ipaddress` import removal does not
drop any other symbol in the module (it does not).

## Rollback considerations

Revert the commit (or `git checkout scripts/mcp_servers/server.py`).

## Validation plan

- `uv run pytest tests/mcp_servers -q` — existing middleware tests pass unchanged.
- `rg -n "exempt_health_on_loopback|_is_loopback_client" scripts tests docs` — no matches.
- Full sequence: `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -q -c pyproject.toml scripts/mcp_servers`, `uv run lint-imports`,
  `uv run pre-commit run --all-files`.

## Completion criteria

No `exempt_health_on_loopback`, `_is_loopback_client`, or `ipaddress` remain in the module;
the closure performs a single authorization check; the middleware unit tests pass.

## Out of scope

web-search wiring (`tests/mcp_servers/web_search/test_web_search_health.py`,
`scripts/mcp_servers/web_search/web_search_server.py`), the agent poll tests, the two
documents, the token model, the other servers' authentication, the runner's loopback bind
check, and the agent's health poll.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `exempt_health_on_loopback` parameter, the closure exemption, `_is_loopback_client`, the `ipaddress` import, and the docstring paragraph | Completed | — | 20261013-175629 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261013-175629 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261013-175629 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261013-175629 |  |

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
- **Requirement ID**: `REQ-001` (reject `/health` without the token from every client), `REQ-002` (remove the admission names)
- **Source issue**: issues/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-185654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-185934
- **Related target files**: scripts/mcp_servers/server.py