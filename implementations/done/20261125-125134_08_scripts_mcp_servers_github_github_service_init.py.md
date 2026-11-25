## Goal

Build the PyGithub client from the configured timeouts with the library retry disabled (REQ-002), so a write is sent at most once per call.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- Verified by runtime inspection of PyGithub 2.9.1: the default `GithubRetry(total=10)` allows POST, PUT, DELETE and retries every 5xx and 403; the default timeout is a single 15 seconds.
- `github_server.py` imports `_GITHUB_TOKEN` and `build_service` from this module; both names are kept.
- PyGithub passes `timeout` to `requests`, which accepts a `(connect, read)` tuple although the annotation says `int`; a `cast` satisfies mypy and the new test pins the runtime behavior.
- Adversarial verification finding (20261125, PyGithub 2.9.1): `Github.__init__` asserts `isinstance(timeout, int)` (MainClass.py line 220), so a tuple cannot be passed to the constructor, and `Requester` has no public `timeout`/`retry` attributes (they are name-mangled privates exposed only through `Requester.kwargs`). The tuple is applied after construction with `object.__setattr__(gh.requester, "_Requester__timeout", (connect, read))`, which `requests` accepts verbatim (Requester.py lines 164, 210); tests read both values through `requester.kwargs`. The procedure below is corrected to this form.

## Design decisions

- The import-time singleton `_gh` is removed: the client now depends on configuration, which is loaded by the server module, so `build_service(cfg)` builds it.
- One client serves reads and writes with `retry=None`; reads rely on the Agent transport's safe read retry.

## Alternatives considered

A second write-only client was rejected: it doubles the injection points of every service mixin for a benefit the single no-retry client already gives.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_init.py`

### Procedure
Add `build_client` (new) and call it from `build_service`; delete the import-time singleton.

### Method
- Define build_client taking `(token, connect_timeout_sec, read_timeout_sec)` and returning `Github(auth=Auth.Token(token) if token else None, timeout=cast(int, (connect, read)), retry=None)`. Corrected per the assumption above: pass an `int` placeholder to the constructor (the assertion rejects a tuple), then apply the `(connect, read)` tuple through `object.__setattr__(gh.requester, "_Requester__timeout", (connect, read))` so `requests` receives it.
- Keep the module-level `_GITHUB_TOKEN` and the warning logged when the token is empty (move the warning into build_client).
- In `build_service`, build the client with the config's two timeouts and pass it to `GitHubService`.

### Details
- Update the module docstring: `_gh` no longer exists.
- The existing characterization test is rewritten by its own document (`tests/mcp_servers/github/test_service_init.py`).

## Compatibility considerations

`_gh` disappears as a module attribute; the only in-tree readers are the test file updated in this release unit.

## Security considerations

Disabling library retry removes the hidden re-send of writes on 5xx and 403; timeouts bound every upstream call.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_service_init.py tests/mcp_servers/github/test_github_write_outcomes.py`
- `uv run mypy scripts/mcp_servers/github/github_service_init.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- The built client has `retry` disabled and the configured timeouts.
- No module-level client is constructed at import.

## Out of Scope

- Config parsing (config models document).
- Outcome translation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-184033 | 20261125-184033 | changed: scripts/mcp_servers/github/github_service_init.py; corrected per adversarial finding: tuple applied via object.__setattr__ on the requester private timeout |
| 2 | Add or update tests per Validation plan | Completed | 20261125-184033 | 20261125-184033 | test_service_init.py rewritten; asserts via requester.kwargs |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-184033 | 20261125-184033 | ruff/mypy/bandit/lint-imports pass; 6 targeted tests pass; full github suite 572 passed |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_service_init.py`