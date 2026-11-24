## Goal
Publish the repository-domain schemas from their request models (REQ-002) and expose `dry_run` on
`github_create_branch` (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/tools_repository.py` (Plan Phase 5).
- Pattern is the one established by seq 08; this row applies it to six tools.

## Assumptions
- `build_input_schema()` exists from seq 01; the repository models are strict with `per_page le=100`
  from seq 06.
- Verified today: `github_list_branches`, `github_list_commits`, and `github_search_code` publish no
  `per_page` although their models accept it; `github_search_repositories` already publishes it;
  `github_create_branch` publishes no `dry_run`.

## Design decisions
- Same shape as seq 08: keep `name`, `description`, the unscoped/repo-scope metadata tails, and every
  spread; replace only each `"inputSchema"` literal with `build_input_schema(<Model>)` at import time.
- Tool `description` strings that advertise behaviour ("Maximum number of results (default:
  configured)") stay as-is: the numeric bound now comes from the generated keywords, not from prose.

## Alternatives considered
- Editing the existing dicts to add `maximum: 100` by hand: rejected — the Plan requires the schema to
  be derived from the model (AC-01), and a hand-edited dict is the drift the Issue removes.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_repository.py`

### Procedure
1. Add `from mcp_servers.request_contract import build_input_schema` and import
   `CreateBranchRequest`, `GetCommitRequest`, `ListBranchesRequest`, `ListCommitsRequest`,
   `SearchCodeRequest`, `SearchRepositoriesRequest` from `mcp_servers.github.github_models_repository`.
2. Replace the six `"inputSchema": { ... }` literals with the matching `build_input_schema(...)` calls
   for `github_search_repositories`, `github_list_branches`, `github_create_branch`,
   `github_list_commits`, `github_get_commit`, `github_search_code`.
3. Keep the unscoped/repo-scope tail constants (this file's `github_search_repositories` and
   `github_search_code` are unscoped) unchanged.

### Method
- One-to-one tool/model mapping as listed above.

### Details
- No `dry_run` on the five read tools: only `CreateBranchRequest` declares it (line 157).

## Compatibility considerations
- Newly accepted inputs (record in seq 18): `dry_run` on `github_create_branch`; `per_page` on
  `github_list_branches`, `github_list_commits`, `github_search_code`.
- The four paginated tools' generated schemas declare `default: 30` (seq 06 moved the model defaults to
  30 to match today's effective dispatch behaviour), replacing the prose-only "default: configured"
  wording in the tool descriptions.
- Newly rejected inputs: unknown keys; `per_page > 100` (previously clamped silently by
  `_clamp_per_page`); `per_page < 1`; empty `query`, `sha`, `branch_name`; empty `branch` or
  `from_branch` supplied explicitly.
- The comment at the top of this file about unscoped search tools keeps its meaning: scope metadata is
  untouched by this row.

## Security considerations
- Advertising `maximum: 100` lets the agent-side gate refuse oversized pages before the request
  reaches the GitHub API.

## Rollback considerations
- Revert this Phase 5 commit.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14; after this row
  all 21 tools are gated) and `uv run pytest tests/mcp_servers/test_tool_schema_contract.py`.
- `uv run pytest tests/mcp_servers/github/` (domain regression).
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/generate_reference_table.py --check` (T-06).

## Completion criteria
- All six entries carry generated schemas; `github_create_branch` publishes `dry_run`; the three
  paginated read tools publish `maximum: 100`.
- Tool names and the file's tool count (6) are unchanged.

## Out of Scope
- Model bounds (seq 06), the drift gate (seq 14), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the six `inputSchema` literals with `build_input_schema()` calls | Pending | — | — | REQ-002 |
| 2 | Confirm `dry_run` publication for `github_create_branch` | Pending | — | — | REQ-003 |
| 3 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | T-02, T-06 |
| 4 | Update documentation | Pending | — | — | N/A: recorded by seq 18 |

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
- **Requirement ID**: `REQ-002` (schemas generated from models), `REQ-003` (publish `dry_run`)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `scripts/mcp_servers/github/tools_repository.py`
