# Procedure: record the exclusion reason for every tool the registry drops

## Goal

Let `RuntimeToolRegistry` remember why a tool was excluded so the resolver can tell posture-excluded and unavailable tools from unknown ones (Plan REQ-002).

## Scope

- Modify only `scripts/shared/runtime_tool_registry.py`.
- In scope: the constructor loop, `_is_excluded_server` and one new lookup method.
- Out of scope: resolution behavior, the constructor signature, tests, docs.

## Assumptions

- `shared` is a leaf package; the change adds no import.
- `resolve()` keeps returning `None` for an excluded name, so existing callers behave as before.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Store `{tool_name: reason}` with reasons `unavailable`, `disabled` and `posture`; expose it through `exclusion_reason(tool_name)` (new).

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py`

### Procedure

- Replace `_is_excluded_server(server_key) -> bool` with `_exclusion_reason(server_key) -> str | None` (new) returning `"unavailable"`, `"disabled"`, `"posture"` (recording the server in `_posture_excluded` as today) or `None`.
- In the constructor loop, call `_exclusion_reason(tool.server_key)` (new); when it is not `None`, store `self._excluded_tools[name] = reason` (new attribute `_excluded_tools: dict[str, str]`) and `continue`.
- Add `exclusion_reason(self, tool_name: str) -> str | None` (new) returning `self._excluded_tools.get(tool_name)`.
- Remove `_is_excluded_server` after confirming with `rg "_is_excluded_server" scripts tests` that nothing else calls it.

### Method

Small refactor of one helper plus one new method; the warning log for posture exclusions is unchanged.

### Details

- Duplicate tool names are excluded earlier by discovery, so a name can appear in `_excluded_tools` (new) at most once.
- `unavailable_servers`, `posture_excluded_servers` and `llm_tool_definitions()` behavior is unchanged.

## Compatibility considerations

- Additive and read-only; no behavior change for existing callers.

## Security considerations

- Only tool names and a short reason are stored; no server configuration is exposed.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_runtime_tool_registry.py tests/shared/test_tool_routing_validation.py -q` | Pass |
| 2 | `uv run ruff format scripts/shared/runtime_tool_registry.py`; `uv run ruff check scripts/shared/runtime_tool_registry.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/runtime_tool_registry.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `exclusion_reason` (new) returns the reason for dropped tools and `None` for registered and unknown names.

## Out of Scope

- Resolver and executor changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-164330 | 20261028-164330 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261028-164330 | 20261028-164330 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-164330 | 20261028-164330 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-164330 | 20261028-164330 |  |

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
- **Requirement ID**: REQ-002 (exclusion reason per dropped tool)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/shared/runtime_tool_registry.py