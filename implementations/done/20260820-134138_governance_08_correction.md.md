# Implementation Procedure: Correct Governance_08 Known-Issues Migration Plan Staleness

## Goal
Add a "Migration Status" correction note to `docs/00_governance_08_known-issues-migration-plan.md` stating the migration was executed on 2026-07-23 (commit `7b04065ce`) with per-area outcome summary, instead of presenting it as an unexecuted plan.

## Scope
- Target file: `docs/00_governance_08_known-issues-migration-plan.md`
- Add "Migration Status" note near the top
- Preserve rest of document as historical record

## Assumptions
- Migration was executed on 2026-07-23 (commit `7b04065ce`)
- Agent area entries subsequently resolved/removed (commit `646152e61`, 2026-07-26)
- Document restructured (commit `96c0d6231`, 2026-08-07) leaving zero Agent entries
- RAG/MCP/EventBus/Shared retain migrated IDs/Status fields but have partially drifted from strict template conformance
- Leave "Current Format Summary" and "Migration Policy" sections as historical record

## Design decisions
- Add "Migration Status" section after "Scope" section (around line 20)
- State execution date, commit, and per-area outcomes
- Do not delete existing content — leave as historical record
- Note that RAG/MCP/EventBus/Shared have drifted from strict template conformance (tracked as follow-up)

## Implementation
### Target file
`docs/00_governance_08_known-issues-migration-plan.md`

### Procedure
1. Read the file
2. Insert "Migration Status" section after "Scope" section (after line ~20)
3. Add per-area outcome summary

### Method
Direct Markdown editing with exact line placement

### Details
**Insert after "Scope" section (after line ~20):**

```markdown
## Migration Status

**Executed:** 2026-07-23 (commit `7b04065ce`)

**Per-area outcomes:**
- **Agent:** Entries subsequently resolved and removed (commit `646152e61`, 2026-07-26); document restructured (commit `96c0d6231`, 2026-08-07) leaving zero entries
- **RAG:** Migrated IDs/Status fields retained; document retains migrated content but has partially drifted from strict template conformance (tracked as follow-up)
- **MCP:** Migrated IDs/Status fields retained; partially drifted from strict template conformance (tracked as follow-up)
- **EventBus:** Migrated IDs/Status fields retained; partially drifted from strict template conformance (tracked as follow-up)
- **Shared/DB:** Migrated IDs/Status fields retained; partially drifted from strict template conformance (tracked as follow-up)

The remainder of this document (Current Format Summary, Migration Policy, Priority Criteria, Suggested Migration Order) reflects the pre-migration planning state and is retained as historical record.
```

**Placement:** Insert after the "Scope" section (after line ~20, before "## Target Files")

## Compatibility considerations
- Documentation-only change
- No content deleted, only added
- Historical sections preserved

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file

## Validation plan
- `git diff docs/00_governance_08_known-issues-migration-plan.md` — confirms migration status note added, no other content altered
- Manual read: note states execution date, commit, and per-area outcomes

## Out of scope
- Re-migrating RAG/MCP/EventBus/Shared to fix template drift (follow-up issue)
- Modifying the migration plan's original content beyond adding status note

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221506_require.md
- Source plan: plans/20260819-174858_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134138
- Related target files: docs/00_governance_08_known-issues-migration-plan.md