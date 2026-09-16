## Goal

Update ADR-013 implementation status and Known Deviations for the stale Problem-section wording. REQ-005.

## Scope

Verify and update ADR-013's Problem section (line 36) and Known Deviations section. Two sub-tasks:
1. Update Problem section to reflect current authentication state
2. Verify Known Deviations no longer lists CI-001 as open

## Assumptions

- ADR-013 exists at `docs/adr/ADR-013-eventbus-authentication-authorization.md`
- ADR-013 line 36 contains a stale claim ("No route authenticates or authorizes")
- EVENTBUS-008 was resolved 2026-09-14 and removed from active inventory
- CI-001 remains accurate today but will be closed by eventbus13's own REQ-006 once its migration lands
- eventbus13 has landed before this plan executes

## Design decisions

- Update Problem section to describe current bearer authentication + incomplete authorization state
- Update Known Deviations to remove CI-001 reference (eventbus13's REQ-006) and confirm EVENTBUS-008 resolution
- If ADR-013 already reflects these updates via eventbus13's REQ-006, skip further action
- Do not overwrite eventbus13's edit with divergent wording

## Alternatives considered

- Independently rewriting Problem section: rejected because eventbus13 owns the authoritative update via REQ-006
- Deferring until eventbus10 executes: not viable since eventbus10 depends on eventbus13 landing first

## Implementation

### Target file

`docs/adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

**Sub-task 1: Update Problem section**

1. Read ADR-013 line 36 (Problem section)
2. If the Problem section still states "No route authenticates or authorizes", replace with:
   ```markdown
   ### Problem
   
   Several routes in `scripts/eventbus/` authenticate and authorize callers via Bearer-token middleware and role-based authorization, but the authentication model has gaps: consumer identity validation can fail-open when no `consumer_id` allowlist is configured for a token, and audit logging of privileged actions is incomplete. Additionally, `load_config()` enforces fail-closed validation for unknown keys, missing required keys, and wrong-type keys — implemented locally, not via `ConfigLoader`.
   ```
3. If the Problem section already reflects the current state, mark this step as complete

**Sub-task 2: Update Known Deviations**

1. Read ADR-013 Known Deviations section
2. If Known Deviations still lists CI-001 as "open", replace with:
   ```markdown
   ## Known Deviations
   
   CI-001 was resolved by the `ConfigLoader` migration (`eventbus13`) — no deviation remains open here. EVENTBUS-008 ("No Production Authentication Model for Event Bus HTTP API", High severity, open) was resolved 2026-09-14 and removed from the active inventory. Neither entry's absence from the active list requires a heading here — do not create `#### CI-001` or `#### EVENTBUS-008` headings.
   ```
3. If Known Deviations already reflects these updates, mark this step as complete

### Method

Adversarial verification: treat the plan's description of current ADR-013 state as unverified. Check each claim against the actual file content.

### Details

**Step 1: Read ADR-013 Problem section (line 36)**

Pre-migration state: "No route in `scripts/eventbus/` authenticates or authorizes callers." — STALE

**Step 2: Read ADR-013 Known Deviations section**

Pre-migration state: references EVENTBUS-008 and CI-001 as both "open" — stale for EVENTBUS-008 (resolved); CI-001 is accurate today but will be closed by eventbus13's own REQ-006 once its migration lands

**Step 3: Apply updates if needed**

If ADR-013 already reflects these edits via eventbus13's REQ-006, skip further action. Do not overwrite eventbus13's edit with divergent wording.

## Compatibility considerations

- This update must occur after eventbus13 lands; executing before eventbus13 would produce false positives for Known Deviations
- ADR-013 may have been updated by eventbus13's REQ-006 — verify alignment rather than duplicating the edit
- The Problem section update should distinguish between the Problem section (which describes the pre-implementation state) and the Known Deviations section (which tracks current deviations)
- If ADR-013 still shows stale content after eventbus13 lands, the gap belongs to eventbus13's execution, not eventbus10

## Security considerations

- None applicable: documentation reconciliation only, no code changes or security boundary modifications

## Rollback considerations

- No rollback needed: this is a documentation update, not a code change
- If ADR-013 needs correction, defer to eventbus13's REQ-006 rather than applying an independent fix

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| docs/adr/ADR-013-eventbus-authentication-authorization.md | Manual review: verify Problem/Known Deviations match current code | Manual inspection | No stale claims remain |

## Completion criteria

- ADR-013 Problem section reflects current bearer authentication + incomplete authorization state
- ADR-013 Known Deviations no longer lists CI-001 as open
- ADR-013 Known Deviations confirms EVENTBUS-008 resolution
- No active document simultaneously claims the same control is absent and complete

## Out of scope

- Modifying ADR-013 directly (unless stale content requires correction, which should be deferred to eventbus13)
- Re-deciding the authentication/authorization architecture (answered by eventbus13)
- Updating ADR-002 or CI-001 in the governance doc (separate rows in this plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update ADR-013 Problem section to reflect current auth state | Completed | — | 20260916-071636 | Problem section updated to reflect current auth state |
| 2 | Verify ADR-013 Known Deviations no longer lists CI-001 as open | Completed | — | 20260916-071640 | CI-001 date corrected to 2026-09-15 |
| 3 | Confirm alignment with eventbus13's REQ-006 edit | Completed | — | 20260916-071643 | Aligns with eventbus13's REQ-006 edit format |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-102602_eventbus10_reconcile-adrs-known-issues.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-232643
- **Related target files**: docs/adr/ADR-013-eventbus-authentication-authorization.md