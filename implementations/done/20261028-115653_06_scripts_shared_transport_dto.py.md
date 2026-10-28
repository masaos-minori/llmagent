# Procedure: document the routing error kind in the result DTO comment

## Goal

Add `routing` to the documented values of `ToolCallResult.error_type` without changing any field (Plan REQ-004).

## Scope

- Modify only `scripts/shared/transport_dto.py`.
- In scope: the comment on the `error_type` field.
- Out of scope: fields, `from_transport`, tests, docs.

## Assumptions

- `error_type` is documented as `"transport" | "tool" | ""`; consumers that switch on it must tolerate the new value.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Comment-only change keeps the DTO frozen and unchanged.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`scripts/shared/transport_dto.py`

### Procedure

- Change the comment on `error_type` to `# "transport" | "tool" | "routing" | "" (empty on success)`.
- Add one sentence to the class docstring: `routing` marks a failure before any transport call (see `ToolExecutor.execute`).

### Method

Comment and docstring edit only.

### Details

- Run `rg "error_type" scripts` and confirm no consumer treats unknown values as an error.

## Compatibility considerations

- No field or behavior change.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_tool_executor_routing.py tests/shared/test_transport_dto.py -q` | Pass |
| 2 | `uv run ruff format scripts/shared/transport_dto.py`; `uv run ruff check scripts/shared/transport_dto.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` | No finding; six import contracts kept |
| 3 | `uv run bandit -r scripts/shared/transport_dto.py -c pyproject.toml -ll`; `uv run python tools/check_module_size.py` | No finding; module under the size gate |

## Completion criteria

- The comment lists the `routing` kind.

## Out of Scope

- Field changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-28 | 2026-10-28 | — |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-28 | 2026-10-28 | Comment-only. Static green. No behavior change. |

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
- **Requirement ID**: REQ-004 (documented error kind)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: scripts/shared/transport_dto.py
