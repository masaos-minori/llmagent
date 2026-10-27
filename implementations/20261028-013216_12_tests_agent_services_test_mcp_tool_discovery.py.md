# mcpcompat001-pass-gates-at-the-60-discovery-test-construction-sites

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Pass a real gate mapping at all 60 gate-less `McpToolDiscoveryService(ctx)` constructor
calls in `tests/agent/services/test_mcp_tool_discovery.py`, so the file keeps passing after
procedure 06 makes `posture_gates` required (REQ-004; AC-4).

## Scope

- All 60 gate-less constructions (AST-verified 2026-10-28; lines 146, 185, 225, 263, 299,
  328, 358, 386, 410, 433, 458, 475, 507, 551, 582, 612, 642, 672, 706, 722, 739, 752, 764,
  778, 790, 803, 847, 867, 889, 911, 951, 1002, 1023, 1041, 1064, 1092, 1199, 1253, 1284,
  1318, 1347, 1383, 1417, 1450, 1483, 1515, 1552, 1602, 1650, 1694, 1769, 1841, 1901, 1956,
  2004, 2061, 2116, 2173, 2222, 2254).
- No assertion, fixture, or helper changes; no existing test renamed or deleted.

## Assumptions

- Uniform edit rule verified against the current file: every construction sits on a `ctx`
  built by `_make_ctx(servers, ...)` (L97-109), which sets `ctx.cfg.mcp.mcp_servers = servers`
  as a real dict on the mock (L105). Therefore the single mechanical replacement
  `McpToolDiscoveryService(ctx)` -> `McpToolDiscoveryService(ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers))`
  keys the gates exactly to that context's servers at every site.
- Green gates reproduce today's behavior: all ctx servers green -> `allowed_server_keys()`
  returns all of them -> the registry registers exactly the same tools as the `None` path did
  (characterization preservation).
- `gates_from` (new) is importable from `tests.agent.services._discovery_gates` after
  procedure 11 lands.
- File overlap: this file is also a target row of the unprocessed `mcpcompat003` duplicate
  pair (`20261027-111522` / `20261027-121337`). This procedure lands first (it belongs to the
  frozen canonical 110516 plan); the later mcpcompat003 procedure must rebase onto the gated form.

## Design decisions

- Derive gates from `ctx.cfg.mcp.mcp_servers` rather than per-test literals: the mapping is
  already the single source of truth for each test's servers, so one uniform expression keeps
  all 60 sites consistent and immune to a later `_make_ctx` server-count change.
- A scripted, deterministic rewrite (count-checked) rather than 60 hand edits — the replacement
  is string-regular and the pre/post AST counts gate the result.

## Alternatives considered

- Hoisting the literal `{"srv": _server()}` dicts into local variables per test: rejected —
  60 larger diffs for the same result; the ctx-attribute derivation is shorter and uniform.
- Keeping a `posture_gates=None` default and only deleting this test class's gate-less calls:
  rejected — contradicts REQ-003's required-argument decision.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. Add the import with the module's import block (after the `agent.services...` imports):
   ```python
   from tests.agent.services._discovery_gates import gates_from
   ```
2. Run the gated rewrite and confirm both counts before touching assertions:
   ```bash
   uv run python - <<'EOF'
   import pathlib
   p = pathlib.Path("tests/agent/services/test_mcp_tool_discovery.py")
   src = p.read_text()
   old = "McpToolDiscoveryService(ctx)"
   new = "McpToolDiscoveryService(ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers))"
   n = src.count(old)
   assert n == 60, n  # AST-verified count; abort on drift
   p.write_text(src.replace(old, new))
   print("replaced", n)
   EOF
   ```
   Any remaining `McpToolDiscoveryService(` construction that is not the gated form (e.g. a
   site with a second positional argument) gets the same `posture_gates=gates_from(...)` keyword
   by hand.

### Method

Bulk keyword-argument insertion; assertions and helpers untouched.

### Details

- Post-change AST scan must report zero `McpToolDiscoveryService` calls lacking the
  `posture_gates` keyword in this file (the same scan used for verification).
- Tests that deliberately probe gate semantics live in
  `test_mcp_tool_discovery_posture_gate.py`, not here, so no test in this file loses meaning.

## Compatibility considerations

- Lands after procedure 11 (helper import) and before procedure 06 (signature flip) — plan
  Phase 2 order; running this file against the current optional-`None` signature is green
  either way, so the file is transition-safe.
- `tests/agent/services/test_mcp_tool_discovery_posture_gate.py` stays independent (procedure 13).

## Security considerations

- Test-only edits; fakes and mocks only, no network or secrets introduced.

## Rollback considerations

- `git checkout -- tests/agent/services/test_mcp_tool_discovery.py`; revert together with
  procedures 06 and 11 (the required-argument flip assumes gated sites).

## Validation plan

- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` — all tests pass.
- AST gate-less-call scan for this file returns 0.
- `uv run ruff check tests/agent/services/` and `uv run mypy --no-namespace-packages tests/agent/services/` — clean.
- Full-suite confirmation belongs to plan Phase 4 (procedure-level validation).

## Completion criteria

- Zero gate-less constructions in the file; all existing tests pass unmodified otherwise
  (REQ-004, AC-4).

## Out of Scope

- The signature flip — procedure 06.
- The `TypeError` replacement test — procedure 13.
- The other two gate-less files — procedures 14, 15.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | After procedure 11; before procedure 06 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Existing tests are the regression net |
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
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
