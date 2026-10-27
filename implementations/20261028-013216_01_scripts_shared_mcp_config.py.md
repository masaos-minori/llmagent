# mcpcompat001-remove-the-health-re-export-from-mcp-config

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Remove the Health-type re-export from `scripts/shared/mcp_config.py` so
`shared.mcp_health` becomes the only import path for `McpServerHealthState` and
`McpServerHealthRegistry` (REQ-002; AC-2).

## Scope

- `scripts/shared/mcp_config.py`: delete the re-export block at current L19-L22:
  > from shared.mcp_health import (  # noqa: F401
  >     McpServerHealthRegistry,
  >     McpServerHealthState,
  > )

## Assumptions

- The eight importers listed in the Plan's Background were re-verified against the
  current source on 2026-10-28 (AST scan): `scripts/shared/tool_transport_invoker.py:15`,
  `scripts/agent/startup_reporter.py:84`, `scripts/agent/services/mcp_status.py:16`,
  `scripts/agent/context.py:31`, `tests/integration/test_agent_mcp_integration.py:18`,
  `tests/shared/test_tool_transport_invoker.py:14`,
  `tests/shared/test_tool_executor_routing.py:14`, `tests/shared/test_tool_executor.py:15`
  — identical to the Plan's list.
- UNK-03 (external consumers outside this repository) remains the owner's risk; the
  deletion is one revertable commit.

## Design decisions

- The deletion is a single-block removal; no replacement code is added. After it, the
  module must not reference either type name (AC-2).

## Alternatives considered

- Keeping the re-export with a DeprecationWarning shim: rejected — the Issue's goal is
  one canonical import path; a warning shim preserves the second path.

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. Immediately before editing, re-run the repository-wide importer search (Plan Risk
  mitigation): `rg "from shared.mcp_config import" scripts tests tools` piped through a
  syntax-level filter for the two Health names; stop if an importer outside the eight
  Plan-listed files appears.
2. Only when the importers are already moved (procedures 02-05 and 07-10 of this batch
  have landed), delete the L19-L22 import block verbatim, including the `# noqa: F401`.

### Method

Block deletion; the surrounding imports (`shared.config_utils`, `shared.logger`) and
`logger = logging.getLogger(__name__)` stay as written.

### Details

- Post-change the file contains neither string `McpServerHealthRegistry` nor
  `McpServerHealthState` (AC-2 check: `rg "McpServerHealth" scripts/shared/mcp_config.py`
  returns nothing).
- The `# noqa: F401` marker is removed with the block; ruff must then report no unused
  import in the file.

## Compatibility considerations

- Hard step dependency: this procedure lands after every importer-movement procedure in
  this batch (02, 03, 04, 05, 07, 08, 09, 10); landing earlier breaks those modules at
  import time.
- `shared.mcp_config` is imported by 64 files for other names (`McpServerConfig`,
  `TransportType`, `StartupMode`, loaders); those imports are untouched.
- The companion document sentence is removed by procedure 16 in the same change set.

## Security considerations

- None directly; the change closes a duplicated import surface.

## Rollback considerations

- Single revertable commit restoring the L19-L22 block; importers on the canonical path
  keep working either way.

## Validation plan

- `uv run pytest tests/shared/test_mcp_config.py -v` (pass).
- `uv run mypy --no-namespace-packages scripts/` (no new finding).
- `uv run ruff check scripts/shared/mcp_config.py` (no unused-import finding).
- AC-2 `rg` check above.

## Completion criteria

- The file no longer references either Health type and carries no `# noqa: F401` for
  them (AC-2).
- Tests and type checks pass.

## Out of Scope

- The eight importer edits — covered by procedures 02-05 and 07-10.
- The document sentence — covered by procedure 16.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands after procedures 02-05, 07-10 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | No new test; existing test file guards |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | pytest, mypy, ruff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | Procedure 16 covers the doc |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: scripts/shared/mcp_config.py
