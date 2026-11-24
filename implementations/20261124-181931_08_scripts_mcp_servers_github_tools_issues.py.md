## Goal
Publish the issues-domain schemas from their request models instead of hand-written dicts, so the
discovered contract equals the runtime contract and `dry_run` becomes visible on the two write tools
(REQ-002 generate every `inputSchema` from its model; REQ-003 publish `dry_run` on write tools).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `scripts/mcp_servers/github/tools_issues.py` (Plan Phase 2).
- This row is the pattern-setter: seq 09, 10, 11 repeat it for the other three domains.

## Assumptions
- `build_input_schema()` exists from seq 01 and the issues models are strict from seq 03.
- Verified today (`MCP_GITHUB_AUTH_TOKEN=x uv run python`, `TOOL_LIST` dump): the five published
  issues schemas declare no validation keyword at all, and `github_list_issues` does not declare
  `per_page` although `ListIssuesRequest` accepts it.
- The schema-2.1 metadata fields (`policy_version`, `status`, `config_dependent`, `is_write`,
  `requires_serial`, `resource_scope_kind`, `resource_scope_keys`, `preview_capability`,
  `agent_safety_tier`, `side_effect_class`, `retry_policy`) are a separate contract validated by
  `scripts/shared/resource_scope.py::validate_tool_schema_v2()` and by
  `tests/mcp_servers/test_tool_schema_contract.py`; only `inputSchema` changes here.
- `preview_capability: "dry_run"` stays as the metadata signal; REQ-003 is satisfied by `dry_run`
  appearing in `properties`, not by removing that field.

## Design decisions
- Each entry keeps its `"name"`, `"description"`, and every metadata head/tail spread unchanged; only
  the `"inputSchema"` value is replaced by a call, e.g.
  `"inputSchema": build_input_schema(ListIssuesRequest)`.
- Schemas are computed once at module import (inside the `TOOL_LIST` literal), not lazily: the
  module is imported at server start anyway, and a single computation per tool is what lets the seq 14
  drift gate compare the published dict with a fresh generator call.
- Models are imported from their own domain module (`from mcp_servers.github.github_models_issues
  import ...`), not from the `github_models.py` re-export shim, so the dependency is explicit.

## Alternatives considered
- Registering `tool_validators.py` validators per GitHub tool: rejected in the Plan Design — it
  duplicates the model as a second validator definition, the exact drift pattern this Issue removes.
- Keeping the hand-written dicts and only adding `dry_run` by hand: rejected — AC-01/AC-05 require the
  schema to be derived from the model, and a hand-maintained copy is what drifted today.

## Implementation
### Target file
`scripts/mcp_servers/github/tools_issues.py`

### Procedure
1. Add `from mcp_servers.request_contract import build_input_schema` and
   `from mcp_servers.github.github_models_issues import (AddIssueCommentRequest, CreateIssueRequest,
   GetIssueRequest, ListIssuesRequest, SearchIssuesRequest)`.
2. Replace the five `"inputSchema": { ... }` literals (starting at lines 73, and the corresponding
   blocks for `github_get_issue`, `github_create_issue`, `github_search_issues`,
   `github_add_issue_comment`) with `build_input_schema(<Model>)` for the matching model.
3. Keep the `_GithubIssueMetadataHead` / `_GithubIssueRepoScopeTail` / `_GithubIssueNoScopeTail`
   TypedDicts and both spread sites exactly as they are.
4. Delete the now-unused hand-written schema text only after the matching entry is replaced (no
   leftover dict fragments).

### Method
- One-to-one tool/model mapping: `github_list_issues` -> `ListIssuesRequest`, `github_get_issue` ->
  `GetIssueRequest`, `github_create_issue` -> `CreateIssueRequest`, `github_search_issues` ->
  `SearchIssuesRequest`, `github_add_issue_comment` -> `AddIssueCommentRequest`.

### Details
- The tool `description` strings stay hand-written (they are prose guidance, not a validation
  contract); only the per-field descriptions come from the models' `Field(description=...)` text.
- The comment above the TypedDicts (lines 17-25) stays valid: nothing about the metadata split changes.

## Compatibility considerations
- Newly accepted inputs for these tools (record in seq 18): `dry_run` on `github_create_issue` and
  `github_add_issue_comment`; `per_page` on `github_list_issues` (accepted by the model but absent
  from the published dict today, so the agent-side gate rejected it before).
- Newly rejected inputs: any key absent from `properties` (`additionalProperties: false`), an empty
  `owner`/`repo`/`query`/`title`/`body`, `issue_number < 1`, `per_page > 100`, `title` over 256,
  `body` over 65536, more than 100 `labels`/`assignees`, and a `state` value outside the model pattern.
- `tests/mcp_servers/test_tool_schema_contract.py` imports these `TOOL_LIST` exports and validates
  metadata fields only; it must keep passing without edits.
- `/v1/tools` payload changes for these five tools; tool names, count (5), ports, and the
  `mcp_01_tool_ownership_matrix.md` generated block are unchanged (`generate_reference_table.py --check`).

## Security considerations
- The published schema becomes enforceable: `additionalProperties: false` plus model bounds mean the
  agent-side gate and the server enforce the same rules before any GitHub API call (AC-03).

## Rollback considerations
- Revert this Phase 2 commit: the five hand-written dicts return; models stay strict (seq 03) but
  their bounds stop being advertised until re-applied.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02 drift gate, seq 14) and
  `uv run pytest tests/mcp_servers/test_tool_schema_contract.py`.
- `uv run pytest tests/mcp_servers/github/` (domain regression).
- `uv run ruff check`, `uv run mypy`, `uv run lint-imports`, `uv run python tools/check_module_size.py`
  (the file shrinks as dicts are replaced), `uv run python tools/generate_reference_table.py --check`
  (T-06).

## Completion criteria
- All five entries have `inputSchema` produced by `build_input_schema()` and no hand-written schema
  literal remains in the file.
- `github_create_issue` and `github_add_issue_comment` published schemas contain a `dry_run` property
  with `default: false` (AC-01).
- Metadata validation tests and the tool count (`5` in this file, `21` overall) still pass.

## Out of Scope
- Model changes (seq 03), other domains (seq 09-11), the drift gate itself (seq 14), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the five `inputSchema` literals with `build_input_schema()` calls | Pending | — | — | REQ-002 |
| 2 | Confirm `dry_run` publication for the two write tools | Pending | — | — | REQ-003 |
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
- **Related target files**: `scripts/mcp_servers/github/tools_issues.py`
