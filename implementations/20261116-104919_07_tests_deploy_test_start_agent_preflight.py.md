## Goal

Confirm `tests/deploy/test_start_agent_preflight.py` still satisfies the agent binary pre-flight
after the multi-main build, and make only the minimal, necessary change. The multi-main build
keeps the agent as a separate binary (only the ten MCP servers share one artifact), so
`deploy/start_agent.sh`'s `check_agent_binary` pre-flight is unchanged and this test keeps
validating the same fail-fast-before-launch behavior.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The agent keeps its own built binary (seq 01 builds the agent separately from the ten MCP
  servers), so `deploy/start_agent.sh` still locates `/opt/llm/bin/agent` and runs
  `check_agent_binary` before launch.
- The pre-flight checks presence/executability and aborts with a `[FATAL]` naming
  `deploy/build_binaries.sh` and `deploy/deploy.sh` for recovery.

## Design decisions

- **Keep the test as a guard; do not rewrite it.** The test exercises the real
  `check_agent_binary` from `deploy/start_agent.sh` via a sourced driver. Since the agent keeps
  its own binary, the behavior under test is unchanged, so adding cases would duplicate coverage.

## Alternatives considered

- **Tying the pre-flight to the ten MCP names.** Rejected — the pre-flight is agent-only; the ten
  MCP names are a `deploy/deploy.sh` / `tools/manage_binaries.py` concern (`REQ-004`).

## Implementation
### Target file
`tests/deploy/test_start_agent_preflight.py`

### Procedure

1. Confirm `deploy/start_agent.sh` still defines `check_agent_binary` (presence/executable check
   that prints `[FATAL] Agent binary not found or not executable` and lists
   `deploy/build_binaries.sh` and `deploy/deploy.sh` for recovery) and still calls it before
   launch.
2. Confirm both cases pass: `test_missing_binary_aborts_and_names_recovery` (exit 1, `[FATAL]`,
   recovery paths named, no `PRESENT_OK`) and `test_present_binary_proceeds` (exit 0,
   `PRESENT_OK`).
3. Make no structural change unless the multi-main build gave the agent a different binary name or
   moved the pre-flight, in which case apply the smallest update to `_AGENT` / the assertion.

### Method

- Expected result: no edit. The agent keeps its own binary, so `check_agent_binary` and this
  test's assumptions hold.

### Details

- `_write_driver` sources the real `deploy/start_agent.sh` and calls `check_agent_binary` against
  an isolated bin dir, so the test exercises the actual function, not a stub.
- The missing-binary case asserts the recovery hint points at
  `deploy/build_binaries.sh` (rebuild) and `deploy/deploy.sh` (deploy), matching
  `deploy/start_agent.sh:23-25`.

## Compatibility considerations

- No change to the driver format, the `isolated` subprocess env, or the `agent` binary name.

## Security considerations

- The pre-flight prevents launching the agent when its binary is missing or non-executable, a
  fail-fast gate before the agent runs. Keeping this test green preserves that gate.

## Rollback considerations

`N/A: revert the commit`; no code change is expected.

## Validation plan

- `uv run pytest tests/deploy/test_start_agent_preflight.py`.
- `uv run ruff check tests/deploy/test_start_agent_preflight.py`;
  `uv run mypy tests/deploy/test_start_agent_preflight.py`.

## Completion criteria

- `deploy/start_agent.sh` still runs `check_agent_binary` before launch.
- Both cases pass; no structural change was introduced unless a specific multi-main alteration
  required it.

## Out of Scope

- The agent binary build (that is `deploy/build_binaries.sh`, `REQ-001`).
- The ten MCP names pre-check (that is `deploy/deploy.sh`, `REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | verify existing coverage; no edit expected |
| 2 | Add or update tests per Validation plan | Pending | — | — | existing file, both cases |
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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-193516_buildperf001_mcp-multidist-binary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-104919
- **Related target files**: `tests/deploy/test_start_agent_preflight.py`
