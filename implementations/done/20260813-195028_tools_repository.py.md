## Goal

Add the schema-2.0 per-tool metadata contract to all 6 entries in
`scripts/mcp_servers/github/tools_repository.py`'s `TOOL_LIST`, giving mutating and
owner/repo-addressable read calls `resource_scope_kind="github_repo"`,
`resource_scope_keys=["owner","repo"]`, and correctly marking `github_create_branch`
as the sole write tool in this module.

## Scope

In scope: the 6 dict literals inside `TOOL_LIST` (lines 9-133) —
`github_search_repositories` (11-31), `github_list_branches` (33-48),
`github_create_branch` (50-73), `github_list_commits` (75-93),
`github_get_commit` (95-114), `github_search_code` (116-132). Out of scope: any
change to the GitHub API client/auth logic elsewhere in the github-mcp server, and
`tools_file.py`/`tools_issues.py`/`tools_pull_requests.py` (separate documents).

## Assumptions

- None of the 6 entries currently declare any of the 4 new fields (confirmed:
  `rg "is_write|requires_serial|resource_scope"` on this file returns no hits) —
  fully missing on all 6.
- Only `github_create_branch` mutates state in this module — confirmed by
  description ("Create a branch...") vs. the other 5 ("Search...", "Retrieve the
  list...", "Retrieve the commit history...", "Retrieve details of a specific
  commit...", "Full-text search for code...").
- `github_search_repositories` (11-31) and `github_search_code` (116-132) do **not**
  have `owner`/`repo` properties in their `inputSchema` — confirmed by reading both
  entries: their only properties are `query` (and `per_page` for the repositories
  search) — they operate across all of GitHub, not one repository. Applying
  `resource_scope_keys=["owner","repo"]` to these two would violate the plan's own
  validator rule ("`resource_scope_keys` a `list[str]` each present in the tool's own
  `inputSchema["properties"]`"), so this document scopes them as unscoped instead
  (see Design decisions).
- The remaining 4 entries (`github_list_branches`, `github_create_branch`,
  `github_list_commits`, `github_get_commit`) all have both `owner` and `repo` as
  required `inputSchema` properties (confirmed by reading each entry's `required`
  list), so `resource_scope_keys=["owner","repo"]` is valid for all 4.

## Design decisions

- `github_create_branch` (the one write tool): `is_write=True`,
  `requires_serial=False`, `resource_scope_kind="github_repo"`,
  `resource_scope_keys=["owner", "repo"]` — per the plan's per-module instruction
  ("All mutating calls get repository-level scope").
- `github_list_branches`, `github_list_commits`, `github_get_commit` (read tools that
  address a specific repo): `is_write=False`, `requires_serial=False`,
  `resource_scope_kind="github_repo"`, `resource_scope_keys=["owner", "repo"]` — kept
  scoped (not unscoped) even though read/read pairs never become conflict-graph edges
  per the plan's Design (UNK-05 resolution), so declaring the scope is harmless and
  keeps the schema meaningfully descriptive of what repository each call touched.
- `github_search_repositories`, `github_search_code` (cross-repository search, no
  `owner`/`repo` parameter): `is_write=False`, `requires_serial=False`,
  `resource_scope_kind=""`, `resource_scope_keys=[]` — unscoped, mirroring the plan's
  explicit precedent for `web_search_tools.py`'s `search_web`/`browser_fetch`
  ("read-only, non-serial, unscoped (`resource_scope_kind=""`)"), since these two
  tools have no per-repository argument to resolve a scope from.

## Alternatives considered

Considered forcing `resource_scope_keys=["query"]` (treating the search string itself
as a pseudo-scope) for the two search tools — rejected: `query` is free-text, not a
resource identifier, and would not produce a meaningful conflict-detection signal;
unscoped (`""`/`[]`) is the correct, plan-consistent representation of "no
resolvable per-resource scope," matching the `web_search_tools.py` precedent cited in
the plan.

## Implementation

### Target file: `scripts/mcp_servers/github/tools_repository.py`

### Procedure

1. `github_search_repositories` (11-31): after `"config_dependent": True,` (line 30),
   add `"is_write": False,`, `"requires_serial": False,`, `"resource_scope_kind": "",`,
   `"resource_scope_keys": [],`.
2. `github_list_branches` (33-48): after `"config_dependent": True,` (line 47), add
   `"is_write": False,`, `"requires_serial": False,`,
   `"resource_scope_kind": "github_repo",`, `"resource_scope_keys": ["owner", "repo"],`.
3. `github_create_branch` (50-73): after `"config_dependent": True,` (line 72), add
   `"is_write": True,`, `"requires_serial": False,`,
   `"resource_scope_kind": "github_repo",`, `"resource_scope_keys": ["owner", "repo"],`.
4. `github_list_commits` (75-93): after `"config_dependent": True,` (line 92), add the
   same read-scoped block as step 2.
5. `github_get_commit` (95-114): after `"config_dependent": True,` (line 113), add the
   same read-scoped block as step 2.
6. `github_search_code` (116-132): after `"config_dependent": True,` (line 131), add
   the same unscoped block as step 1.

### Method

Direct literal-dict edits, one insertion per entry (6 total), no new imports/helpers.

### Details

- `github_search_repositories` currently ends (lines 26-31):
  ```python
  "required": ["query"],
      },
      "status": "production",
      "config_dependent": True,
  },
  ```
  becomes:
  ```python
  "required": ["query"],
      },
      "status": "production",
      "config_dependent": True,
      "is_write": False,
      "requires_serial": False,
      "resource_scope_kind": "",
      "resource_scope_keys": [],
  },
  ```
- `github_list_branches` currently ends (lines 43-48):
  ```python
  "required": ["owner", "repo"],
      },
      "status": "production",
      "config_dependent": True,
  },
  ```
  becomes:
  ```python
  "required": ["owner", "repo"],
      },
      "status": "production",
      "config_dependent": True,
      "is_write": False,
      "requires_serial": False,
      "resource_scope_kind": "github_repo",
      "resource_scope_keys": ["owner", "repo"],
  },
  ```
- `github_create_branch` ends (lines 69-73) with `"required": ["owner", "repo", "branch_name"],`; same trailing block as `github_list_branches` but `"is_write": True,`.
- `github_list_commits` (`required": ["owner", "repo"]`) and `github_get_commit`
  (`required": ["owner", "repo", "sha"]`) each get the identical read-scoped block as
  `github_list_branches`.
- `github_search_code` ends with `"required": ["query"],`; gets the identical
  unscoped block as `github_search_repositories`.

## Compatibility considerations

Additive-only. No existing test file parametrizes over
`mcp_servers.github.tools_repository` today (confirmed:
`tests/mcp_servers/test_tool_schema.py`'s `_SCHEM_MODULES` only lists the file/git
modules) — the new `test_tool_schema_contract.py` will be the first test to cover
this module's schema shape. `build_tools_response()` in `server.py` continues to pass
extra keys through unchanged via `{**t, "server_key": ...}`.

## Security considerations

Correctly marking `github_create_branch` as `is_write=True` and scoping it to
`owner`/`repo` lets the future scheduler serialize concurrent branch-creation calls
against other mutating GitHub calls on the same repository. Leaving the two
cross-repository search tools unscoped (rather than forcing an invalid/misleading
scope) avoids a validator false-pass on keys that don't exist in their schemas — a
`resource_scope_keys` entry not present in `inputSchema["properties"]` would be
rejected by the plan's validator, so this design avoids introducing that failure
mode.

## Rollback considerations

Trivial: revert the 6 additive blocks. No other file depends on these fields yet.

## Validation plan

- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` (once implemented)
  — expect all 6 entries to pass, including the two unscoped search tools.
- `uv run python -c "from mcp_servers.github.tools_repository import TOOL_LIST; writes = {t['name'] for t in TOOL_LIST if t['is_write']}; assert writes == {'github_create_branch'}"` — manual smoke check.
- `uv run python -c "from mcp_servers.github.tools_repository import TOOL_LIST; unscoped = {t['name'] for t in TOOL_LIST if t['resource_scope_kind']==''}; assert unscoped == {'github_search_repositories','github_search_code'}"` — manual smoke check of the unscoped subset.

## Out of scope

- `tools_file.py`, `tools_issues.py`, `tools_pull_requests.py` (separate documents).
- The GitHub API client/auth/rate-limit logic elsewhere in the github-mcp server.
- The shared contract validator itself.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195028
- Related target files: scripts/mcp_servers/github/tools_repository.py
