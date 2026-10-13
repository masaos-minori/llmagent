## Goal
- Give `ShellConfig` a server-side `auth_token`, resolved from `${ENV:...}` references like `GitConfig`, so the server module (row 2) can authenticate (REQ-001).

## Scope
- In: one new defaulted dataclass field and its `from_dict` loading in this module.
- Out: the refusal for an empty value (server module, row 2), the TOML entry, tests.

## Assumptions
- The default stays `""` so every existing `from_dict`/constructor caller keeps working; an unset referenced variable raises `ValueError` through `get_str` (Explicit in code — `scripts/shared/config_utils.py`).
- Anchors verified: `ShellConfig` (class at line 45, `from_dict` at line 64); the imports at lines 13-15 do not yet include `get_str`; `from_dict` uses the module's `_or_default` helper for the other fields.

## Design decisions
- Mirror `GitConfig`: field `auth_token: str = ""` and `auth_token=get_str(d, "auth_token")`.
- Add the field last so no positional construction shifts.

## Alternatives considered
- Reject an empty value in `from_dict`: rejected (existing tests build the model from minimal dictionaries; the refusal lives in the server module).

## Implementation
### Target file
`scripts/mcp_servers/shell/shell_models.py`

### Procedure
1. Add `get_str` to the `shared.config_utils` import (change A).
2. Add the defaulted `auth_token` field as the last field (change B).
3. Load it in `from_dict` with `get_str(d, "auth_token")` (change C).

### Method
- Reference pattern: `scripts/mcp_servers/git/git_models.py` (`GitConfig.from_dict`). `ShellConfig.from_dict` uses `_or_default` for its other fields, but `auth_token` must resolve `${ENV:...}` references, so it uses `get_str` like `GitConfig`.
- Run `uv run ruff check scripts/mcp_servers/shell/shell_models.py --fix` afterwards so the import order is normalized.

### Details
Change A — import (Before/After):

```python
# Before:
from shared.config_loader import ConfigLoader
from shared.protocols.shell import ShellPolicy
# After:
from shared.config_loader import ConfigLoader
from shared.config_utils import get_str
from shared.protocols.shell import ShellPolicy
```

Change B — field (Before/After):

```python
# Before:
    env_allowlist: list[str] = dataclasses.field(default_factory=list)
    env_denylist: list[str] = dataclasses.field(default_factory=list)
# After:
    env_allowlist: list[str] = dataclasses.field(default_factory=list)
    env_denylist: list[str] = dataclasses.field(default_factory=list)
    auth_token: str = ""
```

Change C — `from_dict` argument (Before/After):

```python
# Before:
            env_allowlist=list(_or_default(d.get("env_allowlist"), [])),
            env_denylist=list(_or_default(d.get("env_denylist"), [])),
        )
# After:
            env_allowlist=list(_or_default(d.get("env_allowlist"), [])),
            env_denylist=list(_or_default(d.get("env_denylist"), [])),
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
- `uv run ruff format scripts/mcp_servers/shell/shell_models.py`, `uv run ruff check scripts/mcp_servers/shell/shell_models.py`, `uv run mypy --no-namespace-packages scripts/`.
- `uv run pytest tests/mcp_servers/shell/test_shell_server_auth.py -q` (model loading tests) and `uv run pytest tests/mcp_servers -q`.

## Completion criteria
- `ShellConfig.from_dict({"auth_token": "abc"}).auth_token == "abc"`; `from_dict({}).auth_token == ""`; a `${ENV:VAR}` reference to an unset variable raises `ValueError`.
- Static checks pass.

## Out of scope
- The server module, the TOML file, and tests (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the field and `from_dict` changes | Pending | — | — | Plan Step 3 |
| 2 | Add or confirm the model tests in the paired new test file | Pending | — | — | row 29 |
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
- **Related target files**: scripts/mcp_servers/shell/shell_models.py
