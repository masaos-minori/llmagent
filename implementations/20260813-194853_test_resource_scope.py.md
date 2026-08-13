## Goal

Add `tests/shared/test_resource_scope.py`, the unit-test suite for the new
`scripts/shared/resource_scope.py` module: `resolve_resource_scopes()`,
`_scopes_conflict()`, and `validate_tool_schema_v2()`, covering every scenario the plan's
Phase 1 bullet enumerates plus the validator's acceptance/rejection cases.

## Scope

In scope: creating `tests/shared/test_resource_scope.py` exercising only
`scripts/shared/resource_scope.py`'s public/internal surface via direct unit tests
(constructing `RuntimeTool` fixtures with `build_runtime_tool()` and plain `dict` args).
Out of scope: testing `runtime_tool_registry.py`'s integration of this module (covered by
the `test_runtime_tool_registry.py` doc) and testing any MCP server `TOOL_LIST` against
`validate_tool_schema_v2()` (Phase 2's separate `tests/mcp_servers/test_tool_schema_contract.py`,
not in this doc set).

## Assumptions

- This test file imports `build_runtime_tool` from `shared.runtime_tool` (already
  updated per the `runtime_tool.py` doc, so `resource_scope_kind`/`resource_scope_keys`
  are available as constructor kwargs) to build realistic `RuntimeTool` fixtures rather
  than hand-rolling dataclass instances.
- `resolve_resource_scopes(tool, args)` and `_scopes_conflict(a, b)` are both importable
  from `shared.resource_scope` (the latter as a "private" name, acceptable to import
  directly in a unit test file per this repo's existing convention of testing
  underscore-prefixed helpers directly, e.g. no leading-underscore avoidance is visible
  elsewhere in `tests/shared/`).
- `validate_tool_schema_v2(entry)` takes a plain `dict` shaped like an MCP server's raw
  tool-list entry (`name`, `inputSchema`, `is_write`, `requires_serial`,
  `resource_scope_kind`, `resource_scope_keys`), independent of `RuntimeTool`.

## Design decisions

- **One test class per function**, mirroring this repo's existing convention (e.g.
  `TestRuntimeTool` in `test_runtime_tool.py`, `TestRuntimeToolRegistry` in
  `test_runtime_tool_registry.py`): `TestResolveResourceScopes`, `TestScopesConflict`,
  `TestValidateToolSchemaV2`.
  - **Scenario-per-test-method**, not table-driven `pytest.mark.parametrize`, matching
  the existing style in `test_runtime_tool.py`/`test_runtime_tool_registry.py` (both use
  one method per named scenario, no `parametrize` usage observed in either file).

## Alternatives considered

Using `pytest.mark.parametrize` for the many scope-kind resolution cases (filesystem,
git, github, cicd, rag, mdq, shell) to reduce line count. Rejected in favor of matching
the existing one-method-per-scenario style already established in
`tests/shared/test_runtime_tool.py` and `test_runtime_tool_registry.py`, both read as
part of this doc set's grounding — consistency with sibling test files in the same
directory outweighs the line-count savings.

## Implementation

### Target file: `tests/shared/test_resource_scope.py` (new)

### Procedure

1. Create the file with a module docstring in the established
   `"""tests/shared/test_resource_scope.py\nUnit tests for ...` format (matching
   `test_runtime_tool.py` line 1–2 and `test_runtime_tool_registry.py` line 1–4 exactly
   in style).
2. Add imports: `from __future__ import annotations`; `from shared.resource_scope import
   resolve_resource_scopes, validate_tool_schema_v2` and, separately,
   `from shared.resource_scope import _scopes_conflict` (or import the module and access
   `resource_scope._scopes_conflict`, whichever reads cleaner — prefer the direct
   `from ... import _scopes_conflict` form for symmetry with the other two imports);
   `from shared.runtime_tool import build_runtime_tool`.
3. Add a small fixture helper, e.g. `_tool(**overrides)`, wrapping `build_runtime_tool(
   name="t", server_key="s", **overrides)` to keep each test's `RuntimeTool` construction
   terse, mirroring `test_runtime_tool.py`'s own `_minimal_kwargs()` helper pattern
   (lines 13–15).
4. Implement `TestResolveResourceScopes` with one method per scenario from the plan's
   Phase 1 bullet:
   - `test_filesystem_exact_match_resolves_single_scope` — tool with
     `resource_scope_kind="filesystem"`, `resource_scope_keys=("path",)`,
     `is_write=True`; args `{"path": "/data/a.txt"}`; assert result ==
     `("filesystem:/data/a.txt",)`.
   - `test_filesystem_ancestor_descendant_pair_resolves_distinct_scopes` — two separate
     `resolve_resource_scopes()` calls (one for a directory-like path, one for a nested
     file path under it) each resolving to their own distinct `"filesystem:..."` string;
     this test asserts *resolution* produces the two different strings (the
     *conflict-detection* of that ancestor/descendant pair is `TestScopesConflict`'s job,
     not this class's).
   - `test_move_file_resolves_dual_source_destination_scopes` — tool with
     `resource_scope_kind="filesystem"`, `resource_scope_keys=("source", "destination")`,
     `is_write=True`; args `{"source": "/a/x.txt", "destination": "/b/y.txt"}`; assert
     result == `("filesystem:/a/x.txt", "filesystem:/b/y.txt")` (order preserved,
     matching `resource_scope_keys` declaration order).
   - `test_git_repo_same_and_different_repo_paths_resolve_distinct_scopes` — kind
     `"git_repo"`, key `("repo_path",)`; two calls with the same vs. different
     `repo_path` values resolve to equal vs. different scope strings respectively.
   - `test_github_repo_scope_composes_owner_and_repo` — kind `"github_repo"`, keys
     `("owner", "repo")`; args `{"owner": "org", "repo": "name"}`; assert result contains
     a scope string equal to `"github_repo:org/name"` (per the plan's Design section
     example).
   - `test_cicd_workflow_scope_composes_repo_workflow_ref` — kind `"cicd_workflow"`,
     keys `("repo", "workflow", "ref")`; args `{"repo": "org/repo", "workflow": "ci.yml",
     "ref": "main"}`; assert result == `("cicd_workflow:org/repo:ci.yml:main",)` (per the
     plan's Design section literal example string).
   - `test_rag_store_and_mdq_store_resolve_fixed_scope` — two sub-cases (or two test
     methods) for `resource_scope_kind="rag_store"`/`"mdq_store"` with a fixed key (e.g.
     `("store",)`) and args `{"store": "default"}`, asserting `"rag_store:default"` /
     `"mdq_store:default"` respectively, matching the plan's literal examples.
   - `test_shell_fixed_process_scope_ignores_args` — kind `"process"`,
     `resource_scope_keys=()`, `is_write=True`; called with empty `args={}`; since
     `is_write=True` and no keys resolve, expect the fallback `("global:write",)` *unless*
     the shell tool is modeled with a synthetic always-present key — per the plan's
     literal example `"process:global"`, model this instead as
     `resource_scope_keys=("scope",)` with args `{"scope": "global"}` resolving to
     `("process:global",)`, keeping the fallback case fully separate (see next bullet).
   - `test_unscoped_read_returns_empty_tuple` — `resource_scope_kind=""`, `is_write=False`;
     any args; assert result == `()`.
   - `test_known_write_tool_with_unresolvable_scope_falls_back_to_global_write` — tool
     with `is_write=True`, non-empty `resource_scope_kind`/`resource_scope_keys` (e.g.
     `"filesystem"`/`("path",)`) but args missing that key entirely (`args={}`); assert
     result == `("global:write",)` — explicitly also assert the tool's own `name` never
     appears anywhere in the result, matching the plan's "never the tool name" acceptance
     criterion.
5. Implement `TestScopesConflict` with:
   - `test_identical_scope_strings_conflict`.
   - `test_different_kind_prefixes_never_conflict_even_with_same_suffix` — e.g.
     `"filesystem:/a"` vs. `"git_repo:/a"` — asserts `False`, directly testing the UNK-05
     resolution (kind-prefix namespacing prevents cross-kind collision).
   - `test_filesystem_descendant_path_conflicts_with_ancestor` — `"filesystem:/data"` vs.
     `"filesystem:/data/a.txt"` — asserts `True` in both argument orders (symmetry check).
   - `test_filesystem_unrelated_siblings_do_not_conflict` — `"filesystem:/data/a"` vs.
     `"filesystem:/data/b"` — asserts `False`.
   - `test_non_filesystem_equal_kind_different_value_does_not_conflict` — e.g.
     `"git_repo:/x"` vs. `"git_repo:/y"` — asserts `False` (only exact match or
     filesystem ancestor/descendant conflict; no other overlap rule exists).
6. Implement `TestValidateToolSchemaV2` with:
   - `test_accepts_fully_declared_entry` — a complete, valid entry dict; assert result
     `== []`.
   - `test_rejects_missing_name`.
   - `test_rejects_missing_or_invalid_input_schema`.
   - `test_rejects_missing_is_write`, `test_rejects_non_bool_is_write` (e.g. `is_write=1`).
   - `test_rejects_missing_requires_serial`, `test_rejects_non_bool_requires_serial`.
   - `test_rejects_unknown_resource_scope_kind` — e.g. `resource_scope_kind="bogus"`.
   - `test_rejects_resource_scope_key_absent_from_input_schema_properties` — a key listed
     in `resource_scope_keys` that is not a key of `inputSchema["properties"]`.
   - `test_accepts_empty_resource_scope_kind_and_keys` — the unscoped-tool case
     (`resource_scope_kind=""`, `resource_scope_keys=[]`) is valid on its own.

### Method

Plain `pytest` test classes/methods, each self-contained (build its own `RuntimeTool`/
`dict` fixture inline or via the `_tool()` helper, call the function under test, assert).
No shared mutable fixtures across tests; no mocking needed since
`scripts/shared/resource_scope.py` is pure.

### Details

- Test file location/name: `tests/shared/test_resource_scope.py`, alongside its sibling
  `test_runtime_tool.py`/`test_runtime_tool_registry.py` in the same directory.
- Every `resolve_resource_scopes()` test that expects a non-fallback result must use a
  tool constructed via `build_runtime_tool(..., resource_scope_kind=..., resource_scope_keys=(...))`
  — never construct `RuntimeTool(...)` directly, to also exercise `build_runtime_tool()`'s
  own default-resolution path incidentally (consistent with how `test_runtime_tool_registry.py`
  exclusively uses `build_runtime_tool()` for its fixtures too, per `_registry_with()`'s
  usage throughout that file).
- The fallback test (`test_known_write_tool_with_unresolvable_scope_falls_back_to_global_write`)
  is the single most safety-critical case in this file — it directly tests the plan's
  fail-closed acceptance criterion and must remain even if other cases are later
  trimmed for time.

## Compatibility considerations

N/A — new test file, no existing test behavior to preserve.

## Security considerations

This test file is the primary regression guard for the fail-closed fallback behavior
(`("global:write",)`) and for the cross-kind non-collision guarantee (UNK-05); both are
security-relevant (an incorrect scope resolution could let two conflicting writes run
concurrently). Do not weaken or remove
`test_known_write_tool_with_unresolvable_scope_falls_back_to_global_write` or
`test_different_kind_prefixes_never_conflict_even_with_same_suffix` without an explicit,
separate design decision.

## Rollback considerations

Deletable independently of source changes (test-only file); however it will fail to
collect/import if `scripts/shared/resource_scope.py` (its subject) is reverted without
also reverting this file, so revert both together.

## Validation plan

- `uv run pytest tests/shared/test_resource_scope.py -v` — every case above passes.
- `uv run pytest tests/shared/test_resource_scope.py --cov=shared.resource_scope --cov-report=term-missing` —
  confirms all branches of `resolve_resource_scopes()`/`_scopes_conflict()`/
  `validate_tool_schema_v2()` are exercised (informal local check; the plan's formal gate
  is the repo-wide `diff-cover ≥ 90%` run in Phase 3, out of scope here).

## Out of scope

Testing `runtime_tool_registry.py`'s call to `resolve_resource_scopes()` (covered in
`test_runtime_tool_registry.py`), testing any real MCP server `TOOL_LIST` against
`validate_tool_schema_v2()` (Phase 2's `tests/mcp_servers/test_tool_schema_contract.py`).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-183049_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-194853
- Related target files: tests/shared/test_resource_scope.py
