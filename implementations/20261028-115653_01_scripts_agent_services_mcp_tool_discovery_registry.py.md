# Procedure: require allowed_servers in the registry builder functions

## Goal

Make `allowed_servers` a required argument of `_build_runtime_tools` and `_dedupe_and_build`; an empty set stays fail-closed (Plan REQ-001).

## Scope

- Modify only `scripts/agent/services/mcp_tool_discovery_registry.py`.
- In scope: the two signatures, their docstrings and the internal call.
- Out of scope: `RuntimeToolRegistry`'s constructor (UNK-02), the discovery service, tests, docs.

## Assumptions

- `McpToolDiscoveryService` already passes `allowed_servers` (a `frozenset`) into `_dedupe_and_build`; the mcpcompat001 procedures make the service-side `posture_gates` required.
- Tests call the two functions in `tests/agent/services/test_mcp_tool_discovery.py` (two call sites) and are updated by row 17.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Required keyword argument, no default: a forgotten gate becomes a `TypeError` instead of an ungated registry.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery_registry.py`

### Procedure

- Change `_build_runtime_tools(unique_entries, unavailable_servers, allowed_servers=None)` to `allowed_servers: frozenset[str]` with no default.
- Change `_dedupe_and_build(entries, unavailable_servers, allowed_servers=None)` the same way and keep passing it through unchanged.
- Rewrite both docstrings: `allowed_servers` is the posture-derived allowlist; a `frozenset` lets only its members through and an empty `frozenset` registers nothing; remove the `None` sentence.

### Method

Remove two defaults and the `| None` annotations; the rest of both functions is unchanged.

### Details

- `_dedupe_and_build` forwards `allowed_servers` unchanged to `_build_runtime_tools`, which hands it to `RuntimeToolRegistry(tools=built, allowed_servers=allowed_servers)`; no other module defines or imports these two private functions except the discovery service and `tests/agent/services/test_mcp_tool_discovery.py`.

## Compatibility considerations

- The only production caller (`McpToolDiscoveryService`) already supplies the argument; any other caller must pass it explicitly.

## Security considerations

- Removes the silent "no posture gate" state from registry building.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | Pass |
| 2 | `uv run ruff format scripts/agent/services/mcp_tool_discovery_registry.py`; `uv run ruff check scripts/agent/services/mcp_tool_discovery_registry.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/agent/services/mcp_tool_discovery_registry.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |
| 4 | `uv run python tools/check_compat_shims.py` | No finding |

## Completion criteria

- Both functions require `allowed_servers`; an empty set registers no tools.

## Out of Scope

- `RuntimeToolRegistry` constructor, discovery service.

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
- **Requirement ID**: REQ-001 (posture allowlist required at registry building)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/agent/services/mcp_tool_discovery_registry.py
