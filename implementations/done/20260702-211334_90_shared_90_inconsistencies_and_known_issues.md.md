# Implementation: Verify `tool_call_id` entries in `90_shared_90_inconsistencies_and_known_issues.md`

## Goal

Confirm that `docs/90_shared_90_inconsistencies_and_known_issues.md` contains no open issue entry
describing `tool_call_id` as "unused" or "not used". If such an entry exists, remove it or mark
it as resolved. If no such entry exists, no change is needed.

Then run a project-wide grep to confirm zero remaining stale "UNUSED" claims for `tool_call_id`
across all docs and scripts.

## Scope

- **In scope**: `docs/90_shared_90_inconsistencies_and_known_issues.md`; final project-wide
  grep validation across `docs/` and `scripts/`.
- **Out of scope**: Changes to source code; changes to `90_shared_04` or `90_shared_05`.

## Assumptions

1. Per the plan (Assumption 3), the file currently contains no entry mentioning `tool_call_id`.
2. If no entry exists, no edit is required.
3. If an entry is found, it must be removed or marked as resolved (e.g., append `[RESOLVED]`
   and note the fix).

## Implementation

### Target file

`docs/90_shared_90_inconsistencies_and_known_issues.md`

### Procedure

1. Search the file for any `tool_call_id` reference:
   ```bash
   grep -n "tool_call_id" docs/90_shared_90_inconsistencies_and_known_issues.md
   ```
2. If **0 results**: no edit required. Proceed to validation.
3. If results found: inspect each line for "unused", "UNUSED", "not used", or similar language.
   - If found: remove the offending table row or paragraph, or append `[RESOLVED — tool_call_id
     is actively persisted by SessionMessageRepository as of <date>]` at the end of the entry.
   - If the mention is already correct (e.g., a resolved-status note): leave it as-is.
4. Run project-wide validation grep (Phase 4 of the plan):
   ```bash
   grep -R "tool_call_id.*UNUSED\|UNUSED.*tool_call_id" docs scripts -n
   ```
   Confirm 0 results.

### Method

Grep-first, then targeted Edit only if a stale entry is found. No structural change to the file
unless stale content is identified.

### Details

- The file uses a known-issues table format. If a removal is needed, remove the entire row
  (pipe-delimited markdown table row).
- When marking as resolved instead of removing, use the convention already present in the file
  for resolved issues (check file header or existing resolved entries for the pattern).
- If the file has no `tool_call_id` entry at all: this implementation step is a no-op verify.

## Validation plan

| Check | Command / Action | Expected result |
|---|---|---|
| No open issue for `tool_call_id` | `grep -n "tool_call_id" docs/90_shared_90_inconsistencies_and_known_issues.md` | 0 results, or only resolved entries |
| No stale "UNUSED" in any doc or script | `grep -R "tool_call_id.*UNUSED\|UNUSED.*tool_call_id" docs scripts -n` | 0 results |
| No "not used" claim | `grep -Rin "tool_call_id.*not used\|not used.*tool_call_id" docs/ -n` | 0 results |
