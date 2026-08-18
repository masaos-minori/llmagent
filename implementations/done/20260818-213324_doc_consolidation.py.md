## Goal

Verify claims in the original require document against current source. Determine which cleanup actions are actually valid based on evidence.

## Scope

**In-Scope:**
- Verify each claim in the require document against current source.
- Determine which cleanup actions are valid vs invalid based on evidence.
- Update this document with corrected assessment.

**Out-of-Scope:**
- Making any actual code changes if claims are invalidated by evidence.

## Assumptions

- The require document's claims may be outdated — this verification corrects them based on direct evidence.

## Findings

### Claim 1: There are duplicated sections across design documents that need consolidation

**Status: VALID — but only as cross-references, not content duplication**

Search for "Deprecated Items" and "Canonical Source Rule" across all docs/ returned 40 matches. These are links/references to the canonical documents (`00_governance_02_canonical-source-rule.md`, `00_governance_05_deprecated-items.md`), not duplicated content blocks. The pattern is consistent: each doc ends with a list of governance links pointing to these two canonical files. No actual content duplication exists.

### Claim 2: The `00_governance_05_deprecated-items.md` file is the canonical location for deprecated items

**Status: VALID**

Confirmed by direct evidence. The file exists and contains the deprecated items section.

### Claim 3: The `00_governance_02_canonical-source-rule.md` file is the canonical location for the Canonical Source Rule

**Status: VALID**

Confirmed by direct evidence. The file exists and contains the canonical source rule section.

## Revised Plan

### Actions NOT to take:
1. Do NOT make any changes — no actual content duplication exists.
2. Do NOT assume the duplicates exist without verifying.

## Implementation

### Target file

N/A — no changes required

## Compatibility considerations

- Markdown links are backward compatible — existing readers see no difference.
- TOC updates do not affect content rendering.
- Attribution notes use HTML comments — invisible to markdown renderers.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert true duplication removals: restore original content from git history.
- Revert near-duplication merges: separate merged content back into individual documents.
- Revert link updates: restore original links.
- No schema changes — rollback is purely code-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All modified docs | Manual review: verify no broken cross-references | Visual inspection of each changed document | No broken links, no misleading content |
| All modified docs | Automated: verify no duplicate sections remain | `rg -n "Deprecated Items\|Canonical Source Rule" docs/` — check for remaining raw text vs. links | Only links to canonical docs remain |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond link replacements and attribution notes.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260817_06_issue.md
- Source requirement: requires/20260818-171100_require.md
- Source plan: plans/20260818-183303_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-213324
- Related target files: docs/**/*.md
