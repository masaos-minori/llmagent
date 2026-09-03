# Implement canonical-source validation and CI enforcement

## Priority
Medium

## Summary
Implement automated validation for the Canonical Source Registry and make invalid canonical-source mappings fail CI.

## Background
The governance verification matrix identifies duplicate canonical declarations, multiple Primary sources, and missing canonical references as incomplete or manual checks.

## Problem
The new target-based authority model requires deterministic validation; without it, invalid, ambiguous, missing, or stale canonical-source mappings can be merged undetected.

## Reason for Change
A registry with no enforcement is only as reliable as manual review, which is the exact failure mode the target-based model (`M-01-02`) and registry (`M-01-04`) were introduced to replace.

## Implementation Intent
Detect invalid, ambiguous, missing, and stale canonical-source mappings before documentation changes are merged.

### Required validation rules

#### Blocking errors

- Duplicate canonical source for the same decision target and claim type
- Missing registered source file
- Unknown decision target format
- Unknown claim type
- Draft normative document registered as canonical
- Proposed ADR registered as the canonical source for an adopted decision
- Duplicate ADR identifier
- Multiple canonical Specifications for the same target and claim type
- Registry schema violation
- Area guide or generated output contradicting the registry
- Legacy universal-precedence declarations reintroduced into active governance documents

#### Warnings

- Non-canonical Reference does not link to its canonical source
- Potentially stale non-canonical document conflicts with a canonical source
- Canonical source has no validation reference where one is required
- Unregistered target-like authority declaration is found
- Non-canonical document uses terms such as `authoritative` or `source of truth`

## Target Files or Areas
- `tools/check_docs_structure.py`
- `tools/check_docs_quality.py`
- Existing ADR reference and invariant validators
- Documentation test files
- CI workflow files
- Governance Verification Matrix
- Canonical Source Registry and schema

If an existing tool already owns cross-document governance validation, extend that tool instead of introducing overlapping validators.

## Required Changes
1. Reuse existing documentation validation infrastructure where appropriate.
2. Keep registry schema validation separate from semantic validation.
3. Produce deterministic output.
4. Include the following in every error:
   - Rule ID
   - Decision target
   - Claim type
   - Conflicting or invalid source path
   - Expected condition
5. Support validation of all documentation and validation of changed files in CI.
6. Add dedicated rule IDs for canonical-source checks.
7. Add unit tests for individual rules.
8. Add integration tests using a temporary registry and temporary documentation tree.
9. Add the validator to the blocking CI workflow.
10. Update the Governance Verification Matrix to reflect actual implementation status.

### Required test cases

- One valid source
- Duplicate normative sources
- Missing source
- Invalid claim type
- Invalid target identifier
- Draft Specification used as canonical
- Proposed ADR used as Accepted architecture source
- Duplicate ADR ID
- Multiple implementation files for permitted runtime behavior
- Multiple normative files where only one is permitted
- Guide content generated from registry
- Guide content conflicting with registry
- Legacy recency-based authority statement

### Example error format

    CANONICAL-001: Multiple canonical sources
    Target: agent.tool-routing
    Claim type: architecture-decision
    Sources:
      - docs/adr/ADR-003-runtime-tool-registry-routing-authority.md
      - docs/05_agent_03_runtime-tool-routing.md
    Expected: exactly one normative canonical source

## Constraints
Keep registry schema validation separate from semantic validation; reuse existing documentation validation infrastructure (`tools/check_docs_structure.py`, `tools/check_docs_quality.py`, existing ADR validators) where it already covers the need, per `rules/ai-execution.md` Repository Tool Usage, rather than introducing an overlapping validator.

## Acceptance Criteria
- [ ] Registry schema errors fail validation.
- [ ] Duplicate normative canonical sources fail validation.
- [ ] Missing source paths fail validation.
- [ ] Draft normative sources fail validation.
- [ ] Proposed ADRs cannot satisfy Accepted decision ownership.
- [ ] Duplicate ADR IDs fail validation.
- [ ] Errors include target, claim type, source, and expected condition.
- [ ] Warnings do not silently pass as successful checks without visible output.
- [ ] Unit and integration tests cover all required cases.
- [ ] CI runs the validator as a blocking check.
- [ ] Governance documentation reports the validator as implemented only after CI is active.

## Testing Expectations
Add unit tests for each individual validation rule; add integration tests using a temporary registry and temporary documentation tree covering all required test cases listed above; verify the validator runs as a blocking CI check per `rules/toolchain.md`'s standard validation sequence.

## Documentation Impact
Yes — update the Governance Verification Matrix to reflect actual implementation status only after the validator is active in CI, per Required Changes item 10.

## Out of Scope
- Do not resolve the content of existing conflicts in this issue.
- Do not automatically rewrite canonical documents.
- Do not infer that code complies with an ADR because both are registered.

## Dependencies
Depends on `M-01-04`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-04`'s registry schema has landed before implementing validation against it. Before creating a new validator, inspect `tools/check_docs_structure.py`, `tools/check_docs_quality.py`, and the existing ADR reference/invariant validators for overlapping coverage, per `rules/ai-execution.md` Repository Tool Usage — extend an existing tool rather than duplicating cross-document governance validation logic. Do not automatically rewrite canonical documents to fix a detected violation; report it instead. Do not mark the Governance Verification Matrix entry as implemented until the validator is actually wired into blocking CI.
