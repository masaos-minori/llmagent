# Procedure: rewrite the resolver tests for kinds, None rejection and removed modes

## Goal

Replace the mode test with kind, `None` and `ValueError`-compatibility tests (Plan REQ-003).

## Scope

- Modify only `tests/shared/test_route_resolver.py`.
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

`tests/shared/test_route_resolver.py`

### Procedure

- Remove `test_strict_mode_error_message_mentions_runtime_registry` (the option no longer exists).
- Add `test_unwired_resolver_raises_not_ready` (new), `test_unknown_name_raises_unknown_tool` (new), `test_posture_excluded_name_raises_posture_excluded` (new) and `test_unavailable_server_name_raises_server_unavailable` (new), each asserting `exc.kind` and that the exception is a `ValueError`; build the registries with `RuntimeToolRegistry(allowed_servers=...)` and `unavailable_servers=...`.
- Add `test_set_runtime_registry_rejects_none` (new) expecting `TypeError`.
- Keep the existing `pytest.raises(ValueError, match="Unknown tool")` tests; they stay green because the message prefix is unchanged.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Rows 2 and 3 have landed; use `ToolRoutingError` from `shared.route_resolver`.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_route_resolver.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/test_route_resolver.py`; `uv run ruff check tests/shared/test_route_resolver.py` | No finding |

## Completion criteria

- Each kind is covered and the removed-mode test is gone.

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
- **Requirement ID**: REQ-003, REQ-007 (resolver contract)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/shared/test_route_resolver.py
