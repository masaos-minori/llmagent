## Goal
- Remove the EventBus DLQ code that can no longer run (unused `deadletter_dir` parameters, an unreachable `OSError` handler), the result fields and columns that repeat other data (`RequeueResult` duplicates, `events.dlq_requeue_count`, `events.consumer_id`), and the old name and private-attribute access, so each fact is stored and returned once and names match the schema. The `deadletter_dir` setting, the outbox worker, reconcile, and archive behavior stay unchanged.

## Priority
Medium

## Scope
- **In-Scope**: `deadletter_dir` removal from `_shared_promote`, `_shared_promote_single`, `promote_single`, `sweep_orphans`, and their callers; the `/nack` `except OSError`; `RequeueResult` reduced to `status`, `new_event_id`, `new_seq`; removal of the `events.dlq_requeue_count` and `events.consumer_id` columns (DDL, requeue write, `/dlq` response); deletion of the unused `_COL_REDISTRIBUTED_FROM`, `_COL_DLQ_REQUEUE_COUNT`, and `_COL_CONSUMER_ID` constants; the `counter._name` read and the `route_helpers.py` shebang; tests, documents, and the generated manifest that describe them.
- **Out-of-Scope**: the `deadletter_dir` configuration key, the outbox worker, `reconcile_missing_dlq_files`, archive behavior; EventBus configuration, authorization, and audit (rmcompat004); `ERR_*` constants (all have users); migration of an existing `eventbus.sqlite` (`compatrm001`); the `eventbus_12` NACK-table row (already scheduled by an open adrrev014 procedure, see Background).
- **Dependencies**: None open. The schema-fingerprint Plan (adrrev005) has landed (its steps 1-6 are `Completed`; only its deployment step is pending), so the schema edits here use the generalized fingerprint gate. The history-comment sweep (rmcompat007) follows this Plan.

## Background
Re-verified 2026-11-12 (Step 2 and Step 3). Revalidated 2026-11-13 (plan-to-implementation-procedure Step 2 and adversarial row re-check): all 20 target rows confirmed against current source unchanged — `dlq.py` defs at lines 115, 151, 187, 328; `ack_route.py` `except OSError` at 216-221; `dlq_repo.py:16,24-39,82-124`; `event_repo.py` `fetch_dlq` select at 126; `_constants.py:13-17,24-28`; `route_helpers.py:1,66`; `schema.sql:11,13`; manifest `sweep_orphans`/`promote_single` entries at 284-294; `test_eventbus_dlq.py` 25 call sites and the `dlq_requeue_count` assertions at 301-333 and 488-493; `test_eventbus_dlq_promotion.py` requeue test at 205-255 and the `OSError` patch test at 550-585 (`raise OSError` at 567); `test_eventbus_requeue_edge_cases.py:574`; `test_eventbus_dlq_outbox.py:101`; `test_eventbus_shutdown.py` fake `sweep_orphans` signatures at 67 and 121; `test_eventbus_schema_version.py:97-112`. The `test_eventbus_dlq_promotion.py` patch test still asserts `dlq_promoted is True`, confirming the patch has no effect on the DB-only path:
- `scripts/eventbus/dlq.py`: `_shared_promote` (line 115), `_shared_promote_single`, `promote_single` (line 330), and `sweep_orphans` (line 189) take `deadletter_dir`; their docstrings say it is "Kept for call-site signature stability; unused here" (lines 124, 166, 343). `reconcile_missing_dlq_files`, `process_outbox`, `archive_dlq_record`, and `_count_orphan_dlq_files` use it and keep it.
- `scripts/eventbus/ack_route.py:208-221`: `is_promotable()` and `promote_single()` are wrapped in `except OSError` that logs "deferred to sweep"; both touch only SQLite, so the handler cannot run. The test that exercises it (`tests/eventbus/test_eventbus_dlq_promotion.py` around line 555) patches `dlq._atomic_write` to raise, which promotion never calls, so the patch has no effect.
- `RequeueResult` (`dlq_repo.py:24-39`) carries `original_event_exists` and `already_redelivered`, determined by `status` (`dlq_repo.py:82,102,103,119,124`). Only `tests/eventbus/test_eventbus_requeue_edge_cases.py:574` reads `already_redelivered`; `dlq_route.py` has no reference to either field.
- `events.dlq_requeue_count` is written once (`dlq_repo.py:89`), read once (`event_repo.py:126`, which feeds `/dlq`), and defined in `schema.sql:11`; `events.consumer_id` (`schema.sql:13`) is never written (both `INSERT INTO events` statements omit it) and never read; `_COL_CONSUMER_ID` is defined and exported but unused.
- `_COL_REDISTRIBUTED_FROM` (`_constants.py:14`) is defined and exported but has no user; `get_counter_value` reads `counter._name` (`route_helpers.py:66`); line 1 is `# /usr/bin/env python3`.

Corrections found against the Issue's claims:
- `dlq_route.py` needs no edit: it branches on `status` only and has no reference to the duplicate fields (the Issue lists it as a target); `consumer_id=""` at `dlq_route.py:78` is an audit parameter, not the column.
- `_COL_REDISTRIBUTED_FROM` has no user, so it is deleted rather than renamed (the acceptance search `rg -n "REDISTRIBUTED" scripts/` is met either way). The same holds for `_COL_CONSUMER_ID` and `_COL_DLQ_REQUEUE_COUNT` (only `dlq_repo.py` uses the latter, and that use is removed).
- The fingerprint code needs no edit: the gate compares a database with the canonical DDL built from `schema.sql` (`scripts/shared/schema_fingerprint.py`; no column list is stored), so removing the columns from `schema.sql` is the whole schema change. `tests/eventbus/test_eventbus_schema_version.py:103` drops `consumer_id` from a fresh database to test "malformed shape is refused" and breaks once the column is gone; it moves to a column that stays.
- `eventbus_12` (line 74) already has the obsolete NACK row scheduled for removal by `implementations/20261112-072954_08_docs_24_eventbus_eventbus_12_ack_nack_endpoints.md.md`; it is a reference file here, not a target. `eventbus_06` does not list `dlq_requeue_count` or `events.consumer_id`, so it needs no edit.
- The documents that do describe the removed items are `eventbus_04` (line 32), `eventbus_05` (line 227), `eventbus_07` (lines 198, 202), ADR-006 (lines 241, 334), and the generated `eventbus_08` rows and manifest (`sweep_orphans` and `promote_single` signatures); the Issue does not name `eventbus_07`, `eventbus_08`, or the manifest.
- The `Counter` public API gives the base name through `metric.name` (probed with the installed `prometheus_client`: family name `<name>`, sample `<name>_total`), so `metric.name + "_total"` replaces `counter._name + "_total"`.

## Problem
Parameters kept only for signature stability suggest that promotion still writes files; an unreachable handler and a test that patches a function promotion never calls document a failure that cannot happen. Redundant fields and columns can disagree when one is updated and the other is not. An unused column, three unused constants, and a private-attribute read are leftovers that mislead or break silently on a client-library upgrade.

## Reason for Change
The current-only policy (`compatrm001`) forbids signature-stability shims and old names. No external deadline; nothing observed is failing today.

## Implementation Intent
- DLQ code contains only reachable behavior, each fact is stored and returned once, and names match the schema.
- The schema change (removing `dlq_requeue_count` as decided 2026-11-10, and `consumer_id` because no reader or writer exists) is a new canonical schema with no migration: an old file fails the existing fingerprint gate with the archive-and-recreate error.

## Requirements
- `REQ-001`: No promotion or sweep function takes `deadletter_dir`, and callers (`app.py`, `ack_route.py`) are updated.
- `REQ-002`: `/nack` has no `except OSError`, and the test that patched the unreachable path is updated.
- `REQ-003`: `RequeueResult` has only `status`, `new_event_id`, and `new_seq`.
- `REQ-004`: `events.dlq_requeue_count` and `events.consumer_id` are absent from `schema.sql`, the requeue write, the `/dlq` query and response, and the constants; a database with the old shape is refused by the existing gate.
- `REQ-005`: `_COL_REDISTRIBUTED_FROM` is gone (`rg -n "REDISTRIBUTED" scripts/` returns nothing), `get_counter_value` reads only public API, and `route_helpers.py` has a valid shebang or none.
- `REQ-006`: The documents and the generated manifest describe the DB-only promotion, the single requeue fact, and the `/dlq` response without the removed field; the ADR-006 edit updates the INV-08 verification row (the cited test) and the `events` column list; INV-08 itself ("state, count, and history of ... Requeue are persisted") is unchanged because the Requeue count and history stay persisted through the `redelivered_from` lineage, so no new approval record is needed unless the maintainer rewrites INV-08 (UNK-03).

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/dlq.py` | DLQ promotion and sweep | Remove `deadletter_dir` from the four functions and their docstrings | REQ-001 / AC-1 | lines 115-124, 153-166, 189-201, 330-347 (checked in Step 2) | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/ack_route.py` | `/nack` handler | Call `promote_single` without the directory; remove `except OSError` and its log | REQ-001, REQ-002 / AC-1, AC-2 | lines 208-221 (checked in Step 2) | `tests/eventbus/test_eventbus_dlq_promotion.py` | Verified |
| `scripts/eventbus/app.py` | Background sweep | Call `sweep_orphans` without `cfg.deadletter_dir` | REQ-001 / AC-1 | line 171 (checked in Step 2) | `tests/eventbus/test_eventbus_shutdown.py` | Verified |
| `scripts/eventbus/dlq_repo.py` | Requeue repository | Reduce `RequeueResult`; remove the `dlq_requeue_count` update and import; fix the docstring | REQ-003, REQ-004 / AC-3, AC-4 | lines 16, 24-39, 82-124 (checked in Step 3) | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Verified |
| `scripts/eventbus/event_repo.py` | `/dlq` query | Drop `dlq_requeue_count` from the `fetch_dlq` select | REQ-004 / AC-4 | line 126 (checked in Step 3) | `tests/eventbus/test_eventbus_dlq.py` | Verified |
| `scripts/eventbus/_constants.py` | Column constants | Delete `_COL_REDISTRIBUTED_FROM`, `_COL_DLQ_REQUEUE_COUNT`, `_COL_CONSUMER_ID` and their `__all__` entries | REQ-004, REQ-005 / AC-4, AC-5 | lines 13-17, 24-28; no other user (checked in Step 2) | acceptance search | Verified |
| `scripts/eventbus/route_helpers.py` | Metrics helper | Use `metric.name`; fix the shebang line | REQ-005 / AC-5 | lines 1, 66 (checked in Step 2) | `tests/eventbus/test_eventbus_health.py` | Verified |
| `scripts/eventbus/schema.sql` | Canonical DDL | Remove the two `events` columns | REQ-004 / AC-4 | lines 11 and 13 (checked in Step 2) | `tests/eventbus/test_eventbus_schema_version.py` | Verified |
| `registry/manifests/eventbus_api.yaml` | Generated manifest | Regenerate; the `sweep_orphans` and `promote_single` signatures change | REQ-006 / AC-6 | lines 284-285, 294 (checked in Step 2) | `generate_reference_table.py --check` | Verified |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Decision evidence | Update the INV-08 verification row (cited test and wording) and the `events` column list; INV-08 text unchanged | REQ-006 / AC-6 | lines 241, 334 (checked in Step 2) | `tools/check_adr_preservation.py` | Verified |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | `/dlq` doc | Remove `dlq_requeue_count` from the item description | REQ-006 / AC-6 | line 32 (checked in Step 2) | docs checkers | Verified |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Delivery doc | Remove the requeue-count audit-trail step | REQ-006 / AC-6 | line 227 (checked in Step 2) | docs checkers | Verified |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Operations doc | Describe DB-only promotion with file generation by the outbox worker; remove the requeue-count increment | REQ-006 / AC-6 | lines 198, 202 (checked in Step 2) | docs checkers | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Reference API | Regenerate the guarded block; the two signatures and `RequeueResult` row change | REQ-006 / AC-6 | lines 103-108 (checked in Step 2) | `generate_reference_table.py --check` | Verified |
| `tests/eventbus/test_eventbus_dlq.py` | DLQ tests | Update `promote_single`/`sweep_orphans` calls; drop `dlq_requeue_count` assertions | REQ-001, REQ-004 / AC-1, AC-4 | 25 call sites; lines 301-333, 488-493 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Promotion tests | Update calls; keep the requeue test without its `dlq_requeue_count` assertion under a new name (ADR-006 INV-08 cites it); replace the `OSError` nack test with one that asserts DB-only promotion | REQ-001, REQ-002, REQ-004 / AC-1, AC-2, AC-4 | 11 call sites; lines 205-255, 555-580 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Requeue tests | Update `sweep_orphans` calls; drop `dlq_requeue_count` and `already_redelivered` assertions | REQ-001, REQ-003, REQ-004 / AC-1, AC-3, AC-4 | lines 145-307, 157-243, 450-489, 574-646 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_dlq_outbox.py` | Outbox tests | Update the `promote_single` call | REQ-001 / AC-1 | line 101 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_shutdown.py` | Shutdown tests | Update the two fake `sweep_orphans` signatures | REQ-001 / AC-1 | lines 67, 121 (checked in Step 3) | itself | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Schema gate tests | Drop a column that stays in the schema instead of `consumer_id` | REQ-004 / AC-4 | lines 96-112 (checked in Step 3) | itself | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/dlq_route.py` | Branches on `status` only; unchanged | REQ-003 |
| `scripts/shared/schema_fingerprint.py` | Builds the canonical shape from `schema.sql`; holds no column list | REQ-004 |
| `scripts/eventbus/schema.py` | The EventBus startup gate that refuses an old-shape file | REQ-004 |
| `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` | The obsolete NACK row (line 74) is removed by `implementations/20261112-072954_08_docs_24_eventbus_eventbus_12_ack_nack_endpoints.md.md` | REQ-002 |
| `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` | Verified to list neither removed column | REQ-004 |
| `plans/done/20261110-095137_adrrev005_schema-fingerprint-unify.md` | Landed fingerprint change; records the deployed file's divergence | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001): `rg -n "deadletter_dir" scripts/eventbus/dlq.py` shows it only in `reconcile_missing_dlq_files`, `process_outbox`, `archive_dlq_record`, `_atomic_write`, and `_count_orphan_dlq_files`; `promote_single` and `sweep_orphans` do not take it.
- AC-2 (REQ-002): `rg -n "OSError" scripts/eventbus/ack_route.py` returns nothing in the `/nack` handler.
- AC-3 (REQ-003): `RequeueResult` has exactly `status`, `new_event_id`, `new_seq`.
- AC-4 (REQ-004): `rg -n "dlq_requeue_count|_COL_CONSUMER_ID" scripts` returns nothing, `schema.sql` has neither column, and a database created from the old DDL is refused by the gate.
- AC-5 (REQ-005): `rg -n "REDISTRIBUTED" scripts/` returns nothing; `get_counter_value` uses no attribute starting with an underscore.
- AC-6 (REQ-006): the documents and manifest match the code; `generate_reference_table.py --check` and the docs and ADR checkers pass.
- AC-7: `uv run pytest tests/eventbus` and the validation sequence pass.

## Tests
- REQ-001: existing promotion, sweep, and outbox tests call the new signatures.
- REQ-002: the nack test asserts that promotion is a database-only transaction and that no file is written inline.
- REQ-003, REQ-004: requeue tests assert on `status` and the descendant row; `test_eventbus_schema_version.py` asserts an old-shape (extra column) file is refused and left unchanged.
- REQ-005: the existing health test covers `get_counter_value` through the lock-contention metric.

## Documentation Impact
- Documentation must be updated (REQ-006): `eventbus_04`, `eventbus_05`, `eventbus_07`, the generated `eventbus_08` block, and ADR-006 (the INV-08 verification row and the implementation notes; INV-08 text is unchanged, so no new approval record), located through `docs/00_index.md` "Document References by Task". Describe behavior and failure handling, not field catalogs. Run the `routing.md` checkers, `check_docs_consistency.py --domain eventbus`, and the ADR checkers.

## Assumptions
- Removing `events.consumer_id` is justified by the zero-reference search the Issue asks for (no writer in either `INSERT INTO events`, no reader in `scripts/`, one constant with no user); the maintainer decided the `dlq_requeue_count` removal and the Issue pairs `consumer_id` with it as one schema update.
- `/dlq` returns rows built from `fetch_dlq`, so dropping the column from the select removes the key from the response; this API change is documented in `eventbus_04`.
- Deleting unused constants is the same intent as the requested rename (names match the schema) and removes the stale name entirely.
- Step 8b overlap judgements (`tools/check_plan_target_overlaps.py`): `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, and `registry/manifests/eventbus_api.yaml` with `plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md` are compatible (that Plan edits the authorization and audit sentences and regenerates the same generated artifacts; the second regeneration includes the first's change, so regenerate with the tool after both code changes rather than editing by hand).
- Step 8b overlap judgements, all compatible: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` with `plans/20261111-104147_adrrev015_adr-index-matrix.md` (that Plan edits INV-13 wording at line 186, the INV-04/INV-07 rows at lines 232 and 240, and the requeue paragraph at line 276; this Plan edits the INV-08 row at line 241 and the column list at line 334, so re-read the table first) and with `plans/20261111-104605_adrrev016_adr-authority-format.md` (front matter, Related ADRs, and INV-15 ownership only); `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` with `plans/20261111-112439_adrrev019_docs-stale-statements.md` (that Plan adds an `events.jsonl` note to the Cleanup Procedure at lines 177-193; this Plan edits line 227).
- Implementation procedures of `plans/done/20261111-103238_adrrev014_eventbus-spec-gaps.md` (edit `dlq_repo.py` (adds a read-only terminal-failure count), `app.py`, `eventbus_05` (cleanup procedure, lines 177-193), ADR-006 (outbox and replay sections), and `eventbus_12`) are now all archived under `implementations/done/` (all ten `20261112-072954_*` documents, checked 2026-11-13): their edits are already reflected in the current source and no concurrent edit from that Plan is pending; re-read each file before editing anyway.
- Step 8b overlap judgement (2026-11-13, `tools/check_plan_target_overlaps.py`): `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/route_helpers.py`, `docs/24_eventbus/eventbus_08_reference_api.md`, and `registry/manifests/eventbus_api.yaml` are also targeted by `plans/20261112-122030_rmcompat007_history-comment-sweep.md` — compatible: that Plan only deletes stale history comments and regenerates the same generated artifacts; this Plan runs first (`tools/plan_dependency_order.py` recommends it and rmcompat007 records that it follows this Plan), and each Plan regenerates `eventbus_08` and the manifest with the tool in its own cycle, so the last regeneration includes both changes.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The operator's plan for the deployed `eventbus.sqlite`, which already differs from the current schema (`user_version 0`, recorded in the adrrev005 Plan); removing columns makes every older file fail the gate, and the handling of undelivered events in the old file is not decided | Operator decision | Deployment hand-off in Phase 6; archive and recreate when the operator chooses | False |
| UNK-02 | Whether an operator script or external consumer reads `dlq_requeue_count` from `/dlq` or `events.consumer_id` | Operator knowledge | None found in the repository; ask before deploy | False |
| UNK-03 | Whether the maintainer wants INV-08 reworded now that `dlq_requeue_count` is gone (the lineage still records the Requeue count and history) | Maintainer preference | If yes, add a pending approval record per `governance_05`; the maintainer writes the statement, not the implementer | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/dlq.py` | Modify | Medium | 7 | N/A | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | Modify | Medium | 10 | N/A | not applicable (rsynced) |
| `scripts/eventbus/app.py` | Modify | Medium | 13 | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq_repo.py` | Modify | Medium | 8 | N/A | not applicable (rsynced) |
| `scripts/eventbus/event_repo.py` | Modify | Low | 4 | N/A | not applicable (rsynced) |
| `scripts/eventbus/_constants.py` | Modify | Low | 2 | N/A | not applicable (rsynced) |
| `scripts/eventbus/route_helpers.py` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `scripts/eventbus/schema.sql` | Modify | High | 10 | N/A | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | Modify | Low | 7 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | Modify | Low | 5 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | Modify | Low | 11 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Modify | Low | 19 | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Modify | Low | 23 | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq_promotion.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_dlq_outbox.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_shutdown.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_schema_version.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- Consumer scan (`tools/scan_change_consumers.py --seed dlq_requeue_count --seed _COL_CONSUMER_ID --seed RequeueResult`; testmon state stale and not opened): the scripts candidates are `_constants.py`, `event_repo.py`, `schema.sql`, and `dlq_repo.py` (all target rows) and `dlq_route.py` (`not affected`: it imports `RequeueResult` for a return annotation and reads no field); the docs candidates are the target rows `eventbus_04`, `eventbus_05`, `eventbus_07`, `eventbus_08`, and ADR-006; the ADR test-citation candidates (ADR-006 lines 236 and 241) cite tests this Plan edits: the INV-08 row cites `test_dlq_requeue_increments_dlq_requeue_count_not_consumer_delivery_failure_count`, which is kept without its `dlq_requeue_count` assertion under a name that no longer mentions the column, and the citation is updated in the same change; the line 236 citations keep their test names. A text search over `scripts tests docs tools registry deploy` found the `promote_single` and `sweep_orphans` callers (`ack_route.py`, `app.py`, tests) and the single `get_counter_value` caller (`health_route.py:94`). The scan lists candidates only.
- Persisted schema check (`rules/persisted-schema-change.md`): item 1 (version stores) and 5, 6 (migration registry): the EventBus has a registry for migrations, but this change registers no step by design (`compatrm001`: no migration, archive and recreate); the fingerprint gate refuses the old shape. Item 2: a column removal moves the fingerprint, which is the intended refusal path; `tools/check_db_separation.py` is run for the DDL change. Item 3 (rebuild and cascade): no rebuild. Item 4 (`NOT NULL` write path): the removed `dlq_requeue_count` was `NOT NULL DEFAULT 0` and its only writer (`dlq_repo.py:89`) goes with it; `rg -n "INSERT (OR \w+ )?INTO events" scripts/ tests/` lists the writers, none names the removed columns. Item 7: rows with an old meaning do not apply; a file with the old columns is refused, not read.
- Requeue design: `redeliver_event` keeps its transaction and the unique index on `redelivered_from`; it returns `RequeueResult(status, new_event_id, new_seq)`. The "already redelivered" race mapping stays.
- Import architecture: `lint-imports` baseline (6 contracts kept, in the rmcompat001 Plan Design); the change removes parameters and constants only; the eventbus-is-isolated contract is unaffected.
- Complexity (`radon cc`): no touched function is above C. `vulture` and `bandit` baselines are in the rmcompat001 Plan Design; deletions add no finding. No port, process, or dependency change (`ss`, `fuser`, `pip-audit` N/A).
- Historical: churn above from `git log --since=30.days`; bus factor not measured.

## Implementation steps
1. **Phase 1: Promotion and sweep signatures, unreachable handler**
   - [ ] Remove `deadletter_dir` from the four functions (REQ-001; `scripts/eventbus/dlq.py`)
   - [ ] Update the callers and remove `except OSError` (REQ-001, REQ-002; `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`)
   - [ ] Update the tests, replacing the unreachable-path test (REQ-001, REQ-002; `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_dlq_outbox.py`, `tests/eventbus/test_eventbus_shutdown.py`)
2. **Phase 2: `RequeueResult`**
   - [ ] Reduce the dataclass and its constructors (REQ-003; `scripts/eventbus/dlq_repo.py`)
   - [ ] Drop the duplicate-field assertions (REQ-003; `tests/eventbus/test_eventbus_requeue_edge_cases.py`)
3. **Phase 3: Remove the two columns**
   - [ ] Remove the columns (REQ-004; `scripts/eventbus/schema.sql`)
   - [ ] Remove the requeue write, the select column, and the constants (REQ-004, REQ-005; `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/event_repo.py`, `scripts/eventbus/_constants.py`)
   - [ ] Update the tests (REQ-004; `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_schema_version.py`)
4. **Phase 4: Metrics helper**
   - [ ] Use `metric.name`; fix the shebang (REQ-005; `scripts/eventbus/route_helpers.py`)
5. **Phase 5: Documents and generated files**
   - [ ] Update the INV-08 verification row and the `events` column list (REQ-006; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`)
   - [ ] Update the three EventBus documents (REQ-006; `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`); regenerate the reference block and manifest (REQ-006; `docs/24_eventbus/eventbus_08_reference_api.md`, `registry/manifests/eventbus_api.yaml`)
6. **Phase 6: Deployment and verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the operator decides when to archive and recreate `eventbus.sqlite` and what to do with undelivered events in the old file (UNK-01). Run the acceptance searches, the validation sequence, and the docs and ADR checkers (REQ-001 to REQ-006)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| EventBus DLQ, nack, requeue, schema | Unit and integration | `uv run pytest tests/eventbus` | Pass |
| Changed Python files | Static | `uv run ruff format`, `ruff check`, `mypy --no-namespace-packages`, `lint-imports`, `bandit -r scripts/ -c pyproject.toml`, `python tools/check_module_size.py` | No new finding |
| DDL change | Static | `uv run python tools/check_db_separation.py` | Pass |
| Whole change | Search | the AC-1 to AC-5 `rg` commands | Match the criteria |
| Manifest and reference | Generator | `uv run python tools/generate_reference_table.py --check` (and `--type eventbus` to refresh) | No drift |
| Documents and ADR | Docs | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus`, `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_known_deviation_sync.py` | No findings |
| Coverage | Coverage | diff-cover sequence in `rules/toolchain.md` section 7 | At or above the threshold |

## Risks
- **Risk**: The deployed `eventbus.sqlite` fails the gate after the schema change and undelivered events in it are lost on recreate → **Mitigation**: UNK-01 and the Phase 6 prerequisite; the file already differs from the current schema, so recreate is needed regardless; the operator chooses the timing.
- **Risk**: An external reader depends on `dlq_requeue_count` in the `/dlq` response → **Mitigation**: UNK-02; the response change is documented in `eventbus_04`.
- **Risk**: adrrev014 edits to `dlq_repo.py`, `app.py`, `eventbus_05`, ADR-006, or `eventbus_12` interact with this Plan's edits → **Mitigation**: its procedures are archived in `implementations/done/` (checked 2026-11-13), so their edits are already in the source; re-read before editing; regenerate generated artifacts with the tool; `eventbus_12` is left to its procedure.
- **Risk**: Removing `consumer_id` is wrong if a reader exists outside the searched trees → **Mitigation**: the Issue instructs re-running the zero-reference search before deleting; the procedure repeats it (`scripts`, `tests`, `tools`, `docs`, `registry`, `deploy`).
- **Risk**: Replacing the `OSError` test removes the only coverage of `/nack` promotion failure → **Mitigation**: the replacement asserts the DB-only transaction, which is the real behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `deadletter_dir` from promotion and sweep, remove the unreachable handler, update tests | In Progress | — | — |  |
| 2 | Reduce `RequeueResult` and its test assertions | In Progress | — | — |  |
| 3 | Remove `dlq_requeue_count` and `consumer_id` (schema, writes, reads, constants, tests) | In Progress | — | — |  |
| 4 | Use the public Counter API and fix the shebang | In Progress | — | — |  |
| 5 | Update the documents, regenerate the reference block and manifest | In Progress | — | — |  |
| 6 | Deployment hand-off and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-173721_01_scripts_eventbus_dlq.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-173721_02_scripts_eventbus_ack_route.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-173721_03_scripts_eventbus_app.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-173721_04_scripts_eventbus_dlq_repo.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261113-173721_05_scripts_eventbus_event_repo.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261113-173721_06_scripts_eventbus__constants.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261113-173721_07_scripts_eventbus_route_helpers.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261113-173721_08_scripts_eventbus_schema.sql.md | 3 | Procedure | Pending | — | — |
| implementations/20261113-173721_09_registry_manifests_eventbus_api.yaml.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_10_docs_10_adr_adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_11_docs_24_eventbus_eventbus_04_dlq_endpoint.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_12_docs_24_eventbus_eventbus_05_dlq_offsets_and_delivery_semantics.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_13_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_14_docs_24_eventbus_eventbus_08_reference_api.md.md | 5 | Procedure | Pending | — | — |
| implementations/20261113-173721_15_tests_eventbus_test_eventbus_dlq.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261113-173721_16_tests_eventbus_test_eventbus_dlq_promotion.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-173721_17_tests_eventbus_test_eventbus_requeue_edge_cases.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261113-173721_18_tests_eventbus_test_eventbus_dlq_outbox.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261110-170926_rmcompat005_eventbus-dlq-leftovers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261112-121134
- **Related target files**: `scripts/eventbus/dlq.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/app.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/event_repo.py`, `scripts/eventbus/_constants.py`, `scripts/eventbus/route_helpers.py`, `scripts/eventbus/schema.sql`, `registry/manifests/eventbus_api.yaml`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`, `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_dlq_promotion.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_dlq_outbox.py`, `tests/eventbus/test_eventbus_shutdown.py`, `tests/eventbus/test_eventbus_schema_version.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `dlq.py:115-124,153-201,330-347` | `scripts/eventbus/dlq.py` | 1 | AC-1 | `tests/eventbus/test_eventbus_dlq.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 (callers); `ack_route.py:214` | `scripts/eventbus/ack_route.py` | 1 | AC-1 | `tests/eventbus/test_eventbus_dlq_promotion.py` | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 (callers); `app.py:171` | `scripts/eventbus/app.py` | 1 | AC-1 | `tests/eventbus/test_eventbus_shutdown.py` | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; 25 call sites | `tests/eventbus/test_eventbus_dlq.py` | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; 11 call sites | `tests/eventbus/test_eventbus_dlq_promotion.py` | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; `sweep_orphans` calls | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; `test_eventbus_dlq_outbox.py:101` | `tests/eventbus/test_eventbus_dlq_outbox.py` | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-001 | Testing Expectations; `test_eventbus_shutdown.py:67,121` | `tests/eventbus/test_eventbus_shutdown.py` | 1 | AC-1 | itself | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `ack_route.py:208-221` | `scripts/eventbus/ack_route.py` | 1 | AC-2 | `tests/eventbus/test_eventbus_dlq_promotion.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; `test_eventbus_dlq_promotion.py:555-580` | `tests/eventbus/test_eventbus_dlq_promotion.py` | 1 | AC-2 | itself | Confirmed by repository evidence |
| REQ-003 | Required Changes 3; `dlq_repo.py:24-39,82-124` | `scripts/eventbus/dlq_repo.py` | 2 | AC-3 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3; `test_eventbus_requeue_edge_cases.py:574` | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | 2 | AC-3 | itself | Confirmed by repository evidence |
| REQ-004 | Required Changes 4 and 5; `schema.sql:11,13` | `scripts/eventbus/schema.sql` | 3 | AC-4 | `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4; `dlq_repo.py:16,89` | `scripts/eventbus/dlq_repo.py` | 3 | AC-4 | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4; `event_repo.py:126` | `scripts/eventbus/event_repo.py` | 3 | AC-4 | `tests/eventbus/test_eventbus_dlq.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 4 and 5; `_constants.py:13,17` | `scripts/eventbus/_constants.py` | 3 | AC-4 | acceptance search | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; `test_eventbus_dlq.py:301-333,488-493` | `tests/eventbus/test_eventbus_dlq.py` | 3 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; `test_eventbus_dlq_promotion.py:205-255` | `tests/eventbus/test_eventbus_dlq_promotion.py` | 3 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Testing Expectations; requeue-count assertions | `tests/eventbus/test_eventbus_requeue_edge_cases.py` | 3 | AC-4 | itself | Confirmed by repository evidence |
| REQ-004 | Testing Expectations (old-shape refusal); `test_eventbus_schema_version.py:96-112` | `tests/eventbus/test_eventbus_schema_version.py` | 3 | AC-4 | itself | Confirmed by repository evidence |
| REQ-005 | Required Changes 6; `_constants.py:14,25` | `scripts/eventbus/_constants.py` | 3 | AC-5 | acceptance search | Confirmed by repository evidence |
| REQ-005 | Required Changes 6; `route_helpers.py:1,66` | `scripts/eventbus/route_helpers.py` | 4 | AC-5 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-006 | Documentation Impact; ADR-006 lines 241, 334 | `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | 5 | AC-6 | ADR checkers | Explicit in issue |
| REQ-006 | Documentation Impact; `eventbus_04:32` | `docs/24_eventbus/eventbus_04_dlq_endpoint.md` | 5 | AC-6 | docs checkers | Explicit in issue |
| REQ-006 | Documentation Impact; `eventbus_05:227` | `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` | 5 | AC-6 | docs checkers | Explicit in issue |
| REQ-006 | Derived from `eventbus_07:198,202` | `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | 5 | AC-6 | docs checkers | Derived from confirmed evidence |
| REQ-006 | Derived from `eventbus_08:103-108` | `docs/24_eventbus/eventbus_08_reference_api.md` | 5 | AC-6 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-006 | Derived from `eventbus_api.yaml:284-294` | `registry/manifests/eventbus_api.yaml` | 5 | AC-6 | `generate_reference_table.py --check` | Derived from confirmed evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-173721 -->