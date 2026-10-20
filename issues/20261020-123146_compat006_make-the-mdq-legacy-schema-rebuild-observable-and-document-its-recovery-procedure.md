# Make the MDQ legacy-schema rebuild observable and document its recovery procedure

## Priority
Medium

## Summary
The MDQ service silently drops and recreates its `chunks` tables when it finds the legacy shape. Decide how an operator learns that this happened, document how the index is repopulated from the Markdown sources, and set the condition under which the legacy branch is removed. Record the decisions and the operator procedure in the documents; file separate issues for any code change they require.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed persistent-data migrations. It read documents only; the facts below were re-checked against the current code, tests, and documents on 2026-10-20.
- `create_production_tables()` in `scripts/mcp_servers/mdq/db_schema.py` runs every time the MDQ service starts. `_migrate_legacy_chunks_schema()` treats the schema as legacy when the first column of `chunks` is named `id`, then drops `chunks_fts`, `chunks`, and the three sync triggers, and the function recreates the current tables. The `documents` table is created only `IF NOT EXISTS`, so it is not dropped. (Explicit in code)
- The only record of the rebuild is an `INFO` log line, "Detected old chunks schema (id column); rebuilding to chunk_id PRIMARY KEY". No warning level, health field, or startup failure marks it. (Explicit in code, Verified by test: `test_logs_info_message_on_legacy_schema_detection`)
- The behavior is covered by tests in `tests/mcp_servers/mdq/test_db_schema.py`: the rebuilt table has `chunk_id` as primary key, and the legacy rows are gone afterwards. (Verified by test)
- The database document (`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, section 8d) already states that the detection runs on every start, that the drop is unconditional, and that existing data is lost; it describes the rebuild as silent. No document gives the operator steps to repopulate the index. (Documentation only; absence verified by search)
- The MDQ tools include `index_paths` and `refresh_index`, and indexing writes `documents` rows with `INSERT OR REPLACE`. Whether stale `documents` rows left after a rebuild can stop a document from being re-indexed was not verified. (Needs confirmation)
- The legacy test fixture creates only a `chunks` table, so the legacy shape probably predates the `documents` table. (Strongly implied by code)

## Problem
Losing the whole MDQ index on an ordinary service start is acceptable only if the operator can notice it and recover. Today the notice is one `INFO` log line that is easy to miss, and no recovery steps exist. The legacy branch also has no owner and no removal condition, so it stays on the startup path indefinitely.

## Reason for Change
MDQ is a derived store: the Markdown sources are the source of truth, so a rebuild is safe only when the index is reloaded afterwards. If it is not, search returns nothing without an error. A visible signal and a documented recovery path turn a silent loss into a managed upgrade, and an end condition lets the branch be deleted once no legacy database can exist.

## Implementation Intent
- Treat this as a decision and documentation task: choose the operator signal (log level, health surface, or startup refusal), write the recovery procedure for the operator, and set the removal condition for the legacy branch.
- Keep the derived-store principle: no migration of legacy chunk data, because it is rebuilt from Markdown.
- Any code change (for example, raising the log level or exposing the rebuild in `/health`) is a separate follow-up issue once the signal is chosen.
- Tie the removal condition to the baseline decision in `compat001`.

## Target Files or Areas
- `docs/22_mcp/mcp_04_04_mdq.md` (operator-facing recovery procedure and signal)
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (section 8d: signal decision and removal condition)
- `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md` (only if the chosen signal is a health reason)
- Read for evidence: `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/indexer.py`, `scripts/mcp_servers/mdq/index_write.py`
- Tests, read only: `tests/mcp_servers/mdq/test_db_schema.py`

## Required Changes
- Verify, on a copy of a legacy-shaped database, whether re-indexing the Markdown sources after the rebuild fully repopulates the index, including when stale `documents` rows remain; record the result.
- Decide the operator signal for a legacy rebuild and record it in the database document; file a follow-up issue if it needs code.
- Write the operator procedure in the MDQ document: how to tell a rebuild happened, how to repopulate the index (naming the tools to run), how long it takes at the current corpus size, and what to do if re-indexing fails.
- Record the removal condition for the legacy branch, derived from the baseline in `compat001`, and file a removal issue when the condition holds.
- Register anything unconfirmed in the Needs Confirmation inventory.

## Constraints
- No change to `scripts/` or `tests/` in this issue; the rebuild behavior stays as it is, including the unconditional drop.
- Do not migrate legacy chunk data; MDQ is a derived store and is rebuilt from the Markdown sources.
- Run any verification on a copy of the database, never on the deployed file.
- Documentation follows the docs content policy: intent, constraints, failure behavior, and operational notes; no code listing or schema copy; written in English.

## Acceptance Criteria
- The documents state the operator signal for a legacy rebuild, or record it as an open decision with an owner.
- The MDQ document contains the recovery procedure, with the tools to run and the check that confirms the index is repopulated.
- The result of the re-index verification on a legacy-shaped copy is recorded, including whether stale `documents` rows matter.
- The removal condition for the legacy branch is recorded and tied to the `compat001` baseline.
- No file under `scripts/` or `tests/` is changed, and the documentation checkers pass.

## Testing Expectations
- Manual verification on a copy of a legacy-shaped database, recorded in the issue or document.
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_consistency.py --domain mcp`, and `uv run python tools/check_needs_confirmation_inventory.py`.

## Documentation Impact
Yes. Update the MDQ document with the operator procedure and signal (operational notes, failure behavior), and the database document with the signal decision and the removal condition (constraints, data-loss notes). Keep the existing data-loss warning.

## Out of Scope
- Changing `_migrate_legacy_chunks_schema()`, its log level, or the health output.
- Migrating legacy chunk data instead of rebuilding.
- The schema baselines of the other databases (`compat001`).
- Removing the legacy branch.

## Dependencies
- Depends on: `compat001` for the minimum supported schema baseline.
- Sibling-issue check: no open issue under `issues/` touches the MDQ schema or its documents.
- Blocks: any follow-up that changes the signal or removes the legacy branch.

## Unresolved Questions
- Does re-indexing repopulate the index fully when stale `documents` rows remain after a rebuild? (Needs confirmation; the verification above answers it)
- Does any deployment still hold a database with the legacy `chunks` shape? (Needs confirmation; the repository cannot answer this)
- Is an `INFO` log line an acceptable signal for an operator, or should the rebuild be a warning or a health reason?
- Who owns the MDQ index and the decision to drop the legacy branch?

## AI Implementation Instruction
- Do not change `scripts/` or `tests/`, and do not run any step against a deployed database; use a copy.
- Do not describe an operator step that was not verified; record the unverified step as an open question instead.
- Keep the documentation to decisions, constraints, and operational notes; do not copy the schema or code.
- File a separate issue for any code change a decision requires; do not implement it here.
- Run the documentation checkers listed above before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123146
- **Related target files**: `docs/22_mcp/mcp_04_04_mdq.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`, `scripts/mcp_servers/mdq/db_schema.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `tests/mcp_servers/mdq/test_db_schema.py`
