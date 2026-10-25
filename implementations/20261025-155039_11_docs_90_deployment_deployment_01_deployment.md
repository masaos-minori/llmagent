## Goal

Correct the overstatement in `docs/90_deployment/deployment_01_deployment.md` §3.1 (`REQ-007`): replace the claim that `init_db.sh` verifies all mandatory EventBus tables and that the EventBus service refuses a different table shape with an accurate description of the shared-validator shape policy, the fail-closed behavior, and the bounded process+health readiness sequence.

## Scope

- Modify `docs/90_deployment/deployment_01_deployment.md` only, within §3.1 (Applying Schema, currently lines 296-305): correct the overstatement and document the shared-validator + readiness-gate behavior.
- Do not modify `deploy/init_db.sh`, `deploy/setup_services.sh`, `scripts/db/create_schema.py`, `scripts/eventbus/schema.py`, `scripts/shared/eventbus_schema_fingerprint.py`, or any other target here — they are the deployment/runtime targets this doc describes (`REQ-007`).

## Assumptions

- The current §3.1 text (lines 296-305) states that `init_db.sh` "Verifies all mandatory tables exist; aborts if any are missing" for the EventBus database and that "the EventBus service refuses a different version or table shape" — both overstatements. Reality is a Workflow-only table-presence check plus a shared-validator shape check for EventBus.
- After `REQ-001`/`REQ-003`, one shared validator (`scripts/shared/eventbus_schema_fingerprint.py`) defines a valid EventBus schema and is used by both the deployment path (`create_eventbus_schema()` / `init_db.sh`) and the runtime startup path (`_init_schema()` in `scripts/eventbus/schema.py`).
- After `REQ-004`, `deploy/setup_services.sh` proves EventBus process liveness and readiness with a bounded poll before reporting success.

## Design decisions

- **Correct, do not gut.** The useful facts in lines 296-305 (the four databases are created create-only, the Workflow database has mandatory tables, the schema is stamped with `PRAGMA user_version`) are kept; only the two overstatements are replaced with accurate statements of the shared-validator shape policy and the fail-closed behavior.
- **Document the shared fingerprint, not a table list.** The corrected text explains that the validator derives tables, columns (name/type/nullability/default/pk), indexes, table-level constraints, foreign keys, and triggers (if any) from `schema.sql` via `PRAGMA` on a fresh in-memory apply and raises on any mismatch even when `user_version` matches — so a correctly-stamped-but-malformed database is refused.
- **Document fail-closed equivalence and the bounded gate.** The corrected text states that the malformed database is refused both at `init_db.sh`/`create_eventbus_schema()` and at runtime startup with equivalent results, and that `setup_services.sh` treats a dead child, a persistent connection failure, a non-200, or a `status != ok` body as fatal with child cleanup while tolerating capacity-only `degraded_reasons`.

## Alternatives considered

- **Delete the "Responsibilities of init_db.sh" list entirely.** Rejected: the list conveys correct, useful facts (create-only databases, Workflow mandatory tables, version stamp); only the overstatement needs correcting, so the list is retained and amended.
- **Keep "refuses a different table shape" verbatim.** Rejected: it implies a per-table presence check; the actual mechanism is the shared-validator shape comparison, which is more precise and must be documented.

## Implementation

### Target file

`docs/90_deployment/deployment_01_deployment.md`

### Procedure

1. Open `docs/90_deployment/deployment_01_deployment.md` and locate the §3.1 "Responsibilities of init_db.sh" list and its following paragraph (currently lines 296-305).
2. Replace the bullet "Verifies all mandatory tables exist; aborts if any are missing" with a statement that the Workflow database is the only one with a table-presence check and that the EventBus database is verified by the shared validator's shape comparison instead.
3. Rewrite the concluding paragraph so it documents that the shared validator fails closed on a malformed stamped database (equivalently at runtime startup) and that `setup_services.sh` proves process liveness and readiness with a bounded poll before reporting success.

### Method

- Retain the first three bullets and the "Records the schema version" bullet unchanged; remove the fourth bullet ("Verifies all mandatory tables exist; aborts if any are missing") and add a sentence noting the Workflow database is the only one with a table-presence check.
- Insert a paragraph after the bullet list explaining the shared validator: it derives tables, columns (name/type/nullability/default/pk), indexes, table-level constraints, foreign keys, and triggers (if any) from `schema.sql` via `PRAGMA` on a fresh in-memory apply and raises on any mismatch against the target connection even when `PRAGMA user_version` matches; `create_eventbus_schema()` applies it after DDL and fails closed on a malformed database already stamped with the current version, and `init_db.sh` runs the same validator for each required database.
- State that a correctly-stamped but structurally malformed EventBus database is refused both at `init_db.sh`/`create_eventbus_schema()` and at runtime startup (`_init_schema()` in `scripts/eventbus/schema.py`), with equivalent results.
- Rewrite the final sentence so "the EventBus service refuses a different version or table shape" becomes: the service proves process liveness and readiness before reporting success — the bounded poll treats a dead child, a persistent connection failure, a non-200, or a `status != ok` body as fatal with child cleanup and last-response logging, while tolerating capacity-only `degraded_reasons` (`lock_wait_high`, `slow_consumers_detected`, `query_duration_high`, `broker_queue_backlog_high`, `subscribers_at_capacity`) so a healthy start on transient degradation is not summarized as a failure.
- Keep the surrounding facts intact: a workflow or EventBus database older than the current schema is recreated, not migrated (archive first with `rotate_all_dbs()`, delete, then run `init_db.sh`), and the workflow definition must not contain `require_approval` (the loader rejects the key).

### Details

- The corrected text cites the shared validator by its full path `scripts/shared/eventbus_schema_fingerprint.py` and the capacity reasons by the exact strings `scripts/eventbus/health_route.py` publishes, so the doc matches the implementation rather than the old overstatement.
- The fail-closed equivalence is stated without overclaiming: the malformed database is refused at both the deployment and runtime boundaries, which is the observable behavior the acceptance criterion requires.
- The readiness-sequence description mirrors the deploy gate: readiness is `db == ok` AND `dlq_task == running`, and capacity-only degradation does not fail a healthy start.

## Compatibility considerations

- The change is confined to §3.1 prose; no headings, tables, or other sections are altered, so downstream references and the auto-generated sections are unaffected.

## Security considerations

- None: this is a documentation accuracy correction with no behavioral effect.

## Rollback considerations

- Restore the original §3.1 text (or `git checkout` the parent commit); the change is prose only.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/90_deployment/deployment_01_deployment.md` | Document review: §3.1 no longer claims an EventBus table-presence check or a generic "refuses a different table shape"; it documents the shared-validator shape policy, fail-closed equivalence, and the bounded readiness gate | manual read of §3.1 | §3.1 accurately describes the shared-validator shape policy, fail-closed rejection, and the bounded process+health readiness sequence |

## Completion criteria

- §3.1 no longer states that `init_db.sh` verifies all mandatory EventBus tables or that the EventBus service refuses a generic "different table shape".
- §3.1 documents the shared-validator shape policy, the fail-closed rejection of a correctly-stamped-but-malformed database (equivalently at runtime startup), and the bounded process+health readiness sequence in `setup_services.sh`.
- `stale_detector` passes on the corrected document.

## Out of Scope

- The shared validator implementation (`REQ-001`), the runtime startup gate (`REQ-002`), the `init_db.sh`/`create_schema.py` strict gate (`REQ-003`), and the deploy readiness gate implementation (`REQ-004`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the "verifies all mandatory tables" overstatement in §3.1 (current lines 296-305) | Pending | — | — | REQ-007 |
| 2 | Document the shared-validator shape policy and fail-closed equivalence | Pending | — | — | REQ-007 |
| 3 | Document the bounded process+health readiness sequence in `setup_services.sh` | Pending | — | — | REQ-007 |
| 4 | Run `stale_detector` on the corrected document | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this is the doc |

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
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`
