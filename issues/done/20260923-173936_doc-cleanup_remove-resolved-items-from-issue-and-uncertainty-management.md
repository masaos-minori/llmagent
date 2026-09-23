# Physically remove resolved items from docs/00_governance_03_issue-and-uncertainty-management.md

## Priority
Medium

## Summary
Physically delete all resolved Known Issue and Needs Confirmation entries from
`docs/00_governance_03_issue-and-uncertainty-management.md`. Also update resolved
invariant statuses in `docs/adr-index.md`. Per the Current-Specification-Only Policy,
resolved entries must be removed from the active inventory, not retained with a
closed-out status.

## Background
Per `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1 Section
"Lifecycle": "An item is removed from this active inventory once it is resolved or
no longer applies to the current system; it is not retained here with a closed-out
status." This policy also applies to Part 2 (Needs Confirmation), Part 3 (Canonical
Source Conflict), and Part 4 (Configuration Drift). However, 24 resolved items remain
as inline removal-placeholder paragraphs scattered throughout the Active Items lists,
creating noise and making it harder to identify genuinely open items. The policy says
resolved items should be removed, but their removal-placeholder text persists because
the policy also requires evidence of resolution — a tension between "remove" and
"retain for audit trail."

## Problem
The Active Items lists contain 24 resolved items mixed with open items, violating
the spirit of the Current-Specification-Only Policy. Each resolved entry has a
removal-placeholder paragraph explaining why its heading was omitted, but these
paragraphs are long, verbose, and distract from genuinely open items.

## Reason for Change
Clarity of the governance document. Operators scanning the Active Items list should
see only open/investigating/deferred items without needing to skip past resolved
entries. Physical deletion reduces cognitive load and makes the document more usable.

## Implementation Intent
Delete all resolved-item paragraphs from their scattered locations in the Active Items
lists. Do NOT create a "Resolved Items" section — the policy explicitly states resolved
items are removed, not retained. Update `adr-index.md`'s invariant verification matrix
to mark resolved invariants consistently.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/adr-index.md`

## Required Changes

### Part 1: Known Issues — Resolved Items to Delete

Delete the following resolved entries from the Active Items list:

1. RAG-003 ("Unresolved usage status of `RegisteredDocument` DTO") — resolved 2026-09-14
2. RAG-004 ("Unresolved usage status of `models_config.py` configuration dataclasses") — resolved 2026-09-14
3. RAG-005 (sqlite-vec lacks FK constraints) — resolved
4. DESIGN-1 ("External RAG and local RAG corpus difference not documented") — resolved 2026-09-14
5. EVENTBUS-001 (Collision detection via `ValueError`) — resolved
6. EVENTBUS-002 (Replay JSON response schema) — resolved
7. EVENTBUS-008 ("No Production Authentication Model for Event Bus HTTP API") — resolved 2026-09-14
8. SHARED-001 (transferred to SHARED-002/003, both resolved) — resolved
9. CI-001 ("EventBus process reads configuration directly instead of using ConfigLoader") — resolved 2026-09-15
10. CI-002 ("former-ADR-011 INV-01/INV-02 production/local recovery distinction — stale reference") — resolved 2026-09-09
11. CI-003 (ADR-002 INV-01 config isolation test coverage) — resolved
12. CI-004 ("ADR-010 INV-02 — in-process fallback potentially triggered on non-transport errors") — resolved 2026-09-14
13. CI-005 ("ADR-004 INV-03 — fail-closed for missing config not implemented") — resolved 2026-09-14
14. CI-006 ("ADR-004 Decision Details #4 — local safety-related fail-closed behavior not verified") — resolved 2026-09-14
15. CI-007 ("ADR-009 INV-09 — FTS5 rebuild rules not verified") — resolved 2026-09-20
16. REQ-001 ("Immutable discovery-time visibility field (`llm_visibility_base`) not enforced during config reload") — resolved 2026-09-20
17. REQ-002 ("Atomic registry swap invariant not verified during config reload") — resolved 2026-09-20

### Part 2: Needs Confirmation — Resolved Items to Delete

1. NC-022 ("Are `RAG → EventBus`, `MCP → EventBus`, and `Agent → EventBus` unimplemented design intent, or a documentation error?") — resolved 2026-09-14
2. NC-030 ("Should `adr` and `security` be permanent `area` enum values, or folded into an existing area?") — resolved 2026-09-14
3. NC-038 ("Which of the 6 candidate `docs/05_agent_12_*.md` chapter files is/are the correct target for Memory-layer Reference-class migration under Option B?") — resolved 2026-09-20

### Part 3: ADR Invariant Verification Matrix Updates

In `docs/adr-index.md`, update the following invariants whose verification status
changed to "Resolved":

1. INV-019 — change status to "Resolved"
2. INV-020 — change status to "Resolved"
3. INV-021 — change status to "Resolved"
4. INV-024 — change status to "Resolved"

## Constraints

- Do NOT create a "Resolved Items" section — the policy explicitly states resolved
  items are removed from the active inventory, not retained.
- Preserve the existing structure of remaining open items (headings, formatting,
  ordering convention by ID-prefix).
- Maintain the existing ID format (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*,
  REQ-*, NC-*) within the remaining Active Items list.
- Do not modify cross-references in other documents (ADR files, etc.) that cite
  resolved items — those references are valid historical citations.

## Acceptance Criteria

- [ ] All 17 resolved Known Issues are physically deleted from the Active Items list
      in Part 1.
- [ ] All 3 resolved Needs Confirmation items are physically deleted from the Active
      Items list in Part 2.
- [ ] No "Resolved Items" section is created anywhere in the document.
- [ ] Remaining open items retain their original formatting and ordering.
- [ ] `adr-index.md` invariant verification statuses are updated for INV-019,
      INV-020, INV-021, INV-024.

## Testing Expectations
Not required — this is a documentation-only task with no behavioral impact.

## Documentation Impact

This issue IS the documentation cleanup task. After completion:
- The Active Items list in Part 1 will contain only open/investigating/deferred items
- The Active Items list in Part 2 will contain only open/investigating/deferred items
- The document will comply fully with the Current-Specification-Only Policy's
  directive that "resolved entries are removed from the active inventory"

## Out of Scope

- Updating cross-references in ADR files or other documents that cite resolved items
  (those are valid historical citations)
- Modifying the Known Issue template or Status values
- Adding new issues or needs confirmation items
- Creating a "Resolved Items" section (policy prohibits retention of resolved items)

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Concise constraints for an AI coding agent implementing this issue.

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` carefully.
2. Identify all resolved-item paragraphs (they contain phrases like "was resolved",
   "resolved and removed", "Its absence from the active list").
3. Delete each resolved-item paragraph entirely — do NOT move them to any section.
4. Clean up any resulting blank lines or orphaned headings.
5. Update `docs/adr-index.md` invariant statuses for INV-019, INV-020, INV-021,
   INV-024 to "Resolved".
6. Verify no resolved-item content remains in the Active Items lists.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-173936
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md, docs/adr-index.md
