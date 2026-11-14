## Goal

Add a `storage_format` column to the `session_diagnostics` DDL so retrieval can report encrypted / redacted-plaintext / decrypt-failed records distinctly (`REQ-006`, `AC-4`).

## Scope
**Release unit**: `storage_format` column + save()/fetch() write-and-read path

## Assumptions
- `session.sqlite` is **recreate-only**: no migration registry or version stamp (unlike `workflow.sqlite`/`eventbus.sqlite`).
- The column is `storage_format TEXT NOT NULL DEFAULT 'plaintext'`; the write path (`diagnostic_store.py::save()`) always sets it explicitly (`encrypted` when a key encrypts, otherwise `plaintext`), so the default is only a fallback.
- Pre-existing `session_diagnostics` rows are discarded on recreation; they are operator-facing auxiliary data with low retention value.

## Design decisions
- **Add the column to the canonical DDL only.** The column lives in `_SESSION_SCHEMA_TEMPLATE` (the SSOT DDL). No backfill is needed because the DB is recreated, not migrated.
- **Ship the DDL with its write/read path as one release unit** (Phases 2-3): a fresh DB created after this change has the column, so every `INSERT` into `session_diagnostics` must populate it.

## Alternatives considered
- **Nullable column with NULL default.** Rejected: `save()` always knows the format, so `NOT NULL` with an explicit per-write value is stricter and makes the stored state self-describing.

## Implementation
### Target file
`scripts/db/schema_sql.py`
### Procedure
- Add `storage_format` to the `session_diagnostics` table in `_SESSION_SCHEMA_TEMPLATE`.
### Method
- In `_SESSION_SCHEMA_TEMPLATE`, inside the `session_diagnostics` block (lines 134-142), add a `storage_format` column after `task_id` (line 140):
  ```sql
      CREATE TABLE IF NOT EXISTS session_diagnostics (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id  INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
          kind        TEXT    NOT NULL,
          content     TEXT    NOT NULL,
          workflow_id TEXT,
          task_id     TEXT,
          storage_format TEXT NOT NULL DEFAULT 'plaintext',
          created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
      );
  ```
### Details
- `diagnostic_store.py::save()` (its own row) must add `storage_format` to its `INSERT` column list and values, and `fetch()` must select and classify on it. Both must ship with this DDL change so a fresh DB and the `INSERT` stay in sync.

### Companion test files
N/A.

## Compatibility considerations
**Operational impact — production `session.sqlite` recreation.** Adding a column changes the canonical DDL. `create_schema.py::_refuse_existing_drift` + `assert_matches` and `session_consistency.py::_check_schema_fingerprint` compare the live schema against canonical DDL, so any existing `session.sqlite` fails the fingerprint gate on startup and must be **archived and recreated**. Pre-existing diagnostic rows are lost. Communicate this recreation to the owner before landing. This is the highest-impact change in the Plan.

## Security considerations
The column lets `fetch()` refuse to return ciphertext as ordinary content (`AC-4`): a decrypt-failed row is reported distinctly instead of leaking encrypted bytes to a consumer.

## Rollback considerations
Revert the commit. Reverting this file restores the pre-change canonical DDL; on next recreate the column disappears. Revert together with `diagnostic_store.py` so the `INSERT`/`SELECT` stay aligned with the DDL.

## Validation plan
- Integration: fresh canonical schema includes `storage_format`; fingerprint matches the canonical DDL.
- Command: `uv run python tools/check_db_separation.py` plus the schema fingerprint test.

## Completion criteria
- `_SESSION_SCHEMA_TEMPLATE`'s `session_diagnostics` includes `storage_format TEXT NOT NULL DEFAULT 'plaintext'`.
- `check_db_separation.py` and the fingerprint test pass.

## Out of Scope
- Populating the column in `save()` and classifying it in `fetch()` (`scripts/agent/diagnostic_store.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `scripts/db/schema_sql.py`
