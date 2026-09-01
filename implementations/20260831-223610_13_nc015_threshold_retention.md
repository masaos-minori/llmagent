## Goal

Verify that the fact recorded in archived NC-015 about Threshold/retention functions is already present in `05_agent_12_02_memory-gate-data-model-search.md`, and add it if missing.

## Scope

Check `05_agent_12_02_memory-gate-data-model-search.md` for the presence of the fact that `DEDUP_THRESHOLDS` consumed by `_get_dedup_threshold()` and `RETENTION_DAYS` dead code. Add a concise statement if not already present.

## Assumptions

- The archived NC-015 entry recorded verified facts about current code behavior
- The fact may or may not already be documented in the cited source file
- If the fact is already documented, no action is needed

## Design decisions

- Only add what is genuinely missing; do not restore the removed NC record's framing
- Follow `skills/DESIGN.md` Avoid implementation-reference duplication when writing any addition
- Use concise current-fact statements without "NC-XXX confirmed..." framing or investigation narrative

## Alternatives considered

- Keeping the fact only in the archived NC record — rejected because the NC record was removed and the fact may not be discoverable elsewhere
- Restoring the full NC record — rejected because the Current-Specification-Only Policy prohibits retaining historical content

## Implementation

### Target file

`05_agent_12_02_memory-gate-data-model-search.md`

### Procedure

1. Read `05_agent_12_02_memory-gate-data-model-search.md` to identify existing threshold/retention documentation
2. Check whether the following facts are already present:
   - `DEDUP_THRESHOLDS` consumed by `_get_dedup_threshold()`
   - `RETENTION_DAYS` dead code
3. If either fact is missing, add a concise statement of the current fact

### Method

Direct verification — read the file, search for the relevant sections, and add missing facts.

### Details

```markdown
# Facts to verify/add:
# NC-015: Threshold/retention functions
# - DEDUP_THRESHOLDS consumed by _get_dedup_threshold(); RETENTION_DAYS dead code

# If missing, add concise statement like:
# "DEDUP_THRESHOLDS consumed by _get_dedup_threshold(); RETENTION_DAYS is dead code."
```

## Compatibility considerations

- REQ-002: Each archived NC entry must be checked against its cited source file
- Adding facts must not duplicate existing documentation

## Security considerations

N/A: This is a documentation verification task. No security-sensitive code changes involved.

## Rollback considerations

- If facts are added incorrectly, revert git changes to restore original content

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `05_agent_12_02_memory-gate-data-model-search.md` | Manual comparison of archived NC-015 vs current content | Read file, compare facts | Fact accounted for (already present or added) |

## Completion criteria

- [ ] Checked whether NC-015 facts are already documented in the file (REQ-002)
- [ ] Added missing facts if not already present
- [ ] No duplicate documentation introduced

## Out of scope

- Changes to threshold/retention configuration itself
- Changes to other governance documents
- Modifying governance-policy documents already updated by the prior task

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read source file and check for existing facts | Pending | — | — | |
| 2 | Add missing facts if not present | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260831-162016_govdocs001_historical_content_removal_and_transfer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-223610_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-01T00:00:00Z
- **Related target files**: 05_agent_12_02_memory-gate-data-model-search.md
