## Goal

Resolve a store-kind write that declares no scope keys to the store identity `<kind>:<server_key>` instead of the fail-closed synthetic global write scope, so the two MDQ write tools occupy one stable scope regardless of argument order or duplication (`REQ-002` stable store identity).

## Scope
**Release unit**: N/A: not part of a release unit

- `resolve_resource_scopes()` gains one branch for a store-kind write with no declared keys, placed before the `_FALLBACK_WRITE_SCOPE` return (132-134).
- Store kinds that declare keys keep the current behavior, including the `str(value)` normalization at 129.

## Assumptions

- `mdq_store` is already in `_KNOWN_SCOPE_KINDS` (52) and is not in `_FILESYSTEM_LIKE_KINDS` (59), so the change is a new branch for the no-keys case, not a change to normalization.
- The identity source is `RuntimeTool.server_key` (`scripts/shared/runtime_tool.py:83`), because the schema-2.1 contract requires every `resource_scope_keys` entry to be an argument property (`_scope_keys_problems()`, 169-175) and a store identity cannot come from args without a client-controlled field. The alternative is the Plan's UNK-03, not decided here.
- The rule is defined by kind, so the other store-kind write, `rag_store` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py:131`, already declaring no keys), changes its resolved scope string from `global:write` to `rag_store:<server_key>`. Both are `requires_serial: True`, so serialization is unchanged; only the conflict-graph name changes. Recorded as the Plan's UNK-04 and confirmed with the scheduler owner before merging.
- The tests that pin the global fallback pin `filesystem` and `github_branch` kinds only (`tests/shared/test_resource_scope.py:186-199`, `tests/shared/test_runtime_tool_registry.py:102,143`, `tests/shared/test_tool_routing_validation.py:100,144`, `tests/agent/test_tool_scheduler_serialization.py:178`), so they are unaffected by the store-kind branch; the closed `ResourceKeyKind` set pinned by `tests/shared/test_tool_metadata.py:53` is not touched.
- MDQ is a single store (`config/mdq_mcp_server.toml:16`, `scripts/mcp_servers/mdq/health_check.py:182`), so the server key identifies it.

## Design decisions

- Define the identity by kind class (a store kind with no declared keys) rather than by an MDQ-specific special case, so both store-kind writes follow one rule and the plan default is not a server name hard-coded in the resolver.
- Keep the fail-closed fallback for kinds that declare keys but resolve nothing, so the fail-closed posture documented in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:122` is preserved for those kinds.

## Alternatives considered

- Add a `ResourceKeyKind` value for a store identity: rejected, the identity would still come from args and the value set is closed and pinned (`tests/shared/test_tool_metadata.py:53`).
- Add a server-owned identity field to the schema-2.1 contract: rejected as the plan default, it changes `validate_tool_schema_v2()` and the `RuntimeTool` required-field contract and needs the contract owner (Plan UNK-03).

## Implementation
### Target file
`scripts/shared/resource_scope.py`

### Procedure
1. In `resolve_resource_scopes()`, before the no-resolved-scope fallback, return `f"{kind}:{server_key}"` when the tool is a write, its kind is a store kind, and `resource_scope_keys` is empty.
2. Leave the declared-key loop and `_FALLBACK_WRITE_SCOPE` unchanged.

### Method

- The convention `f"{kind}:{identity}"` is the one already documented in the resolver's docstring (90-91); the new branch fills the identity from a server-owned value instead of an argument value.
- `_scopes_conflict()` is not modified: equal scope strings already conflict (the exact-equal case in the predicate, 138-141), so two calls to `index_paths` and `refresh_index` conflict once they resolve to the same string.

### Details

- After row 02 removes the `{"paths": "path"}` declarations, no tool in the repository resolves a list-valued scope key, so the order- and duplicate-sensitivity is removed by the declaration plus this branch, not by new normalization code.
- The store-kind set is the existing `mdq_store` and `rag_store` entries in `_KNOWN_SCOPE_KINDS`; the branch keys on those two values, not on the tool name.

## Compatibility considerations

- Blast radius is high: the resolver is shared by every MCP server and the Agent conflict graph, so the agent and every MCP server restart at deploy time (`rules/workflow-lifecycle.md`, Plan's Affected areas row).
- `scripts/shared/runtime_tool_registry.py` and `scripts/agent/tool_scheduler.py` consume the predicate unchanged; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` is updated by row 15 to record the store-kind rule.
- `ADR basis` is unchanged: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:72` names `resource_scope_kind` and `resource_scope_keys` as producer-declared fields; this row changes how a declared kind resolves, not who declares it.

## Security considerations

- The identity is server-owned rather than argument-derived, so a caller cannot widen or narrow the scope through an argument value; the fail-closed posture for kinds that declare keys is preserved.

## Rollback considerations

- N/A: revert the commit; no persisted state depends on the resolved scope string.

## Validation plan

- `uv run pytest tests/shared/test_resource_scope.py tests/shared/test_runtime_tool_registry.py tests/agent/test_tool_scheduler_serialization.py`
- `uv run ruff check scripts/shared/resource_scope.py && uv run mypy scripts/shared/resource_scope.py`
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the `rules/toolchain.md` threshold.

## Completion criteria

- `index_paths` and `refresh_index` resolve to the same store scope string for any argument order or duplication (`AC-3`).
- A store kind that declares keys still resolves through the existing convention, and a key-declaring write that resolves nothing still falls back to `global:write`.

## Out of Scope

- The tool declarations that must stop declaring path keys (`scripts/mcp_servers/mdq/mdq_tools.py`, row 02).
- The scheduler's conflict grouping and the read/read non-conflict rule (`scripts/agent/tool_scheduler.py`): consumed unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 3 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Assertions live in rows 07, 11 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Row 15 records the rule in the dispatch-and-routing doc |

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
- **Requirement ID**: REQ-002 (store-kind write resolves to one stable store identity)
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `scripts/shared/resource_scope.py`
