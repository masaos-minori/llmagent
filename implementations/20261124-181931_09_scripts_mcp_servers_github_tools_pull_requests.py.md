## Goal
Publish the pull-requests-domain schemas from their request models (REQ-002, generate every
`inputSchema`) and expose `dry_run` on the three write tools (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/tools_pull_requests.py` (Plan Phase 3).
- Pattern is the one established by seq 08; this row applies it to six tools.

## Assumptions
- `build_input_schema()` exists from seq 01; the PR models are strict from seq 04.
- Verified today: `github_list_pull_requests` publishes `owner`/`repo`/`state` only, although
  `ListPullRequestsRequest` also accepts `per_page`; the three write tools publish no `dry_run`.
- The `UpdatePullRequestRequest` no-op rule (seq 04 model validator) is a cross-field rule that
  `model_json_schema()` cannot express as a JSON Schema keyword; the published schema therefore shows
  the field-level contract only, and the no-op behavior is recorded by seq 18 and tested by seq 15 and
  seq 17. Stated here as a known limit of AC-03's "same invalid arguments" claim for this one rule.

## Design decisions
- Same shape as seq 08: keep `name`, `description`, and all schema-2.1 metadata spreads; replace only
  each `"inputSchema"` literal with `build_input_schema(<Model>)`, computed once at module import.
- Models imported from `scripts/mcp_servers/github/github_models_pull_requests.py` directly, not via
  the `github_models.py` shim.

## Alternatives considered
- Adding a hand-written anyOf to the `github_update_pull_request` schema to express the no-op rule:
  rejected — it would re-introduce a hand-maintained schema fragment, the drift this Plan removes; the
  model validator plus the docs row (seq 18) carry the rule instead.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_pull_requests.py`

### Procedure
1. Add `from mcp_servers.request_contract import build_input_schema` and import
   `CreatePullRequestRequest`, `GetPullRequestRequest`, `ListPullRequestsRequest`,
   `MergePullRequestRequest`, `SearchPullRequestsRequest`, `UpdatePullRequestRequest` from
   `mcp_servers.github.github_models_pull_requests`.
2. Replace the six `"inputSchema": { ... }` literals with the matching `build_input_schema(...)` calls:
   `github_list_pull_requests`, `github_get_pull_request`, `github_create_pull_request`,
   `github_search_pull_requests`, `github_update_pull_request`, `github_merge_pull_request`.
3. Keep this file's metadata head/tail TypedDicts and spreads unchanged (largest GitHub tools file,
   9978 B today; it shrinks as the dicts are replaced).

### Method
- One-to-one tool/model mapping, as listed above.

### Details
- The existing per-tool `description` strings and `preview_capability` metadata are untouched.

## Compatibility considerations
- Newly accepted inputs (record in seq 18): `dry_run` on `github_create_pull_request`,
  `github_update_pull_request`, `github_merge_pull_request`; `per_page` on `github_list_pull_requests`.
- Newly rejected inputs: unknown keys; empty `owner`/`repo`/`head`/`base`/`query`; `pr_number < 1`;
  `per_page > 100`; `title` empty or over 256; `body` over 65536; a `state` value outside the model
  pattern; `github_update_pull_request` with no update field (runtime model rule, not a schema keyword).
- `tests/mcp_servers/test_tool_schema_contract.py` and `tests/mcp_servers/github/test_github_tool_registry.py`
  pin tool names/counts (21 overall): unchanged by this row.

## Security considerations
- Rejecting empty `head`/`base` and `pr_number < 1` in the published contract prevents ambiguous write
  targets before the protected-branch guard runs.

## Rollback considerations
- Revert this Phase 3 commit (one commit per domain per the Plan Risk mitigation).

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02, seq 14) and
  `uv run pytest tests/mcp_servers/test_tool_schema_contract.py`.
- `uv run pytest tests/mcp_servers/github/test_service_dispatch.py` (pins 21 tools at `tests/mcp_servers/github/test_service_dispatch.py:698`).
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/check_module_size.py`,
  `uv run python tools/generate_reference_table.py --check` (T-06).

## Completion criteria
- All six entries carry generated schemas; `dry_run` appears in the three write tools' `properties`.
- The published `github_list_pull_requests` schema advertises `minimum: 1` / `maximum: 100` for
  `per_page` and the `state` pattern.

## Out of Scope
- Model changes (seq 04), the drift gate (seq 14), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the six `inputSchema` literals with `build_input_schema()` calls | Pending | — | — | REQ-002 |
| 2 | Confirm `dry_run` publication for the three write tools | Pending | — | — | REQ-003 |
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
- **Related target files**: `scripts/mcp_servers/github/tools_pull_requests.py`
