## Goal

Add the two guardrails this module lacks: each tool entry publishes its model's generated schema, and the two MDQ write tools resolve to the same store scope (`REQ-001`, `REQ-002`, `AC-1`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

- Two new test functions: each entry's `inputSchema` equals `build_input_schema(model)`; the write entries resolve to the same store scope, both through the resolver and through the `ToolSpec` the scheduler receives.
- The existing 6 name/registry/write-flag assertions are unchanged.

## Assumptions

- The name-to-model mapping is the one row 02 uses: `search_docs`/`SearchDocsRequest`, `get_chunk`/`GetChunkRequest`, `outline`/`OutlineRequest`, `index_paths`/`IndexPathsRequest`, `refresh_index`/`RefreshIndexRequest`, `stats`/`StatsRequest`, `grep_docs`/`GrepDocsRequest` (`scripts/mcp_servers/mdq/mdq_models.py`).
- `resolve_resource_scopes()` needs a `RuntimeTool`, and a `TOOL_LIST` entry has no `server_key` field: the server key comes from the registry route (`shared.tool_registry.get_registry().get_server_for_tool()`, `mdq` for all 7 entries), so the new scope test builds the fixture with `server_key="mdq"` from the entry's declared `resource_scope_kind` and `resource_scope_keys`.
- Cross-area import of `tests.shared.runtime_tool_factory.build_fixture_runtime_tool()` is the established convention (`tests/agent/` and `tests/integration/` already import it), and import-linter contracts cover `scripts/` packages only, so the test import is not a boundary finding.
- The `ToolSpec` assertion goes through `RuntimeToolRegistry.tool_spec_for_call()` (`scripts/shared/runtime_tool_registry.py:253`), whose `resource_scopes` come from `resolve_resource_scopes()`; the fixture is built with `build_runtime_tool()`, the same single construction point the discovery path uses (`scripts/agent/services/mcp_tool_discovery_registry.py:82`), so the assertion covers the discovery-to-`ToolSpec` route without starting a server.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.

## Design decisions

- Assert equality with the generated schema through the same generator the production entry uses, so the guardrail cannot pass against a hand-written block that happens to look the same.
- Assert the two write tools produce the same string, rather than asserting the string's literal form, so the guardrail tests the requirement (one stable identity) and not the formatting convention.

## Alternatives considered

- Assert the literal `mdq_store:mdq` scope: rejected, the literal form is row 11's case; this row pins that both tools agree, which is `AC-3`.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`

### Procedure
1. Add a name-to-model mapping constant and assert `entry["inputSchema"] == build_input_schema(model)` for every entry.
2. Add a test that builds a `RuntimeTool` fixture from each write entry's declared fields and asserts the two resolved scope strings are equal and non-empty.
3. Assert the same equality through `tool_spec_for_call()` for both write tools, so the scope the scheduler receives is the same for either tool.
4. Record the RAG store-kind consequence in the test docstring as the documented effect of the rule (Plan UNK-04); no assertion of the RAG entry's declaration is added here, because that file is not a target row.
5. Keep the existing 6 assertions as they are.

### Method

- The schema test reads the entry dict as it is, so it verifies what the registry publishes to the LLM, not the model alone.
- The scope test passes two different argument orders (`{"paths": ["a", "b"]}` and `{"paths": ["b", "a"]}`) to catch order sensitivity, which is the failure `AC-3` is about.

### Details

- The fixture builder's policy-field defaults are conservative, so the assertion depends only on `name`, `server_key`, `is_write`, `resource_scope_kind`, and `resource_scope_keys`.

## Compatibility considerations

- `N/A: test-only change; no other module reads this file.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Each entry's published schema equals its model's generated schema (`AC-1`).
- `index_paths` and `refresh_index` resolve to the same scope string for any argument order (`AC-3`).

## Out of Scope

- The resolver branch itself (`scripts/shared/resource_scope.py`, row 05).
- The entry declarations (`scripts/mcp_servers/mdq/mdq_tools.py`, row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 and Phase 3 (guardrail tests) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, AC-1, AC-3
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
