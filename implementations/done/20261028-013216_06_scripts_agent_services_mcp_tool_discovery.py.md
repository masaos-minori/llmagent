# mcpcompat001-require-posture-gates-in-mcp-tool-discovery-service

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Make `posture_gates` a required argument of `McpToolDiscoveryService`, remove the
`None` branch of `discover_all()`, and rewrite the docstrings without migration-window
wording (REQ-003; AC-3), closing the fail-open default on the Security Posture gate.

## Scope

- `scripts/agent/services/mcp_tool_discovery.py`:
  - the module docstring "Security Posture gating" paragraph (current L45-L50),
  - `__init__` signature (current L92-L96) and its docstring (current L97-L101),
  - the `allowed_servers` expression in `discover_all()` (current L110-L115).
- No other file; `scripts/agent/startup_validation.py` (the only production caller) and
  `scripts/agent/services/mcp_tool_discovery_registry.py` are read-only references.

## Assumptions

- Verified against the current source: signature reads
  `posture_gates: Mapping[str, PostureGate] | None = None`; `discover_all()` passes
  `allowed_servers=None` when the field is `None`; docstrings say "migration-window
  value"; `startup_validation.py` L114-L116 already passes real gates from
  `collect_server_postures()`.
- UNK-02: `RuntimeToolRegistry` and the registry-building helper keep their own `None`
  default (Out of Scope per the Plan); a follow-up issue is the owner's decision after
  implementation.
- Missing-argument enforcement is plain Python: omitting a required positional-or-keyword
  parameter raises `TypeError` at call time (AC-3), guarded by procedure 13's test.

## Design decisions

- Required positional-or-keyword parameter (no default), not a sentinel value: the fail-closed
  meaning stays "empty mapping registers nothing", while forgetting the argument fails
  loudly at construction instead of silently ungating.
- `allowed_server_keys()` is called unconditionally after the change; the `None` branch
  disappears rather than being replaced by a check.

## Alternatives considered

- Keeping `Optional` and raising inside `__init__`: rejected — the signature would still
  advertise a `None` value that cannot be used; the Plan's Implementation Intent names
  the required-argument design.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Rewrite the module docstring paragraph (current L45-L50), replacing the final
  sentence of the paragraph:
   > `posture_gates=None` means no gate was supplied and every reachable server's tools
   > are registered as before.

   with:
   > An empty gate mapping allows no server and adds no MCP tool to the registry.

2. Change the `__init__` signature (current L95) from:
   > posture_gates: Mapping[str, PostureGate] | None = None,

   to:
   > posture_gates: Mapping[str, PostureGate],

3. Rewrite the `__init__` docstring body (current L99-L100) as:
   > `posture_gates` is the gate row `18` (`agent.services.mcp_health`) produced at
   > readiness and is required. An empty mapping is a valid explicit value and
   > registers no MCP tool.

4. Replace the `allowed_servers` expression in `discover_all()` (current L110-L115):
   > allowed_servers = (
   >     None
   >     if self._posture_gates is None
   >     else frozenset(allowed_server_keys(self._posture_gates))
   > )

   with:
   > allowed_servers = frozenset(allowed_server_keys(self._posture_gates))

### Method

Signature flip plus two docstring rewrites plus one expression simplification; the rest
of the service (fetch, dedupe call, findings) is untouched.

### Details

- `self._posture_gates` narrows to `Mapping[str, PostureGate]`; mypy then proves
  `allowed_server_keys()` receives a mapping.
- `_dedupe_and_build(entries, unavailable_keys, allowed_servers=allowed_servers)` keeps
  its keyword call; the helper's own `None` default is unchanged (UNK-02).

## Compatibility considerations

- Ordering correction (adversarial verification): execute procedure 13 immediately after this one; the old no-gate test in `test_mcp_tool_discovery_posture_gate.py` fails once the signature is required and procedure 13 replaces it.

- Lands after procedures 11-15 (tests pass gates first, per the Plan's tests-first
  order); landing earlier fails the 65 call sites with `TypeError`.
- The production startup path is unchanged: `startup_validation.py` already passes gates
  (REQ-007, AC-8).
- The class is constructed only in `startup_validation.py` (scripts) and the four test
  files listed in the Plan's target table.

## Security considerations

- This is the security core of the plan: the gate argument can no longer be forgotten.
- Fail-closed semantics preserved: empty gate map → `allowed_server_keys({})` is empty
  → no MCP tool registered (procedure 13 keeps that test).

## Rollback considerations

- Revert this file with the test procedures 11-15 (they remain green either way because
  they pass explicit gates and the guard test flips with the signature — procedure 13's
  `TypeError` test must revert together with this file).

## Validation plan

- `uv run pytest tests/agent/services -v` (gate-contract tests green).
- `uv run pytest tests/integration/test_production_security_regression.py -v`.
- `uv run mypy --no-namespace-packages scripts/` (flags any remaining missing-argument
  call site).
- AC-3 grep: no docstring contains "migration-window"; `discover_all()` contains no
  `is None` branch.

## Completion criteria

- `McpToolDiscoveryService(ctx)` without gates raises `TypeError` (AC-3, AC-5).
- No `None` branch and no migration-window wording remain (AC-3).
- Production startup behavior unchanged (AC-8).

## Out of Scope

- `RuntimeToolRegistry` and `mcp_tool_discovery_registry.py` `None` defaults (UNK-02).
- Test call-site updates — procedures 12-15.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands after procedures 11-15 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Guard test is procedure 13 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, mypy, integration suite |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | N/A |

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
- **Requirement ID**: REQ-003, REQ-007
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
