## Goal

Add a short classification-before-removal rule to the Backward Compatibility Check section (`check_compat_shims.py`) of `docs/00_governance/governance_04_documentation-checks.md`, stating that a `fallback` or `legacy` search hit must be classified (backward compatibility, operational fallback, replay, idempotency, or other) with evidence before a compatibility removal issue is filed. (`REQ-002`; AC: review guidance requires classification evidence before a removal issue is filed.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Section 4 (Backward Compatibility Check) is the sole human compatibility-review guidance in `docs/`; no checklist lives in `governance_01` (spec/source conflict classification, not compat removal) or elsewhere in `docs/`/`skills/`. Verified.
- The new rule appends to the existing section without altering any existing checker behavior or the Governance Verification Matrix.
- The four categories it references are the ones the glossary in `governance_02` will hold once `REQ-001` lands (backward compatibility, operational fallback, replay, idempotency) plus "other".

## Design decisions
- **Append a short paragraph** to the end of Section 4, after the historical-reference allowlist, so it reads as a manual-review step that complements the automated checks rather than a sixth automated check.
- **Reference the glossary categories by name** so the rule points at `governance_02` as the canonical definition of each category.

## Alternatives considered
- Creating a new review-checklist document. Rejected: no human compat-review guidance exists elsewhere, and appending keeps one home instead of fragmenting guidance across the glossary and a new file.

## Implementation
### Target file
`docs/00_governance/governance_04_documentation-checks.md`
### Procedure
1. Append a short "Classification before removal" paragraph to the end of Section 4 (Backward Compatibility Check), after the historical-reference allowlist paragraph.
### Method
One paragraph stating that any `fallback`/`legacy`/`compatibility` search hit is triaged manually: classify it as backward compatibility, operational fallback, replay, idempotency, or other using the definitions in `governance_02`, record the evidence for the classification, and only then decide whether a removal issue is warranted — a valid runtime-resilience category (operational fallback, replay, idempotency) is not a compatibility shim and must not be removed.
### Details
- Keep it category-level; do not name specific symbols, config values, or line numbers (docs content policy).
- Do not modify the automated-check list, the Governance Verification Matrix, or any other section.

## Compatibility considerations
N/A: additive guidance; no checker behavior changes and no existing text is reworded.

## Security considerations
N/A: documentation-only; no runtime path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `governance_04` | New classification paragraph present; structure/content clean; no new removed-name reintroduction. | `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`, `check_compat_shims.py` | All pass; no new errors. |
| Whole change | No Japanese. | `uv run python tools/check_docs_japanese.py` | Pass. |

## Completion criteria
- Section 4 states that a `fallback`/`legacy` hit must be classified (backward compatibility, operational fallback, replay, idempotency, other) with evidence before a removal issue is filed.
- Structure and content checkers pass.

## Out of Scope
- Adding the glossary rows (`governance_02`, `REQ-001`).
- Rewriting or rewording the existing automated-check descriptions.
- Rewriting EventBus wording (`REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add classification-before-removal rule to `governance_04` §4 | Completed | 20261117-074751 | 20261117-074751 | Append paragraph after historical allowlist |
| 3 | Run the documentation checkers (`rules/toolchain.md`) | Completed | 20261117-074751 | 20261117-074751 | `check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `check_compat_shims.py` |

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
- **Requirement ID**: `REQ-002` (review guidance requires classification evidence before a removal issue)
- **Source issue**: `issues/20261116-115026_compat005_compat-fallback-terminology.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-000631_compat005_compat-fallback-terminology.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-072313
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
