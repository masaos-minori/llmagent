## Goal

Document the cross-scope conflict rule and confirm the `<kind>:<identity>` convention in the MCP
dispatch documentation (REQ-004, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The scheduler section is `docs/22_mcp/mcp_03_01_dispatch-and-routing.md:108-167`; the conflict
  predicate is described as "exact match, or ancestor/descendant for `filesystem:` scopes" only
  (re-verified 20261126, Step 3a). Correction from execution (20261127): the bullet is at line 121 and
  the conflict-graph table row is at 171, not 116 and 167 as cited here — the section range shifted by
  the lines added earlier; the cited wording itself was confirmed.
- The convention is already defined in `scripts/shared/resource_scope.py:81`
  (`resolve_resource_scopes()` docstring), so this row records it, it does not define it.
- The file is also a mcpai012 target row; judged compatible — this procedure adds the cross-scope
  rule, mcpai012 performs the final sweep afterward (execution order: mcpai013 runs after mcpai012
  per the Issue's "Keep last").
- Documentation is written in English per `skills/DESIGN.md` Output language.

## Design decisions
- Update the existing `resource_scopes` bullet (line 121) in place rather than adding a new section,
  so the conflict rule stays in the single place the scheduler's inputs are described.
- Add one sentence to the conflict-graph table row (line 171) naming the GitHub ancestor case, so
  the table and the bullet agree.

## Alternatives considered
- A new "Cross-scope conflicts" subsection: rejected — it would duplicate the predicate description
  already in the Fields list and create a second source of truth for the same rule.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
1. Extend the `resource_scopes` bullet (121) to state the full rule: exact match; `filesystem:`
   ancestor/descendant; and `github_repo:` ancestor of `github_branch:`, `github_issue:`,
   `github_pull_request:` scopes whose identity begins with `<owner>/<repo>/`.
2. State the confirmed convention in the same bullet: every scope string is
   `<kind>:<identity>`, and composed GitHub kinds join their present key values with `/`
   (`_COMPOSED_KIND_SEPARATORS`).
3. Update the conflict-graph table row (171) to mention the GitHub ancestor case alongside the
   existing exact-overlap wording.

### Method
Keep the existing wording for the `filesystem:` rule and the `global:write` fallback unchanged; only
add the GitHub ancestor clause and the convention sentence.

### Details
- No code references are added beyond the module name already cited in the bullet.
- Deviation from Method (20261127): Method said the `global:write` fallback wording stays unchanged, but
  the user decision of 20261127 (recorded in procedure 01) changed the fallback semantics for composed
  GitHub identities — a write tool missing a declared key now resolves to `global:write` instead of a
  partial identity. The `is_write` bullet was extended with that one clause so the documentation matches
  the implementation.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-092247 | 20261127-092247 | Verified against current source: the scheduler section is 112-174 and the conflict predicate wording was confirmed, but the cited line numbers were stale (bullet at 121 not 116, table row at 171 not 167) - corrected in this document. Applied the three edits: the resource_scopes bullet now states the full rule plus the <kind>:<identity> convention and the / composition of GitHub kinds; the conflict-graph table row names the GitHub ancestor case. Deviation: the is_write bullet also gained the partial-identity fail-closed clause required by the user decision of 20261127 (procedure 01), which Method had said to leave unchanged. Changed file: docs/22_mcp/mcp_03_01_dispatch-and-routing.md. |
| 3 | Run the docs checkers (`rules/tool-gates.md`) | Completed | 20261127-092247 | 20261127-092247 | Docs checkers all pass on the changed file: check_docs_quality.py, check_docs_structure.py, check_docs_content_policy.py, check_docs_consistency.py --domain mcp. No ADR target so check_adr_structure.py not applicable. No test cycle for this row (docs-only, Batch mode documentation case). |

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