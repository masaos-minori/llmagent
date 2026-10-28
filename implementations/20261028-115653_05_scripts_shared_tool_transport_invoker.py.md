# Procedure: require health_registry and remove the None branches and the setter

## Goal

Make `health_registry` a required constructor keyword of `ToolTransportInvoker`, remove every `None` branch and `set_health_registry` (Plan REQ-005, REQ-007).

## Scope

- Modify only `scripts/shared/tool_transport_invoker.py`.
- In scope: `__init__`, `set_health_registry`, `_check_health`, `_record_success`, `_record_transport_error`, `_handle_lifecycle_error` and the `finally` of `_run_precall_gates`.
- Out of scope: gate order, HALF_OPEN semantics, semaphore logic, tests.

## Assumptions

- The only production construction is `ToolExecutor` in `scripts/agent/factory.py` (row 7); the invoker is also built directly in `tests/shared/test_tool_transport_invoker*.py` (rows 14 and 15).
- The mcpinv004 procedure edits the semaphore code in this file; keep its result and change only the lines named here (UNK-01).
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Keyword-only required parameter so existing positional arguments keep their positions.
- Keep every health call exactly as is; only the `if self._health_registry is None` branches are deleted.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

- Change `__init__` to `def __init__(self, http, server_configs, concurrency_limits=None, lifecycle=None, *, health_registry: McpServerHealthRegistry)`; set `self._health_registry = health_registry`; the attribute type becomes non-optional.
- Delete `set_health_registry`.
- In `_check_health`, remove the early `if self._health_registry is None: return None, False`.
- In `_record_success`, `_record_transport_error` and `_handle_lifecycle_error`, remove the `if self._health_registry is not None:` guards and dedent the bodies.
- In the `finally` of `_run_precall_gates`, change `if owns_half_open_trial and self._health_registry is not None:` to `if owns_half_open_trial:`.
- Confirm the `McpServerHealthRegistry` import is a runtime or `TYPE_CHECKING` import consistent with the file's current style.

### Method

Delete one setter and five guards; no change to the gate chain.

### Details

- `tools.set_health_registry(...)` is called by `factory.py` and tests only; `rg "set_health_registry" scripts tests` must be empty afterwards.
- `tools/check_module_size.py` must stay green (13754 B before the change).

## Compatibility considerations

- Constructing an invoker or executor without a health registry now fails with `TypeError`; the factory and tests are updated in rows 7 and 12-15, 19-22.

## Security considerations

- Removes the state in which dynamic health gating is silently skipped.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py tests/shared/test_tool_executor.py -q` | Pass |
| 2 | `uv run ruff format scripts/shared/tool_transport_invoker.py`; `uv run ruff check scripts/shared/tool_transport_invoker.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/tool_transport_invoker.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/check_compat_shims.py`; `uv run vulture scripts/ --min-confidence 80` | No new finding |

## Completion criteria

- No `| None` health branch remains; `UNAVAILABLE`, `HALF_OPEN` and cancelled-trial tests pass unchanged apart from construction.

## Out of Scope

- Gate order, semaphore code, executor conversion.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-28 | 2026-10-28 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | Static validation green. 75 test failures deferred to test procedures 12/13/14: fixtures use removed set_health_registry / missing required health_registry arg. |
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
- **Requirement ID**: REQ-005, REQ-007 (health registry required; UNAVAILABLE/HALF_OPEN preserved)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/shared/tool_transport_invoker.py
