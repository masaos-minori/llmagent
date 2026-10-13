## Goal

Stop web-search from opting into the loopback `/health` admission by removing the
`exempt_health_on_loopback=True` keyword from its middleware call
(`REQ-002`; AC-2).

## Scope

Only `scripts/mcp_servers/web_search/web_search_server.py`: remove the one keyword
argument from the existing `attach_auth_middleware` call.

## Assumptions

- The call passes the shared `auth_token` positionally; only the trailing keyword needs to
  go. The middleware definition is changed by its own procedure.

## Design decisions

- Keep the two positional arguments (`cast(_FastAPIApp, app)` and `_cfg.auth_token or ""`)
  and delete only the trailing keyword, so the call shape matches every other server.

## Alternatives considered

N/A: a single keyword removal; no design family applies.

## Implementation

### Target file

`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure

In the `attach_auth_middleware` call (current lines 67-71), delete the
`    exempt_health_on_loopback=True,` line so the call becomes a two-argument positional
call.

### Method

Edit the call, then confirm via the AST wiring test in
`tests/mcp_servers/web_search/test_web_search_health.py` that no server passes a keyword and
that web-search's second positional argument is the config's `auth_token`.

### Details

Current form (lines 67-71):

```python
attach_auth_middleware(
    cast(_FastAPIApp, app),
    _cfg.auth_token or "",
    exempt_health_on_loopback=True,
)
```

After:

```python
attach_auth_middleware(
    cast(_FastAPIApp, app),
    _cfg.auth_token or "",
)
```

The second positional argument stays `_cfg.auth_token or ""` (the shared token the agent's
poll sends). `rg -n "exempt_health_on_loopback" scripts tests docs` must return no match.

## Compatibility considerations

The call now matches every other server's two-positional-argument shape. web-search's
`/health` now requires the shared token, like every other server.

## Security considerations

Tightens web-search `/health` to require the token; no surface is widened.

## Rollback considerations

Revert the commit.

## Validation plan

- AST wiring check in `tests/mcp_servers/web_search/test_web_search_health.py`: every
  `attach_auth_middleware` call has no keyword; web-search's second positional arg is
  `auth_token`.
- `rg -n "exempt_health_on_loopback" scripts tests docs` — no matches.
- Full sequence per `rules/toolchain.md`.

## Completion criteria

The `attach_auth_middleware` call carries no keyword argument; the shared-token wiring is
unchanged.

## Out of scope

The middleware definition (`scripts/mcp_servers/server.py`), the tests, the two documents,
and the token model.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the `exempt_health_on_loopback=True` keyword from the middleware call | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (remove the admission names and opt-in)
- **Source issue**: issues/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-185654_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-185934
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py
