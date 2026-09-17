## Goal

Assign named owners, Resolution Targets, and git-history-recovered First Found dates to every Part 1 entry surviving the other content-fixing Plans in batch CI-008 through CI-016 as one initiative, while extending the Entry Template's field-count declaration so the new Resolution Target field does not break conformance checks. Per REQ-001 through REQ-008; AC-1 through AC-7.

## Scope

- Update Entry Template field-count declaration from 16 to 17 fields (REQ-001)
- Add Resolution Target to RAG-006 and DESIGN-2 (REQ-002)
- Assign Owner, First Found, and Resolution Target to EVENTBUS-005, EVENTBUS-006, EVENTBUS-007 (REQ-003)
- Assign Owner, First Found, and Resolution Target to CI-007 (REQ-004)
- Assign First Found individually and shared TODO(owner)/Resolution Target to CI-008 through CI-016 (REQ-005)
- Add batching-decision note after CI-016 (REQ-006)
- Add quarterly review-cadence subsection near Lifecycle section (REQ-007)
- Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes (REQ-008)

## Assumptions

- The 15 Part 1 entries in scope are exactly the surviving full entries once sibling Plans (`20260916-150416`, `20260916-150753`) land: RAG-006, DESIGN-2, EVENTBUS-005, EVENTBUS-006, EVENTBUS-007, CI-007, CI-008 through CI-016
- CI-008 through CI-016 span five different RACI areas (Agent, Shared/DB, MCP, RAG, EventBus) — no single existing RACI role is accountable across all five; use TODO(owner) fallback per source issue's stated preference over wrong assignment
- git log -S"{ID}" --all against full repository history is reliable for recovering First Found dates since Known Issue IDs were preserved as-is during 2026-09-03 consolidation
- Phase 1 precondition: sibling Plans must be implemented before applying edits to avoid editing soon-to-be-doomed entries

## Design decisions

- Use TODO(owner) marker for CI-008–CI-016 instead of inventing a cross-cutting role that does not exist in the RACI Model; this follows the source issue's explicit fallback ("a wrong owner is worse than a flagged gap")
- Reuse existing quarterly cadence precedent from Part 2 Needs Confirmation items rather than inventing a new interval
- Resolution Target phrasing matches existing conventions: "Next RAG architecture review" for RAG-area entries, "Next EventBus architecture review" for EventBus-area entries, "ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below" for CI-008–CI-016

## Alternatives considered

- Assigning a single cross-cutting QA lead role to CI-008–CI-016: rejected because no such role exists in the RACI Model; @governance-lead is scoped to governance/documentation process, not cross-domain test-writing
- Using annotated lower bound dates where git history could not resolve: not needed — git history resolved every date in scope

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

Phase 1: Preparation
Phase 2: Core Documentation Edit
Phase 3: Verification

### Method

Phase 1: Confirm sibling Plans have landed before any edit. Check that EVENTBUS-001, EVENTBUS-002, CI-003, RAG-005 are already placeholders (not active entries) in the target file. If either has not landed yet, stop and wait rather than editing a soon-to-be-doomed entry.

Phase 2: Apply edits in order:
1. Update Entry Template field-count declaration from "16 fields" to "17 fields" (REQ-001)
2. Add Resolution Target field to RAG-006 and DESIGN-2 entries (REQ-002)
3. Assign Owner: @eventbus-dev, First Found dates, and Resolution Target to EVENTBUS-005, EVENTBUS-006, EVENTBUS-007 (REQ-003)
4. Assign Owner: @data-eng, First Found: 2026-08-23, and Resolution Target to CI-007 (REQ-004)
5. For CI-008 through CI-016: assign individual First Found dates, set Owner: TODO(owner) — cross-area initiative, no single RACI role fits, and Resolution Target: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below (REQ-005)
6. Add batching-decision prose note immediately after CI-016's entry (before NC-021's Part 2 header) recording why CI-008–CI-016 are treated as one initiative and the cross-area ownership finding (REQ-006)
7. Add quarterly review-cadence subsection near the existing Lifecycle section (REQ-007)

Phase 3: Verification
1. Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm it passes (REQ-008)
2. Manual re-scan: each edited entry has exactly 17 fields matching REQ-001's updated declaration

### Details

**Phase 1 — Precondition check:**
Read the target file at implementation time. Verify that EVENTBUS-001, EVENTBUS-002, CI-003, RAG-005 are already converted to removal placeholders (not active entries with Owner/First Found fields). If they are still active entries, stop and wait for sibling Plans to land.

**Phase 2 — Edits:**

REQ-001: Change line 21 from "Each active Known Issue entry must contain these 16 fields:" to "Each active Known Issue entry must contain these 17 fields:"

REQ-002: After RAG-006's existing fields (around line 145), add: `- **Resolution Target**: Next RAG architecture review`. Same for DESIGN-2 (around line 166).

REQ-003: For each of EVENTBUS-005, EVENTBUS-006, EVENTBUS-007:
- Replace `Owner: Unassigned` with `Owner: @eventbus-dev`
- Replace `First Found: Unconfirmed` with the git-history-recovered date (EVENTBUS-005: 2026-09-03, EVENTBUS-006: 2026-09-03, EVENTBUS-007: 2026-09-03)
- Add `- **Resolution Target**: Next EventBus architecture review`

REQ-004: For CI-007:
- Replace `Owner: Unassigned` with `Owner: @data-eng`
- Replace `First Found: Unconfirmed` with `First Found: 2026-09-03`
- Add `- **Resolution Target**: Next RAG architecture review`

REQ-005: For CI-008 through CI-016 (nine entries):
- Replace `Owner: Unassigned` with `Owner: TODO(owner) — cross-area initiative, no single RACI role fits (see batching note)`
- Replace `First Found: Unconfirmed` with individual git-history-recovered dates:
  - CI-008: 2026-09-03, CI-009: 2026-09-03, CI-010: 2026-09-03, CI-011: 2026-09-03, CI-012: 2026-09-03, CI-013: 2026-09-03, CI-014: 2026-09-15, CI-015: 2026-09-03, CI-016: 2026-09-15
- Add `- **Resolution Target**: ADR-invariant test suite initiative — tracked as one cross-area effort, see batching note below`

REQ-006: Insert prose note after CI-016's entry (before NC-021's Part 2 header):
```
Note on CI-008 through CI-016 batching: These nine structurally identical "ADR invariant verified by code inspection, no automated test" entries are treated as one initiative. Their Area fields span Agent (CI-008, CI-016), Shared/DB (CI-009), MCP (CI-010, CI-013, CI-015), RAG (CI-011, CI-014), and EventBus (CI-012) — no single existing RACI role is accountable for a cross-area ADR-invariant-test-suite initiative. This Plan flags the decision for human determination: create a new cross-cutting role vs. revert to per-area ownership.
```

REQ-007: Add a new subsection under Part 1 near the existing Lifecycle section:
```
### Review Cadence

Part 1 entries are reviewed quarterly, consistent with the cadence documented for Part 2 Needs Confirmation items and "Proposed" ADRs in `docs/00_governance_01_documentation-policy.md` line 521.
```

**Phase 3 — Verification:**
Run `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` and confirm zero findings. Manually verify each edited entry contains exactly 17 fields.

## Compatibility considerations

- REQ-001's field-count update (16 → 17) must precede or accompany REQ-002 through REQ-005 adding Resolution Target to entries; otherwise the conformance checker built by `plans/20260916-151710_plan.md` will flag every entry this Plan touches as non-conformant
- The quarterly review-cadence subsection references `docs/00_governance_01_documentation-policy.md` line 521 — if that document changes its cadence interval, this subsection should be updated accordingly
- Owner values (@eventbus-dev, @data-eng) follow the RACI area-role mapping confirmed in `docs/00_governance_01_documentation-policy.md`; if the RACI Model changes, these assignments may need revision

## Security considerations

N/A: documentation-only change, no secrets or credentials involved.

## Rollback considerations

If edits are applied out of phase (before sibling Plans land), entries like EVENTBUS-001, EVENTBUS-002, CI-003, RAG-005 may receive owner assignments moments before being converted to placeholders, requiring a second pass to remove them. The rollback is simply reverting those specific field additions.

For CI-008–CI-016, if the TODO(owner) approach proves unsatisfactory later, the alternative is reverting to nine per-area assignments — this requires creating a cross-cutting role first.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual field-count re-scan | Re-read each of the 15 edited entries | Each has exactly 17 fields (16 template fields + Resolution Target), matching REQ-001's updated declaration |

## Completion criteria

- [ ] No surviving Part 1 entry in scope has Owner: Unassigned, except CI-008–CI-016's explicit TODO(owner) marker (AC-1)
- [ ] Every entry in scope has a Resolution Target and Entry Template declares 17 fields (AC-2)
- [ ] CI-008 through CI-016 batching decision including cross-area ownership finding is recorded (AC-3)
- [ ] Periodic review cadence is documented (AC-4)
- [ ] No entry in scope has First Found: Unconfirmed (AC-5)
- [ ] Every date is repository-history-recovered, not guessed (AC-6)
- [ ] No entry was resolved or closed as part of this Plan (AC-7)
- [ ] `check_docs_quality.py` passes with zero findings (REQ-008)

## Out of scope

- Part 2 (NC-*) entries — owner assignment deferred to separate follow-up
- Resolving, closing, or reclassifying any entry
- Writing ADR-invariant tests for CI-008 through CI-016
- Changing any field other than Owner, Resolution Target, and First Found
- Modifying source code files or other documentation files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm sibling Plans have landed (EVENTBUS-001/002, CI-003, RAG-005 are placeholders) | Completed | 20260917-092030 | 20260917-092030 | Phase 1 precondition met |
| 2 | Update Entry Template field-count from 16 to 17 (REQ-001) | Completed | 20260917-092030 | 20260917-092030 | |
| 3 | Add Resolution Target to RAG-006 and DESIGN-2 (REQ-002) | Completed | 20260917-092030 | 20260917-092030 | |
| 4 | Assign Owner, First Found, Resolution Target to EVENTBUS-005/006/007 (REQ-003) | Completed | 20260917-092030 | 20260917-092030 | First Found dates corrected to 2026-09-03 via git history |
| 5 | Assign Owner, First Found, Resolution Target to CI-007 (REQ-004) | Completed | 20260917-092030 | 20260917-092030 | First Found date corrected to 2026-09-03 via git history |
| 6 | Assign First Found individually and shared TODO(owner)/Resolution Target to CI-008–CI-016 (REQ-005) | Completed | 20260917-092030 | 20260917-092030 | First Found dates corrected to 2026-09-03 for CI-008/009/010/011/012/013/015; 2026-09-15 for CI-014/016 via git history |
| 7 | Add batching-decision note after CI-016 (REQ-006) | Completed | 20260917-092030 | 20260917-092030 | |
| 8 | Add quarterly review-cadence subsection (REQ-007) | Completed | 20260917-092030 | 20260917-092030 | |
| 9 | Run check_docs_quality.py and confirm it passes (REQ-008) | Completed | 20260917-092030 | 20260917-092030 | Passed with zero findings |

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
- **Requirement ID**: REQ-001 through REQ-008
- **Source issue**: issues/20260915-200530_gov04_assign-owners-resolution-targets-and-discovery-dates.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-152251_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-092030
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
