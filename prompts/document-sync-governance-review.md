# Document Sync — Governance Review (Conditional Sub-step)

Called from `prompts/08_document-sync.md` Step 3b, only when a target document
contains unresolved claims, implementation/documentation discrepancies, governance
rules, architecture, operational policy, invariants, or canonical-source
declarations. Skip this file entirely when none of those apply to the current
target document.

## Objective

Verify that the target documents remain compliant with the Current-Specification-Only
Policy. The objective is not to reduce the number of Needs Confirmation items, but to
prevent unresolved uncertainty from silently becoming part of the effective
specification.

## Inventory consistency

Read the centralized Needs Confirmation inventory and the relevant target documents. Verify that:

- Every active inventory entry represents a genuine unresolved matter.
- Every inline Needs Confirmation marker is represented by an inventory entry.
- Resolved or no-longer-applicable items are handled according to the documented lifecycle.
- Entry headings, required fields, status values, ownership values, priorities, and resolution targets conform to the governance specification.
- Resolution notes do not contradict the active-item lifecycle.

Do not treat an explicitly permitted value such as `Unassigned` as invalid. Report it as an actionability risk when no responsible decision path exists. Do not assign an owner automatically.

## Untracked uncertainty detection

Do not search only for the literal phrase `Needs Confirmation`. Use search candidates such as `unconfirmed`, `unclear whether`, `unknown behavior`, `design decision pending`, `owner review required`, `requires investigation`, `requires validation`, `rationale not confirmed`, `TBD`, `target design`, and `intended behavior`.

These expressions are candidates, not proof. Inspect context and exclude policy definitions, templates, examples, headings, and claims already supported by evidence. For each genuine unresolved claim, determine whether it is tracked and whether inventory registration is required.

## Design-intent and canonical-source validation

Verify that active design intent is supported by an Accepted ADR, active Specification, Governance Policy, or current Operational Policy. Do not infer missing rationale from incidental implementation details.

When a canonical source contains unresolved behavior, verify corresponding ADR, Needs Confirmation, and Known Issue coverage. Report untracked uncertainty as a governance defect. Use `Needs Confirmation` when the intent cannot be verified.

## Current-Specification-Only compliance

Verify that active documents contain only current behavior, active architecture, active constraints, active policies, and active operational requirements. Identify historical migration decisions, superseded architecture, deprecated features, compatibility-only explanations, resolved investigations, resolved Needs Confirmation items, and historical implementation behavior.

Before removal, preserve every still-current requirement, constraint, invariant, rationale, and verification rule in the appropriate active canonical document. Recommend one preferred disposition:

- Resolve by implementation
- Resolve by ADR decision
- Resolve by specification update
- Convert to Known Issue
- Retain as Needs Confirmation
- Remove obsolete content

Moving content to historical documentation is permitted only when the repository already defines an approved historical-document location and policy. Do not create a new archive unless explicitly in scope.

## Governance-tool consistency

When relevant, compare governance documents with validation tooling. Inspect configured inventory paths, entry-heading patterns, required fields, accepted status vocabulary, ownership rules, extraction patterns, and test coverage. Do not assume a documented tool is current or effective merely because it exists or exits successfully.

If policy and tooling disagree:

- Report the mismatch and its practical impact.
- Do not silently choose an interpretation.
- Apply the repository's canonical-source rules.
- Do not modify governance documents or tooling unless explicitly included in scope.

## Finding classification

Classify each finding as one of:

- Missing Inventory Entry
- Untracked Uncertainty
- Missing ADR
- Unassigned Owner
- Missing Owner
- Invalid Status
- Stale Resolved Entry
- Governance Rule Violation
- Documentation-Tool Mismatch
- Canonical Source Ambiguity
- Current-Specification-Only Violation
- Requires Architectural Decision

## Reporting and prioritization

Add a `Current-Specification-Only Review` subsection to `docs/99_documentation_sync_report.md`. For each finding include Type, Source File, Section, Evidence, Description, Impact, Recommended Action, and Priority (High / Medium / Low). Keep temporary governance analysis out of target design documents unless it represents lasting current-specification content.

Escalate to High when:

- An unresolved canonical-source statement affects implementation or operation.
- A documentation/tool mismatch can make a required governance check ineffective or misleading.
- A resolved item remains active contrary to lifecycle policy.
- The uncertainty affects security, authorization, approval, audit, persistence, data integrity, or system invariants.
- Implementation would require guessing because intent cannot be established from code, tests, ADRs, or active specifications.

Do not remove a Needs Confirmation item merely to reduce the count. Remove it only after a formal decision, when it no longer applies, after conversion to the appropriate ADR/Known Issue/Specification, or after removal of the underlying feature. Record required out-of-scope changes as follow-up work.

## Back to the caller

Once this review completes (or is skipped per the applicability condition above),
return to `prompts/08_document-sync.md` Step 4. Its Governance Summary (Step 7) is
populated only when this review was applied.
