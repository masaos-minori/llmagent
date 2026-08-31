# Implementation Procedure: Correct ADR-012 Known Deviations MCP-004 Entry (REQ-004a)

## Goal

Correct ADR-012's Known Deviations MCP-004 entry to reflect that the core mismatch (approval tier falling back to MEDIUM/y-N instead of HIGH/full-word-yes) is already fixed, and the remaining scope is narrower (config floor, real-config test, preview quality).

## Scope

Update line 179 of `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`:
```markdown
- **Known Issue**: MCP-004 — approval tier for these tools falls back to `MEDIUM` (`y/N`) rather than the documented `HIGH` (full-word `yes`).
```
to reflect the corrected status.

## Assumptions

- The existing MCP-004 entry format uses bold label + description pattern consistent with other entries.
- The core mismatch described in the original MCP-004 entry is already resolved (verified by reading config/agent.toml and tool_approval.py source).
- The remaining open items are: config floor check, real-config verification test, and git-specific approval preview quality.

## Design decisions

- Keep the entry concise — one sentence summarizing the current state.
- Do not remove the MCP-004 entry entirely; it still documents a known deviation (the remaining narrow scope).
- Reference the narrower remaining scope explicitly so future reviewers understand what is still open vs. what was closed.

## Alternatives considered

- Remove the MCP-004 entry entirely. Rejected: the remaining scope (config floor, real-config test, preview quality) is still a known deviation worth documenting until fully addressed.
- Split into two entries (one for resolved, one for remaining). Rejected: unnecessary fragmentation; a single updated entry is clearer.

## Implementation

### Target file

`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`

### Procedure

Replace the existing MCP-004 Known Deviations entry with an updated version reflecting the corrected scope.

### Method

Edit line 179 in the Known Deviations section:

**Before:**
```markdown
- **Known Issue**: MCP-004 — approval tier for these tools falls back to `MEDIUM` (`y/N`) rather than the documented `HIGH` (full-word `yes`).
```

**After:**
```markdown
- **Known Issue**: MCP-004 — effective risk below HIGH for git tools can occur if config is downgraded (no floor check); approval-screen preview for git tools falls through to generic JSON dump; no end-to-end test exercises the shipped config through the actual approval flow.
```

### Details

The updated entry captures three remaining concerns:
1. Config downgrade protection gap (REQ-001): no floor prevents effective risk below HIGH
2. Approval-screen preview quality gap (REQ-003): git_* tools lack purpose-built preview
3. Verification completeness gap (REQ-002): no test exercises the real config through the actual pipeline

## Compatibility considerations

- This is a documentation-only change. No code behavior changes.
- Future reviewers will see the corrected status of MCP-004 without needing to cross-reference the Plan.

## Security considerations

- Accurate documentation of remaining security gaps is important for risk assessment and prioritization.

## Rollback considerations

- If the correction is reverted, the ADR will again show stale information about the MCP-004 status.

## Validation plan

- Manual review: verify the updated entry accurately reflects the current state of MCP-004.
- Verify no other references to the old MCP-004 description exist in the ADR.

## Completion criteria

- ADR-012's Known Deviations MCP-004 entry reflects the corrected, narrower scope.
- Entry mentions all three remaining open items: config floor, preview quality, real-config test.

## Out of scope

- Updating other MCP-004 entries in docs/04_mcp_90_inconsistencies_and_known_issues.md (separate procedure document).
- Modifying any other Known Deviations entries.
- Adding new sections or restructuring the ADR.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update MCP-004 entry in ADR-012 Known Deviations section | Completed | 20260831-150523 | 20260831-150523 | Already updated on disk (commit `e8f0086bf`, prior session) — `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` line 211's Known Issue entry matches this document's "After" text verbatim, mentioning all three remaining items (config floor, preview quality, real-config test). `uv run python tools/check_docs_quality.py` clean; no other MCP-004 references found in the ADR needing correction. |

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
- **Source issue**: issues/20260828-163234_mcp004_approval_risk_hierarchy_gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-150209_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-205709
- **Related target files**: docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md
