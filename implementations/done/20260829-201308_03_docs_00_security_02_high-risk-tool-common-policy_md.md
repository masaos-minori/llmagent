# Implementation Procedure: DOC-005 Update security policy doc Git MCP bullet

## Goal

Update `docs/00_security_02_high-risk-tool-common-policy.md`'s Git MCP bullet: remove claim that `GIT-001`/`GIT-002` gaps remain open, replacing it with a statement reflecting their resolved state.

## Scope

- Replace the claim "Dirty-Worktree/Detached-HEAD/postcondition verification gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`; see `04_mcp_90_inconsistencies_and_known_issues.md`)" with a statement reflecting their resolved state (DOC-005 REQ-007)

## Assumptions

- The plan's claim that line 187 states "gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`)" is correct (verified in this cycle)
- The plan's claim that `GIT-001`/`GIT-002` are now resolved (per DOC-005 target rows 1-2) is correct

## Design decisions

- Replace the stale claim with a statement reflecting the resolved state — e.g., "Dirty-Worktree/Detached-HEAD guards and postcondition verification are implemented (see `04_mcp_90_inconsistencies_and_known_issues.md`)."
- Do NOT reference `GIT-001`/`GIT-002` as open gaps since they are now resolved.

## Alternatives considered

- Simply remove the entire clause about `GIT-001`/`GIT-002` — rejected because it leaves no trace of what was there and loses the informational value that these concerns are addressed.
- Change the wording to "were previously tracked as Known Issues `GIT-001`/`GIT-002`, now resolved" — acceptable but slightly verbose; prefer the cleaner positive statement.

## Implementation

### Target file

`docs/00_security_02_high-risk-tool-common-policy.md`

### Procedure

#### Phase 1: Preparation

1. Confirm current content at line 187: "The Force-Push block is not applicable because `git_push` exposes no `force` parameter. Dirty-Worktree/Detached-HEAD/postcondition verification gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`; see `04_mcp_90_inconsistencies_and_known_issues.md`)."

#### Phase 2: Core Logic Implementation

2. Replace the sentence "Dirty-Worktree/Detached-HEAD/postcondition verification gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`; see `04_mcp_90_inconsistencies_and_known_issues.md`)" with "Dirty-Worktree/Detached-HEAD guards and postcondition verification are implemented (see `04_mcp_90_inconsistencies_and_known_issues.md`)."

#### Phase 3: Deployment & Verification

3. Manual verification — re-read the affected section to confirm edits are accurate and consistent (AC-005)

### Method

- Line 187 currently reads: "The Force-Push block is not applicable because `git_push` exposes no `force` parameter. Dirty-Worktree/Detached-HEAD/postcondition verification gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`; see `04_mcp_90_inconsistencies_and_known_issues.md`)."
- The first sentence about Force-Push is still valid (no `force` parameter exists). Only the second sentence needs updating.
- New wording should reflect that both pre-condition (Dirty-Worktree/Detached-HEAD) and post-condition checks are now implemented per DOC-005 target row 1.

### Details

#### Current content at line 187:

```markdown
- **Git MCP**: `GitConfig.protected_branches` and `GitSecurityGuards._check_protected_branch()` enforce a protected-branch policy (tests: `test_git_security_compliance.py::test_check_protected_branch`, `test_git_checkout_protected_branch`, `test_git_push_protected_branch`, `test_is_safe_ref`). The Force-Push block is not applicable because `git_push` exposes no `force` parameter. Dirty-Worktree/Detached-HEAD/postcondition verification gaps remain open (tracked as Known Issues `GIT-001`/`GIT-002`; see `04_mcp_90_inconsistencies_and_known_issues.md`).
```

#### New content:

```markdown
- **Git MCP**: `GitConfig.protected_branches` and `GitSecurityGuards._check_protected_branch()` enforce a protected-branch policy (tests: `test_git_security_compliance.py::test_check_protected_branch`, `test_git_checkout_protected_branch`, `test_git_push_protected_branch`, `test_is_safe_ref`). The Force-Push block is not applicable because `git_push` exposes no `force` parameter. Dirty-Worktree/Detached-HEAD guards and postcondition verification are implemented (see `04_mcp_90_inconsistencies_and_known_issues.md`).
```

## Compatibility considerations

- No source-code compatibility impact — documentation-only change.
- Other documents referencing `GIT-001`/`GIT-002` as open will be consistent once all DOC-005 rows are applied.

## Security considerations

- Low risk: documentation correction only. Incorrectly claiming these are resolved when they are not could mislead reviewers, but the adversarial verification in this cycle confirms the guards are actually implemented.

## Rollback considerations

- Simple revert: restore previous text. No operational impact since no code changes are involved.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_security_02_high-risk-tool-common-policy.md` | Manual review: verify Git MCP bullet no longer claims GIT-001/GIT-002 gaps remain open | Manual read | Bullet reflects resolved state |

## Completion criteria

- Git MCP bullet no longer claims `GIT-001`/`GIT-002` gaps remain open (REQ-007)

## Out of scope

- Updating Known Issues doc entries for GIT-001/GIT-002 (separate target file row)
- Updating ADR-012's Known Deviations section (separate target file row)
- Changing ADR-012's Status field (owner decision tied to NC-019)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260831-110636 | 20260831-110636 | Adversarial re-check confirmed line 187's target sentence matches the plan verbatim (no drift, unlike DOC-005 rows 1-2). Adjacent first-sentence claim about `GitSecurityGuards._check_protected_branch()` was noted but left untouched — out of scope for REQ-007. |
| 2 | Add or update tests per Validation plan | Completed | 20260831-110636 | 20260831-110636 | Not required — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260831-110636 | 20260831-110636 | Not required — documentation-only change; ran `tools/check_docs_structure.py`/`check_docs_quality.py` instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260831-110636 | 20260831-110636 | This document's Target file *is* the documentation edit. Structure check's 1 pre-existing finding (missing '## Keywords') confirmed via `git stash` comparison to predate this edit — left as-is, out of scope. |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260828-161729_doc005_git001_git002_stale_open_status.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260829-121751_doc005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260829-201308
- **Related target files**: docs/00_security_02_high-risk-tool-common-policy.md
