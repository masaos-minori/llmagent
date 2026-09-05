# Remove document recency as a canonical-authority rule

## Priority
Medium

## Summary
Remove the rule that the most recently reviewed or modified document is authoritative. Document recency may be used only as evidence for staleness investigation and must never change canonical authority.

## Background
The documentation checks currently state that the most recently reviewed document is authoritative among conflicting documents.

## Problem
This can allow a newer Reference, Note, or Guide to override an Accepted ADR or canonical Specification solely because it was reviewed later. Review date, modification date, commit date, and file recency describe chronology. They do not establish ownership of a claim.

## Reason for Change
A recency-based authority rule directly contradicts the target-based resolution model (`M-01-02`): a stale-but-canonical Specification would lose authority to a newer non-canonical Note purely because of its timestamp, even though timestamp carries no ownership information.

## Implementation Intent
Ensure that canonical authority is derived only from the approved decision-target and claim-type model.

## Target Files or Areas
- `docs/00_governance_01_documentation-policy.md`
- `docs/00_governance_04_documentation-checks.md`
- All area document guides
- Documentation review templates
- Pull request templates
- Documentation validation tools

## Required Changes
1. Remove all statements that make the newest or most recently reviewed document authoritative.
2. Add a normative rule stating that review date, modification date, commit date, and recency do not determine canonical authority.
3. Define permitted uses of recency:
   - Detecting potentially stale non-canonical content
   - Prioritizing investigation
   - Scheduling periodic review
   - Identifying the revision of the same canonical file
4. Define prohibited uses of recency:
   - Overriding an Accepted ADR
   - Overriding a canonical Specification
   - Overriding an official API contract or schema
   - Overriding deployed configuration
   - Overriding an Operations runbook
   - Promoting a Note or Reference to canonical status
5. Update manual review procedures and merge checklists.
6. Search the repository for equivalent wording, including `most recent`, `latest reviewed`, `newest`, `last modified`, `authoritative`, and `source of truth`.
7. Update or add tests for any automated rule that derives authority from timestamps.

### Required normative text

Add wording equivalent to the following without duplicating it across multiple canonical documents:

`Review date, modification date, commit date, and document recency do not determine canonical authority. They may be used only as investigation evidence for identifying stale or conflicting non-canonical content.`

## Constraints
N/A: none beyond preserving recency-based staleness detection, investigation prioritization, periodic-review scheduling, and same-file revision identification as the only permitted uses of recency.

## Acceptance Criteria
- [ ] No active governance rule grants authority based on recency.
- [ ] Recency is explicitly limited to staleness detection and investigation support.
- [ ] Manual review instructions use the canonical resolution algorithm.
- [ ] Accepted ADRs cannot be overridden by newer non-canonical documents.
- [ ] Canonical Specifications cannot be overridden by newer Guides, Notes, or References.
- [ ] Repository-wide searches find no conflicting active rule.
- [ ] Tests cover timestamp-independent authority resolution where applicable.
- [ ] Documentation validation tests pass.

## Testing Expectations
Run repository-wide searches for the listed keywords (`most recent`, `latest reviewed`, `newest`, `last modified`, `authoritative`, `source of truth`) to confirm no conflicting rule remains active; run `uv run python tools/check_docs_quality.py`; add or update automated-rule tests for any tool that currently derives authority from timestamps.

## Documentation Impact
Yes — this issue's entire scope is the governance documents, review templates, and PR templates listed in Target Files or Areas.

## Out of Scope
- Do not remove review dates that are used for maintenance scheduling.
- Do not remove Git history or audit metadata.
- Do not decide canonical ownership for every existing target.

## Dependencies
Depends on `M-01-01` and `M-01-02`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-01` and `M-01-02` have landed before editing — this issue's replacement wording assumes the target-based resolution algorithm already exists as the normative alternative to cite. Search broadly (the listed keywords are a minimum, not an exhaustive list) but review each match semantically before removing it — a legitimate maintenance-scheduling use of "review date" must not be deleted. Do not remove Git history or audit metadata as part of this issue.
