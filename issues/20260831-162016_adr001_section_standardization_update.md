# Update individual ADR files to the new 14-section standard (drop Migration / Change History)

## Priority
Medium

## Summary
`docs/00_governance_01_documentation-policy.md`'s ADR Section Header Standardization was
updated to a 14-section structure that removes `Migration` and `Change History`, and the ADR
Change Protocol now requires updating the current Accepted ADR directly instead of creating a
new ADR and marking the original Superseded. Individual ADR files under `docs/adr/` have not
yet been updated to reflect either change — that work was explicitly deferred by the
governance-policy task that introduced these rules.

## Background
The governance-policy update established: (1) ADRs use Proposed/Accepted status only — no
Rejected, Deprecated, or Superseded; (2) the ADR Change Protocol updates the current Accepted
ADR directly; (3) the ADR section standard drops `Migration` and `Change History`, keeping 14
sections (Context, Assumptions, Decision, Rationale, Alternatives Considered, Consequences,
Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval,
Related Documents, Completion Checklist). `docs/adr-index.md`'s ADR List confirms all 13
current ADRs already carry only `Proposed` or `Accepted` status (Evidence: Explicit in code —
`docs/adr-index.md` ADR List table), so no status-value migration is needed. Whether each
ADR's internal section structure matches the new 14-section standard has not been checked.

## Problem
- Each of the 13 ADR files under `docs/adr/` may still contain `Migration` and/or `Change
  History` sections following the old 16-section standard. (Evidence: Needs confirmation —
  requires reading each file.)
- Some ADRs may contain content under `Migration`/`Change History` that is a still-valid
  current requirement (e.g., a constraint on how a transition must be handled) mixed with
  historical narrative (e.g., a record of when a decision changed). Removing the section
  wholesale without checking risks losing a current requirement.
- `docs/adr-index.md`'s "Maintenance Rules" duplicate the ones already updated in
  `docs/00_governance_01_documentation-policy.md` and `docs/00_governance_04_documentation-checks.md` in the prior task — whether `adr-index.md` itself needs a corresponding
  update was flagged as a required follow-up by that task but not investigated.

## Reason for Change
Leaving individual ADRs on the old section standard means the governance policy and the
actual ADR documents disagree about required structure, which will surface as review friction
or tooling confusion the next time an ADR is edited or a new one is drafted from an existing
ADR as a template.

## Implementation Intent
For each ADR file: read its current `Migration` and `Change History` sections (if present);
for any content that states a still-applicable requirement, constraint, invariant, rationale,
or verification rule, move it into the appropriate current section (typically Alternatives
Considered, Consequences, Known Deviations, or Verification — per which kind of information it
is); then remove the `Migration` and `Change History` headers and any purely historical
narrative under them. Reorder remaining sections to match the current 14-section standard
where they are out of order. Do not alter the substance of the Decision, Rationale, or
Invariants sections beyond this reorganization.

## Target Files or Areas
- `docs/adr/ADR-001-workflow-engine-mandatory.md` through `docs/adr/ADR-013-mcp-tool-availability-model.md` (13 files — see `docs/adr-index.md` ADR List for the full set)
- `docs/adr-index.md` — only if its own Maintenance Rules or other content needs alignment with the governance-policy change (see Unresolved Questions)

## Required Changes
- Update each of the 13 ADR files' section structure to the current 14-section standard.
- Preserve any still-valid requirement currently recorded under a `Migration` or `Change
  History` section by relocating it to the appropriate current section before removing the
  historical section.
- Confirm `docs/adr-index.md`'s Maintenance Rules section does not still state the
  now-removed rules (ADR deletion requiring documented replacement, Superseded ADRs remaining
  accessible, etc.) — update if it does.

## Constraints
- Do not change any ADR's Decision, Rationale, Invariants, or Verification content's
  substance — only its section placement and the removal of historical-only sections.
- Do not change any ADR's Status value — all 13 are already Proposed or Accepted.
- Do not consolidate, merge, or delete any ADR file in this task — that is a separate,
  larger decision outside this issue's scope.
- Preserve the three duplicate notes required across all ADRs (per
  `docs/00_governance_01_documentation-policy.md`'s ADR Section Header Standardization) exactly
  as currently worded.

## Acceptance Criteria
- None of the 13 ADR files contain a `Migration` or `Change History` section header.
- Each ADR's remaining sections appear in the standard 14-section order.
- Any requirement, constraint, invariant, rationale, or verification rule previously recorded
  under a removed `Migration`/`Change History` section is either already present elsewhere in
  the ADR, or has been added to the appropriate current section — with the outcome recorded
  per ADR (nothing lost / relocated / not applicable).
- `docs/adr-index.md` accurately reflects the current governance policy (Maintenance Rules do
  not restate removed history-preservation requirements).

## Testing Expectations
Documentation-only change; not required. Run the repository's documentation validation
commands (`uv run python tools/check_docs_quality.py docs/adr/*.md`, `uv run python
tools/check_docs_structure.py docs/adr/*.md`) after editing and resolve any errors found in
the edited files only.

## Documentation Impact
This issue is itself the documentation update. No other document beyond the 13 ADR files and
possibly `docs/adr-index.md` is expected to need a change.

## Out of Scope
- Changing any ADR's Decision, Rationale, Invariants, or Verification substance beyond
  relocating still-valid content out of a removed historical section.
- Deleting, merging, or superseding any ADR.
- Changing ADR Status values (none currently need it).
- Modifying the four governance-policy documents themselves (already updated by the prior
  task).

## Dependencies
Follows the governance-policy change that introduced the current 14-section ADR standard and
the direct-update ADR Change Protocol (no issue file was generated for that task; see the
corresponding session's final report for context).

## Unresolved Questions
- Whether `docs/adr-index.md`'s Maintenance Rules section (which duplicates content already
  updated in the four governance-policy documents) needs the same edit, or whether it is
  intentionally out of scope per that task's explicit "do not modify `docs/adr-index.md`,
  except to report a required follow-up" instruction — this issue is that reported follow-up,
  so the update should happen here unless a maintainer decides otherwise.
- Whether any of the 13 ADRs currently contain `Migration`/`Change History` content that
  qualifies as a still-valid requirement (needs confirmation per-file during implementation).

## AI Implementation Instruction
- Read each ADR file in full before editing it — do not assume its structure from the ADR
  index alone.
- For each `Migration`/`Change History` section found, explicitly decide per-statement
  whether it is historical narrative (delete) or a still-valid requirement (relocate) before
  removing the section — do not delete wholesale without this check.
- Do not change Decision/Rationale/Invariants/Verification substance while reorganizing.
- Process one ADR file at a time; do not batch-edit all 13 without reviewing each individually.
- Stop and report if an ADR's content makes the historical-vs-current distinction genuinely
  ambiguous, rather than guessing.
