## Goal

Fix the stale claims in `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
that `workflow_db_path` is not an `agent.toml` key and that the workflow path falls back
to a code-level default when absent from `agent.toml`. (`REQ-007` stale-claim fix)

## Scope
**Release unit**: WORKFLOW-CONFIG

## Assumptions

- Primary anchor: the line-34 claim "`workflow.sqlite` uses a Python-level default path
  (`workflow_db_path` is not an `agent.toml` key`" — becomes false once procedure 03
  lands.
- The section-3 sentence "`The workflow path falls back to a code-level default when
  absent from agent.toml.`" (`:44`) is the same claim class; the repo config carries the
  key, so it is corrected in the same edit (plan Validation Status "Verified" applies to
  the row's claims, and leaving it would keep a false path-key claim in the same doc).

## Design decisions

- State that all four platform databases have their own path keys in `agent.toml`, with
  the `DbConfig` field default as the single code default; do not quote the path value
  (docs content policy: mechanism claims, config values live in the config).

## Alternatives considered

- N/A: claim fix with one wording target per sentence.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. In the line-34 sentence (`:34`), replace "`workflow.sqlite` uses a Python-level
   default path (`workflow_db_path` is not an `agent.toml` key`)" with text stating all
   four platform databases have their own path keys in `agent.toml`
   (`rag_db_path`, `session_db_path`, `workflow_db_path`).
2. In section 3 (`:44`), re-word the fallback sentence so it says `agent.toml` sets
   `workflow_db_path` and the `DbConfig` field default is the single code default used
   when a caller constructs `DbConfig` directly.

### Method
Keep sentence density and the surrounding paragraph structure unchanged; no other
section of the doc is touched.

### Details
`db_02` table references and the derived-stores paragraph (`:36`) stay untouched.

## Compatibility considerations

- N/A: docs-only change.

## Security considerations

- N/A: docs-only change.

## Rollback considerations

- N/A: revert the commit (WORKFLOW-CONFIG unit).

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain db` (plan row validation) —
  clean.
- `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py
  docs/41_db/db_01_architecture_and_schema-overview-and-config.md`,
  `uv run python tools/check_docs_content_policy.py` (routing.md Tools: docs scope) —
  all clean.

## Completion criteria

- Neither sentence claims `workflow_db_path` is absent from `agent.toml` (AC-4).

## Out of Scope

- `docs/90_deployment/deployment_01_deployment.md` (procedure 13, generator-only).
- `scripts/db/config.py` and `config/agent.toml` (procedures 03/04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the two path-key claims | Completed | 2026-11-18 | 2026-11-18 |  |
| 2 | Run the docs checkers (routing.md Tools, docs scope) | Completed | 2026-11-18 | 2026-11-18 |  |

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
- **Requirement ID**: `REQ-007` (db_01 path-key claim fix)
- **Source issue**: issues/done/20261117-123019_adrchk019_mdq-workflow-db-settings.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-155712_adrchk019_mdq-workflow-db-settings.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-162732
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`