# Procedure: convert routing failures to a normalized result and require the health registry

## Goal

Return a `ToolCallResult` for each `ToolRoutingError`, take `health_registry` at construction and reject `None` in `set_runtime_registry` (Plan REQ-003..005).

## Scope

- Modify only `scripts/shared/tool_executor.py`.
- In scope: `__init__`, `set_runtime_registry` and `execute` / `_raw_execute`.
- Out of scope: the invoker internals (row 5), the DTO comment (row 6), tests, docs.

## Assumptions

- Rows 3 and 5 have landed: `ToolRoutingError` exists and `ToolTransportInvoker.__init__` takes a required `health_registry` keyword.
- The mcpinv004 procedure may have changed this file's constructor; keep its parameters and add the new keyword (UNK-01).
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Convert only `ToolRoutingError`; any other exception keeps propagating to the per-call boundary in `tool_runner.py`.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

- Add a keyword-only parameter `health_registry: McpServerHealthRegistry` to `__init__` and forward it to `super().__init__`; import the type under `TYPE_CHECKING` as the module already does for `RuntimeToolRegistry`.
- In `set_runtime_registry`, raise `TypeError` when `registry is None` before delegating to the resolver.
- In `execute`, wrap `await self._raw_execute(tool_name, args)` in `try`/`except ToolRoutingError as exc`: log a warning with kind and tool name and return `self._error_result("", f"routing:{exc.kind}: {exc}", error_type="routing")`.
- Update the class docstring to state the wiring order: health registry at construction, runtime registry after discovery.

### Method

One new parameter, one guard and one `try`/`except`.

### Details

- `_error_result` is defined on `ToolTransportInvoker`; an empty `server_key` is used because no server was resolved.
- Dynamic `UNAVAILABLE` / `HALF_OPEN` results are produced later in `_run_precall_gates` and are unchanged.

## Compatibility considerations

- `execute()` no longer raises for routing failures; callers that inspect `ToolCallResult.error_type` see the new `routing` kind (UNK in the Plan: grep consumers of `error_type` before finishing).

## Security considerations

- Fail-closed: a routing failure never reaches a transport; the output names the kind and tool, not server configuration.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_tool_executor.py tests/shared/test_tool_executor_routing.py tests/integration -m 'not integration and not production_paths_allowed' -q` | Pass |
| 2 | `uv run ruff format scripts/shared/tool_executor.py`; `uv run ruff check scripts/shared/tool_executor.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/tool_executor.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `rg "error_type" scripts --glob '*.py'` | Every consumer of `error_type` handles or ignores the `routing` value |

## Completion criteria

- Each routing failure kind yields a `routing:<kind>:` result and no transport call; the executor cannot be built without a health registry.

## Out of Scope

- Invoker internals, factory wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-28 | 2026-10-28 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | Static green. Routing-result conversion verified manually. Test failures deferred to procedures 12/13 (fixture construction). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-28 | 2026-10-28 | — |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005 (routing result contract; health registry at construction)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/shared/tool_executor.py
