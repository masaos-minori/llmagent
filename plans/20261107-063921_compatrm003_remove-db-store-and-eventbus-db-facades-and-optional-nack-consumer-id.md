# Plan: Remove the db.store and eventbus.db facades and require the consumer-scoped NACK contract

## Goal
- Delete the `scripts/db/store.py` and `scripts/eventbus/db.py` re-export facades, migrate every importer to the responsibility-specific modules, and make `consumer_id` a required non-empty argument of `nack_event()`, removing the no-consumer code path and its tests.

## Priority
Medium

## Scope
- **In-Scope**: Deletion of the two facade modules; import migration of 7 production `scripts/eventbus/` modules and 11 test files for `eventbus.db`, and of the `db.store` docstring/test references; `nack_event()` signature tightening and branch removal in `scripts/eventbus/delivery_repo.py`; removal of the no-consumer NACK tests; removed-name patterns in `tools/check_compat_shims.py`; import-boundary and NACK documentation updates (`docs/41_db/`, `docs/24_eventbus/`, `scripts/eventbus/README.md`, `scripts/db/__init__.py` docstring).
- **Out-of-Scope**: Reorganizing the responsibility-specific modules, changing EventBus ACK semantics, changing the DLQ threshold, deprecation warnings or transition aliases, and the checker-configuration consolidation owned by `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.
- **Dependencies**: Can run in parallel with compatrm001/compatrm002 (disjoint files except the import-boundary rule text in docs). Must complete before `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.
  - **Depends on**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md | phase all | 004 adds the removed facade paths to the blocking rules in one change; 003 defines those paths.

## Background
- Initiative issue M-1 of `memo-issue.md`, third of four. Verified 2026-11-07 against current source:
  - `scripts/db/store.py` (55 lines) re-exports 10 symbols from `db.store_protocols` / `db.store_impl` with a "Stable public import surface" docstring. Its only live references are its own docstring examples and `tests/db/test_db_public_api.py` (fixture, `__all__` assertions, `exec("from db.store import *")` wildcard test) — no production importer exists (grep-verified: production code already imports `db.store_protocols` / `db.store_impl` directly in `rag_consistency.py`, `create_schema.py`, `maintenance.py`, `agent/commands/memory_data_ops.py`, `agent/factory.py`, and test helpers). Removing it is near-zero risk, as the Issue's adversarial validation noted.
  - `scripts/db/__init__.py` imports store symbols directly from `store_impl` / `store_protocols` (lines 49-60) and lists them in its own `__all__` — it does not import through `db.store`, so it is not a facade re-creation; only its module docstring line 8 (`db.store: Protocols + SQLite impls (protocol re-exports)`) needs updating.
  - `scripts/eventbus/db.py` (42 lines) re-exports 15 symbols from `db_conn`, `event_repo`, `delivery_repo`, `dlq_repo`. Importers: 8 production import sites in 7 modules (`dlq_route.py:11`, `ack_route.py:14` + `:79`, `app.py:42`, `health_route.py:9`, `publish_route.py:13`, `replay_route.py:13`, `route_helpers.py:133`) and 11 test files (`test_eventbus_offsets.py`, `test_eventbus_restart_resume.py`, `test_eventbus_route_helpers_metrics.py` (`import eventbus.db as eb_db`), `test_eventbus_concurrent.py`, `test_eventbus_ack_nack.py`, `test_eventbus_requeue_edge_cases.py`, `test_eventbus_dlq_promotion.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_dlq.py`, `test_eventbus_dlq_outbox.py`, `test_eventbus_crash_ack.py`, `test_eventbus_shutdown.py` (`import eventbus.db as eb_db`) — 12 files by name; two use module-object imports and must be handled as attribute access, not symbol import).
  - `nack_event()` (`scripts/eventbus/delivery_repo.py:37-43`) takes `consumer_id: str | None = None` with the "internal-only: the /nack route always supplies consumer_id" comment; three `if consumer_id is not None:` branches exist (lines 76, 117-133, 136-149), and the final `return NackResult("ok")` (line 150) is the success-without-delivery-state path to delete.
  - The `/nack` route (`scripts/eventbus/ack_route.py:133-160`) already requires `consumer_id` (`Query(...)`, REQ-007), validates the (event_id, consumer_id) pair via `authorize_event_pair()` (403 on ungranted consumer), and always passes `consumer_id` positionally (line 173). The route-side authorization requirement is already satisfied; the Issue's remaining work is the repository-level contract.
  - Two-argument `nack_event(db, event_id)` call sites exist only in tests: `tests/eventbus/test_eventbus_ack_nack.py` lines 367, 386, 389, 395, 485 (tests `test_nack_event_increments_failure_count`, `test_nack_event_increments_again`, `test_nack_event_not_found`, `test_nack_no_consumer_id_unaffected_by_consumer_acks`) plus no-consumer idempotency tests `test_nack_same_key_no_increment_no_consumer_id` (line 736) and `test_nack_different_key_no_consumer_id` (line 761). `tests/eventbus/test_eventbus_dlq_promotion.py:657` already passes `"consumer-A"` positionally and needs only the import migration.
  - Route-level tests for the current contract stay unchanged: `test_nack_event_mandatory_consumer_id` (422 on missing param, line 592), 403 tests (lines 791-847), idempotency-key tests.
  - Facade decision records to update: `scripts/eventbus/README.md` "Stub Module Pattern" section with the "Decision (2026-10-27): Retain this facade" line; `docs/41_db/db_01` line 34 and `db_04` section 1a ("Callers must always import from `db.store`"); `docs/41_db/db_05` section 3 headings naming `db/store.py`.
  - NACK contract docs: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` lines 93/101 describe `nack_event` conditioned on "when consumer_id is provided" — must state the required-consumer contract.
  - Import-linter: `.importlinter` contracts name packages only (`eventbus` isolation contract), no `db.store` / `eventbus.db` module entries — contracts stay as-is; removal only changes intra-package imports. 6 contracts currently kept.

## Problem
- The facades make obsolete entry points look supported and hide the real module and security boundaries. The optional `consumer_id` preserves a call pattern that cannot represent the consumer-scoped authorization and delivery-state model.

## Reason for Change
- Callers should depend on the actual module boundaries, and every NACK must be tied to a validated, authenticated consumer.

## Implementation Intent
- Expose only the current boundaries: storage contracts and helpers from `db.store_protocols`, SQLite implementations from `db.store_impl`, connection operations from `eventbus.db_conn`, event operations from `eventbus.event_repo`, delivery operations from `eventbus.delivery_repo`, DLQ operations from `eventbus.dlq_repo`, and every NACK associated with a validated consumer ID. No package-level alias or wrapper recreates a deleted entry point.

## Requirements
- `REQ-001`: Delete `scripts/db/store.py` and `scripts/eventbus/db.py`; no equivalent re-export is added to any package `__init__.py` (verified `db/__init__.py` imports submodules directly; `eventbus/__init__.py` exports nothing).
- `REQ-002`: Replace every `from eventbus.db import ...` with the responsibility-specific module (`db_conn` for `open_db`/`check_db`/`get_db_lock`, `event_repo` for `insert_event`/`get_seq`/`fetch_events_since`/`fetch_dlq`/`count_dlq`, `delivery_repo` for `nack_event`/`ack_event_for_consumer`/`get_consumer_offset`/`get_resume_position`/`NackResult`, `dlq_repo` for `redeliver_event`), including the two `import eventbus.db as eb_db` module-object uses.
- `REQ-003`: Remove `db.store`-specific tests (`__all__`, wildcard, fixture reload of `db.store`) from `tests/db/test_db_public_api.py`; keep the `db`-module `__all__` tests; update the `db.store` docstring lines in `scripts/db/__init__.py` and `scripts/db/store.py` (deleted).
- `REQ-004`: `nack_event()` takes `consumer_id: str` (no default); an empty `consumer_id` raises `ValueError` before any query; all three `consumer_id is not None` branches and the delivery-state-less `return NackResult("ok")` path are deleted.
- `REQ-005`: The `/nack` route keeps its existing validation (400 on missing/empty consumer_id, 403 via `authorize_event_pair()`, topic authorization, idempotency-key gating); duplicate NACK idempotency keys do not increment the failure count twice; only per-consumer failure state is updated. No deprecation warnings or aliases.
- `REQ-006`: Add removed-name patterns for the facade import paths (`db.store`, `eventbus.db`) to `tools/check_compat_shims.py` `COMPAT_PATTERNS` (full checker-configuration consolidation stays with compatrm004).
- `REQ-007`: Update import-boundary and NACK documentation: `scripts/eventbus/README.md` stub-module section (decision reversed), `docs/41_db/db_01` import-boundary sentence, `docs/41_db/db_04` section 1a rule, `docs/41_db/db_05` section 3, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` NACK contract wording.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed 2026-11-07: every row `Verified` against current
source; `tools/check_plan_target_overlaps.py` reports no overlap involving this Plan;
`tools/check_workitem_structure.py` clean.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/store.py | DELETE | Re-export facade with no live production caller | REQ-001 / AC-001 | Exists (55 lines); grep shows only own docstring + one test | tests/db/test_db_public_api.py (MODIFY) | Verified |
| scripts/eventbus/db.py | DELETE | Re-export facade over the four layer modules | REQ-001 / AC-001 | Exists (42 lines), 15 re-exports | eventbus tests below | Verified |
| scripts/eventbus/delivery_repo.py | MODIFY | `nack_event` signature: `consumer_id: str` required, empty-value `ValueError`, delete three `consumer_id is not None` branches and the no-delivery-state `NackResult("ok")` return | REQ-004, REQ-005 / AC-003 | Lines 37-43 signature, 76, 117-133, 136-150 branches | tests/eventbus/test_eventbus_ack_nack.py (MODIFY) | Verified |
| scripts/eventbus/dlq_route.py | MODIFY | `from eventbus.db import count_dlq, fetch_dlq, redeliver_event` → `event_repo` + `dlq_repo` | REQ-002 / AC-002 | Line 11 | tests/eventbus/test_eventbus_dlq.py | Verified |
| scripts/eventbus/ack_route.py | MODIFY | `from eventbus.db import nack_event as _nack_event` (line 14) and deferred `ack_event_for_consumer` (line 79) → `delivery_repo` | REQ-002 / AC-002 | Lines 14, 79 | tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_ack_endpoint.py | Verified |
| scripts/eventbus/app.py | MODIFY | `from eventbus.db import get_db_lock, open_db` → `db_conn` | REQ-002 / AC-002 | Line 42 | tests/eventbus/test_eventbus_startup.py, tests/eventbus/test_eventbus_shutdown.py | Verified |
| scripts/eventbus/health_route.py | MODIFY | `from eventbus.db import check_db` → `db_conn` | REQ-002 / AC-002 | Line 9 | tests/eventbus/test_eventbus_dlq.py lock usage | Verified |
| scripts/eventbus/publish_route.py | MODIFY | `from eventbus.db import insert_event` → `event_repo` | REQ-002 / AC-002 | Line 13 | tests/eventbus/test_eventbus_dlq_promotion.py | Verified |
| scripts/eventbus/replay_route.py | MODIFY | `from eventbus.db import fetch_events_since` → `event_repo` | REQ-002 / AC-002 | Line 13 | tests/eventbus/test_eventbus_offsets.py | Verified |
| scripts/eventbus/route_helpers.py | MODIFY | Deferred `from eventbus.db import get_db_lock` → `db_conn` | REQ-002 / AC-002 | Line 133 | tests/eventbus/test_eventbus_route_helpers_metrics.py | Verified |
| scripts/db/__init__.py | MODIFY | Module docstring line 8 names `db.store` as the re-export surface | REQ-001, REQ-003 / AC-002 | Line 8; lines 49-60 import submodules directly (no facade use) | tests/db/test_db_public_api.py (MODIFY) | Verified |
| scripts/eventbus/README.md | MODIFY | "Stub Module Pattern" section + "Decision (2026-10-27): Retain this facade" reversed to module-direct imports | REQ-007 / AC-005 | Lines 17-21 | — | Verified |
| tests/eventbus/test_eventbus_ack_nack.py | MODIFY | Facade imports (17 sites) → `delivery_repo`; convert five two-argument `nack_event` calls to pass consumer_id; delete `test_nack_no_consumer_id_unaffected_by_consumer_acks`, `test_nack_same_key_no_increment_no_consumer_id`, `test_nack_different_key_no_consumer_id`; add empty-consumer_id `ValueError` regression test | REQ-002, REQ-004 / AC-003 | Lines 10, 18, 54, 352-781 verified by grep | — | Verified |
| tests/eventbus/test_eventbus_dlq.py | MODIFY | 33 facade `open_db`/`get_db_lock` imports → `db_conn` | REQ-002 / AC-002 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_dlq_promotion.py | MODIFY | 13 facade `open_db` imports → `db_conn` (`nack_event` call already passes consumer_id) | REQ-002 / AC-002 | Lines 142-629 | — | Verified |
| tests/eventbus/test_eventbus_dlq_outbox.py | MODIFY | 10 facade `open_db` imports → `db_conn` | REQ-002 / AC-002 | Lines 160-609 | — | Verified |
| tests/eventbus/test_eventbus_offsets.py | MODIFY | Facade imports (7 sites) → `db_conn`/`event_repo`/`delivery_repo` | REQ-002 / AC-002 | Lines 122-307 | — | Verified |
| tests/eventbus/test_eventbus_restart_resume.py | MODIFY | Facade imports (7 sites) → `db_conn`/`event_repo`/`delivery_repo` | REQ-002 / AC-002 | Lines 153-392 | — | Verified |
| tests/eventbus/test_eventbus_requeue_edge_cases.py | MODIFY | 5 facade `open_db` imports → `db_conn` | REQ-002 / AC-002 | Lines 120-611 | — | Verified |
| tests/eventbus/test_eventbus_crash_ack.py | MODIFY | Facade imports (4 sites) → `db_conn`/`event_repo`/`delivery_repo` | REQ-002 / AC-002 | Lines 45-211 | — | Verified |
| tests/eventbus/test_eventbus_ack_endpoint.py | MODIFY | Facade `get_consumer_offset` import → `delivery_repo` | REQ-002 / AC-002 | Line 320 | — | Verified |
| tests/eventbus/test_eventbus_concurrent.py | MODIFY | Facade `open_db` import → `db_conn` | REQ-002 / AC-002 | Line 74 | — | Verified |
| tests/eventbus/test_eventbus_shutdown.py | MODIFY | `import eventbus.db as eb_db` module-object use (line 163) → module-direct attributes; facade `open_db` imports (311, 397) → `db_conn` | REQ-002 / AC-002 | grep-verified | — | Verified |
| tests/eventbus/test_eventbus_route_helpers_metrics.py | MODIFY | `import eventbus.db as eb_db` module-object use (line 213) → `db_conn` attribute | REQ-002 / AC-002 | grep-verified | — | Verified |
| tests/db/test_db_public_api.py | MODIFY | Delete `db.store` fixture reload, `test_store_all_exists`, `test_store_all_symbols_exist`, `test_store_wildcard_import_works`; keep `db`-module `__all__`/wildcard tests | REQ-003 / AC-001 | Lines 24-66 | — | Verified |
| tools/check_compat_shims.py | MODIFY | Add `COMPAT_PATTERNS` entries for the facade import paths (`\bfrom db\.store import\b`, `\bfrom eventbus\.db import\b`, `\bimport eventbus\.db\b`) | REQ-006 / AC-004 | Pattern mechanism exists (compatrm002 precedent) | tests/tools/test_check_compat_shims.py (no edit: generic iteration verified in compatrm002 plan) | Verified |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md | MODIFY | Line 34 "Callers should always import from `db.store`" → responsibility-specific module rule | REQ-007 / AC-005 | grep-verified | — | Verified |
| docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md | MODIFY | Section 1a rules naming `db/store.py` as "the public API surface" → contracts from `store_protocols`, impls from `store_impl` | REQ-007 / AC-005 | Line 25 | — | Verified |
| docs/41_db/db_05_api_and_operations-protocol-and-backend.md | MODIFY | Section 3 heading "`db/store.py` Protocol Groups" and helper-export sentence | REQ-007 / AC-005 | Lines 18-22 | — | Verified |
| docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md | MODIFY | Lines 93/101 "when consumer_id is provided" wording → required-consumer NACK contract | REQ-007 / AC-005 | grep-verified | — | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/eventbus/db_conn.py | Connection-layer import targets (`open_db`, `check_db`, `get_db_lock`) | REQ-002 |
| scripts/eventbus/event_repo.py | Event-layer import targets (`insert_event`, `get_seq`, `fetch_events_since`, `fetch_dlq`, `count_dlq`) | REQ-002 |
| scripts/eventbus/dlq_repo.py | DLQ-layer import target (`redeliver_event`) | REQ-002 |
| scripts/eventbus/ack_route.py `authorize_event_pair()` call site | Confirms route already validates consumer ownership (403) before `nack_event` | REQ-005 |
| docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md | May restate layer boundaries; checked 2026-11-07: no `eventbus.db` facade reference found, so no edit needed | REQ-007 |
| .importlinter | Import contracts are package-level only; confirms deletion breaks no contract | REQ-002 / AC-004 |
| tools/compat_exceptions.toml | Exceptions manifest the checker reads; no new exception should be needed once all references are deleted | REQ-006 |

## Acceptance Criteria
- AC-001: `scripts/db/store.py` and `scripts/eventbus/db.py` are deleted; no source, test, tool, or active document uses either import path (REQ-001, REQ-003).
- AC-002: No package-level re-export recreates a removed facade; all callers import from the responsibility-specific module (REQ-002).
- AC-003: `consumer_id` is a required non-empty string for `nack_event()`; no caller invokes it without `consumer_id`; no wrapper preserves the old signature; empty `consumer_id` raises `ValueError` (REQ-004).
- AC-004: Unauthorized consumer IDs fail with HTTP 403; duplicate idempotency keys do not increment the failure count twice; the import-linter contracts and static checks stay green and the shim checker rejects the removed import paths (REQ-005, REQ-006).
- AC-005: Import-boundary and NACK documentation name the responsibility-specific modules and the required-consumer contract (REQ-007).
- AC-006: The complete test suite passes.

## Tests
- AST-based repository import scan (or grep gate) for `db.store` and `eventbus.db` returns nothing outside `tools/check_compat_shims.py` pattern literals and this Plan's frozen rows (AC-001).
- NACK unit matrix on `delivery_repo.nack_event`: valid consumer, missing argument (`TypeError`), empty string (`ValueError`), duplicate idempotency key (no double increment), multi-consumer independence (AC-003).
- NACK route integration: 400 missing/empty consumer_id, 403 ungranted consumer, 403 ungranted topic, 422 missing param, 404 unknown event — existing tests must continue to pass unchanged (AC-004).
- `PYTHONPATH=scripts uv run lint-imports` (import-linter) green (AC-004).
- `uv run python tools/check_compat_shims.py` clean before, failing on reintroduced facade imports (AC-004).
- Full suite `uv run pytest tests/` (AC-006).

## Documentation Impact
Yes: REQ-007 drives updates named in the `docs/00_index.md` "Document References by Task" DB and EventBus rows: `docs/41_db/db_01`, `db_04`, `db_05` (import-boundary rules) and `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (NACK contract). `scripts/eventbus/README.md` is a source-tree module document updated in the same row set.

## Assumptions
- Overlap judgments (Step 8b, against Frozen plans; all pairs judged **compatible**):
  - `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` with compatrm001: 001 rewrites the lifecycle sentences (lines 17-20); this Plan edits the import-boundary sentence (line 34). Disjoint regions.
  - `scripts/eventbus/app.py` with compatrm002: 002 edits the auth import/call (lines 26, 84); this Plan edits the facade import (line 42). Disjoint regions.
  - `tools/check_compat_shims.py` with compatrm002/compatrm003: all additions are entries in the same `COMPAT_PATTERNS` dict; non-contradictory, consolidated by compatrm004 later.
  - `tests/eventbus/test_eventbus_ack_nack.py`, `test_eventbus_ack_endpoint.py`, `test_eventbus_crash_ack.py` with compatrm002: 002 edits auth map/fixture regions; this Plan edits facade import lines and NACK call sites. Disjoint regions; land after 002 and re-verify line positions.
- `scripts/db/__init__.py` keeps its existing store-symbol `__all__` (it imports submodules directly and predates the facade; deleting those exports would break unrelated callers and is outside this Issue's "add no equivalent exports" wording, which forbids new re-exports, not existing direct imports). Verified lines 49-60.
- `tests/db/test_db_public_api.py` is modified (facade tests removed), not deleted, because its `db`-module `__all__`/wildcard tests cover the surviving package API.
- The empty-`consumer_id` guard raises `ValueError` at the repository layer; the route's existing 400 guard already prevents it from being reachable through HTTP (AC-004 tests both layers).
- The two `import eventbus.db as eb_db` sites use the module object for attribute access (`eb_db.<attr>`); migration picks the owning layer module per attribute.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Exact attributes accessed through `eb_db` in `test_eventbus_shutdown.py:163` and `test_eventbus_route_helpers_metrics.py:213` | Attribute-access lines not yet enumerated | Enumerate during Phase 1 implementation; both files are in the target table | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/store.py | DELETE | docstring-only references | 1 | 1 | Yes — file sync (stale copy must not survive deploy sync) |
| scripts/eventbus/db.py | DELETE | 8 production import sites | 5 | 1 | Yes — file sync + eventbus service restart |
| scripts/eventbus/delivery_repo.py | MODIFY | every NACK path | 14 | 1 | Yes — service restart |
| scripts/eventbus/ack_route.py | MODIFY | /nack and /ack routes | 13 | 1 | Yes — service restart |
| scripts/eventbus/dlq_route.py | MODIFY | DLQ routes | 3 | 1 | Yes — service restart |
| scripts/eventbus/app.py | MODIFY | lifespan db open/lock | 12 | 1 | Yes — service restart |
| scripts/eventbus/health_route.py | MODIFY | health check | 3 | 1 | Yes — service restart |
| scripts/eventbus/publish_route.py | MODIFY | publish path | 1 | 1 | Yes — service restart |
| scripts/eventbus/replay_route.py | MODIFY | replay path | 1 | 1 | Yes — service restart |
| scripts/eventbus/route_helpers.py | MODIFY | shared route helper | 4 | 1 | Yes — service restart |
| scripts/db/__init__.py | MODIFY | docstring only | 1 | 1 | Yes — file sync |
| scripts/eventbus/README.md | MODIFY | module doc | 2 | 1 | No |
| tests/eventbus/ (12 files) | MODIFY | eventbus test suite imports | 2-18 per file | 1 | No |
| tests/db/test_db_public_api.py | MODIFY | facade tests removed | 0 | 1 | No |
| tools/check_compat_shims.py | MODIFY | CI checker patterns | 10 | 1 | No (tools/ is not deployed) |
| docs/41_db/ (3 files), docs/24_eventbus/eventbus_05 (1 file) | MODIFY | import-boundary + NACK docs | 4-19 | 1 | Yes — docs sync |

## Design
- **Facade deletion, one atomic cutover.** `scripts/eventbus/db.py` removal and the migration of its 8 production import sites + 12 test files land in the same change; no intermediate state leaves a broken import. Import mapping is mechanical (db.py's own import block is the authority): `db_conn` for connection ops, `event_repo` for event ops, `delivery_repo` for delivery ops, `dlq_repo` for `redeliver_event`. Deferred/lazy imports inside functions (`ack_route.py:79`, `route_helpers.py:133`, test-local imports) migrate to the same target modules.
- **`db.store` removal is a docs/test-only change**: production code already imports the submodules directly, so deletion only removes the facade module, its docstring examples (deleted with it), the `db/__init__.py` docstring line, and the facade-specific tests.
- **NACK contract**: `nack_event(conn, event_id, consumer_id: str, last_nack_attempt=None)`. Guard at function entry: `if not consumer_id: raise ValueError(...)`. Delete the `consumer_id is not None` branches: the pre-update acked-consumer check (line 76 block) becomes unconditional, the consumer_delivery UPSERT becomes unconditional, the read-back becomes unconditional, and the trailing delivery-state-less `return NackResult("ok")` disappears (every successful NACK now returns the per-consumer count). Docstring loses the "internal-only" comments and the "None otherwise" sentence.
- **Route unchanged**: `ack_route.nack()` already enforces 400/422 for missing or empty consumer_id and 403 via `authorize_event_pair()`; keep as is (Constraints: topic authorization and idempotency intact).
- **Removed-name protection**: three regex literals in `COMPAT_PATTERNS` match import statements, not the bare words, so they cannot collide with legitimate prose; the existing checker self-reference exception in `tools/compat_exceptions.toml` covers the literals inside the checker source. Full checker configuration consolidation remains with compatrm004.
- **Path notes**: dependency inspection enumerated every importer by grep (8 production sites, 12 test files); historical data — 30-day churn shows the eventbus route/test layer is actively maintained together, supporting the single atomic cutover; `.importlinter` is package-level and unaffected.

## Implementation steps
1. **Phase 1: NACK contract tightening (RED tests first)**
   - [ ] Rewrite `tests/eventbus/test_eventbus_ack_nack.py`: convert the five two-argument `nack_event` calls to pass a consumer_id; delete `test_nack_no_consumer_id_unaffected_by_consumer_acks`, `test_nack_same_key_no_increment_no_consumer_id`, `test_nack_different_key_no_consumer_id`; add missing-argument `TypeError` and empty-string `ValueError` regression tests (REQ-004, REQ-007 AC-003).
   - [ ] Tighten `scripts/eventbus/delivery_repo.py`: required `consumer_id: str`, entry guard, delete the three conditional branches and the no-delivery-state return (REQ-004, REQ-005).
2. **Phase 2: Facade migration and deletion**
   - [ ] Migrate the 8 production import sites in `scripts/eventbus/dlq_route.py`, `ack_route.py`, `app.py`, `health_route.py`, `publish_route.py`, `replay_route.py`, `route_helpers.py` to the layer modules (REQ-002).
   - [ ] Migrate the 12 test files' facade imports, including the two `import eventbus.db as eb_db` module-object uses (REQ-002); resolve UNK-01 during this step.
   - [ ] Delete `scripts/db/store.py` and `scripts/eventbus/db.py`; strip the facade tests from `tests/db/test_db_public_api.py`; update the `scripts/db/__init__.py` docstring line (REQ-001, REQ-003).
   - [ ] Add the three facade-import patterns to `tools/check_compat_shims.py` `COMPAT_PATTERNS` (REQ-006).
3. **Phase 3: Documentation**
   - [ ] Update `scripts/eventbus/README.md` stub-module section, `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`, `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`, `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` (REQ-007).
4. **Phase 4: Verification and deploy check**
   - [ ] Run `uv run pytest tests/eventbus/ tests/db/`, then the full suite; `PYTHONPATH=scripts uv run lint-imports`; `uv run python tools/check_compat_shims.py`; grep gate for `db.store` / `eventbus.db` import paths; `rules/toolchain.md` §1-§8 gates (AC-001-AC-006).
   - [ ] Deployment: file sync (including deletion of the two facade files on the deploy target) + eventbus service restart. No persisted data is touched. No deploy without explicit user approval.

### Release units
**Unit**: facade-cutover | **Phases**: 1, 2 | **Reason**: Phase 2 test migrations import `delivery_repo.nack_event` under the new signature and Phase 1 leaves the old optional parameter in place; deleting the facades before migrating imports breaks collection, so Phases 1+2 must be delivered and validated as one unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/delivery_repo.py | Unit: valid/missing/empty consumer_id, duplicate key, multi-consumer | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` | All pass; no delivery-state-less NACK path |
| scripts/eventbus/ack_route.py | Integration: 400/403/404/422 matrix (existing tests unchanged) | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py` | Route behavior unchanged |
| Facade deletion | Repository-wide import scan | `grep -rn "from eventbus\.db import\|import eventbus\.db\b\|from db\.store import" scripts/ tests/ tools/` | Zero matches |
| Import contracts | Static check | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept |
| tools/check_compat_shims.py | Unit + self-check | `uv run python tools/check_compat_shims.py`; `uv run pytest tests/tools/test_check_compat_shims.py` | Clean before, fail on reintroduction |
| Whole repository | Suite + gates | `uv run pytest tests/`; `uv run ruff check .`; `uv run mypy scripts/`; `uv run bandit -q -r scripts/ -c pyproject.toml`; `uv run radon cc scripts/eventbus/ -s -n B`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; pre-commit | Baselines preserved |

## Risks
- **Risk**: 12 test files + 7 production modules change imports at once; a missed site breaks suite collection → **Mitigation**: the deletion of `eventbus/db.py` itself is the enforcement — any remaining import fails collection immediately; grep gate in Phase 4.
- **Risk**: Deploy target keeps a stale copy of the deleted facade files and old imports → **Mitigation**: deploy runbook step removes `scripts/db/store.py` and `scripts/eventbus/db.py` from the target during file sync (deploy.sh syncs the tree; verify no stale files post-deploy).
- **Risk**: `\bfrom db\.store import\b`-style patterns could match documentation examples that intentionally describe the old path → **Mitigation**: patterns match import syntax only; active docs are rewritten in Phase 3; done/ archives are excluded by the checker's existing path rules (verified precedent).
- **Risk**: `ValueError` from the repository layer could surface as a 500 if a future route forgets its 400 guard → **Mitigation**: the existing route guard remains covered by tests; the guard order (validation before repository call) is asserted by the 400/422 integration tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: NACK contract tightening | Pending | — | — | |
| 2 | Phase 2: Facade migration and deletion | Pending | — | — | |
| 3 | Phase 3: Documentation | Pending | — | — | |
| 4 | Phase 4: Verification and deploy check | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-063921
- **Related target files**: scripts/db/store.py, scripts/eventbus/db.py, scripts/eventbus/delivery_repo.py, scripts/eventbus/dlq_route.py, scripts/eventbus/ack_route.py, scripts/eventbus/app.py, scripts/eventbus/health_route.py, scripts/eventbus/publish_route.py, scripts/eventbus/replay_route.py, scripts/eventbus/route_helpers.py, scripts/db/__init__.py, scripts/eventbus/README.md, tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_dlq.py, tests/eventbus/test_eventbus_dlq_promotion.py, tests/eventbus/test_eventbus_dlq_outbox.py, tests/eventbus/test_eventbus_offsets.py, tests/eventbus/test_eventbus_restart_resume.py, tests/eventbus/test_eventbus_requeue_edge_cases.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_ack_endpoint.py, tests/eventbus/test_eventbus_concurrent.py, tests/eventbus/test_eventbus_shutdown.py, tests/eventbus/test_eventbus_route_helpers_metrics.py, tests/db/test_db_public_api.py, tools/check_compat_shims.py, docs/41_db/db_01_architecture_and_schema-overview-and-config.md, docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md, docs/41_db/db_05_api_and_operations-protocol-and-backend.md, docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md

### Requirement Traceability
| Requirement ID | Source | Acceptance Criteria | Implementation Target Files | Procedure | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md Required Changes | AC-001, AC-002 | scripts/db/store.py, scripts/eventbus/db.py, scripts/db/__init__.py | — | Planned |
| REQ-002 | same, Required Changes | AC-002 | production route/app rows + eventbus test rows | — | Planned |
| REQ-003 | same, Required Changes | AC-001 | tests/db/test_db_public_api.py, scripts/db/__init__.py | — | Planned |
| REQ-004 | same, Required Changes | AC-003 | scripts/eventbus/delivery_repo.py, tests/eventbus/test_eventbus_ack_nack.py | — | Planned |
| REQ-005 | same, Constraints | AC-004 | scripts/eventbus/ack_route.py, scripts/eventbus/delivery_repo.py | — | Planned |
| REQ-006 | same, Acceptance Criteria (static checks) | AC-004 | tools/check_compat_shims.py | — | Planned |
| REQ-007 | same, Documentation Impact | AC-005 | scripts/eventbus/README.md, docs/41_db/db_01, db_04, db_05, docs/24_eventbus/eventbus_05 | — | Planned |

## Freeze Decision Log

| Timestamp | Freeze status | Validation evidence |
|---|---|---|
| 2026-11-07 06:42 | Frozen | All `Implementation Target Files` rows `Verified` against HEAD `1b2dded66`: facade files exist (`scripts/db/store.py` 55 lines, `scripts/eventbus/db.py` 42 lines); the 8 production import sites (`dlq_route.py:11`, `ack_route.py:14/79`, `app.py:42`, `health_route.py:9`, `publish_route.py:13`, `replay_route.py:13`, `route_helpers.py:133`) and 12 test importer files enumerated by repository grep in this cycle; `nack_event` signature `delivery_repo.py:37-43` with three `consumer_id is not None` branches and the no-delivery-state return verified by source read; two-argument call sites (5) and the three no-consumer tests verified by grep in `tests/eventbus/test_eventbus_ack_nack.py`; doc lines (`README.md:17-21`, `db_01:34`, `db_04:25`, `db_05:18-22`, `eventbus_05:93/101`) spot-checked. `tools/check_workitem_structure.py` clean; `tools/check_plan_target_overlaps.py` reports no overlap involving this Plan (the single reported finding is the pre-judged compatrm001/compatrm002 pair). No blocking Unknown: UNK-01 `Blocking? = False`. |
