## Goal

Correct the `startup_mode="none"` rejection-location sentence in
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` so it names the live
guard `ToolTransportInvoker._run_precall_gates()` instead of the deleted `ToolExecutor` startup
mode check (REQ-004).

## Scope

- The single sentence in the `startup_mode="none"` entry (current file L57): "All tool calls
  routed to this server are immediately rejected with a `\"disabled (startup_mode=none)\"` error
  by the `ToolExecutor` startup mode check before attempting network access."
- Attribution change only: field semantics, default behavior, and the rest of the entry stay
  byte-identical.

## Assumptions

- This document lands after `20261028-005859_01` (the deletion), because the sentence becomes
  actively false once the method is gone; implementing docs first is also acceptable if the
  wording never references the method as still existing (recommended order: code then docs).
- The live error text produced by `_run_precall_gates()` for a disabled server is the quoted
  `"disabled (startup_mode=none)"`-style rejection the entry already quotes (verified live guard
  in scripts/shared/tool_transport_invoker.py REQ-004 block).

## Design decisions

- Name the guard as the inherited boundary method (`ToolTransportInvoker._run_precall_gates()`)
  rather than the class the caller uses (`ToolExecutor`), so the doc points at the single source
  of truth (plan AC-4).

## Alternatives considered

- Delete the sentence: rejected — the rejection behavior is real and user-visible; only its
  location attribution is wrong.

## Implementation

### Target file

`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure

1. Locate the `**\`startup_mode="none"\`:**` entry (current L57).
2. Replace "by the `ToolExecutor` startup mode check" with "by the shared invocation-boundary
   guard `ToolTransportInvoker._run_precall_gates()` (inherited by `ToolExecutor`)".
3. Leave the quoted error string, the default-when-omitted note, and the surrounding entries
   unchanged.

### Method

One sentence edit inside one bullet.

### Details

- Final wording must make clear the rejection happens before any network attempt (preserved
  from the original sentence).
- No other occurrence of "startup mode check" attributing rejection to `ToolExecutor` may
  remain in the file (AC-4 grep gate).

## Compatibility considerations

- 22_mcp domain documentation consistency check per `rules/toolchain.md` must pass after the
  edit.
- Independent of mcpinv001/mcpinv003 doc edits (different files); independent of mcpinv002's
  `mcp_03_01` row (different file).

## Security considerations

- Accuracy only: the doc currently points maintainers at dead code when investigating a security
  boundary (disabled-server rejection).

## Rollback considerations

- `git checkout -- docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`;
  revert together with `20261028-005859_01` if the code deletion is rolled back, otherwise the
  corrected sentence remains accurate.

## Validation plan

- `rules/toolchain.md` documentation consistency check (22_mcp domain).
- Manual review: sentence names `ToolTransportInvoker._run_precall_gates()` and no longer
  attributes the rejection to a `ToolExecutor` check (AC-4).

## Completion criteria

- The `startup_mode="none"` entry attributes rejection to the inherited boundary guard.
- Documentation consistency check passes.

## Out of Scope

- All other `McpServerConfig` field entries.
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` (`20261028-005859_03`).
- Any `scripts/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | After 20261028-005859_01 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation file (plan row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | 22_mcp docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document is the docs row |

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
- **Source issue**: issues/20261027-001347_mcpinv002_remove-dead-check-startup-mode-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103047_mcpinv002_remove-dead-check-startup-mode-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-005859
- **Related target files**: docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md
