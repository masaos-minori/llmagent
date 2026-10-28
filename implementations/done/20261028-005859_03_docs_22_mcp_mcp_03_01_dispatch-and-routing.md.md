## Goal

Correct the "Not to be confused with `ToolExecutor.server_configs`" note in
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md` so it no longer presents
`self._server_configs.get(server_key)` in `shared/tool_executor.py` as a live startup-mode-check
location after the dead method is deleted (REQ-004).

## Scope

- The single paragraph at current file L109: it currently states `ToolExecutor.server_configs`
  is "used for MCP server transport and startup-mode checks (`self._server_configs.get(server_key)`)".
- Rewrite the usage clause; the paragraph's core claims (distinct from `ToolRouteResolver`,
  current and active, `dict[str, McpServerConfig]`, unrelated to tool-name routing) stay.

## Assumptions

- After `20261028-005859_01` deletes `_check_startup_mode`, the only `self._server_configs.get`
  calls in the runtime path are in `scripts/shared/tool_transport_invoker.py` (verified: L103,
  L268); the attribute itself remains inherited, so "current, active configuration" stays true.
- This file is shared with the mcpinv001 procedure `20261028-004925_03` ("Idempotency and
  retry" section) and mcpinv002's own note: sections are disjoint per both plans' overlap notes
  (recorded by `tools/check_plan_target_overlaps.py`); re-read the file and rebase if the other
  edit landed first.

## Design decisions

- Attribute the startup-mode check to `ToolTransportInvoker._run_precall_gates()` (where the
  `get()` call actually happens, scripts/shared/tool_transport_invoker.py L268) while keeping
  the paragraph's purpose — distinguishing `ToolExecutor.server_configs` from the nonexistent
  `ToolRouteResolver.server_configs`.

## Alternatives considered

- Remove the code-reference clause entirely: acceptable fallback, but keeping the accurate
  location is more useful and matches AC-4's "name the live guard" wording.

## Implementation

### Target file

`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Locate the paragraph beginning "**Not to be confused with `ToolExecutor.server_configs`:**"
   (current L109).
2. Replace "used for MCP server transport and startup-mode checks
   (`self._server_configs.get(server_key)`)" with "used for MCP server transport and — via the
   inherited `ToolTransportInvoker` boundary — startup-mode checks
   (`ToolTransportInvoker._run_precall_gates()` calls `self._server_configs.get(server_key)`)".
3. Leave the rest of the paragraph and the surrounding section untouched.

### Method

One clause edit inside one paragraph.

### Details

- The corrected text must not present `shared/tool_executor.py` as containing the `get()` call;
  after the deletion it does not.
- Do not touch the "Idempotency and retry" section (owned by mcpinv001's row).

## Compatibility considerations

- mcpinv001 `20261028-004925_03` edits the same file in a disjoint section; both plans record
  the overlap as Compatible and the later implementer rebases.
- 22_mcp domain documentation consistency check per `rules/toolchain.md` after the edit.

## Security considerations

- Accuracy only: the note currently documents a guard location that no longer exists, misleading
  anyone auditing disabled-server enforcement.

## Rollback considerations

- `git checkout -- docs/22_mcp/mcp_03_01_dispatch-and-routing.md` reverts only this paragraph if
  applied alone; if reverted together with `20261028-005859_01`, the original text becomes true
  again. Coordinate with `20261028-004925_03` to avoid reverting mcpinv001's section by accident
  (use targeted edits, not whole-file checkout, when both plans' doc edits are partially rolled
  back).

## Validation plan

- `rules/toolchain.md` documentation consistency check (22_mcp domain).
- Manual review: paragraph attributes the startup-mode `get()` call to
  `ToolTransportInvoker._run_precall_gates()`; `grep -n 'tool_executor.py.*startup-mode' docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
  shows no stale attribution (AC-4).

## Completion criteria

- Paragraph names the live guard; no text presents `tool_executor.py` as a startup-mode-check
  location.
- Documentation consistency check passes; mcpinv001's section unaffected.

## Out of Scope

- The "Idempotency and retry" section (mcpinv001's row, `20261028-004925_03`).
- `docs/22_mcp/mcp_06_02_...` (`20261028-005859_02`).
- Any `scripts/` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-110204 | 20261028-111441 | Rebased on 20261028-004925_03 (its "Idempotency and retry" bullet landed first; untouched here) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-111441 | N/A: documentation file (plan row) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-110204 | 20261028-111441 | 22_mcp docs consistency check passed; see Blocker Log for the grep-gate nuance |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-111441 | This document is the docs row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | The prescribed AC-4 grep (`tool_executor.py.*startup-mode`) still matches the corrected paragraph because the sentence legitimately names `shared/tool_executor.py` as the attribute's home on the same line; the check itself is attributed to `ToolTransportInvoker._run_precall_gates()` per the Procedure's mandated wording, so the Completion criterion ("no text presents `tool_executor.py` as a startup-mode-check location") is satisfied — the raw regex is a false positive on the mandated text | Yes | 20261028-110204 |

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
- **Related target files**: docs/22_mcp/mcp_03_01_dispatch-and-routing.md