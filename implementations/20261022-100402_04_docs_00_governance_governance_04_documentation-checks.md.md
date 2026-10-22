## Goal
Document the anchor check in the "Checks performed per domain" list of `governance_04` (REQ-006: document the check; Warning-level, report-only, no gate row).

## Scope
- Edit the "Broken internal links" bullet only.

## Assumptions
- The check is a Warning-level addition to an existing check, not a new gate, so no Verification Matrix row is added.

## Design decisions
- Describe behavior and severity in one sentence; do not list the slug algorithm in prose beyond naming it (GitHub-style heading slugs).

## Alternatives considered
N/A: one-bullet docs edit.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Extend the bullet "Broken internal links (`.md` links resolve correctly)" with a clause stating that a link `#anchor` matching no heading of its target document (same-page links included, GitHub-style heading slugs) is reported as a Warning.

### Method
- Minimal in-place edit; keep the bullet's position and the surrounding list unchanged.

### Details
- Re-read the file immediately before editing: it is also edited by the domain-coverage and glossary procedures of this batch.
- No counts or line numbers in the new text (docs content policy).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The bullet states the anchor check, its Warning level, and its same-page coverage; docs checkers pass.

## Out of Scope
- Matrix rows, gate changes, other bullets.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the "Broken internal links" bullet | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document the check)
- **Source issue**: `issues/20261021-101812_anchorcheck_add-a-dedicated-anchor-validation-check-for-docs-links.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093452_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100402
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
