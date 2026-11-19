## Goal
- Make the EventBus report every background task it depends on, so a stopped authorization sweep degrades `/health` and liveness; remove the confirmed dead and duplicate code (`_ENVELOPE_SCHEMA_PATH`, the second `hashlib` import and fingerprint helper, the always-zero `db_tools version`, the mislabeled outbox comment); and defer the schema task to an owner decision because it forces a database recreation.

## Priority
Medium

## Scope
- **In-Scope**:
  - `/health` reports the authorization sweep task state and its last cycle result and time; a stopped sweep adds a degraded reason and sets liveness to false, and a failing sweep cycle adds a degraded reason without changing liveness (REQ-001).
  - The sweep loop records its last cycle result and time, the lifespan initializes that state, and shutdown tolerates a background task that already ended with an exception (REQ-002).
  - Remove `_ENVELOPE_SCHEMA_PATH` from `app.py` and every test reference (REQ-003).
  - Remove the duplicate `hashlib` import and the duplicate fingerprint helper in `auth.py` (REQ-004).
  - Correct the `dlq_outbox` direction comment in `schema.sql`, a comment-only edit (REQ-005).
  - Remove `db_tools version` and `schema_version()` with their tests (REQ-006).
  - Update the documents that describe `/health` and the readiness gate (REQ-007).
  - Regenerate the generated manifests and the reference block (REQ-008).
- **Out-of-Scope**:
  - The schema task: a dedicated NACK idempotency column, a foreign key from `consumer_delivery` to `events`, and dropping `idx_events_seq`. Each changes the DDL, and a DDL change refuses every existing database (ADR-008 Decision Details 22). It is UNK-01, with an option table in Design.
  - Authorization model changes.
  - Broadening the exception handling of `authz_sweep_loop` (UNK-02).
  - Any DDL change to `schema.sql`.
- **Dependencies**: The data lifecycle issue (adrchk008) and the authorization model issue (adrchk002) are closed; the latter's `auth.py` change (the middleware rename) is already in the tree and does not touch the duplicate helper. The contract manifest sources issue (adrchk014) is open and touches the same generated manifests; it is a sequencing-only overlap (UNK-05).

## Background
The issue was filed from a consolidated ADR review whose claims carry the evidence label `Documentation only`. Step 2 re-verified each claim against current source; the verdicts are in Design. The authorization sweep is a lifespan task started beside the DLQ task, but `/health` monitors only the DLQ task.

## Problem
Confirmed in current source: `authz_sweep_loop` catches only `OSError` and `ValueError`, so any other exception ends the task silently; `/health` computes liveness from the DLQ task alone, so a dead sweep leaves expired grants active with no signal; `_shutdown_lifespan` awaits a task that may already hold an exception, which would abort shutdown before the broker and database are closed; `app.py` carries an unused `_ENVELOPE_SCHEMA_PATH`; `auth.py` imports `hashlib` twice and keeps two fingerprint helpers; `db_tools version` always prints 0; the `schema.sql` comment names the wrong direction for the outbox. The claim that the NACK key lives in a column with a different meaning is narrowed (see Design).

## Reason for Change
The issue's Implementation Intent requires that `/health` reports every background task and that no dead code remains. The no-decision subset can land now; the DDL subset cannot, because it forces archiving and recreating the production database.

## Implementation Intent
Add the sweep task to the health contract with the same shape as the DLQ task (task state, last result and time, a stopped reason, a failing reason), write the failing tests first, then remove the dead code in small revertable steps and regenerate the derived artifacts.

## Requirements
- `REQ-001`: `/health` reports `authz_sweep_task` (`running` or `stopped`) and `last_authz_sweep` (`result` and `time`); a stopped sweep adds the degraded reason `authz_sweep_task_stopped` and sets `liveness` to false; a failed last cycle adds `authz_sweep_failing` without changing `liveness`.
- `REQ-002`: `authz_sweep_loop` records the result (`ok` or `failed`) and time of each cycle on `app.state`; the lifespan initializes both to `not_run` and `None`; `_shutdown_lifespan` logs a background task that ended with an exception and continues closing the broker and the database.
- `REQ-003`: `_ENVELOPE_SCHEMA_PATH` no longer exists in `scripts/eventbus/app.py`, and no test sets or patches it.
- `REQ-004`: `auth.py` has one module-level `hashlib` import and one fingerprint helper (`_derive_token_fingerprint`); the principal map builds fingerprints through it, with identical values.
- `REQ-005`: The `dlq_outbox` comment in `schema.sql` states that the outbox records requests to generate DLQ artifacts for events promoted into the DLQ; no DDL statement changes.
- `REQ-006`: `db_tools` has no `schema_version()` and no `version` subcommand; the tests that used them are updated.
- `REQ-007`: The health endpoint guide, the ADR-006 monitoring bullets, the deployment guide's readiness sentence, and the readiness comment in `setup_services.sh` describe the extended health contract.
- `REQ-008`: `registry/manifests/eventbus_api.yaml`, `registry/manifests/db_schema_versions.yaml`, and the guarded block of `docs/24_eventbus/eventbus_08_reference_api.md` are regenerated, not hand-edited.

## Implementation Target Files
**Freeze status**: Frozen (set to `Frozen` only once `issue-to-plan` Step 8's
Implementation Target Files Validation passes — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/authz_ttl.py` | Modify | Record the last cycle result and time on `app.state` in `authz_sweep_loop` | REQ-002 / AC-3 | The loop catches only `OSError` and `ValueError` and keeps no state, while `_dlq_loop` records `last_dlq_cycle_result` and `last_dlq_cycle_time` (checked in Step 2) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `scripts/eventbus/health_route.py` | Modify | Report the sweep task state and last cycle, add the two degraded reasons, include the sweep task in liveness | REQ-001 / AC-1, AC-2 | `health_check` derives liveness from `dlq_task_status` only and reports no sweep field (checked in Step 2) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `scripts/eventbus/app.py` | Modify | Initialize the sweep state in the lifespan, tolerate a failed task at shutdown, remove `_ENVELOPE_SCHEMA_PATH` | REQ-002, REQ-003 / AC-3, AC-4 | `lifespan` creates `authz_sweep_task` without state; `_shutdown_lifespan` awaits it catching only `CancelledError`; `_ENVELOPE_SCHEMA_PATH` has no reader in `scripts` (checked in Step 2) | `tests/eventbus/eventbus_helpers.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_app_isolation.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, `tests/eventbus/test_eventbus_route_helpers_metrics.py`, `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/auth.py` | Modify | Delete the nested `import hashlib` and the nested `_fingerprint`; call `_derive_token_fingerprint` | REQ-004 / AC-5 | `_build_principal_map` defines a nested `_fingerprint` with its own `import hashlib` beside module-level `_derive_token_fingerprint`, both computing the same SHA-256 prefix (checked in Step 2) | `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py` | Verified |
| `scripts/eventbus/db_tools.py` | Modify | Remove `schema_version()` and the `version` subcommand | REQ-006 / AC-7 | `schema_version()` applies the DDL in memory and returns `PRAGMA user_version`, always the SQLite default because the DDL stamps no version; the only consumers are tests and the generated reference (checked in Step 2) | `tests/eventbus/test_eventbus_db_tools.py` | Verified |
| `scripts/eventbus/schema.sql` | Modify | Correct the `dlq_outbox` comment (comment only) | REQ-005 / AC-6 | The comment says "DLQ->replay promotion requests" while `insert_outbox_row` runs in the transaction that sets `dlq_at`, so requests describe promotion into the DLQ; `shared/schema_fingerprint.py` strips `--` comments before comparing (checked in Step 3) | `tests/eventbus/test_eventbus_schema_version.py` | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Document the new fields, reasons, and the liveness definition | REQ-007 / AC-8 | The guide defines liveness as the DLQ sweep task only and lists the reasons without a sweep entry (checked in Step 2) | N/A: documentation only; checkers in Validation plan | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Add the sweep task state and reasons to the Runtime Monitoring bullets | REQ-007 / AC-8 | The Runtime Monitoring section lists DLQ task state and the alert reasons `db_unavailable`, `dlq_task_stopped` and others (checked in Step 3) | N/A: documentation only; checkers in Validation plan | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Align the readiness-gate sentence with the script's `liveness and readiness` predicate | REQ-007 / AC-8 | The sentence states the predicate as `db == ok` AND `dlq_task == running`, while `setup_services.sh` reads the `liveness` and `readiness` fields (checked in Step 3) | N/A: documentation only; checkers in Validation plan | Verified |
| `deploy/setup_services.sh` | Modify | Update the readiness-gate comment that defines liveness (comment only; fallout of REQ-001, not in the issue's Target Files) | REQ-007 / AC-8 | The comment says "liveness: the DLQ task is running" (checked in Step 3) | `bash -n deploy/setup_services.sh` | Verified |
| `registry/manifests/eventbus_api.yaml` | Modify | Regenerate after the `db_tools` removal; never hand-edit | REQ-008 / AC-9 | The manifest lists the public functions of `scripts/eventbus`, including `schema_version` (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Regenerate the guarded block; never hand-edit | REQ-008 / AC-9 | The guarded block lists `schema_version` (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/db_schema_versions.yaml` | Modify | Regenerate after the `schema.sql` comment edit; never hand-edit | REQ-005, REQ-008 / AC-9 | The manifest records `content_hash` as the SHA-256 of the whole `schema.sql` text, so a comment edit drifts it (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Add loop-state tests; drop the `_ENVELOPE_SCHEMA_PATH` patches | REQ-002, REQ-003 / AC-3, AC-4 | The file patches `_ENVELOPE_SCHEMA_PATH` in two restart tests and has no test of the loop's recorded state (checked in Step 3) | `tests/eventbus/test_authz_generation_ttl.py` | Verified |
| `tests/eventbus/test_eventbus_health.py` | Modify | Add the sweep-stopped, sweep-failing, and shutdown tests; drop the patch | REQ-001, REQ-002, REQ-003 / AC-1, AC-2, AC-3, AC-4 | Existing health tests cover the DLQ task stopped and failing cases and patch `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `tests/eventbus/eventbus_helpers.py` | Modify | Drop the two `_ENVELOPE_SCHEMA_PATH` patches | REQ-003 / AC-4 | `make_eventbus_client` and `eventbus_two_lifecycle_clients` patch the attribute (checked in Step 3) | `tests/eventbus/test_eventbus_startup.py` | Verified |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Drop the patch | REQ-003 / AC-4 | The fixture patches `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `tests/eventbus/test_eventbus_app_isolation.py` | Modify | Drop the patch | REQ-003 / AC-4 | The fixture patches `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_app_isolation.py` | Verified |
| `tests/eventbus/test_eventbus_replay_pagination.py` | Modify | Drop the patch | REQ-003 / AC-4 | The fixture patches `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_replay_pagination.py` | Verified |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Modify | Drop the patch | REQ-003 / AC-4 | The fixture patches `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Verified |
| `tests/eventbus/test_eventbus_offsets.py` | Modify | Drop the patch | REQ-003 / AC-4 | The fixture patches `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_offsets.py` | Verified |
| `tests/eventbus/test_eventbus_restart_resume.py` | Modify | Drop the two patches | REQ-003 / AC-4 | Two fixtures patch `_ENVELOPE_SCHEMA_PATH` (checked in Step 3) | `tests/eventbus/test_eventbus_restart_resume.py` | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Drop the plain assignment to `_ENVELOPE_SCHEMA_PATH` | REQ-003 / AC-4 | The local-app fixture assigns the attribute directly (checked in Step 3) | `tests/eventbus/test_eventbus_auth.py` | Verified |
| `tests/eventbus/test_eventbus_db_tools.py` | Modify | Remove the version assertions; compare the fresh database version with the unstamped default | REQ-006 / AC-7 | `TestEnsure` and `TestCli` call `db_tools.schema_version()` and the `version` subcommand (checked in Step 3) | `tests/eventbus/test_eventbus_db_tools.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/delivery_repo.py` | `nack_event` compares the stored `consumer_last_nack_attempt` with the caller key; confirms the NACK key storage (UNK-01) | UNK-01 |
| `scripts/eventbus/ack_route.py` | The NACK route passes the caller key unchanged | UNK-01 |
| `scripts/eventbus/dlq_repo.py` | `insert_outbox_row` runs inside the promotion transaction; evidence for the outbox direction | REQ-005 |
| `scripts/eventbus/dlq.py` | Promotion callers of `insert_outbox_row` | REQ-005 |
| `scripts/shared/schema_fingerprint.py` | Strips `--` comments before comparing, so a comment edit keeps the fingerprint | REQ-005 |
| `tools/generate_reference_table.py` | Computes `content_hash` and the manifests that REQ-008 regenerates | REQ-008 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Decision Details 22 (recreate on shape mismatch) and 23 (retention accepted risk) | UNK-01 |
| `docs/00_governance/governance_01_documentation-policy.md` | A wording or evidence edit does not reopen ADR approval | REQ-007, UNK-03 |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Mentions the DLQ health reasons only; no sweep change needed | REQ-007 |
| `config/eventbus.toml` | Owns the sweep interval; no change | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): With the sweep stubbed to raise `RuntimeError`, `/health` returns 503, `degraded_reasons` contains `authz_sweep_task_stopped`, `authz_sweep_task` is `stopped`, and `liveness` is false.
- AC-2 (REQ-001): A failed sweep cycle makes `/health` return 503 with `authz_sweep_failing` while `liveness` stays true; a healthy start returns 200 with `authz_sweep_task` `running` and `last_authz_sweep.result` `not_run` or `ok`.
- AC-3 (REQ-002): After each cycle the loop has set the result and time; the lifespan initializes `not_run` and `None`; shutdown with a sweep task that ended with an exception still shuts down the broker and closes the database.
- AC-4 (REQ-003): `rg "_ENVELOPE_SCHEMA_PATH" scripts tests` finds nothing and the eventbus suite passes.
- AC-5 (REQ-004): `auth.py` has exactly one `import hashlib` and one fingerprint helper; principal fingerprints are unchanged (existing tests pass).
- AC-6 (REQ-005): The `schema.sql` diff touches comment lines only, and the shape tests (`test_eventbus_schema_version.py`) pass unchanged.
- AC-7 (REQ-006): `rg "schema_version\(\)|\"version\"" scripts/eventbus/db_tools.py` finds nothing; the updated tests pass.
- AC-8 (REQ-007): The guide lists the new fields, both reasons, and the extended liveness; the ADR-006 bullets, the deployment sentence, and the script comment agree; the docs checkers pass.
- AC-9 (REQ-008): `uv run python tools/generate_reference_table.py --check` exits 0.
- AC-10: `uv run vulture scripts/eventbus --min-confidence 80` reports nothing, as it does at baseline; the issue's vulture criterion is vacuous because vulture does not report an unused module constant at that confidence, so AC-4, AC-5, and AC-7 carry the real checks.
- Not covered by this Plan: the issue's criterion "after the schema task, the fingerprint tests pass" and the schema task itself (UNK-01).

## Tests
- REQ-001: new tests in `test_eventbus_health.py` (stopped sweep, failing sweep, healthy fields), written first and failing before the change.
- REQ-002: new loop-state tests in `test_authz_generation_ttl.py`; a shutdown test in `test_eventbus_health.py` that stubs the sweep to raise and checks the database is closed.
- REQ-003: existing eventbus suite after the patch removals.
- REQ-004: existing `test_eventbus_auth.py` and `test_eventbus_config.py` guard the refactor; behavior does not change.
- REQ-005: existing `test_eventbus_schema_version.py` shape tests.
- REQ-006: updated `test_eventbus_db_tools.py`.
- REQ-007, REQ-008: documentation, script comment, and generated artifacts, verified by the checkers in the Validation plan.

## Documentation Impact
Yes. The EventBus health endpoint guide (REQ-007), the ADR-006 Runtime Monitoring bullets, and the deployment guide's readiness sentence; target docs via `docs/00_index.md` "Document References by Task" (Event Bus rows) and the deployment guide. The generated reference block and manifests are regenerated (REQ-008).

## Assumptions
- A stopped sweep task sets liveness to false, and a failing cycle does not, mirroring the DLQ task and `dlq_sweep_failing` (the issue states the parity).
- `authz_sweep_loop` keeps catching only `OSError` and `ValueError`; detection of any other exception comes from the task state, not from broadening the handler (UNK-02).
- Phase 2 adds no new public top-level symbol to `scripts/eventbus`, so only the `db_tools` removal changes `eventbus_api.yaml`; falsified if the implementer adds a public helper.
- A comment-only edit to `schema.sql` leaves the structural fingerprint unchanged because the shared fingerprint strips `--` comments; it changes `content_hash` in `db_schema_versions.yaml`, which REQ-008 regenerates.
- ADR-008 Decision Details 23 is the recorded data lifecycle decision; it accepts unbounded growth and does not approve any DDL change.
- Editing the ADR-006 Runtime Monitoring bullets is a wording and evidence edit that does not reopen approval (`governance_01_documentation-policy.md`); falsified if `check_adr_preservation.py` reports a Decision or Invariant change (UNK-03).
- The `deployment_01_deployment.md` sentence is aligned with what the script already reads (`liveness` and `readiness`); it changes no deployment behavior.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The schema task: a dedicated NACK idempotency column, a foreign key from `consumer_delivery` to `events`, and dropping `idx_events_seq`. Each changes the DDL and refuses every existing database; ADR-008 Decision Details 22 allows no migration, so the production database would be archived and recreated without its data. The claim that the NACK key sits in a column with a different meaning is narrowed: `consumer_last_nack_attempt` already holds the delivery-attempt key and ADR-006, two guides, and many tests document it under that name | An owner decision on recreating the production database and on whether the rename and the foreign key are worth it | Owner picks from the option table in Design; a follow-up Plan carries the DDL, test, doc, and recreation steps | False |
| UNK-02 | Whether `authz_sweep_loop` should also survive other exceptions instead of ending the task | Owner preference between visibility only (this Plan) and self-healing | Owner decides; a follow-up change would add a handler and a test | False |
| UNK-03 | Whether the ADR-006 monitoring edit needs an approval record | The result of `check_adr_preservation.py` on the edit | Run it in the documentation phase; stop and ask if it reports a Decision change | False |
| UNK-04 | Whether a failed `authz_sweep_failing` state should also stay set after one later successful cycle (it clears on the next `ok` cycle, as `dlq_sweep_failing` does) | None; recorded for the owner | Accept the parity behavior unless the owner objects | False |
| UNK-05 | Landing order against the contract manifest sources issue (adrchk014), which touches the same generated manifests | Owner order decision | Sequencing only; the later change regenerates the manifests | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/authz_ttl.py` | Modify | Low: one loop | 3 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/health_route.py` | Modify | Medium: every health consumer including the deploy gate | 7 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Medium: lifespan and shutdown | 18 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/auth.py` | Modify | Low: one function body | 10 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/db_tools.py` | Modify | Low: operator tool | 2 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `scripts/eventbus/schema.sql` | Modify | Low: comment only | 11 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Low | 5 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium: cited by ADR checkers | 17 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | Low | 14 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `deploy/setup_services.sh` | Modify | Low: comment only | 9 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low: generated | 12 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low: generated block | 25 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `registry/manifests/db_schema_versions.yaml` | Modify | Low: generated | 12 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_authz_generation_ttl.py` | Modify | Low | 6 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_health.py` | Modify | Low | 7 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/eventbus_helpers.py` | Modify | Medium: shared by many suites | 9 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_admin_topics_authorization.py` | Modify | Low | 14 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_app_isolation.py` | Modify | Low | 3 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_replay_pagination.py` | Modify | Low | 3 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Modify | Low | 4 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_offsets.py` | Modify | Low | 5 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_restart_resume.py` | Modify | Low | 8 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | Modify | Low | 16 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_db_tools.py` | Modify | Low | 2 | N/A: git-fame failed with a KeyError | not applicable (rsynced) |

## Design
**Classification**: Path B (more than 3 files).

**Adversarial verification outcomes (Step 2)**

| Issue claim | Verdict | Evidence |
|---|---|---|
| `authz_sweep_loop` catches only `OSError` and `ValueError`, so any other exception ends the task | Confirmed | `authz_ttl.py` |
| `/health` monitors only the DLQ task | Confirmed | `health_route.py` derives liveness and the task field from `dlq_task` alone |
| A dead sweep leaves expired grants active with no signal | Confirmed | No health field or log path reports the sweep |
| The NACK key is stored in a column with a different meaning | Narrowed | `consumer_last_nack_attempt` holds the delivery-attempt key; `nack_event` compares it with the caller key; ADR-006 and two guides document it; only the name is imprecise |
| `consumer_delivery` has no foreign key to `events` | Confirmed | `schema.sql`; `ack_route.py` states that an unknown event can still insert a delivery row |
| `_ENVELOPE_SCHEMA_PATH` is unused in `app.py` | Confirmed, with a consequence | No reader in `scripts`, but ten test files set or patch it, and `monkeypatch.setattr` fails on a missing attribute |
| `idx_events_seq` duplicates the primary key | Confirmed | `seq` is `INTEGER PRIMARY KEY`, the rowid alias |
| The outbox comment states the wrong direction | Confirmed | The `schema.sql` comment says "DLQ->replay"; the rows are inserted in the promotion transaction |
| `db_tools version` always returns 0 | Confirmed | `schema_version()` reads `user_version` after an in-memory apply, and no DDL stamps a version |
| `auth.py` imports `hashlib` twice and has two fingerprint helpers | Confirmed | Nested `_fingerprint` with its own import beside module-level `_derive_token_fingerprint` |
| `vulture --min-confidence 80` reports the listed items | Refuted | It reports nothing at baseline; unused constants are 60 percent confidence |
| The schema task waits only on the data lifecycle decision | Narrowed | The decision (ADR-008 Decision Details 23) accepts unbounded growth; the DDL changes need a recreation decision (UNK-01) |
| Shutdown handles a failed background task | Refuted (new finding) | `_shutdown_lifespan` awaits the task catching only `CancelledError`, so a task that ended with an exception aborts shutdown before the broker and database are closed |

**Health contract (REQ-001, REQ-002)**: the sweep state mirrors the DLQ state. The loop writes `last_authz_sweep_result` (`ok` or `failed`) and `last_authz_sweep_time` (ISO-8601 from `now_iso`) after each cycle; the lifespan initializes `not_run` and `None`. `/health` adds `authz_sweep_task`, `last_authz_sweep`, and the reasons `authz_sweep_task_stopped` (liveness false) and `authz_sweep_failing` (503 only). Detection of an unexpected exception comes from the task state, so the handler stays as it is (UNK-02). Keep the state inline on `app.state` and use only private helpers, so the public symbol set of `scripts/eventbus` does not change.

**Test approach**: stub `sweep_expired_authorizations` in `eventbus.authz_ttl` to raise `RuntimeError` before the lifespan starts, wait until `app.state.authz_sweep_task.done()` is true, then read `/health` (AC-1). The shutdown test confirms the database closes although the sweep task holds an exception. Shutdown stops each task, catches `asyncio.CancelledError` separately, and for any other exception logs it and continues.

**`db_tools version`**: remove it. ADR-008 Decision Details 22 states that version stamping is not supported, so a version command has no meaning; the alternative of stamping a version contradicts that decision.

**`schema.sql` comment**: change the comment so it says the outbox records requests to generate DLQ artifacts for events promoted into the DLQ. The structural fingerprint ignores `--` comments, so the shape check is unchanged, but `content_hash` in `db_schema_versions.yaml` hashes the whole file and is regenerated.

**Option table for the schema task (UNK-01), no behavior change in this Plan**

| Option | Effect | Risk | Effort |
|---|---|---|---|
| A: leave the schema as it is | No recreation; the redundant index and the imprecise column name stay | None | None |
| B: drop `idx_events_seq` only | Removes one redundant index | Refuses every existing database, so the production database is archived and recreated without its data | Medium |
| C: rename the key column, add the foreign key, drop the index in one recreation window | Clean names and integrity | Same recreation cost; edits ADR-006, two guides, and many tests; enforcing the foreign key changes how an ACK of an unknown event behaves | High |

**Consumer scan (`tools/scan_change_consumers.py`)**: seeds `_ENVELOPE_SCHEMA_PATH`, `schema_version`, `last_dlq_cycle_result`. The direct consumers of `_ENVELOPE_SCHEMA_PATH` are the ten test files above; the `schema_version` matches outside `db_tools` belong to other databases' own accessors and are not affected; `last_dlq_cycle_result` is read by `health_route.py` and its tests, which stay unchanged.

**Validation quality baseline (Step 5)**: `radon cc` grade C or worse: `health_check` C(19) (grows with this change; mitigated by a private helper), `sweep_expired_authorizations` C(13) untouched, `_build_principal_map` C(15) shrinks; `vulture` at confidence 80 reports nothing; `bandit` reports no medium or high finding for `scripts/eventbus`; the diff-cover baseline is N/A because the clean tree has no diff against master, and the 90 percent threshold applies after implementation. Architecture: `lint-imports` keeps its contracts and the change adds no import across layers. Persisted schema check: no DDL, schema version, or migration changes (the comment edit and the accessor removal do not alter the persisted shape), so `rules/persisted-schema-change.md` items are not applicable.

## Implementation steps
1. **Phase 1: Failing tests first** (release unit `eventbus-supervision-and-cleanup`)
   - [ ] Write the sweep-stopped, sweep-failing, healthy-field, and shutdown tests and confirm they fail (REQ-001, REQ-002; `tests/eventbus/test_eventbus_health.py`)
   - [ ] Write the loop-state tests and confirm they fail (REQ-002; `tests/eventbus/test_authz_generation_ttl.py`)
2. **Phase 2: Supervision**
   - [ ] Record the last cycle result and time in the loop (REQ-002; `scripts/eventbus/authz_ttl.py`)
   - [ ] Initialize the state and make shutdown tolerate a failed task (REQ-002; `scripts/eventbus/app.py`)
   - [ ] Report the sweep task, add the reasons, extend liveness (REQ-001; `scripts/eventbus/health_route.py`)
3. **Phase 3: Dead-code cleanup**
   - [ ] Drop the `_ENVELOPE_SCHEMA_PATH` patches in the eight test files, then remove the constant (REQ-003; `tests/eventbus/eventbus_helpers.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_app_isolation.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, `tests/eventbus/test_eventbus_route_helpers_metrics.py`, `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_auth.py`, `scripts/eventbus/app.py`)
   - [ ] Remove the duplicate import and helper (REQ-004; `scripts/eventbus/auth.py`)
   - [ ] Remove `schema_version()` and the `version` subcommand and update the tests (REQ-006; `scripts/eventbus/db_tools.py`, `tests/eventbus/test_eventbus_db_tools.py`)
   - [ ] Correct the outbox comment (REQ-005; `scripts/eventbus/schema.sql`)
4. **Phase 4: Documentation**
   - [ ] Document the health fields, reasons, and liveness (REQ-007; `docs/24_eventbus/eventbus_10_health_endpoint.md`)
   - [ ] Update the ADR-006 monitoring bullets and run `check_adr_preservation.py` (REQ-007; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Align the readiness sentence and the script comment (REQ-007; `docs/90_deployment/deployment_01_deployment.md`, `deploy/setup_services.sh`)
5. **Phase 5: Regenerate derived artifacts**
   - [ ] Run `uv run python tools/generate_reference_table.py --manifests`, then `--check`, and confirm only the three expected files changed (REQ-008; `registry/manifests/eventbus_api.yaml`, `docs/24_eventbus/eventbus_08_reference_api.md`, `registry/manifests/db_schema_versions.yaml`)
6. **Phase 6: Deployment & Verification**
   - [ ] Run the Validation plan, commit and push, then hand off to `skills/deploy/SKILL.md`; deploying is the user's decision and requires the change to be committed and pushed first (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006; `scripts/eventbus/health_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/authz_ttl.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/db_tools.py`)

### Release units
**Unit**: eventbus-supervision-and-cleanup | **Phases**: 1, 2, 3, 5 | **Reason**: Phase 1 tests fail until Phase 2 lands; Phase 3 removes `_ENVELOPE_SCHEMA_PATH` (a patch left behind fails) and the `db_tools` accessor and edits `schema.sql`, so `generate_reference_table.py --check` and the CI lint job fail on manifest drift until Phase 5 regenerates them.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/` Python files | Unit and integration | `uv run ruff format --check` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit -r scripts/ -c pyproject.toml -ll`; `PYTHONPATH=scripts uv run lint-imports`; `uv run radon cc scripts/eventbus/health_route.py -s -n C` | No findings; `health_check` complexity does not rise above its baseline grade |
| `tests/eventbus/` | Unit and integration | `uv run pytest tests/eventbus -v`; `rg "_ENVELOPE_SCHEMA_PATH" scripts tests` | All pass; no match |
| Diff-scoped coverage | Coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent on changed lines |
| Dead code | Static | `uv run vulture scripts/eventbus --min-confidence 80` | No output |
| Schema | Shape | `uv run python tools/check_db_separation.py`; `uv run pytest tests/eventbus/test_eventbus_schema_version.py -v` | Pass; the shape check is unchanged |
| Generated artifacts | Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Docs | Documentation | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`, `check_docs_japanese.py`, `check_adr_preservation.py`, `check_adr_structure.py` (all `uv run python tools/...`) | No findings beyond the expected wording change |
| Deploy script | Syntax | `bash -n deploy/setup_services.sh` | Exit 0 |
| ADR-cited tests | Integration | `uv run python .github/run_cited_adr_tests.py` | Pass |
| Work items | Structure | `uv run python tools/check_workitem_structure.py --file <plan>` | No findings |

## Risks
- **Risk**: `health_check` is already C(19) and gains branches → **Mitigation**: derive the task state with a private helper, keep the new code flat, and compare radon before and after.
- **Risk**: The extended liveness fails the deploy gate when the sweep task dies during startup → **Mitigation**: that is the intended signal; the lifespan creates the task, a healthy start reports `running`, and the guide documents the gate.
- **Risk**: Shutdown tolerance swallows a real error or a cancellation → **Mitigation**: handle `asyncio.CancelledError` separately, log any other exception with its task name, and test both paths.
- **Risk**: A missed `_ENVELOPE_SCHEMA_PATH` patch breaks a suite with `AttributeError` → **Mitigation**: remove the test references before the constant, and run `rg` plus the whole eventbus suite.
- **Risk**: The failing-first test is racy because the task may not have run when `/health` is read → **Mitigation**: wait for `authz_sweep_task.done()` through the client's portal before reading `/health`.
- **Risk**: Regenerating manifests pulls in unrelated drift → **Mitigation**: inspect the diff, expect only the three named files, and stop on any other.
- **Risk**: The `schema.sql` edit is mistaken for a DDL change → **Mitigation**: the diff must touch comment lines only, and the shape tests must pass unchanged.
- **Risk**: The schema task stays undone and the redundant index and column name persist → **Mitigation**: UNK-01 carries the option table and a follow-up path; none of it blocks this Plan.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing health and loop-state tests first | Completed | — | 20261119-121222 |  |
| 2 | Sweep supervision: loop state, lifespan state, health contract | Completed | — | 20261119-121222 |  |
| 3 | Dead-code cleanup, `db_tools` removal, outbox comment | Completed | — | 20261119-121222 |  |
| 4 | Health, ADR-006, deployment, and script-comment documentation | Completed | — | 20261119-121222 |  |
| 5 | Regenerate manifests and the reference block | Completed | — | 20261119-121222 |  |
| 6 | Validation, commit, and deploy hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261119-114620_01_scripts_eventbus_authz_ttl.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261119-114620_02_scripts_eventbus_health_route.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261119-114620_03_scripts_eventbus_app.py.md | 2, 3 | Procedure | Completed | — | — |
| implementations/20261119-114620_04_scripts_eventbus_auth.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261119-114620_05_scripts_eventbus_db_tools.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261119-114620_06_scripts_eventbus_schema.sql.md | 3 | Procedure | Completed | — | — |
| implementations/20261119-114620_07_docs_24_eventbus_eventbus_10_health_endpoint.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261119-114620_08_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261119-114620_09_docs_90_deployment_deployment_01_deployment.md.md | 4 | Procedure | Completed | — | — |
| implementations/20261119-114620_10_deploy_setup_services.sh.md | 4 | Procedure | Completed | — | — |
| implementations/20261119-114620_11_registry_manifests_eventbus_api.yaml.md | 5 | Procedure | Completed | — | — |
| implementations/20261119-114620_12_docs_24_eventbus_eventbus_08_reference_api.md.md | 5 | Procedure | Completed | — | — |
| implementations/20261119-114620_13_registry_manifests_db_schema_versions.yaml.md | 5 | Procedure | Completed | — | — |
| implementations/20261119-114620_23_tests_eventbus_test_eventbus_auth.py.md | 3 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261119-113711
- **Related target files**: `scripts/eventbus/authz_ttl.py`; `scripts/eventbus/health_route.py`; `scripts/eventbus/app.py`; `scripts/eventbus/auth.py`; `scripts/eventbus/db_tools.py`; `scripts/eventbus/schema.sql`; `docs/24_eventbus/eventbus_10_health_endpoint.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`; `docs/90_deployment/deployment_01_deployment.md`; `deploy/setup_services.sh`; `registry/manifests/eventbus_api.yaml`; `docs/24_eventbus/eventbus_08_reference_api.md`; `registry/manifests/db_schema_versions.yaml`; `tests/eventbus/test_authz_generation_ttl.py`; `tests/eventbus/test_eventbus_health.py`; `tests/eventbus/eventbus_helpers.py`; `tests/eventbus/test_admin_topics_authorization.py`; `tests/eventbus/test_eventbus_app_isolation.py`; `tests/eventbus/test_eventbus_replay_pagination.py`; `tests/eventbus/test_eventbus_route_helpers_metrics.py`; `tests/eventbus/test_eventbus_offsets.py`; `tests/eventbus/test_eventbus_restart_resume.py`; `tests/eventbus/test_eventbus_auth.py`; `tests/eventbus/test_eventbus_db_tools.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (report the sweep task in `/health`); Reason for Change | `scripts/eventbus/health_route.py` | Phase 2 | AC-1, AC-2 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria (RuntimeError shows 503) | `tests/eventbus/test_eventbus_health.py` | Phase 1 | AC-1, AC-2 | `uv run pytest tests/eventbus/test_eventbus_health.py` | Explicit in issue |
| REQ-002 | Required Changes (last result and time) | `scripts/eventbus/authz_ttl.py` | Phase 2 | AC-3 | `tests/eventbus/test_authz_generation_ttl.py` | Confirmed by repository evidence |
| REQ-002 | Derived: lifespan state and shutdown tolerance | `scripts/eventbus/app.py` | Phase 2 | AC-3 | `tests/eventbus/test_eventbus_health.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes (last result and time) | `tests/eventbus/test_authz_generation_ttl.py` | Phase 1 | AC-3 | `uv run pytest tests/eventbus/test_authz_generation_ttl.py` | Explicit in issue |
| REQ-002 | Derived: shutdown with a failed task | `tests/eventbus/test_eventbus_health.py` | Phase 1 | AC-3 | `uv run pytest tests/eventbus/test_eventbus_health.py` | Derived from confirmed evidence |
| REQ-003 | Required Changes (remove `_ENVELOPE_SCHEMA_PATH`) | `scripts/eventbus/app.py` | Phase 3 | AC-4 | `rg "_ENVELOPE_SCHEMA_PATH" scripts tests`; eventbus suite | Confirmed by repository evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/eventbus_helpers.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_admin_topics_authorization.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_app_isolation.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_replay_pagination.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_offsets.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_restart_resume.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests assign the constant | `tests/eventbus/test_eventbus_auth.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_authz_generation_ttl.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-003 | Derived: tests patch the constant | `tests/eventbus/test_eventbus_health.py` | Phase 3 | AC-4 | eventbus suite | Derived from confirmed evidence |
| REQ-004 | Required Changes (duplicate import and helper) | `scripts/eventbus/auth.py` | Phase 3 | AC-5 | `tests/eventbus/test_eventbus_auth.py`; ruff; mypy | Confirmed by repository evidence |
| REQ-005 | Required Changes (fix the outbox comment) | `scripts/eventbus/schema.sql` | Phase 3 | AC-6 | `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-005 | Derived: `content_hash` covers the whole file | `registry/manifests/db_schema_versions.yaml` | Phase 5 | AC-9 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-006 | Required Changes (remove or fix `db_tools version`) | `scripts/eventbus/db_tools.py` | Phase 3 | AC-7 | `tests/eventbus/test_eventbus_db_tools.py` | Confirmed by repository evidence |
| REQ-006 | Derived: tests use the accessor | `tests/eventbus/test_eventbus_db_tools.py` | Phase 3 | AC-7 | `uv run pytest tests/eventbus/test_eventbus_db_tools.py` | Derived from confirmed evidence |
| REQ-007 | Documentation Impact (health fields) | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Phase 4 | AC-8 | docs checkers | Explicit in issue |
| REQ-007 | Derived: monitoring bullets list the health reasons | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Phase 4 | AC-8 | `check_adr_preservation.py`; docs checkers | Derived from confirmed evidence |
| REQ-007 | Derived: readiness sentence names the predicate | `docs/90_deployment/deployment_01_deployment.md` | Phase 4 | AC-8 | docs checkers | Derived from confirmed evidence |
| REQ-007 | Derived: gate comment defines liveness | `deploy/setup_services.sh` | Phase 4 | AC-8 | `bash -n deploy/setup_services.sh` | Derived from confirmed evidence |
| REQ-008 | Constraints (regenerate generated files) | `registry/manifests/eventbus_api.yaml` | Phase 5 | AC-9 | `generate_reference_table.py --check` | Explicit in issue |
| REQ-008 | Constraints (regenerate guarded blocks) | `docs/24_eventbus/eventbus_08_reference_api.md` | Phase 5 | AC-9 | `generate_reference_table.py --check` | Explicit in issue |
| REQ-008 | Constraints (regenerate generated files) | `registry/manifests/db_schema_versions.yaml` | Phase 5 | AC-9 | `generate_reference_table.py --check` | Explicit in issue |
