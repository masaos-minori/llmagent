## Goal

Fix four mechanical defects in `docs/00_governance_03_issue-and-uncertainty-management.md`'s Part 1/Part 2: relocate the misplaced SHARED-001 entry and document the ordering convention it restores, recover and record CI-002's real resolution history as a removal placeholder, correct NC-033's malformed indentation, and confirm (rather than blindly apply) the identifier-capitalization fixes the source issue names. Per REQ-001 through REQ-006; AC-1 through AC-9.

## Scope

- Move SHARED-001's heading and body (unchanged) from between EVENTBUS-007 and EVENTBUS-008 to immediately after EVENTBUS-008 (REQ-001)
- Document the ID-prefix grouping / ascending-numeric-order convention this move restores (REQ-002)
- Add CI-002 removal placeholder using real resolution history recovered via git log -S"CI-002" --all -p (REQ-003)
- Remove NC-033's leading-space indentation defect on its Blocking field (REQ-004)
- Confirm via repository-wide scan that Ci-/First Foun typos do not exist in docs/ (REQ-005)
- Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes (REQ-006)

## Assumptions

- The SHARED-001 entry currently at lines 261-263 is a prose-form resolved note (not an active entry), so moving it does not change any content
- CI-002's real resolution history was recovered via `git log -S"CI-002" --all -p -- .`, tracing the entry's removal to commit `52129c8aaf95b8e851faf7d9b422ca0e089b8b35` (2026-09-09, "docs: remove resolved Known Issue entries from governance Active Items")
- A repository-wide scan (`grep -rn "Ci-[0-9]" docs/` and case-insensitive prefix scan followed by `grep -rn "First Foun[^d]" docs/`) found zero occurrences — the source issue's Identifiers claims are stale, most plausibly already corrected by an unrelated documentation pass
- memo3.md (repository root, untracked) was not consulted as evidence for this Plan

## Design decisions

- Move SHARED-001 by the source issue's own first-offered option (after the EventBus group) rather than inventing a new taxonomy
- Recover CI-002's real history from Git rather than reporting "unavailable," since investigation found it
- Confirm, not assume, that the identifier-capitalization defects the source issue names still exist before touching any file for them

## Alternatives considered

- Placing SHARED-001 in a different position within the Active Items section: rejected because the source issue explicitly offers the post-EVENTBUS-008 placement as the preferred option
- Creating a fabricated CI-002 placeholder narrative: rejected because git history provided real resolution content

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

Phase 1: Preparation
Phase 2: Core Documentation Edit
Phase 3: Verification

### Method

Phase 1: Re-run identifier typo scans at implementation time to confirm REQ-005's "already fixed, nothing to do" finding still holds.

Phase 2: Apply edits in order:
1. Move SHARED-001's heading and body to immediately after EVENTBUS-008 (REQ-001)
2. Add the ordering-convention statement to the Active Items section (REQ-002)
3. Insert the CI-002 removal placeholder before CI-003, using recovered history (REQ-003)
4. Remove NC-033's leading-space indentation defect (REQ-004)

Phase 3: Verification
1. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes (REQ-006)
2. Re-run `grep -n "^ - \*\*\|^  - \*\*\|^   - \*\*" docs/00_governance_03_issue-and-uncertainty-management.md` and confirm no output (AC-6)

### Details

**Phase 1 — Precondition check:**
Re-run at implementation time:
```bash
grep -rn "Ci-[0-9]" docs/
grep -rn "First Foun[^d]" docs/
```
If either command finds matches, report this in the progress update and consider whether edits are needed for those files. If both return zero matches (as currently confirmed), proceed to Phase 2.

**Phase 2 — Edits:**

REQ-001: Move SHARED-001's entire block (heading + prose body, currently at lines 261-263) from its current position (between EVENTBUS-007 and EVENTBUS-008) to immediately after EVENTBUS-008's block (before CI-001). Content remains unchanged — only position changes.

Current position (lines 261-265):
```
#### SHARED-001

SHARED-001 was fully resolved this cycle...

#### EVENTBUS-008
```

New position (after EVENTBUS-008, before CI-001):
```
#### EVENTBUS-008
...EVENTBUS-008 content...

#### SHARED-001

SHARED-001 was fully resolved this cycle...

#### CI-001
```

REQ-002: Add a one- or two-sentence ordering-convention statement to the Active Items section. Recommended text:
```
Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.
```
Place this near the top of the Active Items subsection, before the first entry heading.

REQ-003: Insert a CI-002 removal placeholder immediately before CI-003's heading (currently at line 273). Use the following prose form matching the established RAG-003/RAG-004/etc. pattern:
```
CI-002 ("former-ADR-011 INV-01/INV-02 production/local recovery distinction — stale reference") was resolved and removed from this active inventory 2026-09-09. Confirmed by direct code inspection while drafting issues/done/20260909-192919_ci002_remove_placeholder.md: investigated against all three tracked ADR-011 revisions and current ADR-008 text, and the cited INV-01/INV-02 pair was found to have never existed; recover_corruption()'s lack of a production/local distinction was confirmed as correct, intended behavior, not a gap; removed 2026-09-09 with no further action required. Its absence from the active list is the correct, policy-compliant state — do not create a #### CI-002 heading.
```

REQ-004: Fix NC-033's leading-space indentation defect. On line 753, change:
```
 - **Blocking**: No
```
to:
```
- **Blocking**: No
```
(removing the single leading space before the hyphen).

**Phase 3 — Verification:**
Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm zero findings. Re-run `grep -n "^ - \*\*\|^  - \*\*\|^   - \*\*" docs/00_governance_03_issue-and-uncertainty-management.md` and confirm no output (no remaining indentation anomalies).

## Compatibility considerations

- REQ-001's move of SHARED-001 must preserve the exact content — no rewording or restructuring of the entry's body text. This is purely a positional change.
- REQ-002's ordering-convention statement should be placed early enough in the Active Items section that readers encounter it before scanning entries.
- REQ-003's CI-002 placeholder uses the established prose-form resolved-note pattern (same as RAG-003, RAG-004, etc.), ensuring consistency with how other resolved entries are documented.
- REQ-004's indentation fix is isolated to NC-033's Blocking field only — no other fields should be modified.

## Security considerations

N/A: documentation-only change, no secrets or credentials involved.

## Rollback considerations

If REQ-001's move of SHARED-001 causes confusion about where the entry belongs, the rollback is simply moving it back to its original position between EVENTBUS-007 and EVENTBUS-008.

For REQ-003's CI-002 placeholder, if the recovered history proves inaccurate, the rollback is removing the inserted placeholder entirely.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual indentation re-scan | `grep -n "^ - \*\*\|^  - \*\*\|^   - \*\*" docs/00_governance_03_issue-and-uncertainty-management.md` | No output |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual heading-sequence re-scan | `grep -n "^#### "` | EVENTBUS-008 immediately followed by SHARED-001; CI-002 placeholder present before CI-003 |

## Completion criteria

- [ ] Active Items follow a stated, consistent order (AC-1)
- [ ] The ordering rule is documented in the section (AC-2)
- [ ] No entry content changed during reordering — SHARED-001's heading and body moved as a whole unit (AC-3)
- [ ] The CI-002 gap is explained in the document, with real recovered history, not a fabricated or "unavailable" narrative (AC-4)
- [ ] No new entry is assigned the CI-002 identifier (AC-5)
- [ ] NC-033's Blocking field is at the same indentation level as its other fields (AC-6)
- [ ] No occurrence of Ci- remains where CI- is meant — confirmed already true; no edit was needed (AC-8)
- [ ] No occurrence of First Foun remains — confirmed already true; no edit was needed (AC-9)
- [ ] check_docs_quality.py passes with zero findings (REQ-006)

## Out of scope

- docs/adr/ADR-002-config-isolation.md and docs/adr/ADR-013-eventbus-authentication-authorization.md — neither file contains the typos the source issue names (confirmed zero occurrences via grep)
- docs/adr/ADR-008-sqlite-4db-separation.md's own stale CI-002 cross-reference (still describes it as an open "suspicion," not as resolved) — recorded as a Risk instead
- Resolving NC-033's underlying lang field enforcement question
- Auditing identifier gaps in series other than CI-*
- Any content or field-value change beyond what REQ-001 through REQ-004 require

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm Ci-/First Foun typos don't exist in docs/ (REQ-005) | Completed | 20260917-092030 | 20260917-092030 | Already fixed; no edit needed |
| 2 | Move SHARED-001 to after EVENTBUS-008 (REQ-001) | Completed | 20260917-092030 | 20260917-092030 | |
| 3 | Add ordering-convention statement to Active Items section (REQ-002) | Completed | 20260917-092030 | 20260917-092030 | |
| 4 | Insert CI-002 removal placeholder before CI-003 (REQ-003) | Completed | 20260917-092030 | 20260917-092030 | |
| 5 | Remove NC-033's leading-space indentation defect (REQ-004) | Completed | 20260917-092030 | 20260917-092030 | |
| 6 | Run check_docs_quality.py and confirm it passes (REQ-006) | Completed | 20260917-092030 | 20260917-092030 | Passed with zero findings |
| 7 | Re-run grep for indentation verification (AC-6) | Completed | 20260917-092030 | 20260917-092030 | No indentation anomalies found |

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
- **Requirement ID**: REQ-001 through REQ-006
- **Source issue**: issues/20260915-200559_gov05_structural-and-typographic-cleanup-of-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-152650_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-092030
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
