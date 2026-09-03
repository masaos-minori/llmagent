# Define the canonical claim-type taxonomy

## Priority
Medium

## Summary
Define a single taxonomy for classifying claims before resolving their canonical source. Canonical authority must be determined by the claim type and decision target, not by a universal ranking of artifact types.

## Background
The current documentation uses multiple competing authority models:

- A universal ordering such as Code > Tests > ADRs > Specifications > Configuration > Documentation
- A decision-target matrix that assigns different canonical sources to different subjects
- Area-level Primary and Secondary document declarations

## Problem
These models cannot consistently resolve cases such as code contradicting an Accepted ADR. Code describes current runtime behavior, while the ADR describes the adopted architectural decision. Both statements may be valid for different claim types.

## Reason for Change
Without a normative claim-type taxonomy, canonical-source conflicts cannot be resolved consistently, and each area or reviewer may apply a different, undocumented authority model — risking silent misclassification of design decisions as implementation bugs, or vice versa.

## Implementation Intent
Create a normative claim-type taxonomy that separates intended design, normative requirements, observed implementation, executable verification, deployed values, operational procedures, and unresolved claims.

### Required claim types

At minimum, define the following claim types:

- `architecture-decision`
- `functional-requirement`
- `external-behavior`
- `api-contract`
- `runtime-behavior`
- `verification-contract`
- `production-effective-value`
- `configuration-schema`
- `database-schema`
- `operational-procedure`
- `security-policy`
- `documentation-metadata`
- `unconfirmed-claim`

Additional claim types may be introduced only when they have a distinct canonical source and conflict-resolution rule.

## Target Files or Areas
- `docs/00_governance_01_documentation-policy.md`
- `docs/00_governance_04_documentation-checks.md`
- All area document guides
- `docs/adr-index.md`
- Existing templates for ADRs, Specifications, References, Operations, Known Issues, and Needs Confirmation

If the actual paths differ, locate the corresponding source documents before editing. Do not rely on the concatenated documentation file as the editable source.

## Required Changes
1. Add a normative definition for each claim type.
2. Define the boundary between each pair of potentially overlapping claim types.
3. Define the default canonical source kind for each claim type.
4. Define permitted auxiliary evidence for each claim type.
5. Define the destination used when a canonical source and auxiliary evidence conflict.
6. Explicitly distinguish authority from evidence.
7. Explicitly state that a single document may contain claims of multiple types.
8. Require conflict analysis at claim level rather than whole-document level.

### Required resolution matrix

The normative documentation must include a matrix with these columns:

- Claim type
- Definition
- Canonical source kind
- Auxiliary evidence
- Conflict destination
- Notes or constraints

The matrix must establish at least these rules:

- Accepted ADRs are canonical for adopted architectural decisions.
- Canonical Specifications are authoritative for normative functional requirements.
- Official API schemas or contracts are authoritative for external interfaces.
- Source code is canonical for current runtime behavior only.
- Tests are authoritative as executable verification, not as automatic replacements for normative requirements.
- Deployed configuration is canonical for effective production values.
- Configuration schemas are canonical for valid configuration structure and value constraints.
- Official DDL or schema generators are canonical for database schema.
- Operations documents or runbooks are canonical for operator procedures.
- Needs Confirmation inventory is canonical for active unconfirmed claims.

## Constraints
Additional claim types beyond the required list may be introduced only when they have a distinct canonical source and conflict-resolution rule — do not add a claim type solely for naming convenience.

## Acceptance Criteria
- [ ] Every required claim type has a normative definition.
- [ ] Each claim type has exactly one default canonical source kind.
- [ ] Authority and evidence are explicitly separated.
- [ ] `runtime-behavior` does not grant code authority over adopted design.
- [ ] `verification-contract` does not allow tests to silently redefine requirements.
- [ ] Overlap between `architecture-decision`, `functional-requirement`, `runtime-behavior`, and `verification-contract` is explicitly resolved.
- [ ] Conflict destinations are defined for all claim types.
- [ ] Claim-level analysis is required instead of whole-document winner selection.
- [ ] Existing canonical-source terminology is updated to use the new taxonomy consistently.
- [ ] Documentation validation tests pass.

## Testing Expectations
Not required beyond documentation validation — run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` against the edited documents; manually review the resolution matrix for internal consistency (no claim type left without a canonical source kind or conflict destination).

## Documentation Impact
Yes — this issue's entire scope is the governance documents listed in Target Files or Areas. The new taxonomy becomes the normative vocabulary that `M-01-02` through `M-01-07` build on.

## Out of Scope
- Do not select the canonical file for every existing subsystem in this issue.
- Do not implement the Canonical Source Registry in this issue.
- Do not modify runtime application behavior.
- Do not resolve existing code-versus-design discrepancies.

## Dependencies
N/A: none. This issue defines the model required by the remaining M-01 issues.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read `docs/00_governance_01_documentation-policy.md`'s current "Canonical Source Precedence" and "Decision Target Canonical Source Matrix" sections in full before drafting the taxonomy — this issue does not itself resolve the conflict between those two sections (that is `M-01-02`'s scope); it only defines the claim-type vocabulary the replacement rule will use. Do not invent a claim type not listed above unless it has a distinct canonical source and conflict-resolution rule. Do not modify runtime application behavior. Locate and verify each file path in Target Files or Areas against current source before editing — do not assume the concatenated documentation file's paths are accurate.
