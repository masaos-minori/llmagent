# Decide on and apply the removal of the eventbus.db re-export facade

## Priority
Medium

## Summary
Decide whether `scripts/eventbus/db.py` stays as the documented single entry point for EventBus persistence or is removed in favor of direct imports from the layer modules, and, if removal is chosen, migrate all callers, delete the facade and guard against its return.

## Background
Source: `memo-issue.md` item H-02, re-verified against current source on 2026-10-27 (Confirmed by repository search). The memo called the facade "likely a removable stub" and left caller coverage unverified.

- `scripts/eventbus/db.py` only re-exports 13 names from `eventbus.db_conn`, `eventbus.event_repo`, `eventbus.delivery_repo` and `eventbus.dlq_repo` (`open_db`, `check_db`, `get_db_lock`, `insert_event`, `get_seq`, `fetch_events_since`, `fetch_dlq`, `count_dlq`, `nack_event`, `ack_event_for_consumer`, `get_consumer_offset`, `get_resume_position`, `NackResult`, `redeliver_event`). Its docstring and `scripts/eventbus/README.md` ("Stub Module Pattern") present it as a deliberate single entry point.
- Production importers (7 files): `scripts/eventbus/ack_route.py` (one module-level and one deferred import), `app.py`, `dlq_route.py`, `health_route.py`, `publish_route.py`, `replay_route.py`, `route_helpers.py` (deferred import).
- Test importers (9 files): `tests/eventbus/test_eventbus_ack_endpoint.py`, `..._ack_nack.py`, `..._concurrent.py`, `..._crash_ack.py`, `..._dlq.py`, `..._dlq_promotion.py`, `..._offsets.py`, `..._requeue_edge_cases.py`, `..._restart_resume.py`. No `tools/` file imports it.
- Documents naming the facade: `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (Implementation References: "facade that re-exports the functions above") and `scripts/eventbus/README.md`. The `docs/` tree has no other hit.
- Prior decision to respect: `issues/done/20261022-124204_ebdocwording_align-eventbus-facade-wording.md` kept the facade and only corrected its wording, stating that the README's "single entry point" description matches the intended wording. The memo's premise ("not a canonical public API") therefore contradicts a recent recorded decision and has not been re-approved by the owner.

## Problem
Whether the facade is canonical API or a removable compatibility stub is not decided in one place: the ADR and README treat it as intended, the memo treats it as a leftover. Until decided, neither removal nor retention can be justified, and the compatibility checker cannot be told which to enforce.

## Reason for Change
The facade hides which layer owns each transaction and lock from route code, and the repository already split the layers. This is a maintainability and ownership-clarity matter, not a defect, and it is not time-sensitive; the decision is needed before any removal work.

## Implementation Intent
Step 1: the owner decides retain or remove. If retain: close this issue by recording the decision (ADR/README wording already matches) and add the facade to the compatibility checker as an allowed canonical entry. If remove: migrate each caller to the owning layer module (connection and lock to `eventbus.db_conn`, event persistence and reads to `eventbus.event_repo`, ACK/NACK and offsets to `eventbus.delivery_repo`, DLQ requeue to `eventbus.dlq_repo`), delete `db.py`, update the README and ADR reference line, and add a checker rule that fails on any `eventbus.db` import or on the file's reappearance.

## Target Files or Areas
- `scripts/eventbus/db.py`
- `scripts/eventbus/ack_route.py`, `app.py`, `dlq_route.py`, `health_route.py`, `publish_route.py`, `replay_route.py`, `route_helpers.py`
- the 9 test files under `tests/eventbus/` listed in Background
- `scripts/eventbus/README.md`
- `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` (Implementation References line only)
- `tools/check_compat_shims.py` and its tests (removal case only)

## Required Changes
- Record the owner decision (retain or remove) in this issue before planning.
- If removal is chosen: migrate the 7 production and 9 test importers; re-run `rg` for `from eventbus.db import`, `import eventbus.db` and `from eventbus import db` to confirm zero callers; delete `scripts/eventbus/db.py`; remove the "Stub Module Pattern" section and the ADR facade line; add the checker rule; run `tools/check_mock_patch_targets.py` because module-level imports in the routes change what a `patch(...)` target must be.
- If retention is chosen: no code change; add the retention rationale where the checker or README states it.

## Constraints
- Transaction, lock and shutdown behavior of EventBus must not change.
- `docs/10_adr/*.md` edits must pass `tools/check_adr_preservation.py`: only the reference line may change, no invariant, Decision or Approval text.
- The `eventbus-is-isolated` import-linter contract must still pass.
- Removal touches 16 files; record the blast radius in the plan.

## Acceptance Criteria
- The decision is recorded.
- If removal: no `eventbus.db` importer remains in `scripts/`, `tests/` or `tools/`; `scripts/eventbus/db.py` does not exist; the compatibility checker fails on a reintroduced import or file; README and ADR name the layer modules as the reference.
- If retention: the issue is closed with the rationale recorded and no code change.
- `uv run pytest tests/eventbus -q` passes, covering ACK/NACK, offsets, DLQ, shutdown and schema tests.

## Testing Expectations
- `uv run pytest tests/eventbus`, then the full suite, mypy (`--no-namespace-packages`), `PYTHONPATH=scripts uv run lint-imports`, ruff.
- `uv run python tools/check_mock_patch_targets.py`, `tools/check_compat_shims.py --check-removed-names --check-doc-symbols`, `tools/check_adr_preservation.py`, and the docs checkers for the edited README/ADR (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain eventbus`).

## Documentation Impact
Yes if removal is chosen: README layer description and the ADR-006 implementation reference. Record boundaries only (which layer owns connection, events, delivery, DLQ); no history note and no function-by-function restatement.

## Out of Scope
- Changing repository function behavior or signatures.
- Other re-exports (for example `db.store`, which is a documented public API and stays).
- The MCP Health and discovery changes (see `issues/*mcpcompat001*`).

## Dependencies
- Shares `tools/check_compat_shims.py` with `mcpcompat001` and `mcpcompat003` of this batch; sequence the checker edits.
- Related done issue: `issues/done/20261022-124204_ebdocwording_align-eventbus-facade-wording.md` (decided to keep the facade; this issue may supersede that decision only with owner approval).
- No open issue or in-flight plan touches `scripts/eventbus/db.py`.

## Unresolved Questions
- 不明: owner decision, retain or remove the facade (blocking; the memo recommends removal, the ADR/README and the 2026-10-22 issue keep it).
- 不明: why `ack_route.py` and `route_helpers.py` use deferred imports of the facade (circular-import avoidance or test patching); to be checked before moving them.
- 不明: whether any test patches a facade-imported name at the route module level (not searched).

## AI Implementation Instruction
Do not start code changes until the decision is recorded. Under removal, change imports only; do not alter function bodies, SQL or lock handling. Re-run the caller search immediately before deleting `db.py`. Do not touch ADR decision text. Stop and report if any importer outside the listed files appears.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-104252
- **Related target files**: scripts/eventbus/db.py, scripts/eventbus/ack_route.py, scripts/eventbus/app.py, scripts/eventbus/dlq_route.py, scripts/eventbus/health_route.py, scripts/eventbus/publish_route.py, scripts/eventbus/replay_route.py, scripts/eventbus/route_helpers.py, scripts/eventbus/README.md, docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md, tools/check_compat_shims.py
