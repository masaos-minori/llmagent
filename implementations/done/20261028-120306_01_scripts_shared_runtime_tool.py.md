# Procedure: require the four metadata fields in the production builder

## Goal

Make `build_runtime_tool()` require `is_write`, `requires_serial`, `resource_scope_kind` and `resource_scope_keys`, reject `None` and correct the module docstring (Plan REQ-001, REQ-006).

## Scope

- Modify only `scripts/shared/runtime_tool.py`.
- In scope: the `build_runtime_tool` signature, its body and docstring, and the module docstring.
- Out of scope: the `RuntimeTool` dataclass, discovery validation, tests, docs.

## Assumptions

- Apply this row after rows 02-08 (ordering note).
- The only production caller, `_build_runtime_tools()` in `scripts/agent/services/mcp_tool_discovery_registry.py`, already passes the four fields by keyword, and discovery rejects an entry missing them before building; no test passes more than two positional arguments (AST count in the planning phase).
- Overlap: none active. Verified 2026-10-28: the mcpexec004 plan is archived with no pending procedures (its `tests/agent/test_mcpexec003*` / `test_mcpexec004*` files and procedures were removed by a deliberate sync), so no other procedure targets this file. The mcpcompat003 work (`implementations/20261028-065435_*`, already executed) edited `tests/shared/test_resource_scope.py`; re-read it before editing (row 08).

## Design decisions

- Required keyword-only parameters: a missing field is a `TypeError` from Python; an explicit `None` is a `ValueError` from one check.
- Other defaults stay conservative: safety tier `WRITE_DANGEROUS`, `enabled_for_llm` `False`, empty capabilities, `allow_extra_fields` `False` (UNK-02).

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/runtime_tool.py`

### Procedure

- Change the signature to `build_runtime_tool(name, server_key, *, is_write: bool, requires_serial: bool, resource_scope_kind: str, resource_scope_keys: tuple[str, ...], server_url="", description="", input_schema=None, raw_definition=None, status="active", agent_safety_tier=None, enabled_for_llm=None, capabilities=None, allow_extra_fields=None, llm_visibility_base=None)`.
- At the top of the body, raise `ValueError(f"{field} is required")` for each of the four values that is `None`.
- Remove `resolved_is_write`, `resolved_requires_serial` and the `_or_default` calls for the two scope fields; pass the arguments straight into `RuntimeTool(...)`.
- Rewrite the `Safe-default rules` docstring: the four fields are required; list the remaining conservative defaults.
- Rewrite the module docstring: `RuntimeTool` is the shape stored by `RuntimeToolRegistry` and built by MCP tool discovery; the builder enforces the schema-2.0 execution metadata (remove "a future `RuntimeToolRegistry`" and "no consumer yet").

### Method

Edit one function and two docstrings; keep `_or_default` for the remaining defaults.

### Details

- `tests/shared/test_runtime_tool.py` holds the strict-builder tests (row 03); every default-reliant test call has moved to the fixture builder before this row.
- `tools/check_compat_shims.py` and `vulture` must stay clean (the helper `_or_default` is still used).

## Compatibility considerations

- A caller that omits a required field now fails at construction (`TypeError`); no production caller does.

## Security considerations

- Fail-closed: a tool of unknown write behavior can no longer be built as read-only.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared tests/agent/services tests/integration -m 'not integration and not production_paths_allowed' -q` | Pass |
| 2 | `uv run ruff format scripts/shared/runtime_tool.py`; `uv run ruff check scripts/shared/runtime_tool.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/runtime_tool.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- Omitting or passing `None` for any of the four fields raises; discovery still builds tools from validated entries.

## Out of Scope

- Discovery validation, registry, routing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 2026-10-28 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-10-28 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 2026-10-28 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 2026-10-28 | N/A: docs update is row 09 |

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
- **Requirement ID**: REQ-001, REQ-006 (strict builder; docstring)
- **Source issue**: issues/20261027-155851_rtool008_fail-closed-runtimetool-builder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120306
- **Related target files**: scripts/shared/runtime_tool.py