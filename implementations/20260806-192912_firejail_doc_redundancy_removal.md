## Goal

Remove redundant firejail installation instructions from pre-production fail-open checklist and replace them with a pointer to the canonical documentation in auth-profiles-and-sandboxing.md.

## Scope

- **In-Scope**:
  - Verifying the removal of redundant content in `docs/04_mcp_06_16_pre-production-fail-open-checklist.md`.
- **Out-of-Scope**:
  - Modifying `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`.

## Assumptions

1. The required changes have already been applied based on the current file content.
2. This plan primarily serves as a verification step rather than an active implementation step.

## Design decisions

- Treat this as a verification-only task since the implementation appears complete.
- Use grep-based checks to confirm both the absence of redundant content and the presence of the cross-reference.

## Alternatives considered

- Rewrite the entire checklist section: rejected because scope is limited to redundancy removal.
- Delete the checklist entirely: rejected because the checklist itself is still useful; only the redundant firejail instructions should be removed.

## Compatibility considerations

- Readers who previously followed firejail installation instructions from the checklist will now need to consult the canonical doc.
- No API contract changes — this is purely a documentation cleanup.

## Security considerations

N/A — documentation-only changes.

## Rollback considerations

- If the canonical doc (`04_mcp_05_02`) is later modified or deleted, the cross-reference will break.
- If firejail installation requirements change, the canonical doc should be updated first before revisiting this checklist.

## Implementation

### Target file

`docs/04_mcp_06_16_pre-production-fail-open-checklist.md`

### Procedure

**Phase 1: Verification**

1. Verify that the file does NOT contain `apt-get install` or `apk add` related to firejail.
2. Verify that the file DOES contain a pointer to `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`.

### Method

Verification via grep commands.

### Details

```bash
# Check for redundant firejail installation instructions
grep -n "apt-get install.*firejail\|apk add.*firejail" docs/04_mcp_06_16_pre-production-fail-open-checklist.md
# Expected: no output (no matches)

# Check for canonical reference
grep -n "04_mcp_05_02\|auth-profiles-and-sandboxing" docs/04_mcp_06_16_pre-production-fail-open-checklist.md
# Expected: at least one match (the cross-reference exists)
```

If verification fails:
- If `apt-get install` or `apk add` is found: remove those lines and replace with a cross-reference to `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`.
- If the cross-reference is missing: add prose such as "For firejail installation details, see [auth-profiles-and-sandboxing](04_mcp_05_02_auth-profiles-and-sandboxing.md)."

## Validation plan

| Check | Tool | Target | Expected Outcome |
|---|---|---|---|
| Redundancy check | `grep` | `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` | No match for `apt-get install` |
| Pointer check | `grep` | `docs/04_mcp_06_16_pre-production-fail-open-checklist.md` | Contains link to `04_mcp_05_02` |

## Out of scope

- Source code modifications (`scripts/`).
- Changes to `docs/04_mcp_05_02_auth-profiles-and-sandboxing.md`.
- Modifications to other documentation not listed above.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260802-075026_mcp_06_16_firejail_install_removal.md
- Source requirement: requires/20260802-144858_require.md
- Source plan: plans/20260804-122541_plan.md
- Source implementation procedure: N/A
- Generated at: 20260806-192912
- Related target files: docs/04_mcp_06_16_pre-production-fail-open-checklist.md
