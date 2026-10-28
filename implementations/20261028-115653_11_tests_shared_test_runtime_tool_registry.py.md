# Procedure: add exclusion-reason tests to the registry tests

## Goal

Cover `exclusion_reason` for unavailable, disabled and posture exclusions and for non-excluded names (Plan REQ-002).

## Scope

- Modify only `tests/shared/test_runtime_tool_registry.py`.
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

`tests/shared/test_runtime_tool_registry.py`

### Procedure

- Add `test_exclusion_reason_unavailable_server` (new) next to `test_unavailable_servers_excludes_tools_from_unavailable_server`.
- Add `test_exclusion_reason_disabled_server` (new) in `TestDisabledServerExclusion`.
- Add `test_exclusion_reason_posture_in_posture_gate` (new) in `TestPostureGate`.
- Add `test_exclusion_reason_is_none_for_registered_and_unknown_names` (new).

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Row 2 has landed. Another Plan (rtool008) changes which builder this file's calls use; keep whatever builder the file uses when this row runs.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/shared/test_runtime_tool_registry.py -q` | Pass |
| 2 | `uv run ruff format tests/shared/test_runtime_tool_registry.py`; `uv run ruff check tests/shared/test_runtime_tool_registry.py` | No finding |

## Completion criteria

- Reasons are reported for each exclusion kind and `None` otherwise.

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
- **Requirement ID**: REQ-002, REQ-007 (exclusion reasons)
- **Source issue**: issues/20261027-155847_mcpexec004_make-mcp-deps-mandatory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093529_mcpexec004_make-mcp-deps-mandatory.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115653
- **Related target files**: tests/shared/test_runtime_tool_registry.py
