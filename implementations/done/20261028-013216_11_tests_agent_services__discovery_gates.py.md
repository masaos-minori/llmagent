# mcpcompat001-create-the-shared-discovery-gate-test-helper

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Create `tests/agent/services/_discovery_gates.py` (new), the one shared test helper
that builds a green `PostureGate` for every server key a test context defines, so the
65 gate-less `McpToolDiscoveryService(...)` call sites can pass real gates with one
expression each (REQ-004; AC-4).

## Scope

- New file `tests/agent/services/_discovery_gates.py` exporting:
  - `green_gate(server_key: str) -> PostureGate` (new) — one accepted gate row.
  - `gates_for(*server_keys: str) -> dict[str, PostureGate]` (new) — green gate per key.
  - `gates_from(servers: Mapping[str, object]) -> dict[str, PostureGate]` (new) — green
    gate per key of a servers mapping (mirrors the `servers` dicts `_make_ctx(servers, ...)`
    takes in the consumer files).
- No changes to the consumers here; they are procedures 12, 14, 15.

## Assumptions

- Gate construction mirrors the already-verified `_gate()` helper at
  `tests/agent/services/test_mcp_tool_discovery_posture_gate.py:86-105`: `PostureGate(server_key=...,
  required=True, reachable=True, posture_accepted=True, ready=True, validated=True,
  reason_code=REASON_OK)` followed by `replace(gate, failure_class=classify_server_failure(gate))`
  so the failure class the row-18 classifier attaches is present (the plan's "green gate" definition).
- Import mechanism verified: `tests/__init__.py` exists and `tests/agent/` has no `__init__.py`,
  yet `from tests.agent._config_test_defaults import ...` already works in
  `tests/agent/test_tool_approval_repos.py:19` (namespace-subpackage precedent), so
  `from tests.agent.services._discovery_gates import ...` resolves from every test directory,
  including `tests/integration/`.
- The plan's sibling pattern is `tests/mcp_servers/_auth_headers.py` imported as
  `tests.mcp_servers._auth_headers` (plan target row); the `_config_test_defaults` precedent
  above is the same mechanism.
- UNK-01 (closed by this verification): the cross-directory import path works; no `__init__.py`
  additions are needed.

## Design decisions

- A stateless module of three plain functions, no fixtures and no shared mutable state: gate
  construction is pure, so consumers stay independent and ordering of test execution is irrelevant.
- `gates_from()` takes the servers mapping directly because most call sites already hold a local
  `servers` dict for `_make_ctx(servers, ...)`; deriving keys from it keeps the gate keys and the
  context servers in lock-step, which is what keeps behavior identical (every ctx server green).
- `green_gate()` is exported separately so a consumer with a single literal server key reads as
  `posture_gates=gates_for("rag")` without constructing a dict first.

## Alternatives considered

- Per-file local factories in each of the three consumer files: rejected — the plan requires
  "one shared test helper", and three copies of `PostureGate(...)` construction would drift when
  the gate row gains fields.
- Refactoring `test_mcp_tool_discovery_posture_gate.py`'s local `_gate()` onto this helper:
  rejected for this pass — `_gate()` carries negative-gate flags (`reachable=False`,
  `posture_accepted=False`, ...) that `green_gate()` deliberately does not expose; widening the
  helper now would bend it to one file's needs while AC-5 only requires keeping that file's tests.

## Implementation

### Target file

`tests/agent/services/_discovery_gates.py` (new)

### Procedure

1. Create the file with this content:
   ```python
   """tests/agent/services/_discovery_gates.py

   Shared test helper: build green PostureGate rows for McpToolDiscoveryService tests.
   A green gate mirrors what agent.services.mcp_health's row-18 classifier produces for a
   server that is reachable, posture-accepted, ready, and validated.
   """

   from __future__ import annotations

   from collections.abc import Mapping
   from dataclasses import replace

   from agent.services.mcp_health import PostureGate, classify_server_failure
   from shared.security.result_dto import REASON_OK


   def green_gate(server_key: str) -> PostureGate:
       """Build one green gate with the failure class the row-18 classifier would attach."""
       gate = PostureGate(
           server_key=server_key,
           required=True,
           reachable=True,
           posture_accepted=True,
           ready=True,
           validated=True,
           reason_code=REASON_OK,
       )
       return replace(gate, failure_class=classify_server_failure(gate))


   def gates_for(*server_keys: str) -> dict[str, PostureGate]:
       """Green gate per named server key."""
       return {key: green_gate(key) for key in server_keys}


   def gates_from(servers: Mapping[str, object]) -> dict[str, PostureGate]:
       """Green gate per key of a servers mapping (the dicts _make_ctx consumes)."""
       return {key: green_gate(key) for key in servers}
   ```

### Method

New-file creation; imports follow the import-layer contract (`agent.services.*` and
`shared.*` are both test-side legal in `tests/`).

### Details

- Module docstring names the green-gate semantics so a future reader does not mistake the
  helper for a production factory.
- `replace(...)` mirrors the verified `_gate()` idiom; constructing without the classifier pass
  would leave `failure_class` unset and diverge from what `allowed_server_keys()` sees at startup.

## Compatibility considerations

- Lands before procedures 12, 14, 15 (their imports break if the file is missing); lands before
  procedure 06 (the signature flip) because the green-gate call sites must exist first —
  plan Phase 2 order.
- `tests/agent/services/test_mcp_tool_discovery.py` is also a target of the unprocessed
  `mcpcompat003` duplicate pair (`20261027-111522` / `20261027-121337`); this helper file is not
  in those plans' target rows, so no rebase conflict is expected (recorded as a cross-plan note).
- No `__init__.py` is added anywhere; the namespace-subpackage import mechanism is unchanged.

## Security considerations

- Test-only helper building in-memory dataclasses; no network, no secrets.

## Rollback considerations

- Delete the file and revert procedures 12, 14, 15 together; nothing else imports it.

## Validation plan

- `uv run ruff format tests/agent/services/_discovery_gates.py`, `uv run ruff check ...` — clean.
- `uv run mypy --no-namespace-packages tests/agent/services/_discovery_gates.py` — clean.
- Import smoke: `uv run python -c "import sys; sys.path.insert(0, 'scripts'); from tests.agent.services._discovery_gates import gates_for; print(gates_for('git'))"` — prints one green gate row.
- `uv run pytest tests/agent/services/test_mcp_tool_discovery_posture_gate.py -q` — unchanged
  green (the helper coexists with the file's local `_gate()` until procedure 13 lands).

## Completion criteria

- The three functions exist and build `PostureGate` rows carrying a classifier-attached
  `failure_class` (REQ-004 groundwork for AC-4).
- Ruff and mypy clean on the new file.

## Out of Scope

- Editing the consumer test files — procedures 12, 14, 15.
- Exposing negative-gate flags on the helper — explicitly rejected above.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands before procedures 06, 12, 14, 15 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Validated by import smoke + existing gate tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | ruff, mypy, pytest |
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
- **Related target files**: tests/agent/services/_discovery_gates.py
