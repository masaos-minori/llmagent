# mcpcompat001-replace-the-no-gate-test-with-a-typeerror-test

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Replace `test_no_gate_supplied_registers_every_reachable_tool` in
`tests/agent/services/test_mcp_tool_discovery_posture_gate.py` with a test that
`McpToolDiscoveryService(ctx)` raises `TypeError`, and keep the empty-gate test unchanged
(REQ-004; AC-4, AC-5).

## Scope

- Rewrite the one test method at current L137-145 in place: rename to
  `test_no_gate_supplied_raises_typeerror` (new) and assert the constructor raises.
- All other tests in the file (L112-135, L147 onward) stay byte-for-byte unchanged: they
  already pass `posture_gates=...` (11 constructions, AST-verified 2026-10-28 as the only
  `McpToolDiscoveryService(` calls in this file besides the replaced one).

## Assumptions

- The file's local `_gate()` helper (L86-105) stays as-is; this file needs no import from
  `_discovery_gates.py` (design decision recorded in procedure 11).
- After procedure 06 removes the `= None` default, Python raises
  `TypeError: __init__() missing 1 required positional argument: 'posture_gates'` for
  `McpToolDiscoveryService(ctx)` — the keyword-only-or-positional distinction does not matter
  because the test asserts only `TypeError`.

## Design decisions

- Assert the failure at construction time with `pytest.raises(TypeError)` and no async run:
  the contract is a signature contract, so pinning it without touching the fetch machinery
  keeps the test deterministic and fast.
- Rename rather than keep the old name: the old name asserts the removed behavior
  ("registers every reachable tool") and would be misleading prose in a failing-test report.

## Alternatives considered

- Deleting the test outright: rejected — AC-4 explicitly requires a test that the gate-less
  construction raises, and deleting would remove the only direct guard of the required-argument
  contract.
- Keeping the test async and asserting the registry is empty instead: rejected — under the new
  signature no registry is ever built; `TypeError` is the specified behavior (plan Phase 2).

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery_posture_gate.py`

### Procedure

1. Replace the current method (L137-145):
   ```python
   @pytest.mark.asyncio
   async def test_no_gate_supplied_registers_every_reachable_tool(self) -> None:
       ...
   ```
   with:
   ```python
   def test_no_gate_supplied_raises_typeerror(self) -> None:
       """The required-argument contract: construction without gates fails at once."""
       http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
       ctx = _make_ctx({"git": _server()}, http)

       with pytest.raises(TypeError):
           McpToolDiscoveryService(ctx)
   ```
   (`@pytest.mark.asyncio` is dropped: the replacement is synchronous.)
2. Touch nothing else in the file.

### Method

In-place single-method replacement; the surrounding helpers (`_resp`, `_gate`, `_http`,
`_make_ctx`, `_server`, `_tools_body`, `_tool_names`) are reused unchanged.

### Details

- The docstring names the contract the test pins, matching the file's existing docstring style
  (see `test_an_empty_gate_registers_no_mcp_tool` L148-149).
- `http`/`ctx` are built with the file's existing helpers so the test reads like its neighbors;
  they are never awaited because the constructor fails first.

## Compatibility considerations

- Ordering correction (adversarial verification): the new `pytest.raises(TypeError)` assertion only passes after procedure 06 flips the signature, and procedure 06 breaks the old test this procedure replaces. Execute 06 and 13 back to back as one change unit (06 first, then 13); the intermediate state is not independently green.

- Lands before procedure 06 (the flip): run against the current optional-`None` signature the
  new test would fail, so land 12 -> 13 -> 14 -> 15 -> 06 in plan order; the file is only
  green after 06 lands, matching Phase 2's single-change-set intent.
  - Transition note: procedures 12/14/15 are green both before and after 06; only this file's
    replaced test requires 06.
- `test_an_empty_gate_registers_no_mcp_tool` (AC-5, fail-closed reading) is left untouched.
- The replaced test keeps one intentional gate-less `McpToolDiscoveryService(ctx)` construction;
  procedure 17's AST rule pairs this file with the `mcp-posture-gate-negative-test` entry in
  `tools/compat_exceptions.toml`, so the Phase 3 checker run stays green.

## Security considerations

- Test-only; mocks only.

## Rollback considerations

- Revert together with procedure 06 (`git checkout -- tests/agent/services/test_mcp_tool_discovery_posture_gate.py
  scripts/agent/services/mcp_tool_discovery.py`); the old test asserts the pre-change contract.

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -q` — all tests
  pass after procedure 06 lands (AC-3, AC-4, AC-5).
- AST scan: this file has exactly one `McpToolDiscoveryService(` call lacking `posture_gates`,
  and it sits inside a `pytest.raises(TypeError)` block.
- `uv run ruff check tests/agent/services/`, `uv run mypy --no-namespace-packages tests/agent/services/` — clean.

## Completion criteria

- The `None`-behavior test no longer exists; a `TypeError` test does (REQ-004, AC-4).
- The empty-gate test passes unmodified (AC-5).

## Out of Scope

- The signature flip itself — procedure 06.
- The other gate-less call sites — procedures 12, 14, 15.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands before procedure 06; green only after 06 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | This document is the test procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, ruff, mypy |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | N/A for this row |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: tests/agent/services/test_mcp_tool_discovery_posture_gate.py
