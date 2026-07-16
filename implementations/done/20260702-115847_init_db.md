# Implementation: Fix deploy/init_db.sh to use the unified schema initialization entrypoint

## Goal

Fix `deploy/init_db.sh` to initialize all DBs (rag/session/workflow/eventbus) via `python -m db.create_schema`.

## Scope

- deploy/init_db.sh: Remove EVENTBUS_SCHEMA variable and eventbus/schema.sql check/load
- Remove any `python -m db.workflow_schema` calls
- Unify to single `python -m db.create_schema` call
- Add table verification comment for eventbus.sqlite
- Fix shell syntax errors detected by shellcheck (`$/...` broken variable references)

## Assumptions

1. Current `init_db.sh` has EVENTBUS_SCHEMA variable but no broken `$/...` patterns
2. `python -m db.create_schema` initializes all 4 DBs after plan 53 (create_eventbus_schema) is implemented
3. Continue using `uv run python` as currently in the script

## Implementation

### Target file

- deploy/init_db.sh → modify

### Procedure

#### Phase 1: shellcheck verification

Run `shellcheck deploy/init_db.sh 2>/dev/null || echo "shellcheck not installed"` and fix any issues.

#### Phase 2: Remove eventbus/schema.sql references

- Delete EVENTBUS_SCHEMA variable definition
- Delete eventbus/schema.sql existence check block (lines 24-29)
- Delete `sqlite3 ... ".read ..."` eventbus initialization block (lines 52-55)
- Delete Event Bus initialization comment (line 49)

#### Phase 3: Unify to create_schema.py one-shot initialization

- Update schema initialization comment to "rag + session + workflow + eventbus"
- Consolidate `python -m db.create_schema` call to a single location

#### Phase 4: Add table verification command

- Add `.tables` verification for eventbus.sqlite
- Add expected value comment (events)

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Shell syntax | `bash -n deploy/init_db.sh` | No errors |
| shellcheck | `shellcheck deploy/init_db.sh` | No warnings (if installed) |
| Manual run | `bash deploy/init_db.sh` | 4 DBs generated |
