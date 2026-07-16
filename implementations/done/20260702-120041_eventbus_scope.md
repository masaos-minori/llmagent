# Implementation: Document Event Bus runtime integration as out of scope

## Goal

Document `eventbus.sqlite` as an initialized target DB in 90_shared_*.md, and explicitly state that Event Bus runtime integration is out of scope for this cleanup.

## Scope

- docs/90_shared_01_overview.md: Add eventbus.sqlite description, note Event Bus runtime not implemented
- docs/90_shared_04_db_architecture_and_schema.md: Document eventbus.sqlite as fourth DB file, note runtime not implemented
- docs/90_shared_05_db_api_and_operations.md: Add eventbus.sqlite schema verification command
- Specify timestamp policy (ISO-8601 UTC Z suffix) for future Event Bus writers
- Note retry_count is deprecated but retained

## Assumptions

1. eventbus.sqlite initialization works after plans 52-53 implementation (build_eventbus_schema_sql() / create_eventbus_schema())
2. 90_shared_04 currently says "Three DB files" — add eventbus as fourth
3. 90_shared_01 has workflow_schema.py line, but plan 54 will remove it — this plan only adds eventbus-related content

## Implementation

### Target files

- docs/90_shared_01_overview.md: Add eventbus.sqlite description
- docs/90_shared_04_db_architecture_and_schema.md: Update to "Four DB files", add eventbus row
- docs/90_shared_05_db_api_and_operations.md: Add eventbus.sqlite verification command

### Procedure

#### Phase 1: Fix 90_shared_04

- Change "Three DB files" heading/description to "Four DB files"
- Add eventbus.sqlite row to DB file table (config key: eventbus_db_path, tables: events)
- Add Event Bus runtime not implemented note (publisher/subscriber/dispatcher/DLQ worker are unimplemented)
- Specify timestamp policy: future Event Bus writers must use ISO-8601 UTC Z suffix
- Note retry_count is deprecated but retained

#### Phase 2: Fix 90_shared_01

- Add eventbus.sqlite related description to db/ module list
- Explicitly note Event Bus runtime (publisher/subscriber etc.) is unimplemented

#### Phase 3: Fix 90_shared_05

- Add eventbus.sqlite verification command to Verification Plan (§10) sqlite3 commands

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| eventbus description consistency | `grep -rn "eventbus" docs/90_shared_*.md` | Consistent descriptions exist |
| Runtime not implemented note | `grep -n "runtime\|publisher\|subscriber" docs/90_shared_04_db_architecture_and_schema.md` | out-of-scope description exists |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
