## Goal

Remove the issue pointer from `mcp_05_02` — the policy wording already states `none` is not permitted, so only the pointer needs removal. (REQ-005 / AC-5)

## Scope

- Remove the issue pointer to `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md` from line 93

## Assumptions

- Option A (never permitted) is the adopted policy
- The policy wording on line 93 already states `none` is not permitted — no text change needed beyond pointer removal

## Design decisions

- Minimal edit: only remove the issue pointer, keep the existing policy wording intact

## Alternatives considered

- Rewriting the policy statement — rejected because the existing wording is already correct

## Implementation

### Target file

`docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`

### Procedure

1. Remove the issue pointer from line 93

### Method

- Edit the line directly to remove the issue reference

### Details

**Before (line 93):**
```markdown
- If `backend == "none"` $\rightarrow$ `RuntimeError`, regardless of environment. The mismatch with the `none` value in the checked-in `config/shell_mcp_server.toml` is tracked in `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md`.
```

**After:**
```markdown
- If `backend == "none"` $\rightarrow$ `RuntimeError`, regardless of environment.
```

## Compatibility considerations

- This document maps to the MCP server-catalog / security-model task entry in `docs/00_index.md`'s "Document References by Task" table
- The change is documentation-only — no code impact

## Security considerations

- This change removes a stale issue pointer — the policy statement remains accurate
- No security behavior changes

## Rollback considerations

- Reverting would restore a stale issue pointer to a resolved issue

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` | Docs consistency | MCP docs checker | Single policy stated; no issue pointers remain |

## Completion criteria

- Issue pointer to `issues/20261005-102246_mcp001_shell-sandbox-none-config-contradicts-startup-audit.md` removed
- Policy statement about `none` → `RuntimeError` remains intact

## Out of scope

- Changes to the sandbox implementation (`init_sandbox`, `build_argv`)
- Other MCP documents not listed in this Plan
- Deployment of documentation changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove pointer from `mcp_05_02` | Completed | 20261006-203959 | 20261006-203959 |  |
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
- **Related target files**: docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md