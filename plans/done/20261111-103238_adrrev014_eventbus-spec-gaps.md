## Goal
Close the verified EventBus specification gaps (the `dlq_outbox` table, the `/replay` contract and the `/subscribe` replay-start behavior in ADR-006, a foreign-key-safe manual cleanup procedure, the obsolete NACK failure row) and make the failures that the DLQ guarantee depends on (terminal outbox failures, repeatedly failing sweeps) observable through `/health`, without changing authorization, liveness, or readiness semantics.

## Priority
Medium

## Scope
- **In-Scope**: ADR-006 (Scope, Data Ownership, `/replay` and `/subscribe` replay contract, outbox observability) and the `eventbus.sqlite` content wording of ADR-008; the EventBus documents `eventbus_03`, `eventbus_05`, `eventbus_10`, `eventbus_12`; the generated reference `eventbus_08`; `/health` additions (terminal-failed outbox row count, last DLQ sweep result and time, matching degraded reasons) through `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`; tests in `tests/eventbus/test_eventbus_health.py`.
- **Out-of-Scope**: ADR-002 and ADR-013 (verified correct: the optional configuration keys have defaults and are specified in `eventbus_07`; the loading-mechanism text is consistent and the `ConfigLoader` migration is recorded as not adopted); changing `/subscribe` to support replay from the start for a Consumer with a stored offset (maintainer decision, UNK-01; the behavior is documented and `/replay` is the alternative); a metrics endpoint (maintainer decision, UNK-02); changing the HTTP status for capacity-only reasons (documented today and kept); authorization, credentials, and roles; route-handler structure; schema changes (`scripts/eventbus/schema.sql` is read-only here); approval records for a maintainer.
- **Dependencies**: N/A: none. The EventBus future-decision issue (adrrev006) is closed (EventBus kept, 2026-11-10). The EventBus authorization Plan (adrrev010) edits only ADR-013, which this Plan does not touch, so no ordering constraint remains. Sequencing note: the ADR-006 and ADR-008 edits are decision-text changes that need pending approval records, which the approval-ledger Plan (adrrev012) tracks.

## Background
EventBus keeps its contract split across ADR-006 (persistence and SSE delivery), the `docs/24_eventbus/` documents, and the code. Verification (2026-11-11) found: `dlq_outbox` (durable DLQ promotion record, `PRIMARY KEY REFERENCES events(event_id)`, status `pending`/`done`/`failed`) appears in `eventbus_03/06/08` but in no ADR, and ADR-008's `eventbus.sqlite` ownership line lists "Events, Offsets, Delivery, and the DLQ" only. The manual cleanup procedure in `eventbus_05` says "The schema defines no foreign keys" and deletes `events` without touching `dlq_outbox`, although the EventBus connection enforces foreign keys. `eventbus_12` still lists a NACK path "inline DLQ file write failed" that has not existed since dlqbox001 made promotion DB-only. `/subscribe` treats `since_seq=0` as unspecified and, for a `consumer_id` with a stored offset, resumes from it; ADR-006 does not describe this or `/replay`. `_dlq_loop` swallows `OSError` and `sqlite3.Error` per cycle, so `dlq_task` stays `running` while every sweep fails, and terminal outbox failures are only logged; `/health` shows neither. There is no `/metrics` route, so the "metered" wording in `eventbus_03` overstates observability.

## Problem
- A table and two endpoint behaviors have no authoritative ADR-level specification, so they can change unnoticed.
- A documented failure row refers to a path that no longer exists, and the manual cleanup procedure is unsafe: with foreign keys enforced it fails, and with them off (a plain `sqlite3` shell) it leaves orphan outbox rows.
- Failures that the fail-closed DLQ design depends on are invisible to operators, who see `dlq_task: running` and `status: ok` while artifact generation or sweeping keeps failing.

## Reason for Change
Unspecified behavior and unobservable failure modes are review risks on a security-relevant service; the maintainer decisions that would change behavior (full replay on `/subscribe`, metrics endpoint) are deferred, so this Plan documents current behavior and adds only the observability the guarantees need.

## Implementation Intent
Document what exists first (ADR-006, ADR-008, `eventbus_05`, `eventbus_12`), then add the smallest observability change: count terminal-failed outbox rows with one read-only query, record the result and time of each DLQ loop cycle on `app.state`, and report both from `/health` with new degraded reasons that return 503 like every other degraded reason and leave `liveness` and `readiness` unchanged.

## Requirements
- `REQ-001`: ADR-006 names `dlq_outbox` in Scope and Data Ownership (purpose, owner, status lifecycle, retention of `done` rows) and ADR-008's `eventbus.sqlite` ownership wording includes it; no table or configuration key of the EventBus is left without an ADR or referenced specification.
- `REQ-002`: ADR-006 states the `/replay` contract (Operator role only; reads any range; changes no Consumer offset) and the `/subscribe` replay-start behavior (`since_seq` takes precedence, then the Consumer's stored resume position, then `Last-Event-ID`; `since_seq=0` is "unspecified", so a Consumer with a stored offset cannot replay from the start on `/subscribe`, and `/replay` is the way to read from the start).
- `REQ-003`: The manual cleanup procedure in `eventbus_05` is foreign-key-safe (delete the dependent `dlq_outbox` rows before the `events` rows, within one transaction with foreign keys enabled) and no longer says the schema has no foreign keys.
- `REQ-004`: The obsolete NACK state row ("Initial NACK, inline DLQ file write failed") is removed from `eventbus_12`, and the surrounding text states that DLQ promotion is a DB transaction with artifact generation deferred to the outbox.
- `REQ-005`: `/health` reports the number of terminal-failed outbox rows and the result and time of the last DLQ loop cycle, adds degraded reasons for terminal-failed outbox rows and for a failing sweep, keeps HTTP 503 for every degraded reason, and leaves `liveness`, `readiness`, and authorization unchanged.
- `REQ-006`: `eventbus_10` documents the new fields, reasons, and the monitoring rule (503 for any degraded reason; `liveness` and `readiness` as the deployment gate), and `eventbus_03` replaces "metered" with what is actually observable.
- `REQ-007`: The generated reference `eventbus_08` matches the code after the new repository function (`generate_reference_table.py --check` passes).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Modify | Add a read-only function that counts `dlq_outbox` rows with status `failed` (9350 bytes) | REQ-005 / AC-5 | `dlq_outbox` row operations at lines 127-210 (`insert_outbox_row`, `get_outbox_state`); no count function exists (checked in Step 3) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `scripts/eventbus/app.py` | Modify | Record the result and time of each `_dlq_loop` cycle on `app.state` (10152 bytes) | REQ-005 / AC-5 | `_dlq_loop` at line 162 catches `OSError`/`sqlite3.Error`, logs, and sleeps; `process_outbox` returns `terminal_failed` counts; no state is stored (checked in Step 3) | `tests/eventbus/test_eventbus_health.py`, `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/health_route.py` | Modify | Report outbox terminal-failed count and last-sweep result and time, add two degraded reasons, keep 503 and liveness/readiness (4538 bytes) | REQ-005 / AC-5 | Lines 78-112: reasons list, `liveness = dlq_task_status == "running"`, `readiness = db_ok`, `status_code = 200 if overall == "ok" else 503` (checked in Step 3) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `tests/eventbus/test_eventbus_health.py` | Modify | Add tests: terminal-failed outbox rows appear and degrade; a failing sweep cycle appears and degrades; status code stays 503; liveness and readiness are unchanged | REQ-005 / AC-5 | Existing fixture builds the real app with `TestClient` and `Bearer test-token` (lines 14-40); ten existing tests (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Add `dlq_outbox` to Scope and Data Ownership; add the `/replay` contract and the `/subscribe` replay-start behavior; pending approval record | REQ-001, REQ-002 / AC-1, AC-2 | Scope at line 87, Data Ownership at line 215; `/replay` and `dlq_outbox` are not mentioned (`rg` over the ADR) (checked in Step 2) | `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py` | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Decision Detail 4 (line 117): add the promotion outbox to the `eventbus.sqlite` contents; pending approval record | REQ-001 / AC-1 | Line 117 "canonical store for Events, Offsets, Delivery, and the DLQ" (checked in Step 2) | `tools/check_db_separation.py`, `tools/check_adr_structure.py` | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Rewrite the Cleanup Procedure (lines 177-193) to be foreign-key-safe | REQ-003 / AC-3 | Lines 181-190 "The schema defines no foreign keys" and `DELETE FROM events WHERE seq <= ?;`; `schema.sql` declares `REFERENCES events(event_id)` and `schema.py` sets `PRAGMA foreign_keys=ON` (checked in Step 2; missing from the issue's target list) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Modify | Remove the obsolete state-transition row (line 74) | REQ-004 / AC-4 | Row "Initial NACK, inline DLQ file write failed"; `dlq.py` `_shared_promote_single` is DB-only since dlqbox001 (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Document the new fields, degraded reasons, and monitoring rule | REQ-006 / AC-6 | Lines 36-69 list fields, 503 rule, and reasons (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify | Replace "metered" (failure table, line 180) with the observable `/health` fields | REQ-006 / AC-6 | Line 180 "terminal `failed` after `outbox_max_attempts`; metered, logged, never blocks other events"; no `/metrics` route exists (checked in Step 2) | `tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Regenerate the guarded reference block for the new `dlq_repo.py` function | REQ-007 / AC-7 | Contains two `AUTO-GENERATED` markers and lists `dlq_repo.py` functions (line 114 `get_outbox_state`) (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/schema.sql` | The `dlq_outbox` DDL (status values, FK, index); read-only, no schema change | REQ-001, REQ-003 |
| `scripts/eventbus/schema.py` | Confirms `PRAGMA foreign_keys=ON` on the EventBus connection | REQ-003 |
| `scripts/eventbus/dlq.py` | `process_outbox` report keys and DB-only promotion | REQ-004, REQ-005 |
| `scripts/eventbus/subscribe_route.py` | `since_seq` precedence and `Last-Event-ID` fallback that ADR-006 must describe | REQ-002 |
| `scripts/eventbus/replay_route.py` | `/replay` is Operator-only and reads without changing offsets | REQ-002 |
| `scripts/eventbus/config.py` | Optional keys with defaults (`_REQUIRED_CONFIG_KEYS`); confirms ADR-002 needs no change | REQ-001 |
| `scripts/eventbus/route_helpers.py` | `run_with_db_lock` used by health and the DLQ loop | REQ-005 |
| `docs/24_eventbus/eventbus_11_replay_endpoint.md` | Existing `/replay` specification that ADR-006 points to | REQ-002 |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Existing `dlq_outbox` schema description and the single inline FK | REQ-001, REQ-003 |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Specifies the optional configuration keys | REQ-001 |
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Verified correct; no change | REQ-001 |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Verified consistent with ADR-002; no change | REQ-001 |
| `tests/eventbus/test_eventbus_dlq_outbox.py` | Existing outbox tests and helpers for creating `failed` rows | REQ-005 |

## Acceptance Criteria
- AC-1: ADR-006 covers `dlq_outbox` in Scope and Data Ownership and ADR-008 lists it among the `eventbus.sqlite` contents; every EventBus table and configuration key is covered by an ADR or a referenced specification (`REQ-001`).
- AC-2: ADR-006 states the `/replay` contract and the `/subscribe` replay-start precedence, including that `since_seq=0` is unspecified for a Consumer with a stored offset (`REQ-002`).
- AC-3: The `eventbus_05` cleanup procedure deletes dependent `dlq_outbox` rows first, states foreign keys exist, and no longer says the schema has none (`REQ-003`).
- AC-4: `eventbus_12` has no inline-DLQ-file-write row (`REQ-004`).
- AC-5: A test with a `failed` outbox row shows the count and a degraded reason in `/health`; a test with a failing sweep cycle shows the last-sweep result and a degraded reason; status code stays 503 for degraded; `liveness`, `readiness`, and role checks are unchanged (`REQ-005`).
- AC-6: `eventbus_10` and `eventbus_03` describe the new fields, reasons, and monitoring rule and no longer say "metered" (`REQ-006`).
- AC-7: `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain eventbus`, `check_db_separation.py`, and `generate_reference_table.py --check` pass; `uv run pytest tests/eventbus -v` passes (`REQ-007`).

## Tests
- `REQ-005` (new, `tests/eventbus/test_eventbus_health.py`): insert a `failed` row into `dlq_outbox` and assert the count and the `dlq_outbox_failed` reason; simulate a failing sweep cycle and assert the last-sweep result and the `dlq_sweep_failing` reason; assert HTTP 503 for degraded and 200 for ok; assert `liveness` and `readiness` unchanged by the new reasons; assert a Monitoring role still gets the response and other roles are rejected as before.
- `REQ-005` regression: existing health, shutdown, and DLQ outbox tests run unchanged.
- Documentation requirements are verified by the checkers in the Validation plan.

## Documentation Impact
`docs/10_adr/` (ADR-006, ADR-008) and `docs/24_eventbus/` (`eventbus_03`, `_05`, `_08` generated, `_10`, `_12`), located through `docs/00_index.md` "Document References by Task" (eventbus and governance areas) (REQ-001 to REQ-004, REQ-006, REQ-007). State intent, data ownership, failure behavior, and monitoring rules; no configuration values and no implementation-location mappings (docs content policy). Write in English.

## Assumptions
- A terminal-failed outbox row is any `dlq_outbox` row with `status = 'failed'` (schema CHECK values: `pending`, `done`, `failed`).
- New degraded reasons return 503 like all existing reasons (the documented rule), because `eventbus_10` already documents 503 for any degraded reason; `liveness` and `readiness` do not include them, matching `health_route.py`'s documented treatment of non-readiness reasons.
- "Last sweep" means the last `_dlq_loop` cycle (sweep, outbox processing, reconciliation); the stored value is `ok`, `failed`, or `not_run` plus an ISO-8601 UTC time, kept in memory on `app.state`, so it resets on restart (no schema change).
- Keeping the status code for capacity-only reasons as documented is the "document the monitoring rule" option of the issue; no behavior change.
- Overlap judgment (`tools/check_plan_target_overlaps.py`): `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` is also targeted by `plans/20261110-233648_adrrev009_adr008-recovery-align.md` (Decision Detail #7/#8 wording and recovery text) and `plans/20261111-095703_adrrev012_adr-approval-ledger.md` (`## Known Deviations` only); compatible, because this Plan edits only Decision Detail 4 (the `eventbus.sqlite` contents line) and adds its own pending approval record.
- Foreign-key-safe cleanup means deleting `dlq_outbox` rows for the cutoff events before deleting the events, in one transaction; `consumer_delivery` orphan behavior in the current text is unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `/subscribe` should support replay from the start for a Consumer with a stored offset | Maintainer decision | This Plan documents the current behavior and `/replay`; a code change would be a separate issue | False |
| UNK-02 | Whether a metrics endpoint is wanted | Maintainer decision; none exists | Out of scope; `eventbus_03` states what is observable instead | False |
| UNK-03 | Whether capacity-only reasons should return 200 | Maintainer decision | Kept at 503 as documented; revisit if monitoring raises false alarms | False |
| UNK-04 | Maintainer approval statements for the ADR-006 and ADR-008 decision-text edits | Approvals are maintainer statements | Write marked pending records and report them; the ledger Plan tracks them | False |
| UNK-05 | Whether `last_sweep` should also persist across restarts | No requirement; in-memory is the smallest change | Not planned; reconsider with the maintainer if restart visibility is needed | False |
| UNK-06 | Whether a `GET /health` query for the failed count adds measurable lock time on a large `dlq_outbox` | Not measured; the `status` column has an index (`idx_dlq_outbox_status`) | The count uses the indexed status filter under `run_with_db_lock`; verify in Phase 2 tests | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/dlq_repo.py` | Modify | Low (one added read function; callers unchanged) | 9 | N/A | Requires deploy of `scripts/` (EventBus restart) |
| `scripts/eventbus/app.py` | Modify | Medium (lifespan and DLQ loop; imported by 17 test modules) | 13 | N/A | Requires deploy of `scripts/` (EventBus restart) |
| `scripts/eventbus/health_route.py` | Modify | Medium (monitoring consumers read the body and status) | 5 | N/A | Requires deploy of `scripts/` (EventBus restart) |
| `tests/eventbus/test_eventbus_health.py` | Modify | Low | 6 | N/A | not applicable (tests are not deployed) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Medium (ADR graph and invariant matrix) | 10 | N/A | not applicable (docs) |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Modify | Medium (edited by other Plans) | 8 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Low | 14 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Modify | Low | 10 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_10_health_endpoint.md` | Modify | Low | 5 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_03_dlq_operations.md` | Modify | Low | 9 | N/A | not applicable (docs) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low (generated) | 24 | N/A | not applicable (docs) |

## Design
Path B (more than 3 files, runtime behavior of a public endpoint changes). Findings from the inspection:
- Architecture: `health_route` already imports `run_with_db_lock`, `get_db`, and `get_config`; adding a repository call follows the existing route-to-repository direction (`dlq_route`, `ack_route` use `dlq_repo`). `eventbus` must not import `agent`, `mcp_servers`, `rag`, or `db` (import-linter `eventbus-is-isolated`); no new import crosses that boundary.
- Dependency graph: `health_route.py` and `app.py` are imported by the app and by many tests; the response body gains fields (additive), the status-code rule is unchanged, and existing keys are not renamed, so existing consumers keep working.
- Historical: churn from `git log --since=30.days`; bus factor `N/A` (git-fame not installed).
- Operational: the EventBus service (single instance) restarts on deploy; no database schema or `PRAGMA user_version` change, so the fingerprint and the `user_version = 6` gate are unaffected. Persisted schema: not applicable. Consumer scan (`tools/scan_change_consumers.py`): no persisted schema, column, or shared constant changes; `not affected: eventbus_08 consumers other than the generated block`.
- Design decisions recorded: (1) in-memory last-cycle state on `app.state` rather than a table (alternative rejected: a persisted status table needs a schema change and a `user_version` bump); (2) new degraded reasons are real failures (503) and not capacity-only; (3) `liveness` and `readiness` keep their meaning so the deployment gate (`is_ready`) does not start refusing a service that is up but has a failed artifact; (4) the failed-count query is one indexed, read-only statement under the DB lock.
- Failure of the count query: a `sqlite3.Error` there must not mask the `db_unavailable` handling; the health route reports the existing `db_unavailable` reason and omits the count rather than raising.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step.

1. **Phase 1: Document current behavior** (REQ-001, REQ-002, REQ-003, REQ-004; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`)
   - [ ] Add `dlq_outbox` to ADR-006 Scope and Data Ownership and to ADR-008 Decision Detail 4; add pending approval records for both decision-text edits.
   - [ ] Add the `/replay` contract and the `/subscribe` replay-start precedence to ADR-006.
   - [ ] Rewrite the `eventbus_05` cleanup procedure (dependent `dlq_outbox` rows first).
   - [ ] Remove the obsolete `eventbus_12` row and fix the surrounding text.
2. **Phase 2: `/health` outbox and sweep reporting** (REQ-005; `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_health.py`)
   - [ ] Write the failing health tests first (terminal-failed row, failing sweep cycle, 503 rule, liveness/readiness unchanged, role checks).
   - [ ] Add the failed-row count function in `dlq_repo.py`.
   - [ ] Record the result and time of each `_dlq_loop` cycle on `app.state`.
   - [ ] Report both from `/health` with the two new degraded reasons.
   - [ ] Run `uv run pytest tests/eventbus -v`.
3. **Phase 3: Health documentation and generated reference** (REQ-006, REQ-007; `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`)
   - [ ] Document the new fields, reasons, and monitoring rule; replace "metered".
   - [ ] Run `uv run python tools/generate_reference_table.py --type eventbus` (or the type that covers `eventbus_08`), then `--check`.
4. **Phase 4: Deployment & Verification** (`scripts/eventbus/dlq_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py` and the documents above)
   - [ ] Run the Validation plan commands and the `rules/toolchain.md` sequence.
   - [ ] Hand off to `skills/deploy/SKILL.md`: the change is committed and pushed first, and deploying is the user's decision (approval gate); the EventBus service restarts on deploy and its monitoring consumers should be told that `/health` gains fields and reasons.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/*.py`, `tests/eventbus/test_eventbus_health.py` | Unit and integration | `uv run pytest tests/eventbus -v` | Pass |
| Python targets | Format, lint, type, security | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy <files>`, `uv run bandit -r scripts/eventbus -c pyproject.toml` | Clean (baseline: 3 pre-existing Low `B101` findings in `auth.py` and `subscribe_route.py`, none in the target files) |
| Architecture | Import contracts | `uv run lint-imports` | Pass |
| Module size | Size gate | `uv run python tools/check_module_size.py` | Pass |
| Coverage | Changed lines | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |
| Generated reference | Guarded block drift | `uv run python tools/generate_reference_table.py --check` | No drift |
| DB separation | Table ownership and DB paths | `uv run python tools/check_db_separation.py` | Pass |
| EventBus and ADR docs | Structure and policy | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` | Pass |
| EventBus docs | Claims against code and config | `uv run python tools/check_docs_consistency.py --domain eventbus` | Pass |
| ADR-006, ADR-008 | ADR structure, authority, matrix, preservation | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_invariant_matrix.py`, `check_adr_preservation.py` | Pass (preservation: only the intended text changes reported) |

Validation quality baseline: `radon` and `vulture` are not installed on this host (Tool availability guard; ruff covers the lightweight checks); `bandit -r scripts/eventbus -c pyproject.toml` reported 3 Low `B101` findings, none in `health_route.py`, `app.py`, or `dlq_repo.py`.

## Risks
- **Risk**: The additional count query under the DB lock slows `/health` or contends with publishers. → **Mitigation**: One read-only, indexed statement under `run_with_db_lock`; a Phase 2 test and the existing `lock_wait_high` metric show contention; if it fails the route reports `db_unavailable` and omits the count.
- **Risk**: New degraded reasons make deployment gates or monitoring flap. → **Mitigation**: `liveness` and `readiness` are unchanged, so the gate (`is_ready`) is unaffected; 503 follows the documented rule; the new reasons trigger only on terminal `failed` rows or a failing cycle, and `eventbus_10` documents them.
- **Risk**: Storing sweep state on `app.state` races with the health read. → **Mitigation**: Replace one small immutable value per cycle (single assignment) and read it once per request; no lock is needed.
- **Risk**: The manual cleanup rewrite instructs an unsafe deletion. → **Mitigation**: Keep the existing precautions (stop the service, back up `eventbus.sqlite`), delete dependents first inside one transaction, and state that events in the DLQ become unrecoverable as before.
- **Risk**: ADR-006 text about `/subscribe` is read as endorsing the lack of full replay. → **Mitigation**: It documents current behavior and the `/replay` alternative; the maintainer decision stays open (UNK-01).
- **Risk**: ADR-006 and ADR-008 decision-text edits lack approval records. → **Mitigation**: Marked pending records, reported, never fabricated (UNK-04).
- **Risk**: Edits to the high-churn `app.py` and `eventbus_08` collide with sibling Plans. → **Mitigation**: Keep the `app.py` edit to the loop body and regenerate `eventbus_08` with the tool last; rerun `tools/check_plan_target_overlaps.py`.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Document current behavior (REQ-001 to REQ-004) | In Progress | — | — |  |
| 2 | `/health` outbox and sweep reporting (REQ-005) | In Progress | — | — |  |
| 3 | Health documentation and generated reference (REQ-006, REQ-007) | In Progress | — | — |  |
| 4 | Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261112-072954_01_scripts_eventbus_dlq_repo.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261112-072954_02_scripts_eventbus_app.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261112-072954_03_scripts_eventbus_health_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261112-072954_04_tests_eventbus_test_eventbus_health.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261112-072954_05_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261112-072954_06_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261112-072954_07_docs_24_eventbus_eventbus_05_dlq_offsets_and_delivery_semantics.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261112-072954_08_docs_24_eventbus_eventbus_12_ack_nack_endpoints.md.md | 1 | Procedure | Pending | — | — |
| implementations/20261112-072954_09_docs_24_eventbus_eventbus_10_health_endpoint.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261112-072954_10_docs_24_eventbus_eventbus_03_dlq_operations.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261112-072954_11_docs_24_eventbus_eventbus_08_reference_api.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-113152_adrrev014_eventbus-spec-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261111-103238
- **Related target files**: `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_health.py`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`, `docs/24_eventbus/eventbus_10_health_endpoint.md`, `docs/24_eventbus/eventbus_03_dlq_operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: add `dlq_outbox` to ADR-006 (Scope, Data Ownership) and ADR-008 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 1 | AC-1 | `check_adr_structure.py`, `check_adr_invariant_matrix.py` | Confirmed by repository evidence |
| REQ-001 | Same; ADR-008 Decision Detail 4 omits the outbox | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Step 1 | AC-1 | `check_db_separation.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes: add the `/replay` contract and document `/subscribe` full replay | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Step 1 | AC-2 | `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: make the manual deletion procedure foreign-key-safe | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Step 1 | AC-3 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-004 | Required Changes: delete the obsolete NACK state row | `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | Step 1 | AC-4 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-005 | Required Changes: failed-outbox count and last sweep result in `/health` | `scripts/eventbus/dlq_repo.py` | Step 2 | AC-5 | `tests/eventbus/test_eventbus_health.py` | Derived from confirmed evidence |
| REQ-005 | Same; the DLQ loop swallows per-cycle errors | `scripts/eventbus/app.py` | Step 2 | AC-5 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-005 | Same; `/health` has no outbox or sweep fields and the 503 rule is documented | `scripts/eventbus/health_route.py` | Step 2 | AC-5 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-005 | Testing Expectations: new tests for `/health` outbox and sweep reporting and the status-code rule | `tests/eventbus/test_eventbus_health.py` | Step 2 | AC-5 | `uv run pytest tests/eventbus -v` | Explicit in issue |
| REQ-006 | Required Changes: update `eventbus_10` | `docs/24_eventbus/eventbus_10_health_endpoint.md` | Step 3 | AC-6 | `check_docs_consistency.py --domain eventbus` | Explicit in issue |
| REQ-006 | Needs confirmation resolved: the "metered" wording overstates observability | `docs/24_eventbus/eventbus_03_dlq_operations.md` | Step 3 | AC-6 | `check_docs_consistency.py --domain eventbus` | Confirmed by repository evidence |
| REQ-007 | Acceptance Criteria: `generate_reference_table.py --check` passes | `docs/24_eventbus/eventbus_08_reference_api.md` | Step 3 | AC-7 | `generate_reference_table.py --check` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261112-072954 -->