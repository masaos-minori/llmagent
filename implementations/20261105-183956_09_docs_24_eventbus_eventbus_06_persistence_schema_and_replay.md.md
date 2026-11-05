## Goal

Correct the EventBus schema passages of `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` so they reflect the canonical version-6 identity contract produced by this Plan: move the "current schema version" from `PRAGMA user_version = 3` to 6, replace the "ADR-008: no migration mechanism" statement with the registered forward-only three-step chain, and document the create/validate/migrate three paths, the fingerprint contract, the version-6 chain, and the single-inline-FK shape.

## Scope
**Release unit**: canonical-version-6

## Assumptions
- The doc is documentation-only; this Plan edits prose only, never the schema or code. The corrected prose must stay consistent with `scripts/eventbus/schema.sql` (version stamp 6, single inline `PRIMARY KEY REFERENCES`, no duplicate `FOREIGN KEY`), `scripts/eventbus/migrations.py` (the three ordered steps), and `scripts/shared/eventbus_schema_fingerprint.py` (`validate_canonical`).
- The stale passage is the single paragraph at L32 plus the "Recreate procedure" intro at L36; the rest of the document (JSONL archive, replay, consistency checks) is unchanged and stays valid.
- ADR-008 was amended 2026-10-30 (source dbmig001) to adopt forward-only migrations recorded in the `schema_migrations` ledger, so "no migration mechanism" is already false; this Plan makes the eventbus passage explicit about the three-step chain.

## Design decisions
- Replace the one stale L32 paragraph in place: update the version literal, rename the version-era descriptions to the version-6 chain, and fold in the three paths, the fingerprint contract, and the FK shape as short follow-up sentences — keeping the document's existing narrative flow.
- Correct the "ADR-008: no migration mechanism" clause to the registered forward-only path (`create_eventbus_schema` validates before any mutation; unmapped versions still fall back to recreation per ADR-008), so the doc no longer asserts a policy the amendment removed.

## Alternatives considered
- Rewriting the whole Schema section: rejected — the stale surface is one paragraph; a targeted edit keeps the diff reviewable and avoids re-introducing drift elsewhere.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Edit the Schema paragraph (L32): change `PRAGMA user_version = 3` to `PRAGMA user_version = 6`; restate the version-era sentence so version 6 names the version-6 chain (`3 -> 4 -> 5 -> 6`: ledger baseline, outbox, FK-dedup rebuild) rather than "Version 3"; and add one sentence describing the three paths (`create_eventbus_schema` creates a fresh DB, validates an existing DB with `validate_canonical` before any stamp, and refuses an unmapped version).
2. In the same paragraph, replace "(the policy is ADR-008: no migration mechanism)" with a statement that ADR-008 now registers a forward-only migration for unmapped versions and that recreation remains the fallback for a refused database.
3. Add a short bullet after the paragraph documenting the fingerprint contract: canonical identity is `PRAGMA user_version` (6) plus the structural fingerprint (tables, columns, indexes, constraints, foreign keys, triggers) compared by `assert_matches`; a version mismatch or shape deviation is refused before any write.
4. Add a short bullet documenting the FK shape: `dlq_outbox` has a single inline `PRIMARY KEY REFERENCES events(event_id)`; the duplicate table-level `FOREIGN KEY` was removed so `PRAGMA foreign_key_list(dlq_outbox)` returns exactly one entry.

### Method
- One in-place paragraph edit plus two appended bullets under the Schema section; no other section is touched. The bullets reuse the document's existing terse style.

### Details
- Pre-change anchors: L30 (partial unique index `idx_events_redelivered_from`), L32 (stale version paragraph), L36 (recreate procedure intro).
- The corrected version literal must match `schema.sql` L75 exactly; if that file is later re-stamped, the doc follows.
- Layering unchanged: this doc references `scripts/db/create_schema.py::create_eventbus_schema()` and `shared.eventbus_schema_fingerprint` as external docs only; no code change.

### Companion test files
- None: this is a documentation correction; the schema/fingerprint behavior it now describes is covered by the code rows' tests.

## Compatibility considerations
- N/A: prose-only edit; no caller, import, or schema is affected.

## Security considerations
- N/A: no behavioral change; the corrected text only describes the existing fail-closed validate-before-write contract.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Docs/ADR checkers: `uv run python tools/check_docs.py` and the ADR checkers named in `routing.md` Tools "When to run which tool"; expect zero findings.

## Completion criteria
- The Schema section states `PRAGMA user_version = 6`, the three create/validate/migrate paths, the fingerprint contract, the version-6 chain, and the single-inline-FK shape; "ADR-008: no migration mechanism" is replaced by the registered forward-only path with recreation as fallback.
- `check_docs.py` / ADR checkers report no findings.

## Out of Scope
- The `schema.sql` version bump and FK removal (seq 02), the 5 -> 6 rebuild step (seq 03), the fingerprint contract code (seq 04), the `create_eventbus_schema` three-path rewrite (seq 01), the equivalence/convergence tests (the test row), and the db_03 eventbus migration passage correction (seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | docs-only row; no tests |
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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`
