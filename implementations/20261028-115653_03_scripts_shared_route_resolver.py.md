# Procedure: add ToolRoutingError, reject None and remove the wording-only resolver modes

## Goal

Raise a `ValueError` subclass that carries the failure kind, reject `None` in the setter and remove `strict_mode` and `warn_on_missing` (Plan REQ-003).

## Scope

- Modify only `scripts/shared/route_resolver.py`.
- In scope: the exception class, `ToolRouteResolver.__init__`, `resolve`, `set_runtime_registry`, `_raise_strict_error` and the module docstring.
- Out of scope: the executor conversion (row 4), tests, docs.

## Assumptions

- `ToolRoutingError` (new) stays a `ValueError` subclass, preserving ADR-003 INV-02 and the existing `pytest.raises(ValueError)` tests.
- The only production construction is `ToolRouteResolver()` inside `ToolExecutor`, so removing the two keyword options affects tests only (rows 10 and 16).
- Row 2 has landed: `RuntimeToolRegistry.exclusion_reason` (created by row 2) exists.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Kinds: `not_ready`, `unknown_tool`, `posture_excluded` (new), `server_unavailable` (new).
- Keep the message prefix `Unknown tool: <name>` so log searches and the existing documented error text stay valid.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/route_resolver.py`

### Procedure

- Add `class ToolRoutingError(ValueError)` (new) with attributes `kind` and `tool_name`, constructed as `ToolRoutingError(kind, tool_name, message)` (new).
- In `resolve`: when `self._runtime_registry is None` raise kind `not_ready` with message `Unknown tool: <name> (RuntimeToolRegistry not ready)`; otherwise look the name up; when it is not found read `self._runtime_registry.exclusion_reason(name)` and map `posture` to `posture_excluded` (new), `unavailable` and `disabled` to `server_unavailable` (new), anything else to `unknown_tool`.
- Remove the `warn_on_missing` and `strict_mode` parameters, `_raise_strict_error` and the two stored flags; keep the `runtime_registry` constructor parameter (the executor builds the resolver before discovery).
- In `set_runtime_registry`, raise `TypeError("runtime registry must not be None")` when given `None`; change its annotation to `RuntimeToolRegistry`.
- Rewrite the module and class docstrings to describe the single contract and the four kinds.

### Method

Replace the resolver body and the exception; no new imports beyond the existing `TYPE_CHECKING` one.

### Details

- `ToolRouteResolver(runtime_registry=None)` stays constructible; resolving then yields the `not_ready` kind.
- Callers outside `shared` use `ToolExecutor.set_runtime_registry` only.

## Compatibility considerations

- Tests that passed `strict_mode` or `warn_on_missing` break by design and are rewritten in rows 10 and 16.

## Security considerations

- Fail-closed: every unresolved name raises; an unwired resolver never routes.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_route_resolver.py tests/shared/test_tool_executor_routing.py -q` | Pass |
| 2 | `uv run ruff format scripts/shared/route_resolver.py`; `uv run ruff check scripts/shared/route_resolver.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/route_resolver.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- `ToolRoutingError` (new) exists with the four kinds; `set_runtime_registry(None)` raises `TypeError`; the two options are gone.

## Out of Scope

- Executor result conversion, ADR edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (typed routing failures; no None registry; no wording-only modes)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/shared/route_resolver.py
