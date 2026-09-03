# Remove Local-only configuration and deployment artifacts and provide a controlled migration

## Priority
Medium

## Summary
Delete obsolete Local/development configuration overlays and external-publication deployment
artifacts after Production-only and loopback-only runtime behavior is available, and provide a
repeatable migration procedure.

## Background
This issue depends on `localremoval` and `loopbackonly` landing first — deleting configuration
files before runtime behavior is migrated can break startup or remove process-owned
configuration required by ADR-002.

## Problem
Leaving Local overlays and public deployment files after the new behavior is implemented
creates ambiguous and unsupported deployment paths.

## Reason for Change
The migration must distinguish obsolete environment overlays from canonical per-process
configuration, and do so only after the behavior that made them obsolete is actually in place.

## Implementation Intent
Inventory Local/development-only TOML files, environment files, Compose overlays, systemd
units, deployment directories, and startup scripts; delete only artifacts whose purpose is
Local/development profile selection or external publication; preserve canonical process-owned
files (`config/agent.toml`, `config/crawler.toml`, `config/chunk_splitter.toml`,
`config/ingester.toml`, `config/eventbus.toml`, `config/workflows/default.json`,
`config/*_mcp_server.toml`); remove references to deleted files from scripts, CI,
documentation, and deployment tooling; define a migration procedure (backup, migrate URLs/bind
addresses, configure MCP authentication and allowlists, enable/verify strict validation,
restart, verify authentication/discovery/routing/tool-visibility/socket binding, verify
external connectivity is unavailable, delete obsolete artifacts only after verification);
define rollback at release level, not as a Local-mode switch.

## Target Files or Areas
- `config/`
- `.env*`
- `deploy/`
- `docker-compose*.yml`
- `systemd/`
- Startup and run scripts
- CI/CD deployment definitions
- Operations and migration documentation

Only delete files that actually exist and whose role has been verified. Candidate patterns:
`config/agent.local.toml`, `config/agent.dev.toml`, `config/local/`, `config/dev/`,
`config/*.local.toml`, `config/*.dev.toml`, `config/*_local.toml`, `config/*_dev.toml`,
`.env.local`, `.env.development`, `docker-compose.local.yml`, `docker-compose.dev.yml`, and
Local-only deployment/systemd definitions.

## Required Changes
- Inventory candidate Local/development artifacts; confirm each one's purpose before deletion.
- Delete confirmed Local/development-only artifacts; preserve all canonical process-owned files listed above.
- Remove references to deleted files from scripts, CI, documentation, and deployment tooling.
- Write the migration procedure (backup → migrate → configure auth/allowlists → verify strict validation → restart → verify → delete) as operator-facing documentation.
- Define release-level rollback guidance that does not restore a Local-mode switch.

## Constraints
- Do not delete canonical per-process configuration files.
- Do not create `common.toml`, `rag_pipeline.toml`, or another shared configuration file.
- Do not remove external third-party credentials or endpoints unrelated to internal service publication.
- Do not rely on `/reload` for authentication, MCP definitions, bind addresses, startup mode, or workflow-definition changes.
- Do not represent rollback as re-enabling Local mode.

## Acceptance Criteria
- No Local/development-only configuration or deployment artifact remains.
- No code, CI job, script, or document references a deleted file.
- Canonical per-process configuration files remain present and valid; configuration-isolation tests continue to pass.
- The migration procedure succeeds on a clean deployment; all affected processes are fully restarted during migration.
- Startup, authentication, discovery, routing, and tool visibility are verified after migration; external connectivity fails after migration.
- Rollback guidance does not retain or restore a Local runtime profile.

## Testing Expectations
Add repository checks for references to deleted artifacts. Run configuration-isolation and
startup tests. Execute the documented migration against a clean or disposable environment;
verify active configuration and actual listener state after restart.

## Documentation Impact
Update configuration inventories, deployment procedures, migration guidance, restart
requirements, and rollback documentation in the same change.

## Out of Scope
- Runtime policy implementation (`localremoval`).
- Loopback enforcement implementation (`loopbackonly`).
- Authentication implementation (`mcpauth`).
- Deleting canonical process-owned configuration.

## Dependencies
Depends on `localremoval` and `loopbackonly` landing first — this issue's deletions assume
those behaviors already exist and are verified.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Do not delete files based only on filename patterns. Read each candidate, identify every
reference, and confirm that `localremoval`/`loopbackonly`/`mcpauth` have removed its functional
purpose before deleting it. Preserve process isolation and make deletion the final step after
successful migration verification.
