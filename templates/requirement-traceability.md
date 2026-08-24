# Requirement Traceability Template (Canonical)

Use this structure for the "Requirement Traceability" subsection of a Plan document
(placed inside the Plan's `Traceability` section, immediately after the
`templates/traceability.md` fields). One row per Requirement ID. Leave fields that do
not apply as `N/A: {short reason}`.

## Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | | | | | | |

## Column Definitions

- **Requirement ID**: the stable ID assigned when the Requirement was created (e.g.
  `REQ-001`).
- **Source Issue section or evidence**: the Issue section, or repository evidence
  location, this Requirement traces back to.
- **Target file**: the repository-relative path(s) this Requirement affects.
- **Implementation step**: the Implementation step(s) in the Plan that implement this
  Requirement.
- **Acceptance criterion**: the Acceptance criterion (or criteria) that verify this
  Requirement.
- **Test or validation item**: the Test or Validation plan entry that exercises this
  Requirement.
- **Status**: the evidence classification this Requirement was based on when it was
  extracted — one of `Explicit in issue`, `Confirmed by repository evidence`, `Derived
  from confirmed evidence`, `Needs confirmation`.

## Notes

- This template is requirement-level traceability (one row per Requirement), distinct
  from the workflow-phase-level traceability in `templates/traceability.md` (one block
  per generated document). The two are complementary — use both in the same
  `Traceability` section, this one as a subsection after the other's fields. For
  workflow-phase traceability, see `templates/traceability.md`.
- Use `N/A: {short reason}` for any column that does not apply to a given Requirement
  (e.g. a Requirement with no direct test, only an acceptance criterion).
- Every Requirement ID that appears in a Plan's `Requirements` section must have exactly
  one row here — do not omit a Requirement, and do not add a row for an ID that does not
  exist in `Requirements`.
- Currently produced by `prompts/01_issue-to-plan.md` and
  `skills/issue-to-plan/SKILL.md` / `workflow.md`. Available for reuse by other workflow
  phases that need the same requirement-level traceability table (e.g. a future revision
  of `prompts/02_plan-to-implementation-procedure.md`), so they are not forced to
  redefine it independently.
