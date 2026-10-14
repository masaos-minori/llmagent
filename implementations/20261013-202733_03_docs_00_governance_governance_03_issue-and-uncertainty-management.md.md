## Goal

Update the EVENTBUS-008 governance ledger entry in
`docs/00_governance/governance_03_issue-and-uncertainty-management.md` to record the
deny-all resolution, and re-check the `ADR-013` / `ADR-006` Known Deviations references that
track EVENTBUS-008.

## Scope

Single file: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. Two
edits:

- Remove the EVENTBUS-008 entry (Active Items table row line 100 and `#### EVENTBUS-008`
  section lines 183-199) to record the resolution, per the owner's confirmed decision (see
  Alternatives considered). The item's canonical scope (Title + Resolution Target) is the
  empty-mapping case, now fully resolved to deny-all.
- Re-check the `ADR-013` (`adr_02_013_eventbus-authentication-authorization.md`) and
  `ADR-006` (`adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md`) Known Deviations
  references to EVENTBUS-008 (ADR-013 lines 42/238/252; ADR-006 lines 378/391/466), and
  schedule the mandatory follow-up that updates them (see Method).

## Assumptions

- `UNK-01` resolved to deny-all at runtime (see the auth.py document); the governance entry
  records that resolution.
- The implementation (deny-all + test) will exist before this doc edit is finalized — the
  governance doc requires implementation evidence before reclassifying a Known Issue
  (Resolution Rules, line 308).
- This phase produces the procedure only; the actual doc edit happens in the code-implementation
  phase.

## Design decisions

- Record the resolution per the doc's OWN Resolution Rules rather than inventing a status:
  the doc has no `resolved` status value (Status Values: open/investigating/deferred, lines
  53-57); a resolved item is removed from the Active Items inventory (lines 59-60), and a
  Known Issue is resolved only when implementation and design agree (line 303).
- The item's canonical scope (Title + Resolution Target) is the empty-mapping case, now fully
  resolved (deny-all). The `auth_token`/`admin_token` "never restricted" sub-case is
  intentional design (`REQ-004`), tracked by no other Known Issue, so removing the entry loses
  no issue tracking.

## Alternatives considered

- **Mark `Status: resolved` and keep the entry**: rejected — no such status value exists in
  the doc (Status Values: open/investigating/deferred only, lines 53-57); this would violate
  the doc's convention.
- **Corrected wording, keep entry open**: rejected — the doc records resolution by removal,
  not by a closed-out status (lines 59-60); keeping a now-resolved title open would leave a
  stale entry.
- **Remove the entry**: chosen. The item's Title and Resolution Target define its scope as the
  empty-mapping case, which is fully resolved; the superuser sub-case is intentional design
  tracked by no other item, so removal loses no issue tracking.

Chosen approach (owner-confirmed): remove the EVENTBUS-008 entry from the Active Items
inventory per lines 59-60. Evidence (a passing deny-all test) must exist before removal
(line 308) — this happens in the code-implementation phase, not now.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. **Correct the `#### EVENTBUS-008` section** (lines 183-199):
   - Update **Summary** and **Observed Implementation** to state that an empty
     `consumer_authorization` AND empty `topic_authorization` pair now resolves to
     `frozenset()` (deny-all) via `_populate_token_maps()`, instead of `None` (unrestricted).
   - Update **Recommended Action** from the prior "deny all ... or reject at startup" options
     to the adopted resolution: deny-all at runtime for empty mappings.
   - Leave Title/Severity/Area/Source/Owner/First Found/Target/Related unchanged unless the
     owner directs otherwise.
2. **Remove the EVENTBUS-008 entry (owner-confirmed decision)**:
   - Delete the Active Items table row at line 100 and the `#### EVENTBUS-008` section at
     lines 183-199. Do NOT set a non-existent `resolved` status (Status Values:
     open/investigating/deferred only, lines 53-57); the doc records resolution by removal
     (lines 59-60).
   - The item's canonical scope (Title + Resolution Target) is the empty-mapping case, now
     fully resolved; the superuser sub-case is intentional design tracked by no other item, so
     removal loses no issue tracking.
   - Apply only after the deny-all implementation test evidence exists (line 308).
3. **Re-check `ADR-013` and `ADR-006`** (read-only):
   - Confirm the current references in
     `adr_02_013_eventbus-authentication-authorization.md` (lines 42, 238, 252) and
     `adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md` (lines 378, 391, 466).
   - These describe EVENTBUS-008 as an open deviation where an empty mapping leaves the
     CONSUMER token unrestricted. Removing the governance entry makes these references dangling
     and leaves the false "empty mapping = unrestricted" claim in the ADRs.

### Method

- Edit only the EVENTBUS-008 section and its table row; preserve the doc's 17-field entry
  structure (Entry Template, line 51) for any entry that stays.
- Path A: do NOT modify `ADR-013`/`ADR-006` in this change (out of the frozen 3-file scope).
- MANDATORY FOLLOW-UP (separate change, not this one): update
  `adr_02_013_eventbus-authentication-authorization.md` (line 252) and
  `adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md` (line 391) Known Deviations
  to remove the empty-mapping mention while retaining the `auth_token`/`admin_token`
  superuser deviation (the empty-mapping part is resolved; the superuser part is a valid
  residual deviation). This closes the dangling reference created by the governance removal
  and removes the now-false "empty mapping = unrestricted" claim. Track it as its own change
  (adding these files to `Implementation Target Files` requires re-freezing the plan); do not
  fold it into the 3-file EVENTBUS-008 change.

## Compatibility considerations

- Editing this entry affects cross-document consistency: `ADR-013`/`ADR-006` still reference
  EVENTBUS-008, and the Active Items table (line 94) must stay in sync with the section body.
- Removing the entry (if chosen) must not leave the ADR Known Deviations or any other doc
  pointing at a now-absent entry without correction — hence the ADR re-check above.
- Keep the Active Items ordering convention (ID-prefix groups, ascending numeric) intact for
  remaining entries.

## Security considerations

N/A: this is a governance ledger documentation edit; it changes no security control. It does
record a security resolution, so keep the recorded wording accurate (deny-all, not
unrestricted) to avoid misleading future reviewers about the fail-closed guarantee.

## Rollback considerations

N/A: ledger edits are additive annotations or a single-row/section removal; a simple revert
of this file restores the prior entry. No code or config impact.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_...md` | Structural: H1/front matter/tables/link reachability intact | `uv run python tools/check_docs_structure.py docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Pass |
| `docs/00_governance/governance_03_...md` | Formatting rules | `uv run python tools/check_docs_quality.py` | Pass |
| `docs/00_governance/governance_03_...md` | No Japanese in doc body | `uv run python tools/check_docs_japanese.py` | Pass |
| `docs/00_governance/governance_03_...md` | No stale "empty mapping = unrestricted" claim remains | manual grep | grep finds no unresolved empty-mapping-unrestricted statement for EVENTBUS-008 |

## Completion criteria

- The EVENTBUS-008 entry is removed from the Active Items inventory (table row line 100 and
  `#### EVENTBUS-008` section lines 183-199) after the deny-all test evidence exists (line 308).
- `ADR-013`/`ADR-006` re-check recorded; the mandatory follow-up to update their Known
  Deviations references is tracked as a separate change (see Method).
- All doc validators pass.

## Out of scope

- Modifying `ADR-013` (`docs/10_adr/adr_02_013_...md`) or `ADR-006`
  (`docs/10_adr/adr_02_006_...md`) — re-checked read-only. OUT OF THE FROZEN 3-FILE SCOPE;
  the update is a MANDATORY FOLLOW-UP as a separate change (see Method), not folded in here.
- Other Known Issue entries in this document.
- Any change to `scripts/eventbus/auth.py`, `tests/`, or `config/` — handled in the other
  documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261013-161114_eballow01_require-non-empty-consumer-authorization-for-eventbus-consumer-token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-185233_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-202733
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
