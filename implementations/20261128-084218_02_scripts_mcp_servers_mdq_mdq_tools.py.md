## Goal

Make each MDQ tool entry publish the schema generated from its request model, declare the store scope without path-derived keys, and stop advertising `with_neighbors` (`REQ-001` one source for the request contract, `REQ-002` stable store identity, `REQ-005` remove an unimplemented field).

## Scope
**Release unit**: N/A: not part of a release unit

- The 7 hand-written `inputSchema` blocks (lines 17, 85, 119, 155, 184, 217, 235) are replaced by calls to the shared generator.
- `resource_scope_keys` for `index_paths` (179) and `refresh_index` (212) becomes an empty mapping.
- The `get_chunk` entry's description loses the `with_neighbors` sentence; the property itself disappears with the generated schema.

## Assumptions

- `RuntimeTool.resource_scope_keys` is a required mapping field (`scripts/shared/runtime_tool.py:92`), so "declares no keys" is written as `{}` rather than by omitting the key; `scripts/shared/resource_scope.py::_scope_keys_problems()` accepts an empty mapping, so `validate_tool_schema_v2()` keeps passing.
- The tool count is unchanged (7 entries), so `tests/mcp_servers/mdq/test_mdq_routing.py:209` and `docs/22_mcp/mcp_01_tool_ownership_matrix.md:95` are unaffected.
- `is_write`, `requires_serial: True` (177, 210), `side_effect_class`, and the other registry fields stay as they are; the guardrail test pins the write flags.
- The read tools keep `resource_scope_kind: ""` (79, 113, 149, 229, 280): reads stay outside the conflict graph.
- The generated schema keeps the same advertised values because the bounds live as model constraints in row 01; this row does not restate them.

## Design decisions

- Call `build_input_schema()` (`scripts/mcp_servers/request_contract.py:44`) per entry instead of writing the schema inline, so the published schema and the enforced model cannot drift.
- Keep the entry descriptions as they are except for the removed field, so LLM-visible wording stays reviewable as a one-line change.

## Alternatives considered

- Keep the hand-written blocks and add a drift test: rejected, `REQ-001` requires one source, and a test cannot fix a schema that is authored twice.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_tools.py`

### Procedure
1. Replace each `inputSchema` block with `build_input_schema(<request model>)` for that tool's model.
2. Set `resource_scope_keys` to `{}` for `index_paths` and `refresh_index`; keep `resource_scope_kind: "mdq_store"`.
3. Remove the `with_neighbors` wording from the `get_chunk` description.

### Method

- `TOOL_LIST` entries stay plain dicts with the same keys; only the `inputSchema` value changes from a literal to a generator call, so the registry path (`scripts/shared/runtime_tool_registry.py`) reads the entry unchanged.
- The generator strips presentation `title` keys, so the published schema is the model's validation-only shape; the values asserted by `tests/mcp_servers/mdq/test_mdq_tool_schema.py` come from the model's `Field` constraints.

### Details

- Model-to-tool mapping: `SearchDocsRequest`, `GetChunkRequest`, `OutlineRequest`, `IndexPathsRequest`, `RefreshIndexRequest`, `StatsRequest`, `GrepDocsRequest` (`scripts/mcp_servers/mdq/mdq_models.py`).
- The entry for `stats` currently publishes an empty properties object (line 217); after the change it is `build_input_schema(StatsRequest)`, which publishes the model's fields.

## Compatibility considerations

- Optional fields now render as `anyOf` in the published schema instead of a hand-written `type`; `tests/mcp_servers/mdq/test_mdq_tool_schema.py` (row 06) is updated to read the generated schema, and `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py` (row 07) compares entry schemas with the generated ones.
- Clients that send `with_neighbors` start failing validation, which is the intended contract change (`REQ-005`).

## Security considerations

- Path authorization (`allowed_dirs`, `authorize_path()`) is not changed by this row; declaring no scope keys only changes the scope string the scheduler sees, not access control.

## Rollback considerations

- N/A: revert the commit; no persisted state depends on the entry shape.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py tests/mcp_servers/mdq/test_mdq_tool_schema.py`
- `uv run ruff check scripts/mcp_servers/mdq/mdq_tools.py && uv run mypy scripts/mcp_servers/mdq/mdq_tools.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- Each entry's `inputSchema` is the model's generated schema (`AC-2`).
- The two write entries declare `mdq_store` with no keys, so the resolved scope does not depend on argument order or duplication (`AC-3`).
- `with_neighbors` is absent from the generated schema and the description (`REQ-005`).

## Out of Scope

- The scope-resolution rule itself (`scripts/shared/resource_scope.py`, row 05).
- Model field constraints (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 and Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in rows 06, 07 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Row 14 states the contract in the mdq doc |

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
- **Requirement ID**: REQ-001 (one source for the request contract), REQ-002 (stable store scope identity), REQ-005 (remove `with_neighbors`)
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `scripts/mcp_servers/mdq/mdq_tools.py`
