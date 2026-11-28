## Goal

Add the store-kind case for a write tool that declares no scope keys, so the resolver's store-identity rule is pinned by a test while the existing key-declaring store case still passes (`REQ-002`, `AC-3`).

## Scope
**Release unit**: N/A: not part of a release unit

- One new case in `TestResolveResourceScopes`: a store-kind write with `resource_scope_keys={}` resolves to `<kind>:<server_key>`.
- `test_mdq_store_resolves_fixed_scope` (lines 164-171) keeps asserting `("mdq_store:default",)` from a declared key.
- The global-fallback cases (lines 186-199 and the `github_branch` case) are unchanged.

## Assumptions

- The `_tool()` helper defaults `server_key` to `"s"`, so the expected string is `("mdq_store:s",)` without changing the helper.
- The identity comes from `RuntimeTool.server_key`, not from an argument, so the case passes no argument value for the identity (`args={}`), which is the condition the resolver branch checks.
- The global-fallback cases use `filesystem` and `github_branch`, not a store kind, so they stay green; the fail-closed posture documented in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:122` is not being tested away.
- Classification: the module is in a classified area and is tracked unclassified in `tools/test_taxonomy_baseline.txt` line 220 with no marker, so no finding arises. Keeping it as it is avoids the `baseline-entry-classified` finding; if the new assertions are classified as `contract`, the baseline entry must be removed in the same change.
- The conflict side of `AC-3` is asserted through the existing `_scopes_conflict` tests: equal scope strings already conflict, so one added case asserts two equal store scopes conflict.

## Design decisions

- Assert the resolved string through the resolver's own convention (`kind:identity`) rather than hard-coding an MDQ name, so the case matches the rule row 05 implements by kind.

## Alternatives considered

- Re-express the global-fallback tests as store-kind cases: rejected, the fallback still applies to kinds that declare keys, and those tests are what pin it.

## Implementation
### Target file
`tests/shared/test_resource_scope.py`

### Procedure
1. Add `test_store_kind_write_with_no_declared_keys_resolves_store_identity` (new): `resource_scope_kind="mdq_store"`, `resource_scope_keys={}`, `is_write=True`, `args={}` → `("mdq_store:s",)`.
2. Add one `_scopes_conflict` case asserting two equal store scopes conflict.
3. Keep the existing cases unchanged.

### Method

- The new cases follow the module's existing style: fixture-built `RuntimeTool`, direct call to `resolve_resource_scopes()`, tuple comparison.

### Details

- Add a `rag_store` no-keys case with the same expectation shape, since row 05 defines the rule by kind class and the resolver change affects that entry too (`scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py:131`).

## Compatibility considerations

- The module is also read by the `workitem-structure` and taxonomy gates; keep the docstring citation consistent with whichever classification is chosen (see Assumptions).

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/shared/test_resource_scope.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- A store-kind write with no declared keys resolves to the store identity (`AC-3`).
- A store kind that declares keys still resolves through the existing convention, and a key-declaring write that resolves nothing still falls back to `global:write`.

## Out of Scope

- The resolver branch itself (`scripts/shared/resource_scope.py`, row 05).
- The MDQ entry declarations (`scripts/mcp_servers/mdq/mdq_tools.py`, row 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 3 |
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
- **Requirement ID**: REQ-002, AC-3
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/shared/test_resource_scope.py`
