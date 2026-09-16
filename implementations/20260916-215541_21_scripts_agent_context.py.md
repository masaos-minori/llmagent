## Goal

Remove the `AGENT_RESTRICT_CONFIG` guard in `AgentContext.__init__` so `ConfigLoader.restrict_to("agent.toml")` is called unconditionally per REQ-001, matching every other process entry point.

## Scope

- Modify `scripts/agent/context.py`: remove the environment-variable gate around `restrict_to()`.

## Assumptions

- The guard was a deliberate, documented test-isolation decision (confirmed by `implementations/done/20260825-174354_01_scripts_agent_context.py.md`).
- `deploy/start_agent.sh` never sets `AGENT_RESTRICT_CONFIG` — confirmed by `grep`.
- Every other process entry point calls `restrict_to()` unconditionally.

## Design decisions

- Remove the `if os.environ.get("AGENT_RESTRICT_CONFIG"): ConfigLoader.restrict_to("agent.toml")` guard entirely.
- Call `ConfigLoader.restrict_to("agent.toml")` unconditionally before `build_agent_config()` runs.

## Alternatives considered

- Adding a new configuration option for this behavior — rejected: out of scope for REQ-001.
- Keeping the guard but making it default to True — rejected: would still leave production unrestricted if the env var were unset.

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Replace the conditional `restrict_to()` call with an unconditional one.

### Method

- **Step 1**: In `AgentContext.__init__`, replace the conditional call:

```python
# Before (around lines 30-40):
class AgentContext:
    def __init__(self, ...):
        # ... other initialization
        if os.environ.get("AGENT_RESTRICT_CONFIG"):
            ConfigLoader.restrict_to("agent.toml")
        self._config = build_agent_config(...)

# After:
class AgentContext:
    def __init__(self, ...):
        # ... other initialization
        # REQ-001: unconditional restriction, matching every other process entry point
        ConfigLoader.restrict_to("agent.toml")
        self._config = build_agent_config(...)
```

### Details

**Step 1 — Remove the guard:**

Replace lines ~30-40 in `scripts/agent/context.py`:

```python
# REQ-001: unconditional restriction, matching every other process entry point
ConfigLoader.restrict_to("agent.toml")
```

The `os.environ.get("AGENT_RESTRICT_CONFIG")` condition is removed entirely. The call is now unconditional, matching the pattern used by `crawler.py`, `ingester.py`, `chunk_splitter.py`, and `server.py::run_http()`.

## Compatibility considerations

- Production Agent process will now always restrict loading to `agent.toml` only.
- Tests that previously relied on the ability to load non-`agent.toml` files after constructing an `AgentContext` may fail — mitigated by the autouse fixture in `tests/conftest.py` (REQ-001).
- The `AGENT_RESTRICT_CONFIG` environment variable is no longer honored.

## Security considerations

- REQ-001 improves security by enforcing process-level config isolation unconditionally.

## Rollback considerations

- Reverting restores the pre-fix conditional behavior.

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_context.py -v`
- Verify `AgentContext()` construction sets `ConfigLoader._allowed_files == frozenset({"agent.toml"})` unconditionally.
- Verify full suite passes (autouse fixture prevents cross-test leakage).
- Static analysis: `uv run ruff check scripts/agent/context.py`, `uv run mypy scripts/agent/context.py`.

## Completion criteria

- `AGENT_RESTRICT_CONFIG` guard removed.
- `restrict_to("agent.toml")` called unconditionally.
- All existing tests pass after updates.
- No new lint/type errors introduced.

## Out of scope

- Modifying `tests/conftest.py` — covered in subsequent row (REQ-001).
- Modifying `tests/agent/test_context.py` — covered in subsequent row (REQ-001).
- Modifying `docs/adr/ADR-002-config-isolation.md` — covered in subsequent row (REQ-008).
- Any MCP server business logic unrelated to the config loader.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove AGENT_RESTRICT_CONFIG guard; add unconditional restrict_to() | Pending | — | — | |
| 2 | Add autouse fixture to tests/conftest.py | Pending | — | — | See next row |
| 3 | Add AgentContext() unconditional-restriction test | Pending | — | — | See next row |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103255_mcpagent07_config-isolation-schema-validation-loader-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-125251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-215541
- **Related target files**: scripts/agent/context.py
