# Replace the universal source ranking with target-based canonical resolution

## Priority
Medium

## Summary
Remove the universal source precedence model and make decision-target plus claim-type resolution the only normative method for selecting a canonical source.

## Background
The existing governance documentation includes both:

- A universal ranking of source types
- A decision-target-specific canonical-source matrix

## Problem
A universal ranking incorrectly suggests that code always overrides tests, ADRs, Specifications, configuration, and documentation. This conflicts with the rule that code is canonical for current behavior but not for adopted design.

## Reason for Change
Two competing, unreconciled authority models currently coexist in the same governance document (`docs/00_governance_01_documentation-policy.md`'s "Canonical Source Precedence" and "Decision Target Canonical Source Matrix" sections). Leaving both active risks a reviewer applying the wrong one and reaching a contradictory conclusion about which artifact is authoritative.

## Implementation Intent
Establish one canonical resolution algorithm based on:

1. The disputed claim
2. The claim type
3. The decision target
4. The canonical source registered for that pair

## Target Files or Areas
- `docs/00_governance_01_documentation-policy.md`
- Any governance document that reproduces the universal ranking
- Any area guide that independently defines artifact-type precedence
- Any template or checklist that says code is always the ultimate source of truth

## Required Changes
1. Remove or explicitly invalidate the universal source ranking.
2. Define the following normative resolution sequence:
   1. Reduce the conflict to one independently verifiable claim.
   2. Identify the decision target.
   3. Classify the claim using the approved claim-type taxonomy.
   4. Resolve the canonical source for the target and claim type.
   5. Treat all other artifacts as auxiliary evidence.
   6. Record unresolved differences through the designated conflict workflow.
3. State that a canonical source for one claim type does not become canonical for other claim types in the same document.
4. Preserve the distinction between intended state and observed state.
5. Explicitly prohibit automatic documentation changes that turn implementation deviations into approved specifications.
6. Define behavior when no canonical source exists.
7. Define behavior when multiple canonical sources exist.
8. Update all cross-references that still describe the universal ranking as normative.

### Required conflict outcomes

Document these minimum outcomes:

- Adopted design differs from code: register a Known Issue.
- Canonical Specification differs from an acceptance test: register a blocking canonical conflict.
- Deployed configuration differs from approved operational configuration: register Configuration Drift.
- No canonical source exists for a required target and claim type: register a design or governance gap.
- Multiple canonical sources exist for the same target and claim type: register a blocking Canonical Source Conflict.
- The claim cannot be classified with available evidence: register Needs Confirmation.

## Constraints
N/A: none beyond the requirement that the replacement algorithm must use only the claim-type taxonomy from `M-01-01` and existing decision-target concepts — no new authority model may be introduced without updating this same resolution sequence.

## Acceptance Criteria
- [ ] The universal Code > Tests > ADRs > Specifications ranking is no longer normative.
- [ ] Canonical authority is resolved using both decision target and claim type.
- [ ] Code is canonical only for current runtime behavior.
- [ ] Accepted ADRs remain canonical for adopted architectural decisions.
- [ ] Canonical Specifications remain authoritative for normative requirements.
- [ ] Tests are treated as executable verification and cannot silently redefine requirements.
- [ ] Intended state and observed state can be represented simultaneously.
- [ ] Missing and duplicate canonical sources have explicit outcomes.
- [ ] All conflicting precedence statements are removed or aligned.
- [ ] Documentation validation tests pass.

## Testing Expectations
Not required beyond documentation validation — run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py`; manually verify no remaining cross-reference restates the removed universal ranking as normative.

## Documentation Impact
Yes — this issue's entire scope is the governance documents listed in Target Files or Areas. The replacement resolution algorithm becomes the sole normative method for canonical-source selection referenced by later M-01 issues.

## Out of Scope
- Do not build the machine-readable registry in this issue.
- Do not migrate every area guide in this issue unless required to remove a conflicting universal precedence statement.
- Do not change application code to match documentation.

## Dependencies
Depends on `M-01-01` (the claim-type taxonomy this resolution sequence classifies claims with).

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-01`'s claim-type taxonomy has landed before drafting the resolution sequence — this issue's Required Changes item 2 step 3 depends on it. Read `docs/00_governance_01_documentation-policy.md`'s "Canonical Source Precedence" (universal ranking) and "Decision Target Canonical Source Matrix" sections in full before editing either. Do not delete the Decision Target Canonical Source Matrix's actual per-target content — only its coexistence with the universal ranking is the defect. Do not change application code to match documentation as part of this issue.
