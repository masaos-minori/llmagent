# Resolve the contradictory follow-up state of the removed-name check in governance_04

## Priority
Medium

## Summary
`governance_04_documentation-checks.md` marks one detection case of the removed-name check as "Not yet implemented (follow-up)" while its own `Follow-up Work Needed` section states that no follow-up work is tracked. Classify the unimplemented case exactly once (Accepted Limit or tracked follow-up) and align the `GV-017` row of the Governance Verification Matrix with that classification.

## Background
- The removed-name check (`check_compat_shims.py --check-removed-names`, rule `GV-017`) has two detection cases. The first (a name fully absent from source) is described as implemented. The second (a name that remains in source but is no longer the current production path) is described as "Not yet implemented (follow-up)". Evidence: `Explicit in code` (document text, section describing the removed-name check in `governance_04_documentation-checks.md`).
- `Follow-up Work Needed` in the same document states "No follow-up work is currently tracked" and says every matrix rule is enforced by design or by existing automation. `Accepted Limits` lists only the `compressverify` and `identmatch` gaps. Evidence: `Explicit in code` (document text).
- The `GV-017` matrix row says "Opt-in by design (--check-removed-names); not promoted to default-on". It does not mention the unimplemented second case. Evidence: `Explicit in code` (document text).
- Recent archived issue `issues/done/20261008-094503_adridx01_correct-adr-index-verification-status-and-pipeline-mapping.md` touched the ADR index, not this section. No open issue or in-flight plan overlaps this section (checked `issues/` and `plans/`).

## Problem
The document states two incompatible things about the same gap: the second detection case is unimplemented and labeled follow-up, but the follow-up register says there is none. A reader cannot tell whether the gap is accepted, tracked, or forgotten, and cannot tell the effective coverage of `GV-017`.

Confirmed limit of this finding: `GV-014` ("no unimplemented auto-checks documented as implemented") is not literally violated, because the document does say the case is unimplemented. The defect is the inconsistent classification, not a false implementation claim.

## Reason for Change
Governance documents define how every other document is verified. An ambiguous coverage statement here can make reviewers assume that a stale name presented as current is detected automatically. Nothing makes the change time-sensitive beyond that risk.

## Implementation Intent
Keep one classification per gap. The recommended classification is `Accepted Limit`: the unimplemented case needs a current-specification section analysis that a name search cannot provide, and it is already covered by manual review. State the owner, the rationale, and the re-evaluation condition in the same form as the existing Accepted Limits. Replace the "Not yet implemented (follow-up)" wording so it no longer implies tracked follow-up work. Preserve the behavior description of the first case and the opt-in design of the check.

## Target Files or Areas
- `docs/00_governance/governance_04_documentation-checks.md` (removed-name check description, `Governance Verification Matrix` row `GV-017`, `Follow-up Work Needed`, `Accepted Limits`)

## Required Changes
- Rewrite the "Not yet implemented (follow-up)" sentence of the second detection case to state that the case is a documented limit of the automated check, detected only by manual review.
- Add the case to `Accepted Limits` with: current behavior stated factually, Owner `Repository owner (reviewed quarterly)`, rationale, and the condition that would justify implementing it.
- Update the `GV-017` row (Status and Follow-up columns) so it states the same classification.
- Keep `Follow-up Work Needed` consistent with the final classification (no change is needed if the case is an Accepted Limit).

## Constraints
- `docs/` content MUST be English and MUST follow `skills/DESIGN.md` "Docs content policy — remove" (no implementation-location mappings, no literal ports, no source line numbers).
- Do not change the behavior or options of `tools/check_compat_shims.py`.
- Do not change the Owner values defined in `governance_03_issue-and-uncertainty-management.md` Owner Values.

## Acceptance Criteria
- The second detection case is classified exactly once, and the classification is the same in the check description, the `GV-017` matrix row, `Follow-up Work Needed`, and `Accepted Limits`.
- No sentence in the document says "follow-up" for this case while `Follow-up Work Needed` says none is tracked.
- The new Accepted Limit names an Owner defined in `governance_03` Owner Values, a rationale, and a re-evaluation condition.
- The documentation checkers listed under Testing Expectations pass.

## Testing Expectations
Documentation-only change. Run:
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`

## Documentation Impact
`governance_04_documentation-checks.md` must be updated: the kind of information affected is the verification boundary (what the removed-name check detects and what remains manual) and the Accepted Limits register.

## Out of Scope
- Implementing the unimplemented detection case in `check_compat_shims.py`.
- Changing the `GV-014` rule text or other matrix rows.
- ADR changes, including any reference to removed command names (tracked separately).

## Dependencies
N/A: none. No open issue or in-flight plan under `issues/` or `plans/` touches this document section.

## Unresolved Questions
- Accepted Limit versus tracked follow-up: the recommendation is Accepted Limit (`Needs confirmation` by the repository owner). If the owner prefers a tracked follow-up, register it in `Follow-up Work Needed` instead and keep the other locations aligned.
- Whether the re-evaluation condition should be time-based (quarterly review) or event-based is `不明`.

## AI Implementation Instruction
Change only the sentences and table rows named under Required Changes. Do not rewrite unrelated governance text. Write all `docs/` content in English. Stop and report if the Accepted Limits section format has changed since this issue was filed.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-101728
- **Related target files**: `docs/00_governance/governance_04_documentation-checks.md`
