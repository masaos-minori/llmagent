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
- Step 3a verification: the three optional `str | None` fields of `github_update_pull_request`
  (`title`, `body`, `state`) publish as `anyOf: [{...string bounds}, {"type": "null"}]` with
  `default: null`. The agent-side gate calls `jsonschema.validate(args, inputSchema)`
  (`scripts/agent/tool_arg_validator.py:204`), which supports `anyOf`, so the published contract stays
  enforceable for those fields.
- Step 3a verification: the no-op update rule (this row's model validator) has no JSON Schema keyword, so
  the published schema advertises the field-level contract only. A client that sends
  `github_update_pull_request` with none of `title`/`body`/`state` passes the agent-side gate and is
  rejected by the model at dispatch; seq 18 must state this and seq 15/17 test it.

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
| 1 | Replace the six `inputSchema` literals with `build_input_schema()` calls | Completed | 20261124-213918 | 20261124-213918 | REQ-002 Changed: scripts/mcp_servers/github/tools_pull_requests.py (-107/+15 lines). Six literals replaced via a line-based swap script (explicit tool->model table, ast.parse validated) because seq 08-11 repeat the same replacement. |
| 2 | Confirm `dry_run` publication for the three write tools | Completed | 20261124-213918 | 20261124-213918 | REQ-003 Dumped TOOL_LIST: dry_run published on create/update/merge pull_request; per_page published on list_pull_requests with minimum 1 / maximum 100. |
| 3 | Run the validation sequence (`rules/toolchain.md`) for this file | Completed | 20261124-225226 | 20261124-225226 | T-02, T-06 ruff format/check, mypy, check_module_size, generate_reference_table --check, lint-imports (6 KEPT) pass; tests/mcp_servers/github/ + test_tool_schema_contract.py = 411 passed. Full-suite run is the end-of-batch run. End-of-batch run (rules/toolchain.md, Batch mode): full pytest 13959 passed / 5 skipped / 6 errors; all 6 errors are the pre-existing tests/tools/test_append_plan_work_items.py contract mismatch (issues/20261124-155017_qa001_append-plan-attr-mismatch.md), none in this batch's files. ruff format+check, mypy, lint-imports, check_module_size, bandit, check_docstrings (after adding the em-dash separator to scripts/mcp_servers/request_contract.py), and diff-cover --fail-under 90 Pass. pre-commit run --all-files fails only on 14 pre-existing procedure-length findings in implementations/20261124-122732_* (issues/20261124-155017_qa002_workitem-structure-unknowns-kind.md); check_workitem_structure --file on this batch's documents reports no findings. |
| 4 | Update documentation | Completed | 20261124-213918 | 20261124-213918 | N/A: recorded by seq 18 N/A: recorded by seq 18. |

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