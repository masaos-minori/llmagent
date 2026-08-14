## Goal

Add the schema-2.0 per-tool metadata contract to all 6 entries in
`scripts/mcp_servers/github/tools_pull_requests.py`'s `TOOL_LIST`, marking
`github_create_pull_request`, `github_update_pull_request`,
`github_merge_pull_request` state-changing (scoped `resource_scope_kind="github_repo"`,
`resource_scope_keys=["owner","repo"]`), the repo-addressable reads
(`github_list_pull_requests`, `github_get_pull_request`) similarly scoped but
read-only, and the cross-repository `github_search_pull_requests` unscoped.

## Scope

In scope: the 6 dict literals inside `TOOL_LIST` (lines 9-166) —
`github_list_pull_requests` (11-29), `github_get_pull_request` (31-49),
`github_create_pull_request` (51-78), `github_search_pull_requests` (80-101),
`github_update_pull_request` (103-133), `github_merge_pull_request` (135-165). Out of
scope: the GitHub API client/auth logic and actual merge-strategy execution elsewhere
in the github-mcp server.

## Assumptions

- None of the 6 entries currently declare any of the 4 new fields (confirmed:
  `rg "is_write|requires_serial|resource_scope"` on this file returns no hits) —
  fully missing on all 6.
- `github_list_pull_requests`, `github_get_pull_request`,
  `github_create_pull_request`, `github_update_pull_request`,
  `github_merge_pull_request` all require both `owner` and `repo` (confirmed by each
  entry's `required` list) — scope-eligible.
- `github_search_pull_requests` (80-101) has only `query`/`per_page` properties, no
  `owner`/`repo` (confirmed by reading the entry) — cross-repository search, matching
  the same pattern as the other 3 GitHub modules' search tools, so treated as
  unscoped for the same reason.
- `github_create_pull_request`, `github_update_pull_request`,
  `github_merge_pull_request` mutate state (create, update title/body/state, merge);
  `github_list_pull_requests`, `github_get_pull_request`, `github_search_pull_requests`
  do not — confirmed by descriptions.

## Design decisions

- `github_create_pull_request`, `github_update_pull_request`,
  `github_merge_pull_request`: `is_write=True`, `requires_serial=False`,
  `resource_scope_kind="github_repo"`, `resource_scope_keys=["owner", "repo"]`.
- `github_list_pull_requests`, `github_get_pull_request`: `is_write=False`,
  `requires_serial=False`, `resource_scope_kind="github_repo"`,
  `resource_scope_keys=["owner", "repo"]`.
- `github_search_pull_requests`: `is_write=False`, `requires_serial=False`,
  `resource_scope_kind=""`, `resource_scope_keys=[]` — unscoped, consistent with the
  cross-repository-search precedent in the other 3 GitHub tool modules.
- `github_merge_pull_request` in particular gets `requires_serial=False` (not
  `True`) despite being the most consequential mutation in this module — the plan
  does not call out any GitHub tool for a global serial barrier (that treatment is
  reserved for `shell_tools.py` per the plan's per-server table); repository-level
  scope overlap detection is deemed sufficient by the plan's Design section for all
  GitHub writes, including merges.

## Alternatives considered

Considered scoping `github_update_pull_request`/`github_merge_pull_request`
additionally by `pr_number` for finer-than-repository granularity — rejected for the
same reason as in `tools_issues.py`'s document: the plan's per-module instruction is
uniformly repository-level across all 4 GitHub tool modules, and introducing
PR-level granularity here alone would be inconsistent with that stated scope.

## Implementation

### Target file: `scripts/mcp_servers/github/tools_pull_requests.py`

### Procedure

1. `github_list_pull_requests` (11-29): after `"config_dependent": True,` (line 28),
   add `"is_write": False,`, `"requires_serial": False,`,
   `"resource_scope_kind": "github_repo",`, `"resource_scope_keys": ["owner", "repo"],`.
2. `github_get_pull_request` (31-49): after `"config_dependent": True,` (line 48), add
   the identical read-scoped block as step 1.
3. `github_create_pull_request` (51-78): after `"config_dependent": True,` (line 77),
   add `"is_write": True,`, `"requires_serial": False,`,
   `"resource_scope_kind": "github_repo",`, `"resource_scope_keys": ["owner", "repo"],`.
4. `github_search_pull_requests` (80-101): after `"config_dependent": True,` (line
   100), add `"is_write": False,`, `"requires_serial": False,`,
   `"resource_scope_kind": "",`, `"resource_scope_keys": [],`.
5. `github_update_pull_request` (103-133): after `"config_dependent": True,` (line
   132), add the identical write-scoped block as step 3.
6. `github_merge_pull_request` (135-165): after `"config_dependent": True,` (line
   164), add the identical write-scoped block as step 3.

### Method

Direct literal-dict edits, one insertion per entry (6 total), no new imports/helpers.

### Details

- `github_list_pull_requests` currently ends (lines 24-29):
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
- `github_get_pull_request` (`required": ["owner", "repo", "pr_number"]`) gets the
  identical read-scoped block.
- `github_create_pull_request` (`required": ["owner", "repo", "title", "head", "base"]`)
  gets the write-scoped block (`is_write=True`).
- `github_search_pull_requests` (`required": ["query"]`) gets the unscoped block.
- `github_update_pull_request` (`required": ["owner", "repo", "pr_number"]`) and
  `github_merge_pull_request` (`required": ["owner", "repo", "pr_number"]`) each get
  the write-scoped block.

## Compatibility considerations

Additive-only. No existing test parametrizes over
`mcp_servers.github.tools_pull_requests` today; the new
`test_tool_schema_contract.py` will be first to cover it. `build_tools_response()`
continues to pass extra keys through unchanged.

## Security considerations

Correctly marking the 3 mutating PR operations `is_write=True` with repository-level
scope lets the future scheduler serialize concurrent PR mutations (including
merges) against the same repository. This file introduces no change to the actual
merge-strategy validation (`merge_method` handling) itself, which remains in the
github-mcp server's dispatch logic.

## Rollback considerations

Trivial: revert the 6 additive blocks. No other file depends on these fields yet.

## Validation plan

- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py -v` (once implemented)
  — expect all 6 entries to pass.
- `uv run python -c "from mcp_servers.github.tools_pull_requests import TOOL_LIST; writes = {t['name'] for t in TOOL_LIST if t['is_write']}; assert writes == {'github_create_pull_request','github_update_pull_request','github_merge_pull_request'}"` — manual smoke check.

## Out of scope

- `tools_repository.py`, `tools_file.py`, `tools_issues.py` (separate documents).
- The GitHub API client/auth/merge-strategy logic elsewhere in the github-mcp server.
- The shared contract validator itself.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-195205
- Related target files: scripts/mcp_servers/github/tools_pull_requests.py
