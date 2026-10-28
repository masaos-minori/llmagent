# Procedure: remove the dead registry-is-not-None guard around set_runtime_registry

## Goal

Call `set_runtime_registry(discovery.registry)` unconditionally because `DiscoveryResult.registry` is never optional (Plan REQ-006).

## Scope

- Modify only `scripts/agent/startup_validation.py`.
- In scope: the `if discovery.registry is not None:` block in `check_services`.
- Out of scope: the rest of the pipeline, tests.

## Assumptions

- `DiscoveryResult.registry: RuntimeToolRegistry` is a non-optional field (checked against `mcp_tool_discovery.py`).
- `check_services` has cyclomatic complexity D (24); removing a branch does not raise it.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Keep the surrounding `try`/`except` so a discovery failure still reports `mcp_tool_discovery` as FATAL.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/agent/startup_validation.py`

### Procedure

- Replace the guarded call with `ctx.services_required.tools.set_runtime_registry(discovery.registry)`.
- Keep the preceding comment about wiring the registry into the resolver.

### Method

Dedent one statement and delete one `if`.

### Details

- If `discovery` raised, the registry stays unwired and the executor returns the `not_ready` routing result (documented in row 23).

## Compatibility considerations

- No behavior change on the success path.

## Security considerations

- Fail-closed on failure is now explicit through the `not_ready` result.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py tests/agent -k startup -q` | Pass |
| 2 | `uv run ruff format scripts/agent/startup_validation.py`; `uv run ruff check scripts/agent/startup_validation.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/agent/startup_validation.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- No `is not None` guard around `set_runtime_registry` remains.

## Out of Scope

- Other startup steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-006 (dead guard removed)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/agent/startup_validation.py
