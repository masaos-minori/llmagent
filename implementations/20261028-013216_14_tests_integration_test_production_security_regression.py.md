# mcpcompat001-pass-gates-at-the-two-production-regression-construction-sites

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Pass a real gate mapping at the 2 gate-less `McpToolDiscoveryService(ctx)` constructor calls
in `tests/integration/test_production_security_regression.py` (current L204, L245; AST-verified
2026-10-28), so the file keeps passing after procedure 06 makes `posture_gates` required
(REQ-004; AC-4).

## Scope

- The 2 constructions at L204 and L245.
- No assertion or context-construction changes; the surrounding
  `types.SimpleNamespace`-built contexts stay as written.

## Assumptions

- Both contexts set a real `mcp_servers` mapping on `ctx.cfg.mcp` (e.g. L195
  `mcp_servers={"required_server": unreachable_cfg}`), so `gates_from(ctx.cfg.mcp.mcp_servers)`
  derives the exact server keys of each context — the same uniform rule as procedure 12.
- `gates_from` (new) is importable from `tests.agent.services._discovery_gates` after procedure
  11 lands; the cross-directory import works via the verified namespace-subpackage precedent
  (`from tests.agent._config_test_defaults import ...` at `tests/agent/test_tool_approval_repos.py:19`).
- Green gates preserve behavior: `allowed_server_keys()` returns every ctx server, matching the
  old `None` path; the tests' subject matter is unreachable-server findings, which gates do not
  alter.

## Design decisions

- Reuse the shared helper instead of a local integration-file factory: the plan requires one
  shared helper (REQ-004), and the ctx-attribute derivation keeps this file identical in shape
  to procedures 12 and 15.

## Alternatives considered

- Local `_gate()` factory inside this file: rejected — a fourth copy of gate construction the
  plan explicitly consolidates; the cross-directory import is already proven in-repo.

## Implementation

### Target file

`tests/integration/test_production_security_regression.py`

### Procedure

1. Add the import with the module's import block:
   ```python
   from tests.agent.services._discovery_gates import gates_from
   ```
2. Replace both sites (current L204 and L245):
   ```python
   result = await McpToolDiscoveryService(ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)).discover_all()
   ```

### Method

Two keyword-argument insertions plus one import line; nothing else in the file changes.

### Details

- If a line-length overflow appears after the insertion, wrap as
  ```python
  result = await McpToolDiscoveryService(
      ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
  ).discover_all()
  ```
  (ruff-format decides the final shape).

## Compatibility considerations

- Lands after procedure 11 and before procedure 06 — plan Phase 2 order; the file is green both
  before and after 06 because green gates reproduce the old `None` behavior.
- This file is not in any other pending plan's target rows; no rebase expected.

## Security considerations

- Test-only; the "production security regression" assertions themselves are untouched.

## Rollback considerations

- `git checkout -- tests/integration/test_production_security_regression.py`; revert together
  with procedures 06 and 11.

## Validation plan

- `uv run pytest tests/integration/test_production_security_regression.py -q` — all tests pass.
- AST gate-less-call scan for this file returns 0.
- `uv run ruff check tests/integration/`, `uv run mypy --no-namespace-packages tests/integration/` — clean.

## Completion criteria

- Zero gate-less constructions in the file; regression assertions unchanged (REQ-004, AC-4).

## Out of Scope

- The signature flip — procedure 06.
- The other gate-less files — procedures 12, 15.

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
- **Related target files**: tests/integration/test_production_security_regression.py
