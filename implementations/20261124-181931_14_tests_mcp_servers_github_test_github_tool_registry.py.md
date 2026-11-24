## Goal
Make CI fail when a GitHub request model and its published `inputSchema` drift, and assert that every
write tool publishes `dry_run` (REQ-009, model-to-schema consistency gate; REQ-003, `dry_run`
publication).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/mcp_servers/github/test_github_tool_registry.py` (Plan Phases 2-5, T-02).
- Existing tests in this file (21-tool count, registry mapping, `name` field) stay unchanged.

## Assumptions
- The gate is added incrementally per domain (seq 08/09/10/11 each extend the mapping) so the mapping
  never lags behind a migrated domain — the Plan's phases stay individually verifiable.
- The file today imports `TOOL_LIST` from `mcp_servers.github.github_tools` (the aggregate) and pins
  `len(TOOL_LIST) == 21` at line 16; the tool count does not change in this Plan.
- `build_input_schema()` (seq 01) is the same function the tools rows call, so the comparison is exact
  equality of two calls, not a structural approximation.

## Design decisions
- One explicit `_TOOL_MODEL_MAP: dict[str, type[BaseModel]]` in the test file, plus a test that its key
  set equals the `TOOL_LIST` name set: a tool added, removed, or renamed fails the gate, so the mapping
  cannot silently lag the registry.
- The equality assertion compares `tool["inputSchema"]` with `build_input_schema(model)` directly. Any
  hand-written residue, missing `dry_run`, or dropped keyword fails with the diff in the message.
- `dry_run` presence is asserted from metadata (`tool["is_write"] is True`) rather than a hard-coded
  tool-name list, so a future write tool is covered without editing the test.

## Alternatives considered
- Putting the drift gate in `tests/mcp_servers/test_tool_schema_contract.py`: rejected — that file is the
  schema-2.1 *metadata* contract for all servers and has no model imports; the Plan resolves Issue Q3 to
  this GitHub consistency file (Plan Design, "Unresolved Question resolved with repository evidence").
- Comparing only property names: rejected — it would not catch a missing bound (`maximum`, `minLength`)
  or a missing `additionalProperties`.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_tool_registry.py`

### Procedure
1. Add a module-level `_TOOL_MODEL_MAP` (new) mapping each of the 21 tool names to its request model class
   imported from the four `github_models_*.py` modules.
2. Add `class TestGitHubModelSchemaConsistency` with:
   - `test_tool_model_map_covers_tool_list` (new): the map's keys equal the `TOOL_LIST` names.
   - `test_published_schema_equals_model_schema` (new) (parametrized over `_TOOL_MODEL_MAP` (new)):
     `tool["inputSchema"] == build_input_schema(model)`.
   - `test_write_tools_publish_dry_run` (new): for every entry with `is_write` True, `"dry_run"` is in
     `properties` and its generated `default` is `False`.
   - `test_generated_schemas_are_deterministic` (new): two generator calls for one model are equal, and the
     published dict contains no `title` key at the schema root (presentation stripping, REQ-002).
3. Keep every existing test and its docstring unchanged.

### Method
- Import `build_input_schema` from `mcp_servers.request_contract` at test scope (the file's existing
  style imports inside each test).

### Details
- Parametrize with the tool name (not the model) so a failure names the tool that drifted.

## Compatibility considerations
- Until the matching domain's tools row lands (seq 08-11), the entry for that domain still compares a
  hand-written dict with the generated schema and would fail: the gate must be extended in the same
  commit as its domain's tools row (seq 08 -> issues, seq 09 -> pull requests, seq 11 -> file,
  seq 10 -> repository).
- `tests/mcp_servers/github/test_service_dispatch.py:698` also pins `== 21`; unaffected.

## Security considerations
- The gate is the mechanism that keeps AC-01/AC-03 true over time; a silently hand-patched schema is the
  failure mode the Issue was created to remove.

## Rollback considerations
- Revert with the domain commit it was added in; the gate is additive and removes no existing test.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_tool_registry.py` (T-02).
- Deliberate drift check while developing: change one model bound locally, confirm the gate fails, then
  revert the local change (do not commit it).
- `uv run pytest tests/mcp_servers/test_tool_schema_contract.py` (metadata contract unaffected).
- `uv run ruff check tests/mcp_servers/github/test_github_tool_registry.py`, `uv run mypy` (T-06).

## Completion criteria
- All 21 tools are covered by the drift gate and the coverage test proves the map cannot lag the
  registry.
- All 9 write tools' published schemas contain `dry_run` with `default: false`.
- A locally introduced model/schema mismatch makes this file fail.

## Out of Scope
- Model-level validation cases (seq 15), HTTP-level rejection tests (seq 17), the tools rows themselves
  (seq 08-11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_TOOL_MODEL_MAP` (new) and the coverage test | Pending | — | — | REQ-009 |
| 2 | Add the schema-equality, `dry_run`, and determinism tests | Pending | — | — | REQ-009, REQ-003 |
| 3 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | T-02, T-06 |
| 4 | Update documentation | Pending | — | — | N/A: docs rows are seq 18-19 |

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
- **Requirement ID**: `REQ-009` (CI fails on model/schema drift), `REQ-003` (`dry_run` in every write schema)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `tests/mcp_servers/github/test_github_tool_registry.py`
