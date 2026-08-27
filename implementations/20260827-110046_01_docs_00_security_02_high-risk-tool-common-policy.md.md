## Goal

Correct the Git MCP bullet in `docs/00_security_02_high-risk-tool-common-policy.md`
(REQ-001: fix the false "no protected-branch policy" claim) per
`plans/20260826-113056_plan.md`.

## Scope

- In scope: the single Git MCP bullet in the "Tool-specific exceptions" section
  (currently ~line 187).
- Out of scope: any other bullet in this document; any code change; any other
  document (covered by other implementation procedures in this same pass).

## Assumptions

- The protected-branch guard mechanism (`GitConfig.protected_branches`,
  `GitSecurityGuards._check_protected_branch()`) is already implemented and tested —
  verified 2026-08-27 against `scripts/mcp_servers/git/git_security.py` and
  `scripts/mcp_servers/git/git_service.py`.
- `config/git_mcp_server.toml` activation of `protected_branches` (REQ-006, a separate
  target file in this pass) does not change the wording required here — this bullet
  describes the policy mechanism, not the shipped config value.

## Design decisions

- State the policy source by symbol name (`GitConfig.protected_branches`,
  `GitSecurityGuards._check_protected_branch()`), per this repository's evidence-
  labeling convention, rather than restating implementation-detail line numbers.
- Keep the existing statement that a technical Force-Push block is not applicable
  (`GitPushRequest` exposes no `force` field) — this part of the current bullet is
  still accurate and must not be removed.
- Do not imply that Dirty-Worktree/Detached-HEAD/postcondition gaps are resolved —
  those remain open (`GIT-001`, `GIT-002`) and are out of scope for this bullet.

## Alternatives considered

- N/A: single-sentence factual correction in an existing bullet; no structural or
  design alternative applies.

## Implementation
### Target file
`docs/00_security_02_high-risk-tool-common-policy.md`

### Procedure
1. Locate the "Git MCP" bullet under "## Tool-specific exceptions" (verified at line
   187 as of 2026-08-27).
2. Replace the false claim with an accurate statement per Method/Details below.
3. Run `uv run python tools/check_docs_consistency.py --domain mcp` to confirm no new
   findings.

### Method
Direct text edit (single bullet, one paragraph) via the Edit tool.

### Details
Current text (verified 2026-08-27):
```
- **Git MCP**: has no protected-branch policy and no technical Force Push block — the
  `branch`/`remote` arguments to `git_checkout`/`git_pull`/`git_push` are passed
  through without command-specific validation, which is an open gap, not a deviation
  covered by an additional restriction (documented in `04_mcp_04_05_git.md`
  Command-specific guard status; tracked as a Known Issue).
```
Replace with text stating: a protected-branch policy exists via
`GitConfig.protected_branches`, enforced by
`GitSecurityGuards._check_protected_branch()` for `git_checkout`/`git_pull`/
`git_push`; a technical Force-Push block is not applicable because `git_push`'s
schema exposes no `force` parameter; Dirty-Worktree/Detached-HEAD/postcondition
verification remain open (`GIT-001`/`GIT-002`, see
`04_mcp_90_inconsistencies_and_known_issues.md`). Cross-reference
`04_mcp_04_05_git.md` "Protected branch authority" and `git_push` policy sections
instead of the now-corrected "Command-specific guard status" section.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- The corrected text must not overstate protection: it must still name the
  Dirty-Worktree/Detached-HEAD/postcondition gaps as open, not silently drop them
  while fixing the protected-branch/Force-Push claims.

## Rollback considerations

- Single-paragraph text revert via `git checkout -- docs/00_security_02_high-risk-tool-common-policy.md`
  (or a targeted `git diff`/`git apply -R`); no other file depends on this exact
  wording.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_security_02_high-risk-tool-common-policy.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no new findings |

## Completion criteria

- The Git MCP bullet no longer states "has no protected-branch policy".
- It names `GitConfig.protected_branches` as the policy source.
- It still states the Force-Push block is not applicable (schema has no `force`
  field), and still names the Dirty-Worktree/Detached-HEAD/postcondition gaps as
  open.

## Out of scope

- Any other section of this document.
- `docs/04_mcp_04_05_git.md`, `docs/04_mcp_90_inconsistencies_and_known_issues.md`,
  and the other four target files of this Plan — each has its own implementation
  procedure document in this same pass.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the Git MCP bullet per Implementation > Method/Details | Pending | — | — | |
| 2 | Run `uv run python tools/check_docs_consistency.py --domain mcp` | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `docs/00_security_02_high-risk-tool-common-policy.md`
