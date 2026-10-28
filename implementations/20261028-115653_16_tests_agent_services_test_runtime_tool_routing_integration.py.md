# Procedure: remove the strict_mode and warn_on_missing cases and pass the health registry

## Goal

Delete the two cases for the removed resolver options and pass a health registry to the one `ToolExecutor(` construction (Plan REQ-003, REQ-005).

## Scope

- Modify only `tests/agent/services/test_runtime_tool_routing_integration.py`.
- Test-only change; no source file is edited.

## Assumptions

- The code procedures of this Plan with a lower `seq` have landed.
- Sequencing: the mcpcompat001, mcpinv002 and mcpinv004 implementation procedures (`implementations/20261028-013216_*` and `implementations/20261028-004831_*`) edit `scripts/shared/tool_executor.py`, `scripts/shared/tool_transport_invoker.py` and the discovery side of the posture gate; re-read the current file before editing and keep whatever those procedures produced (UNK-01).
- Overlap (compatible): `plans/20261028-094739_rtool008_fail-closed-runtimetool-builder.md` also targets `tests/shared/test_runtime_tool_registry.py`; it only changes which builder the existing calls use.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure

- Remove `test_strict_mode_error_message_mentions_runtime_registry` and `test_warn_on_missing_logs_warning_for_unknown_tool`.
- Pass `health_registry=McpServerHealthRegistry()` in the `ToolExecutor(` construction used by `test_set_runtime_registry_preserves_resolver_identity`.
- Keep the `pytest.raises(ValueError, match="Unknown tool")` cases; they stay valid.
- Do not add `allowed_servers` here: the only builder mention in this file is a comment (the Plan row was corrected in the procedure phase).

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Rows 3 and 4 have landed.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` | Pass |
| 2 | `uv run ruff format tests/agent/services/test_runtime_tool_routing_integration.py`; `uv run ruff check tests/agent/services/test_runtime_tool_routing_integration.py` | No finding |

## Completion criteria

- No test passes `strict_mode` or `warn_on_missing`; the file passes.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-003, REQ-005 (resolver options removed; executor construction)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/agent/services/test_runtime_tool_routing_integration.py
