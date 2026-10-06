## Goal

Correct the `shell_sandbox_backend` check-details cell in `mcp_05_03` from "RuntimeError in production if `none`" to "RuntimeError regardless of environment if `none`", removing the implication that `none` is allowed outside production. (REQ-005 / AC-5)

## Scope

- Correct the `shell_sandbox_backend` check-details cell (line 41)

## Assumptions

- Option A (never permitted) is the adopted policy
- The rest of the check-details cell is accurate — only the `none` portion needs correction

## Design decisions

- Change "in production if" to "regardless of environment if" — this is a minimal, targeted correction

## Alternatives considered

- Rewriting the entire check-details cell — rejected because only the `none` portion is incorrect

## Implementation

### Target file

`docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure

1. Correct the `shell_sandbox_backend` check-details cell (line 41)

### Method

- Edit the cell directly

### Details

**Before (line 41):**
```markdown
| `shell_sandbox_backend` | `shell_mcp_server.toml` | RuntimeError if `"firejail"` + binary missing; WARNING if not `"firejail"` or `"none"`; RuntimeError in production if `"none"` |
```

**After:**
```markdown
| `shell_sandbox_backend` | `shell_mcp_server.toml` | RuntimeError if `"firejail"` + binary missing; WARNING if not `"firejail"` or `"none"`; RuntimeError regardless of environment if `"none"` |
```

## Compatibility considerations

- This document maps to the MCP server-catalog / security-model task entry in `docs/00_index.md`'s "Document References by Task" table
- The change is documentation-only — no code impact

## Security considerations

- This change removes the implication that `none` is allowed outside production — aligning with the security policy
- No security behavior changes

## Rollback considerations

- Reverting would restore the implication that `none` is allowed outside production

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` | Docs consistency | MCP docs checker | Single policy stated; no issue pointers remain |

## Completion criteria

- Check-details cell states "RuntimeError regardless of environment if `none`"
- No implication that `none` is allowed outside production

## Out of scope

- Changes to the sandbox implementation (`init_sandbox`, `build_argv`)
- Other MCP documents not listed in this Plan
- Deployment of documentation changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct `none` wording in `mcp_05_03` | Completed | 20261006-205614 | 20261006-205614 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261006-205614 | 20261006-205614 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-205614 | 20261006-205614 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-205614 | 20261006-205614 |  |

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
- **Related target files**: docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md