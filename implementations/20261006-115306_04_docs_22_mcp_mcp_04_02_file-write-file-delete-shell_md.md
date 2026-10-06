## Goal

Align `mcp_04_02` to the single "never permitted" policy for `none`: fix the sandbox table (remove "Local development only" from the `none` row), update the Security Note, and remove the issue pointer. (REQ-005 / AC-5)

## Scope

- Fix the sandbox table row for `"none"` (line 114)
- Update the Security Note (line 118)
- Remove the issue pointer to `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md`

## Assumptions

- Option A (never permitted) is the adopted policy
- The Security Note already states the correct enforcement — only the issue pointer needs removal

## Design decisions

- Remove the "Local development only" qualifier from the `none` row — `none` is never permitted
- Keep the Security Note's enforcement statement but remove the issue pointer

## Alternatives considered

- Rewriting the entire sandbox table — rejected because only the `none` row needs correction
- Keeping the issue pointer as a reference — rejected because the issue is resolved by this Plan

## Implementation

### Target file

`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. Fix the sandbox table row for `"none"` (line 114)
2. Update the Security Note (line 118) to remove the issue pointer

### Method

- Edit the table row directly
- Edit the Security Note paragraph to remove the issue pointer

### Details

**Before (line 114):**
```markdown
| `"none"` | No process isolation; only `RLIMIT_*` limits apply | Local development only |
```

**After:**
```markdown
| `"none"` | No process isolation; only `RLIMIT_*` limits apply | Never permitted |
```

**Before (line 118):**
```markdown
> **Enforcement:** `shell_sandbox_backend = "none"` raises `RuntimeError` regardless of environment. If this configuration is detected, the agent will fail at startup. Either set `shell_sandbox_backend = "firejail"` or disable `shell-mcp`. The mismatch between this enforcement and the `none` value in the checked-in `config/shell_mcp_server.toml` is tracked in `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md`.
```

**After:**
```markdown
> **Enforcement:** `shell_sandbox_backend = "none"` raises `RuntimeError` regardless of environment. If this configuration is detected, the agent will fail at startup. Set `shell_sandbox_backend = "firejail"` or disable `shell-mcp`.
```

## Compatibility considerations

- This document maps to the MCP server-catalog / security-model task entry in `docs/00_index.md`'s "Document References by Task" table
- The change is documentation-only — no code impact

## Security considerations

- This change aligns the documentation with the security policy — `none` is never permitted
- The enforcement statement remains accurate

## Rollback considerations

- Reverting would restore the contradiction between the documentation and the audit
- The issue pointer removal is permanent — the issue is resolved by this Plan

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` | Docs consistency | MCP docs checker | Single policy stated; no issue pointers remain |

## Completion criteria

- Sandbox table row for `"none"` states "Never permitted"
- Security Note does not reference the issue
- No issue pointer to `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md` remains

## Out of scope

- Changes to the sandbox implementation (`init_sandbox`, `build_argv`)
- Other MCP documents not listed in this Plan
- Deployment of documentation changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Align `mcp_04_02` (table + note + remove pointer) | Completed | 20261006-203959 | 20261006-203959 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261006-203959 | 20261006-203959 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-203959 | 20261006-203959 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-203959 | 20261006-203959 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-222431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115306
- **Related target files**: docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md