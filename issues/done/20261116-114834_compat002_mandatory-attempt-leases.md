# Enforce mandatory attempt leases across writer, model, schema, and tests

## Priority
High

## Summary
Remove the lease-less attempt path. The attempt writer must require a valid lease duration, the attempt model must carry the lease fields, and the canonical `attempts` schema must make `owner_id` and `lease_expires_at` `NOT NULL`. A running attempt must always be classifiable as live or expired. No migration or null-filling shim is added.

## Background
Source: `memo-issue.md` Issue 2 (items H-04, H-05, M-02, M-03), re-verified against current source.

- Explicit in code: `begin_stage_if_new()` in `scripts/agent/workflow/idempotency_ops.py` takes `lease_duration_sec: int | None = None`. When it is `None`, `owner_id` and `lease_expires_at` stay `NULL`, and the docstring labels this behavior as being for legacy callers. `StateStore.begin_stage_if_new()` in `scripts/agent/workflow/state_store.py` forwards the same optional parameter.
- Explicit in code: `WorkflowEngine` in `scripts/agent/workflow/workflow_engine.py` is the only production caller and passes `timeout + _LEASE_MARGIN_SEC`, where `_LEASE_MARGIN_SEC` is 30. No production `INSERT INTO attempts` exists outside `idempotency_ops.py` (repository search over `scripts`, `tests`, `tools`; the other hits are tests).
- Explicit in code: `scripts/db/schema_sql.py` declares `owner_id TEXT` and `lease_expires_at TEXT` as nullable.
- Explicit in code: `AttemptRecord` in `scripts/agent/workflow/models.py` has no `owner_id` or `lease_expires_at` field although its docstring calls it a database record.
- Explicit in code: `StateStore` stale recovery already decides staleness only from `lease_expires_at` (the age rule was removed under `adrrev005`, see `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md`), and it leaves lease-less rows live. Such a row therefore stays `running` forever.
- Tests that currently model the lease-less path include `tests/agent/workflow/test_workflow_state_store.py` (a lease-less case and a raw insert without lease columns) and the callers of `begin_stage_if_new()` listed in Target Files.
- The memo's paths `tests/test_workflow_state_store.py`, `tests/test_workflow_stage_persistence.py`, `tests/test_workflow_engine.py`, `tests/agent/services/test_workflow_schema.py`, and `tests/deploy/test_init_db.py` were not found; the real files live under `tests/agent/workflow/`, `tests/db/`, and `tests/deploy/`.

## Problem
A lease-less running attempt has no expiration. If the process dies after the row is created, recovery never reclaims it and the attempt stays `running` indefinitely. The canonical schema permits this invalid state, and the attempt model hides part of the persisted contract. Changing only one layer would leave a hazardous intermediate state, so the writer, model, schema, and tests must change together.

## Reason for Change
Data-integrity risk on the workflow execution path: an unrecoverable running attempt blocks the stage it belongs to. No reviewed production path needs the lease-less form, so the compatibility surface has only cost. Nothing makes the change time-sensitive beyond that risk.

## Implementation Intent
Make a running attempt inseparable from lease ownership. Every created attempt has a non-empty owner and an expiration timestamp; invalid lease durations fail before a database transaction starts; the database rejects null lease metadata as the last backstop; recovery relies only on explicit lease expiration. The writer owns lease-duration validation at the lowest public boundary so future writers reuse it. Preserve the atomic insertion of `attempts` and `processed_events` and the `timeout + 30` calculation. Do not add a migration, null-filling shim, or legacy default; an old nullable database is refused by the existing schema fingerprint gate and left unchanged.

For `AttemptRecord`, preferred: add required `owner_id` and `lease_expires_at` and populate them. Alternative, if an execution projection is intended: rename or document the type and add a separate full-row type. Choosing between them is a plan-time decision.

## Target Files or Areas
- `scripts/agent/workflow/idempotency_ops.py`
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/attempt_ops.py`
- `scripts/agent/workflow/workflow_engine.py` (confirm remains the only writer; no change to the lease calculation)
- `scripts/agent/workflow/models.py`
- `scripts/db/schema_sql.py`
- `scripts/db/create_schema.py`
- `scripts/shared/schema_fingerprint.py`
- `scripts/agent/services/workflow_schema.py`
- `deploy/init_db.sh`
- `tests/agent/workflow/test_workflow_state_store.py`
- `tests/agent/workflow/test_workflow_stage_persistence.py`
- `tests/agent/workflow/test_state_store.py`
- `tests/agent/workflow/test_stale_recovery_lease.py`
- `tests/agent/workflow/test_workflow_status_vocabulary.py`
- `tests/db/test_create_schema.py`
- `tests/db/test_schema_validation_per_database.py`
- `tests/deploy/test_init_db_schema_gate.py`

## Required Changes
- Writer: make `lease_duration_sec` a required `int`, remove the `None` branch and the legacy-caller wording, and always generate `owner_id` and `lease_expires_at`. Validate before entering the transaction and reject `None`, `bool`, zero, negative values, floats, strings, and other non-integers. A failure in owner or timestamp generation must prevent both inserts.
- Facade: make `lease_duration_sec` required in `StateStore.begin_stage_if_new()` and forward it without a default.
- Callers: inspect every `begin_stage_if_new()` call under `scripts/`, `tests/`, and `tools/`; update tests to pass an explicit lease. Confirm no production insert into `attempts` exists outside the canonical writer.
- Validation ownership: keep the strict duration check in one production function and reuse it for any future attempt writer.
- Model: apply the `AttemptRecord` decision above, update row mapping and model tests.
- Schema: declare both lease columns `NOT NULL`; add `CHECK(length(owner_id) > 0)` unless an empty owner is intentionally supported; update the schema fingerprint expectations.
- Recovery: keep recovery based on `lease_expires_at < now`; do not restore age-based recovery. Any remaining defensive handling for a manually corrupted lease-less row must classify it as invalid or missing-lease data, not a supported legacy format.
- Tests: replace lease-less success tests with required-argument and invalid-value tests; keep the live-lease, expired-lease, compare-and-swap, concurrent-recovery, processed-event-deletion, and task-reconciliation tests; use raw SQL only for tests that intentionally model corruption or a rejected old schema, and label them.

## Constraints
- No in-place migration, version stamp, nullable compatibility default, or automatic null fill; `rules/persisted-schema-change.md` governs this schema change and must be read before planning.
- Existing `workflow.sqlite` files with the old nullable shape become incompatible and must be recreated; this is accepted and documented by the documentation issue.
- `tools/check_db_separation.py` must still pass after the DDL change.
- Measure the blast radius of the signature change before editing (`rules/toolchain.md` Impact-radius check); roughly ten test files call the writer.

## Acceptance Criteria
- [ ] No public production API can create a running attempt without a lease.
- [ ] Every successful attempt insert has a non-empty `owner_id` and a non-null `lease_expires_at`.
- [ ] `None`, `False`, `True`, `0`, `-1`, `1.0`, and `"30"` as `lease_duration_sec` fail before any database mutation; a valid positive integer succeeds.
- [ ] Insertion of the attempt and its processed-event row stays atomic, including when owner or timestamp generation fails.
- [ ] `WorkflowEngine` still passes `stage timeout + 30` as the lease duration.
- [ ] `AttemptRecord` represents either the full row or an explicitly named projection.
- [ ] A fresh database defines both lease columns `NOT NULL`; raw inserts with a null lease field fail with `sqlite3.IntegrityError`.
- [ ] A database with the old nullable shape is refused by the fingerprint gate and left byte-for-byte unchanged.
- [ ] No migration or compatibility shim is introduced.
- [ ] Recovery does not use attempt age as a substitute for lease expiration.

## Testing Expectations
- Run `rg -n "begin_stage_if_new\(" scripts tests tools` and `rg -n "INSERT INTO attempts" scripts tests tools` and inspect every hit.
- Unit tests: lease-duration validation matrix; writer atomicity; model mapping; schema `NOT NULL` and `CHECK` behavior.
- Regression: workflow state-store, engine, persistence, and stale-recovery tests under `tests/agent/workflow/`; schema creation and gate tests under `tests/db/` and `tests/deploy/`.
- Manual check: `PRAGMA table_info(attempts)` on a fresh database; open an old-shape database and confirm refusal without modification.
- Run `uv run python tools/check_db_separation.py` and the validation sequence in `rules/toolchain.md`.

## Documentation Impact
Documentation must change, but it is owned by the documentation issue listed under Dependencies. This issue only requires that docstrings it touches (writer, facade, `AttemptRecord`) stop mentioning legacy callers.

## Out of Scope
- Heartbeat or lease renewal.
- Changing the `+30` second margin or the stage `timeout_sec` rules.
- Workflow-definition defaults (separate issue).
- Updating `docs/`, runbooks, or compatibility-checker rules (separate issues).
- Migrating or backfilling existing databases.

## Dependencies
- Recommended after `issues/20261116-114753_compat001_workflow-definition-strict-contract.md` (order only; not a technical dependency).
- Blocks the documentation and checker issues filed from the same source (paths recorded in those issues).
- Sibling check: no other open issue or in-flight plan touches these files. `issues/done/20261109-112715_adrrev005_schema-fingerprint-unify.md` is archived and established the fingerprint gate this issue relies on; re-verify the gate behavior against current source during planning.

## Unresolved Questions
- `AttemptRecord`: full row model or named projection? `不明`, plan-time decision.
- Is an empty `owner_id` ever intentionally supported (affects the `CHECK`)? `不明`.
- Does any other module outside the listed files read or write the `attempts` lease columns (for example under `tools/`)? `Needs confirmation`; the searches above found only the listed files.
- Whether `scripts/agent/services/workflow_schema.py` and `scripts/shared/schema_fingerprint.py` need edits beyond fingerprint expectations: `Needs confirmation`.
- The memo's `tests/agent/services/test_workflow_schema.py` and `tests/deploy/test_init_db.py` were not found; whether equivalent tests exist elsewhere: `不明`.

## AI Implementation Instruction
Change the writer, facade, model, schema, and the listed tests together in one change set; do not land the schema change alone. Preserve atomicity and the lease calculation. Do not add migrations, defaults, or shims. Do not edit `docs/` here. Stop and report if the `AttemptRecord` decision is unresolved at plan time.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261116-114834
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `scripts/db/schema_sql.py`, `scripts/db/create_schema.py`, `scripts/shared/schema_fingerprint.py`, `scripts/agent/services/workflow_schema.py`, `deploy/init_db.sh`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/agent/workflow/test_workflow_status_vocabulary.py`, `tests/db/test_create_schema.py`, `tests/db/test_schema_validation_per_database.py`, `tests/deploy/test_init_db_schema_gate.py`
