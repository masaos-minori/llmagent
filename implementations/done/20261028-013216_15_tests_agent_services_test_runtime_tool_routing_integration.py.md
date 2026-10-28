# mcpcompat001-pass-gates-at-the-two-runtime-routing-construction-sites

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Pass a real gate mapping at the 2 gate-less `McpToolDiscoveryService(ctx)` constructor calls
in `tests/agent/services/test_runtime_tool_routing_integration.py` (current L313, L347;
AST-verified 2026-10-28), so the file keeps passing after procedure 06 makes `posture_gates`
required (REQ-004; AC-4).

## Scope

- The 2 constructions at L313 and L347.
- No routing, resolver, or registry assertions change; the tests' subject (runtime routing)
  is untouched.

## Assumptions

- Path correction against the plan's target table: the file lives at
  `tests/agent/services/test_runtime_tool_routing_integration.py` (verified 2026-10-28);
  `tests/integration/test_runtime_tool_routing_integration.py` does not exist. The plan's own
  Reference-Files wording and the AST scan both use the services path, so this procedure names
  the real file. Recorded as a plan-table correction, not a scope change.
- Both sites sit on a `ctx` whose `ctx.cfg.mcp.mcp_servers` is a real dict assigned directly
  (L303 multi-server literal, L343 `{"srv": _http()}`), so `gates_from(ctx.cfg.mcp.mcp_servers)`
  derives the exact keys — the uniform rule from procedures 12 and 14.
- `gates_from` (new) comes from `tests.agent.services._discovery_gates` after procedure 11; the
  sibling-directory import also works here because pytest inserts
  `tests/agent/services/` on `sys.path` (no `__init__.py` in that directory), and the
  `tests.agent.services._discovery_gates` spelling is the one used repo-wide.
- File overlap: this file is also a target row of the unprocessed `mcpcompat003` duplicate pair
  (`20261027-111522` / `20261027-121337`); the later procedures must rebase onto the gated form.

## Design decisions

- Same shared-helper rule as procedures 12/14 for uniformity across all 65 sites.

## Alternatives considered

- Local gate factory in this file: rejected — same reasoning as procedure 14.

## Implementation

### Target file

`tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure

1. Add the import with the module's import block:
   ```python
   from tests.agent.services._discovery_gates import gates_from
   ```
2. Replace both sites (current L313 and L347):
   ```python
   result = await McpToolDiscoveryService(
       ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
   ).discover_all()
   ```

### Method

Two keyword-argument insertions plus one import line; nothing else in the file changes.

### Details

- The already-gated constructions elsewhere in this file (10 calls pass `posture_gates=gates`
  today, AST-verified 2026-10-28) are left as written — only the 2 gate-less sites change.

## Compatibility considerations

- Lands after procedure 11 and before procedure 06 — plan Phase 2 order; the file is green both
  before and after 06.
- Cross-plan overlap with the mcpcompat003 pair recorded above; `20261028-010601_*` procedures
  (mcpinv003) do not touch this file.

## Security considerations

- Test-only; mocks and in-memory registries only.

## Rollback considerations

- `git checkout -- tests/agent/services/test_runtime_tool_routing_integration.py`; revert
  together with procedures 06 and 11.

## Validation plan

- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` — all tests
  pass.
- AST gate-less-call scan for this file returns 0.
- `uv run ruff check tests/agent/services/`, `uv run mypy --no-namespace-packages tests/agent/services/` — clean.

## Completion criteria

- Zero gate-less constructions in the file; routing assertions unchanged (REQ-004, AC-4).

## Out of Scope

- The signature flip — procedure 06.
- The other gate-less files — procedures 12, 13, 14.

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
- **Related target files**: tests/agent/services/test_runtime_tool_routing_integration.py
