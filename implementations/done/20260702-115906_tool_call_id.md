# Implementation: Fix documentation for messages.tool_call_id to match implementation

## Goal

Fix `docs/90_shared_04_db_architecture_and_schema.md` for `messages.tool_call_id` from "UNUSED" to actual behavior.

## Scope

- docs/90_shared_04_db_architecture_and_schema.md: Fix tool_call_id line
- docs/90_shared_05_db_api_and_operations.md: Fix if any misdescription of tool_call_id exists
- docs/90_shared_90_inconsistencies_and_known_issues.md: Fix if stale tool_call_id UNUSED description exists

## Assumptions

1. SessionMessageRepository persists/restores tool_call_id in save(), save_many(), replace_messages(), fetch_messages()
2. No stale tool_call_id description in 90_shared_90 (grep confirmed no direct mentions)

## Implementation

### Target files

- docs/90_shared_04_db_architecture_and_schema.md: Fix line 171
- docs/90_shared_05_db_api_and_operations.md: Check and fix if needed
- docs/90_shared_90_inconsistencies_and_known_issues.md: Check and fix if needed

### Procedure

#### Phase 1: Full-text search for target locations

Run `rg -n "tool_call_id\|UNUSED" docs/` to identify all locations.

#### Phase 2: Fix 90_shared_04

Line 171: Replace `| tool_call_id | TEXT | UNUSED — column exists in schema but not referenced by any code |` with:
`| tool_call_id | TEXT | ツールコール相関 ID（tool ロールのメッセージ向け）。SessionMessageRepository が persist/restore する。非ツールメッセージでは NULL。|`

#### Phase 3: Check and fix other documents

- Check 90_shared_05 for tool_call_id descriptions, fix if needed

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No stale description | `rg -n "tool_call_id.*UNUSED\|UNUSED.*tool_call_id" docs/` | 0 matches |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
