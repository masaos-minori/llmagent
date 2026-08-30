# Implementation Procedure: Update MCP-004 Resolution Notes in MCP Inconsistencies Doc (REQ-004b)

## Goal

Update the MCP-004 Resolution Notes in `docs/04_mcp_90_inconsistencies_and_known_issues.md` to reflect the corrected, narrower scope (config floor, real-config test, preview quality) rather than leaving it as-is once this issue's items are addressed.

## Scope

Update the Resolution Notes section of the MCP-004 entry (lines ~92-111) in `docs/04_mcp_90_inconsistencies_and_known_issues.md`.

## Assumptions

- The existing Resolution Notes currently describe the policy owner's decision to raise the three tools to the full-word-yes tier and confirm config/agent.toml has the overrides.
- The remaining open items after this Plan are: config floor check, real-config verification test, and git-specific approval preview quality.
- The "currently includes git_checkout, git_pull, and git_push" caveat mentioned in the Resolution Notes refers to a separate document (`04_mcp_05_03`) that should also be updated eventually but is out of scope for this task.

## Design decisions

- Update the Resolution Notes to mention the three remaining open items explicitly.
- Keep the existing content about the policy owner's decision intact — it provides useful historical context.
- Add a clear statement that the core mismatch is resolved and only defense-in-depth items remain.

## Alternatives considered

- Replace the entire Resolution Notes section. Rejected: the existing content about the policy owner's decision is valuable historical context and should be preserved.
- Create a new entry for each remaining item. Rejected: these are small defense-in-depth items, not separate issues warranting their own entries.

## Implementation

### Target file

`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure

Append the three remaining open items to the existing Resolution Notes.

### Method

**Current Resolution Notes (line 110):**
```markdown
- **Resolution Notes**: Policy owner decided to raise these three tools to the full-word-`yes` tier. `config/agent.toml::approval_risk_rules` now sets `git_checkout`/`git_pull`/`git_push = "high"`, matching the `04_mcp_05_03` table's documented intent (Verified by test, `tests/agent/test_tool_policy_comprehensive.py`). `04_mcp_05_03`'s "currently includes git_checkout, git_pull, and git_push" caveat is now stale and should be removed the next time that document is touched.
```

**Updated Resolution Notes:**
```markdown
- **Resolution Notes**: Policy owner decided to raise these three tools to the full-word-`yes` tier. `config/agent.toml::approval_risk_rules` now sets `git_checkout`/`git_pull`/`git_push = "high"`, matching the `04_mcp_05_03` table's documented intent (Verified by test, `tests/agent/test_tool_policy_comprehensive.py`). `04_mcp_05_03`'s "currently includes git_checkout, git_pull, and git_push" caveat is now stale and should be removed the next time that document is touched. Core mismatch is resolved. Remaining open items (narrower scope): (1) config floor check preventing effective risk below HIGH for git tools via ProductionConfigValidator, (2) end-to-end test exercising the shipped config/agent.toml through the actual approval-risk pipeline, (3) git-specific approval-screen preview in build_preview() instead of generic JSON-dump fallback.
```

### Details

The updated Resolution Notes add three clauses separated by semicolons:
1. `(1) config floor check preventing effective risk below HIGH for git tools via ProductionConfigValidator`
2. `(2) end-to-end test exercising the shipped config/agent.toml through the actual approval-risk pipeline`
3. `(3) git-specific approval-screen preview in build_preview() instead of generic JSON-dump fallback`

## Compatibility considerations

- This is a documentation-only change. No code behavior changes.
- Future reviewers will see the corrected status of MCP-004 without needing to cross-reference the Plan.

## Security considerations

- Accurate documentation of remaining security gaps is important for risk assessment and prioritization.

## Rollback considerations

- If the update is reverted, the doc will again show incomplete information about the MCP-004 status.

## Validation plan

- Manual review: verify the updated Resolution Notes accurately reflect the current state of MCP-004.
- Verify no other references to the old MCP-004 status exist in the doc.

## Completion criteria

- MCP-004 Resolution Notes in docs/04_mcp_90_inconsistencies_and_known_issues.md reflect the corrected, narrower scope.
- Notes mention all three remaining open items: config floor, real-config test, preview quality.

## Out of scope

- Updating the "currently includes git_checkout, git_pull, and git_push" caveat in `04_mcp_05_03` (mentioned in the existing Resolution Notes but out of scope for this task).
- Modifying any other MCP inconsistency entries.
- Restructuring the doc format.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update MCP-004 Resolution Notes in docs/04_mcp_90_inconsistencies_and_known_issues.md | Pending | — | — | |

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
- **Related target files**: docs/04_mcp_90_inconsistencies_and_known_issues.md
