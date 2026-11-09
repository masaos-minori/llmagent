## Goal
Restate the dedup config-location contract in the db_03_07 doc to match the resolver-based config path and the one-load-per-process caching that `183007_01` introduces (`REQ-001`, `REQ-002`), and pin the unchanged `DEFAULT_DB_PATH` fallback wording for the store database (`REQ-003`).

## Scope
**Release unit**: wfaudit011-full

- Covers Plan `plans/20261108-084012_wfaudit011_dedup-config-path-boundary.md` row 2 only: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`.
- Two text locations in that doc: the "File location" bullet (L43-44) and the Config keys paragraph (L69-71). No other section changes.

## Assumptions
- `183007_01` (the `scripts/shared/mcp_dedup.py` resolver/cache procedure) lands with this document; the doc describes the post-change state, matching this repository's documentation policy.
- `docs/90_deployment/` contains no `mcp_dedup` location statements (grep verified 20261108 in the plan's Documentation Impact), so no deployment-doc edit accompanies this change.
- The doc describes behavior only: the new private symbols of `183007_01` stay unnamed here per `skills/DESIGN.md` Docs content policy.

## Design decisions
- State the caching contract at the public-API level (`load_dedup_config()` reads once per process; restart to pick up changes) instead of describing the cache internals — the doc already describes behavior, not implementation.
- Keep the existing error semantics (`ConfigMissingError` / `ConfigParseError`) and the default `/opt/llm/db/mcp_dedup.sqlite` value verbatim; only the location/resolution wording changes.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
Rewrite the "File location" bullet and append one caching sentence to the Config keys paragraph.

### Method
1. In the "File location" bullet (L43-44), replace
   "- File location: `dedup.db_path` in `config/mcp_dedup.toml`, default `/opt/llm/db/mcp_dedup.sqlite`.
   A missing config file raises `ConfigMissingError`; bad values raise `ConfigParseError`."
   with: "- File location: the config file is resolved through `resolve_config_dir()` (overridable with
   `LLMAGENT_CONFIG_DIR`), like every other config consumer. The store database is `dedup.db_path` in
   `config/mcp_dedup.toml`, default `/opt/llm/db/mcp_dedup.sqlite` — the same fallback-literal shape the
   other platform databases use. A missing config file raises `ConfigMissingError`; bad values raise
   `ConfigParseError`."
2. In the Config keys paragraph (L69-71), after the sentence ending "the agent-side stale-pending
   classification in `workflow.sqlite`.", append: "The config file is read once per process: after the
   first successful load the parsed config is cached until the service restarts, and a failed load is
   not cached."

### Details
- The bullet today implies a CWD-relative `config/mcp_dedup.toml`; after `183007_01` the default is resolver-managed, so the sentence must not name a bare relative path as the location.
- The fallback literal itself is unchanged by the plan (`REQ-003`): the added clause only names the convention it mirrors; no configured database path changes.

## Compatibility considerations
- N/A: documentation-only change.

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- Revert this document with `git checkout -- docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` (plus the `183007_01` landing if reverting together).

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `uv run python tools/check_docs_content_policy.py`, and `uv run python tools/check_docs_consistency.py --domain db` per `routing.md` Tools.

## Completion criteria
- Both edited passages state the resolver-based config location and the one-load-per-process caching contract; the default database path and error semantics are unchanged; the four docs checkers report no findings.

## Out of Scope
- The Replay Decision Table and `tool_call_state` sections of the same doc — untouched.
- Any deployment-doc config-mirroring note — confirmed unnecessary (see Assumptions).

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the "File location" bullet (L43-44) and append the caching sentence to the Config keys paragraph (L69-71) | Completed | 20261109-100136 | 20261109-100136 |  |
| 2 | Run docs checkers (quality, structure, content policy, consistency --domain db) | Completed | 20261109-100136 | 20261109-100136 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `wfaudit011` (via the source plan)
- **Source requirement**: see the plan's Requirements (`REQ-001`, `REQ-002`, `REQ-003`)
- **Source plan**: `plans/20261108-084012_wfaudit011_dedup-config-path-boundary.md`
- **Generated at**: 20261108-183007
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-183007 -->