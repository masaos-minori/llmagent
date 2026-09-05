## Goal
Add `allowed_remote_urls: list[str]` to `GitConfig` so `REQ-004`'s enforcement (in
`format_output.py`) has a config-backed allowlist to check resolved remote URLs
against (`REQ-002`).

## Scope
- In scope: the `GitConfig` dataclass field and its `from_dict()` parsing/construction.
- Out of scope: any enforcement logic (lives in `format_output.py`, a separate row);
  the `config/git_mcp_server.toml` documented example (a separate row).

## Assumptions
- Fail-closed-when-empty, consistent with `allowed_repo_paths`'s existing convention:
  an empty `allowed_remote_urls` list means no remote is authorized, not "no
  restriction" — REQ-004 rejects when the resolved URL is "not present in
  `allowed_remote_urls`", which is true for every URL when the list is empty.

## Design decisions
- Mirror the existing `protected_branches` field exactly: `list[str] =
  dataclasses.field(default_factory=list)`, parsed via `get_typed(d,
  "allowed_remote_urls", list, "a list", default=[])`, following the same
  `from_dict()` local-variable-then-constructor-arg pattern already used for every
  other list field in this class.

## Alternatives considered
- A `dict[str, str]` mapping remote *name* to an authorized URL was considered and
  rejected: `REQ-001` requires authorization to validate what a remote name
  *currently resolves to*, independent of which name was used to reach it — a flat
  list of authorized URLs (checked against the resolved URL, not the name) is the
  correct shape; name-keyed authorization would reintroduce the exact alias-based gap
  `REQ-001`/the Problem section describes.

## Implementation
### Target file
`scripts/mcp_servers/git/git_models.py`

### Procedure
1. Add the new field to the `GitConfig` dataclass (line 36, immediately after
   `allow_detached_head: bool = False`).
2. Add parsing in `from_dict()` (after line 51's `allow_detached_head` parsing block,
   before the `return cls(...)` at line 52).
3. Add the corresponding constructor keyword argument (after line 59's
   `allow_detached_head=allow_detached_head,`).

### Method
Follow the exact structural twin of `protected_branches` (dataclass field, line 34)
and its parsing (lines 46-48) — same `get_typed(..., list, "a list", default=[])`
call shape, same `list(...)` coercion at the constructor call site (line 58's
pattern).

### Details
- Field: `allowed_remote_urls: list[str] = dataclasses.field(default_factory=list)`.
- Parsing: `allowed_remote_urls = get_typed(d, "allowed_remote_urls", list, "a list", default=[])`.
- Construction: `allowed_remote_urls=list(allowed_remote_urls),`.
- No change to `GitConfig.load()` (line 63-65) — it already delegates to
  `from_dict()` unconditionally.

## Compatibility considerations
- Purely additive: a new optional-with-default field does not change any existing
  `GitConfig(...)` call site's required arguments, and existing
  `config/git_mcp_server.toml` files without the key parse via the `default=[]`
  fallback (fail-closed, per Assumptions).

## Security considerations
- The fail-closed-when-empty default means a config file that omits the new key
  authorizes zero remotes once `format_output.py`'s enforcement (a separate row)
  lands — this is the intended safe default, not a regression, since no
  authorization exists in the current codebase at all (Background).

## Rollback considerations
- Reverting this field alone (before `format_output.py`'s enforcement row lands) is a
  no-op from a behavior standpoint — the field is inert until read. Reverting after
  both land requires reverting `format_output.py`'s enforcement in the same change,
  since it depends on this field.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_git_models.py -v` (existing suite, per
  Plan's Validation plan row for this file) — add a case constructing `GitConfig`
  from a dict containing `allowed_remote_urls` and asserting the parsed list, plus a
  case omitting the key and asserting the `[]` default.
- `uv run ruff check scripts/mcp_servers/git/git_models.py`; `uv run mypy
  scripts/mcp_servers/git/git_models.py`.

## Completion criteria
- `GitConfig` exposes `allowed_remote_urls: list[str]`, parsed correctly from a dict
  containing the key and defaulting to `[]` when absent; `test_git_models.py`'s new
  cases pass.

## Out of scope
- Enforcement logic, URL normalization/redaction, and the `config/git_mcp_server.toml`
  documented example are separate `Implementation Target Files` rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: scripts/mcp_servers/git/git_models.py
