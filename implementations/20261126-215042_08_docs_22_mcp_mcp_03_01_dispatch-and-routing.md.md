## Goal

Document the cross-scope conflict rule and confirm the `<kind>:<identity>` convention in the MCP
dispatch documentation (REQ-004, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The scheduler section is `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:108-167`; the conflict
  predicate is described at line 116 as "exact match, or ancestor/descendant for `filesystem:`
  scopes" only (re-verified 20261126, Step 3a).
- The convention is already defined in `scripts/shared/resource_scope.py:81`
  (`resolve_resource_scopes()` docstring), so this row records it, it does not define it.
- The file is also a mcpai012 target row; judged compatible — this procedure adds the cross-scope
  rule, mcpai012 performs the final sweep afterward (execution order: mcpai013 runs after mcpai012
  per the Issue's "Keep last").
- Documentation is written in English per `skills/DESIGN.md` Output language.

## Design decisions
- Update the existing `resource_scopes` bullet (line 116) in place rather than adding a new section,
  so the conflict rule stays in the single place the scheduler's inputs are described.
- Add one sentence to the conflict-graph table row (line 167) naming the GitHub ancestor case, so
  the table and the bullet agree.

## Alternatives considered
- A new "Cross-scope conflicts" subsection: rejected — it would duplicate the predicate description
  already in the Fields list and create a second source of truth for the same rule.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
1. Extend the `resource_scopes` bullet (116) to state the full rule: exact match; `filesystem:`
   ancestor/descendant; and `github_repo:` ancestor of `github_branch:`, `github_issue:`,
   `github_pull_request:` scopes whose identity begins with `<owner>/<repo>/`.
2. State the confirmed convention in the same bullet: every scope string is
   `<kind>:<identity>`, and composed GitHub kinds join their present key values with `/`
   (`_COMPOSED_KIND_SEPARATORS`).
3. Update the conflict-graph table row (167) to mention the GitHub ancestor case alongside the
   existing exact-overlap wording.

### Method
Keep the existing wording for the `filesystem:` rule and the `global:write` fallback unchanged; only
add the GitHub ancestor clause and the convention sentence.

### Details
- No code references are added beyond the module name already cited in the bullet.

## Compatibility considerations
- mcpai012's final sweep runs after this change; the added sentences must not restate mcpai012's
  scope, which is the documentation sweep itself.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Documentation consistency | `uv run python tools/check_docs_quality.py` | No findings |
| Documentation structure | `uv run python tools/check_docs_structure.py` | No findings |
| Content policy | `uv run python tools/check_docs_content_policy.py` | No findings |
| Domain consistency | `uv run python tools/check_docs_consistency.py --domain mcp` | No findings |

## Completion criteria
- The documentation states the cross-scope conflict rule and the confirmed `<kind>:<identity>`
  convention (AC-4).
- All four documentation checkers report no findings.

## Out of Scope
- The predicate implementation — procedure 01.
- mcpai012's final documentation sweep.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | N/A: documentation row; validation is the docs checkers |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is the documentation change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at procedure creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (the `<kind>:<identity>` convention is confirmed and documented)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
