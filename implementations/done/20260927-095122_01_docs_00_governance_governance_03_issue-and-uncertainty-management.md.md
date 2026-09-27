## Goal

Add a brief explanatory note in the Needs Confirmation Inventory of `docs/00_governance/governance_03_issue-and-uncertainty-management.md` documenting why NC-036's `Priority: High` is intentionally different from NC-027/028/029/033/034/035's `Priority: Low` — confirmed via Plan verification to be a legitimate severity difference, not an inconsistency (REQ-002).

## Scope

In scope: adding one explanatory note to NC-036's entry (or to a shared preamble covering the whole Priority-difference question). Out of scope: changing any Priority value (REQ-003's "if inconsistent, reconcile" branch does not apply, per the confirmed finding); changing the Needs Confirmation Inventory's structure (REQ-004).

## Assumptions

- The Plan's own confirmed evaluation outcome (recorded in its Background section) is authoritative: the Priority difference is intentional (NC-036 documents an active, currently-in-effect code/ADR contradiction with a named owner and required architect judgment, materially more severe than NC-027/028/029/033/034/035's "unknown historical rationale for a tuning constant" questions) — REQ-002 (document the reason) applies, not REQ-003 (reconcile values).

## Design decisions

- Add the explanation as a short note attached to NC-036's own entry (e.g. appended to its `Required Action` field or as a new brief line within the entry), rather than a separate standalone preamble — keeps the explanation co-located with the item it concerns, matching this document's existing per-entry structure.

## Alternatives considered

- Adding a general note near the top of the Needs Confirmation Inventory explaining Priority semantics for the whole section: rejected as broader than necessary — the difference in question is specific to NC-036 vs. its neighbors; a note attached to NC-036 itself is more directly discoverable by a reader comparing the two.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Re-confirm NC-036's exact current entry content and line number via `grep -n "^#### NC-036" docs/00_governance/governance_03_issue-and-uncertainty-management.md` (adversarial re-verification — confirm the entry's fields, especially `Priority` and `Required Action`, have not changed since this Plan's investigation).
2. Add a brief note to NC-036's entry clarifying why its `Priority: High` differs from the surrounding `Low`-priority entries, e.g. appended to the `Required Action` field or as an additional short field/line: "(Priority intentionally differs from neighboring NC entries: this item documents an active code/ADR contradiction with a named owner requiring architect judgment, not an unknown-rationale documentation question.)"

### Method

Single-entry text addition (one clause or short line) — no change to any Priority value, no change to NC-027/028/029/033/034/035's entries, no structural change to the inventory.

### Details

- Confirmed current state (as of this Plan's investigation): NC-027, NC-028, NC-029, NC-033, NC-034, NC-035 all show `Priority: Low` with `Required Action` fields asking for historical/empirical rationale confirmation on tuning constants (no present behavioral contradiction). NC-036 shows `Priority: High`, `Assigned To: @data-eng`, and a `Required Action` requiring "Owner/architect judgment... (1) If intentional, amend ADR-010... (2) If unintended, fix `call_rag_service()`."
- The added note should not alter any existing field's substantive content (Question, Evidence, Impact, Required Action's own instructions, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking) — it is purely additive.

## Compatibility considerations

- Documentation-only, additive change; no existing field value is altered, so no downstream consumer of this inventory (if any) is affected beyond gaining an explanatory note.

## Security considerations

N/A: documentation clarity change, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added note.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Manual verification | Read NC-036's entry | The explanatory note is present and does not alter any existing field's substantive content; NC-027/028/029/033/034/035 remain unchanged |

## Completion criteria

- NC-036's entry includes a note explaining why its Priority is intentionally `High` relative to its neighbors.
- No Priority value (NC-036's or any other NC entry's) is changed.
- The Needs Confirmation Inventory's overall structure is unchanged.

## Out of scope

- Any other NC entry in this document.
- Any other section of this document (e.g. Part 1 Known Issues, Part 3, Part 4 — not touched by this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-104658 | 20260927-104658 | Re-confirmed NC-036 entry unchanged before editing; note appended to Required Action field only |
| 2 | Add or update tests per Validation plan | Completed | 20260927-104658 | 20260927-104658 | N/A: documentation-only, manual verification per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-104658 | 20260927-104658 | `check_docs_content_policy.py`: pass. `check_docs_quality.py`: 3 pre-existing Lifecycle-similarity warnings at lines 699/733, unrelated to this edit (confirmed via `git show HEAD`, present before this change). `check_docs_structure.py`: pre-existing file-size-limit finding (45598 bytes pre-edit vs 24576 limit), unrelated to this edit — out of scope per `rules/ai-execution.md` Step-Level Failure Triage. `check_needs_confirmation_inventory.py`: N/A — tool expects filename `00_governance_03_...md`, actual file has no `00_` prefix; also inapplicable since no NC marker was added/resolved/removed, only an existing entry's field text extended |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-104658 | 20260927-104658 | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-002: document the reason for NC-036's intentionally-different Priority
- **Source issue**: issues/20260926-183302_nc_priority_inconsistency.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-200359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-095122
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
