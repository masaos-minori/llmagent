# Implementation: Deploy verification for backward-compatibility removal (Phase 5)

## Goal

Confirm that the Phase 1-4 backward-compatibility removals require no `deploy/deploy.sh` copy-list changes (no files added or removed, only content edited), and define the deployment/rollback coordination needed for the two production-affecting changes: the `use_tool_dag`/`POST /ack` breaking removal (Phase 3) and the `events.retry_count` schema migration (Phase 4).

## Scope

**In:**
- Verify `deploy/deploy.sh` needs no copy-list update, since Phases 1-4 only modify existing files (no new modules, no deleted files under `scripts/`)
- Define the production deployment sequence for Phase 4's SQLite schema migration (service stop order, pre-migration `.sqlite` file backup, rollback plan)
- Confirm CHANGELOG / release-notes entries from Phase 3 are in place before deployment

**Out:**
- No new environment variables, ports, or MCP server registrations are introduced by any phase — nothing to add to `config/agent.toml`'s `[mcp_servers]` section or to `rules/env.md`

## Assumptions

1. All four phases modify only pre-existing files; none add or remove a file under `scripts/`, so `deploy/deploy.sh`'s copy list is unaffected — to be confirmed by diffing the file list touched across Phases 1-4 against `deploy/deploy.sh`'s current copy list at implementation time.
2. The Event Bus process must be stopped before applying the Phase 4 schema migration if the deployment process does not already serialize "stop old version → migrate → start new version" — this needs confirming against the actual `skills/deploy/SKILL.md` procedure at implementation time, since a running old-version process could hold the SQLite connection open during migration.

## Implementation

### Target file

`deploy/deploy.sh` (verification only, no expected edits)

### Procedure

1. Diff the full list of files touched by Phases 1-4 (see `plans/20260710-102535_plan.md`, Affected areas tables) against `deploy/deploy.sh`'s existing copy list; confirm every touched file is already covered and no file was added/removed.
2. Confirm the CHANGELOG / release-notes entry for `use_tool_dag=false` and `POST /ack` removal (added in Phase 3) is present before cutting a release.
3. Before applying Phase 4 in production: back up the Event Bus `.sqlite` file, stop the Event Bus service, deploy the updated code (which runs the `DROP COLUMN` migration on next `open_db()` call), then start the service and verify `/health` returns 200.
4. If the Phase 4 migration fails in production (e.g., unexpectedly old SQLite version), restore the pre-migration `.sqlite` backup and redeploy the previous release tag.

### Method

Verification-only step — no source code is produced by this document; it records the deployment checklist referenced by `plans/20260710-102535_plan.md`'s "Phase 5: デプロイ" section.

### Details

- This document intentionally has no "Method: code changes" section because Phase 5 in the plan is a coordination/checklist step, not a file-level implementation task.
- Coordinate the exact stop/deploy/start ordering with `skills/deploy/SKILL.md` at execution time, since it is authoritative for this repository's deployment procedure.

## Validation plan

```bash
# Confirm no file additions/removals require a deploy.sh copy-list change
git diff --name-status master...HEAD -- scripts/ | grep -v '^M'   # expect no output (only 'M'odified files)

# Confirm the Event Bus health check passes post-migration
curl -s http://127.0.0.1:<eventbus_port>/health   # expect HTTP 200
```

Expected outcome: no unmodified-copy-list drift, CHANGELOG entry present, and the Event Bus reports healthy after the Phase 4 migration is applied in production.
