# Remove obsolete API compatibility surfaces and require current call contracts

## Priority
Medium

## Summary
Remove the `db.store` and `eventbus.db` re-export facades and the optional `consumer_id` form of `nack_event()`, and update all callers, tests, and documentation to use the responsibility-specific modules and the consumer-scoped NACK contract. They are one issue because both remove compatibility at Python call boundaries and need the same repository-wide caller migration and import and API regression checks.

## Background
Initiative issue M-1 of `memo-issue.md`. Verified 2026-11-06: `scripts/db/store.py` and `scripts/eventbus/db.py` exist, about 20 files under `scripts/`, `tests/`, and `tools/` import `db.store` or `eventbus.db`, and `nack_event()` in `scripts/eventbus/delivery_repo.py` takes `consumer_id: str | None = None` with the comment that it is internal-only because the `/nack` route always supplies it. `db.store` keeps one import surface over `store_protocols.py` and `store_impl.py`; `eventbus.db` keeps one over `db_conn.py`, `event_repo.py`, `delivery_repo.py`, and `dlq_repo.py`.

## Problem
The facades make obsolete entry points look supported and hide the real module and security boundaries. The optional `consumer_id` preserves a call pattern that cannot represent the consumer-scoped authorization and delivery-state model.

## Reason for Change
Callers should depend on the actual module boundaries, and every NACK must be tied to a validated, authenticated consumer.

## Implementation Intent
Expose only the current boundaries: storage contracts and helpers from `db.store_protocols`, SQLite implementations from `db.store_impl`, connection operations from `eventbus.db_conn`, event operations from `eventbus.event_repo`, delivery operations from `eventbus.delivery_repo`, DLQ operations from `eventbus.dlq_repo`, and every NACK associated with a validated consumer ID. No package-level alias or wrapper recreates a deleted entry point.

## Target Files or Areas
`scripts/db/store.py`, `scripts/eventbus/db.py`, every importer of those modules, `scripts/eventbus/delivery_repo.py` (`nack_event`), the EventBus NACK route, every `nack_event()` call site, the import-boundary checker configuration, and public API documentation that recommends `db.store` or `eventbus.db`.

## Required Changes
Remove the re-export facades:
- Replace every import from `db.store` and `eventbus.db` with the responsibility-specific module.
- Delete `scripts/db/store.py` and `scripts/eventbus/db.py`; add no equivalent exports to any package `__init__.py`.
- Remove facade-specific `__all__` and import-contract tests; update source comments, examples, and active documentation.

Enforce the current NACK contract:
- Make `consumer_id` a required non-empty `str` argument of `nack_event()` with no default, and remove all `consumer_id is not None` branches and the path that reports success without updating consumer delivery state.
- Update every caller to pass the authenticated consumer ID, and remove tests for the old two-argument form.
- Ensure the route validates that the requested consumer ID belongs to the authenticated principal; keep topic authorization and idempotency intact.

## Constraints
Security: a missing or empty consumer ID fails validation; a consumer ID not granted to the principal returns HTTP 403; topic authorization stays enforced; duplicate NACK idempotency keys do not increment the failure count twice; only per-consumer failure state is updated. Provide no deprecation warnings or transition aliases. The common policy of the initiative applies:

Common policy (shared by all four issues of this initiative):

1. Support only the current database schema, API, import path, and authentication model.
2. Do not provide automatic database migration, version stamping, compatibility aliases, re-export facades, or deprecated call signatures.
3. Reject incompatible existing databases before mutation.
4. Do not automatically delete an incompatible database.
5. Permit an operator to archive an incompatible database and recreate it manually.
6. Preserve rotation, archive validation, and supported corruption recovery: they protect current data and are not backward-compatibility features.
7. Prevent deleted symbols, modules, imports, and specifications from being reintroduced through CI and pre-commit checks.

## Acceptance Criteria
- [ ] `scripts/db/store.py` and `scripts/eventbus/db.py` are deleted, and no source, test, tool, or active document uses either removed import path.
- [ ] No package-level re-export recreates a removed facade; all callers import from the correct responsibility-specific module.
- [ ] `consumer_id` is a required non-empty string for `nack_event()`; no caller invokes it without `consumer_id`; no wrapper preserves the old signature.
- [ ] Unauthorized consumer IDs fail with HTTP 403; duplicate idempotency keys do not increment the failure count twice.
- [ ] Static checks reject the removed import paths and the old call form.
- [ ] The complete test suite passes.

## Testing Expectations
An AST-based repository import scan; source, test, tool, and documentation searches for the removed imports; NACK tests for missing, empty, unauthorized, valid, duplicate, and multi-consumer cases; EventBus route, repository, startup, and integration tests; `PYTHONPATH=scripts uv run lint-imports`.

## Documentation Impact
Yes: public API and architecture documents that recommend `db.store` or `eventbus.db` (name the responsibility-specific modules instead), and the NACK contract wherever it is described. Use `docs/00_index.md` "Document References by Task" to find them.

## Out of Scope
Reorganizing the responsibility-specific modules, changing EventBus ACK semantics, changing the DLQ threshold, and deprecation warnings or transition aliases.

## Dependencies
Complete before the policy-enforcement issue `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`, so that all removed paths are added to the blocking rules in one change.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Migrate all callers in the same change that deletes the facades; do not add re-exports to keep any caller working. Keep the import layer contract (`.importlinter`) passing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-125144
- **Related target files**: `scripts/db/store.py`, `scripts/eventbus/db.py`, `scripts/eventbus/delivery_repo.py`
