## Goal
- `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-006`: make the Deployment chapter's DB inventory include `mdq.sqlite`, with its initialization, recovery stance, and health-check behavior, and note its path source beside the generated DB Path Reference.

## Scope
- `docs/90_deployment/deployment_01_deployment.md` only (section 3.0, the text just below its table, and a note after the generated block). The ADR-008 cross-reference is the other row's document.

## Assumptions
- The facts to restate are verified: `db_08` lists `mdq.sqlite` (owner, config source, lifecycle); ADR-008 states it is a derived store rebuilt from Markdown files and not covered by the backup and rotation helpers; `db_03` section 8d describes legacy-schema detection at every MDQ service start; `deploy/deploy.sh` provisions the DB directory; `deploy/init_db.sh` does not create `mdq.sqlite`; the MDQ health check reports a missing DB file and schema problems as degraded.
- The chapter intentionally does not state default paths (the existing text says so), so no literal path for `mdq.sqlite` is written; the config key is named instead.

## Design decisions
- Add one row to the section 3.0 table and one short paragraph below it; do not add a new section or a second table.
- Keep the generated block untouched and put one hand-written sentence after its closing guard comment.

## Alternatives considered
N/A: extending the generator to read `config/mdq_mcp_server.toml` was decided against with the requester.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
- In the section 3.0 table, add the row: DB `mdq.sqlite`, config key `db_path` in `config/mdq_mcp_server.toml` (not an `agent.toml` key), purpose "Markdown index of the MDQ server (derived store)".
- After the table's following explanatory paragraph, add a paragraph stating that: `mdq.sqlite` is not one of the platform databases above but a derived index owned by the MDQ server (links to ADR-008 "Derived Stores Outside the Four Domains" and `db_08`); `init_db.sh` does not create it, `deploy.sh` provisions the DB directory, and the MDQ service creates the file and tables when it starts, dropping and recreating a legacy `chunks` schema as described in `db_03` section 8d; recovery is by re-indexing the Markdown files, and the backup and rotation helpers do not cover it (ADR-008); the MDQ health check reports a missing DB file or an unhealthy schema as degraded.
- Immediately after `<!-- END AUTO-GENERATED -->`, add one sentence saying `mdq.sqlite` is absent from that table because the table is generated only from `scripts/db/config.py` and `config/agent.toml`, and that its path is the `db_path` key of `config/mdq_mcp_server.toml`.

### Method
- Use relative links in the form the chapter already uses (for example `../10_adr/adr_02_008_sqlite-4db-separation.md`, `../41_db/db_08_active_databases.md`, `../41_db/db_03_architecture_and_schema-migration-and-scaling.md`).
- Avoid forms the content-policy checker flags: no `defaults to` phrasing, no "implemented by `<file>.py`" mapping, no extra tables with per-file descriptions, no port numbers.
- Write in English and do not edit text between the guard comments.

### Details
- If `check_docs_structure.py` requires it, add `adr_02_008_sqlite-4db-separation.md`, `db_08_active_databases.md`, and `db_03_architecture_and_schema-migration-and-scaling.md` to the front matter `related:` list as bare `.md` basenames.
- State nothing about directory permissions, capacity, or WAL monitoring (Plan UNK-01 and UNK-02).

## Compatibility considerations
N/A: documentation only; the generated block and the existing four-database table rows are unchanged.

## Security considerations
N/A: no secrets or configuration values are added; the config key is named without its value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/90_deployment/deployment_01_deployment.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_docs_consistency.py --domain deployment`, `uv run python tools/generate_reference_table.py --check`

## Completion criteria
- Section 3.0 lists `mdq.sqlite` and the new paragraph matches `db_08`, ADR-008, and `db_03` section 8d without adding a claim they do not make.
- The note after the generated block names the path source, and the generator check reports no drift.
- The docs checkers above report no new finding.

## Out of scope
- The generator, the ADR-008 text, the other chapter sections, `db_08`, `db_03`, and any `deploy/*.sh` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `mdq.sqlite` row and paragraph to section 3.0 and the note after the generated block | Completed | 20261016-131842 | 20261016-131948 | changed: docs/90_deployment/deployment_01_deployment.md (row, paragraph, note; intro sentence adjusted so 'each platform database' stays accurate) |
| 2 | Run the docs checkers and the generator check | Completed | 20261016-131948 | 20261016-131948 | check_docs_quality/structure/content_policy --strict/japanese/consistency --domain deployment: clean; generate_reference_table --check: no drift |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (inventory, initialization, recovery and health check), REQ-004 (path-source note), REQ-006 (consistency and checkers)
- **Source issue**: issues/20261016-125807_dep001_add-mdq.sqlite-to-the-deployment-db-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-130739_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-131326
- **Related target files**: docs/90_deployment/deployment_01_deployment.md