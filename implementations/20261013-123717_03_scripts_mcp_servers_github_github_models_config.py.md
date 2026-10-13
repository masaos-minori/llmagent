## Goal
- Give `GitHubConfig` a server-side `auth_token`, resolved from `${ENV:...}` references like `GitConfig`, so the server module (row 4) can authenticate (REQ-001).

## Scope
- In: one new defaulted dataclass field and its `from_dict` loading in this module.
- Out: the refusal for an empty value (server module, row 4), the TOML entry, tests.

## Assumptions
- The default stays `""` so every existing `from_dict`/constructor caller keeps working; an unset referenced variable raises `ValueError` through `get_str` (Explicit in code — `scripts/shared/config_utils.py`).
- Anchors verified: `GitHubConfig` (class at line 28, `from_dict` at line 43); `get_str` is already imported at line 16.

## Design decisions
- Mirror `GitConfig`: field `auth_token: str = ""` and `auth_token=get_str(d, "auth_token")`.
- Add the field last so no positional construction shifts.

## Alternatives considered
- Reject an empty value in `from_dict`: rejected (existing tests build the model from minimal dictionaries; the refusal lives in the server module).

## Implementation
### Target file
`scripts/mcp_servers/github/github_models_config.py`

### Procedure
1. Add the defaulted `auth_token` field as the last field (change A).
2. Load it in `from_dict` with `get_str(d, "auth_token")` (change B).

### Method
- Reference pattern: `scripts/mcp_servers/git/git_models.py` (`GitConfig.from_dict`). `GitHubConfig.from_dict({})` is called from 11 sites in 8 existing test files; the default stays empty so those callers keep working (the refusal lives in the server module).
- Run `uv run ruff check scripts/mcp_servers/github/github_models_config.py --fix` afterwards so the import order is normalized.

### Details
Change A — field (Before/After):

```python
# Before:
    max_per_page: int = 100
    llm_url: str = ""
# After:
    max_per_page: int = 100
    llm_url: str = ""
    auth_token: str = ""
```

Change B — `from_dict` argument (Before/After):

```python
# Before:
            max_per_page=int(d.get("max_per_page", 100)),
            llm_url=get_str(d, "llm_url"),
        )
# After:
            max_per_page=int(d.get("max_per_page", 100)),
            llm_url=get_str(d, "llm_url"),
            auth_token=get_str(d, "auth_token"),
        )
```

## Compatibility considerations
- Additive: a new defaulted field; no existing caller changes. `dataclasses.fields()`-based assertions (see Plan row 27) must include the new field.

## Security considerations
- N/A: the model only carries the resolved token; the fail-closed decision is in the server module. The resolved secret is not logged here.

## Rollback considerations
- Revert the field and the `from_dict` argument (and the import in the same commit).

## Validation plan
- `uv run ruff format scripts/mcp_servers/github/github_models_config.py`, `uv run ruff check scripts/mcp_servers/github/github_models_config.py`, `uv run mypy --no-namespace-packages scripts/`.
- `uv run pytest tests/mcp_servers/github/test_github_server_auth.py -q` (model loading tests) and `uv run pytest tests/mcp_servers -q`.

## Completion criteria
- `GitHubConfig.from_dict({"auth_token": "abc"}).auth_token == "abc"`; `from_dict({}).auth_token == ""`; a `${ENV:VAR}` reference to an unset variable raises `ValueError`.
- Static checks pass.

## Out of scope
- The server module, the TOML file, and tests (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the field and `from_dict` changes | Pending | — | — | Plan Step 4 |
| 2 | Add or confirm the model tests in the paired new test file | Pending | — | — | row 30 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: `REQ-001` (server-side `auth_token` in the configuration model)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: scripts/mcp_servers/github/github_models_config.py
