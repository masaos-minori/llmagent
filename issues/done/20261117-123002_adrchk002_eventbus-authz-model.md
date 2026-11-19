# Redesign the EventBus authorization model and complete ADR-013

## Priority
High

## Summary
The EventBus authorization code and ADR-013 disagree on consumer identity, role concentration, publish authorization, configuration validation, and auditing. Fix them together because they share the same files.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H02`; merged from ADRCHK-H02, M13, M16, M17, M19, L07, L15, L22 (review findings N34, N44, N52, N53, M9, M10, N13)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
All claims below come from the review (`Documentation only` until re-verified).

## Reason for Change
- Consumers are not isolated: every `consumer_authorization` pair attaches to the single CONSUMER principal built from `consumer_token`, and `ack_route.py` checks only the (`consumer_id`, topic) pair. A holder of the consumer token can ACK or NACK as another consumer, move its offset, and push its events into the DLQ. ADR-013 requires an explicit consumer identity binding.
- Roles are concentrated: the shared `auth_token` grants OPERATOR, MONITORING, and ADMIN. One leaked token can replay every topic (`/replay` has no topic authorization) and rewrite authorization. ADR-013 does not record this as an accepted risk.
- Publish is open: any PUBLISHER can publish to any topic, `producer` comes from the request body and can be forged, and a JSONL append failure after the DB commit is only logged. ADR-006 does not say whether the JSONL file is canonical, a mirror, or optional.
- Configuration checks are incomplete or unreachable: nothing validates the per-role token rule that a config comment states, the `admin_token` principal is built twice, and the 500 branch in `resolve_principal` for an empty `auth_token` cannot run because config load rejects it.
- ADR-013 is incomplete: generation compare-and-swap, the 409 conflict, TTL, the expiry sweep, and the restart baseline have no Invariants; Decision Details references do not match the list; `admin_route.py`, `authz_ttl.py`, and `test_admin_topics_authorization.py` are missing from Scope and Implementation References; a TTL grant loses its expiry when it returns to the baseline; the requeue value `delivery: "replay"` is undefined.
- Audit records cannot be told apart: authorization changes use `privileged_action`, `error_type` has no value for the 409 conflict or TTL removal, and the EventBus `attach_auth_middleware` shares a name with the MCP authentication middleware.

## Implementation Intent
- A request can act only as the consumer IDs bound to its credential; role and topic rights follow least privilege, or a recorded decision accepts the risk.
- Every authorization behavior in the code maps to an ADR-013 Invariant and a test, and ADR-013 describes only behavior that exists.
- Configuration errors are rejected at load, and no unreachable security branch remains.
- The audit log separates authorization changes, conflicts, and expiries.

## Target Files or Areas
- `scripts/eventbus/auth.py`
- `scripts/eventbus/config.py`
- `scripts/eventbus/ack_route.py`
- `scripts/eventbus/publish_route.py`
- `scripts/eventbus/replay_route.py`
- `scripts/eventbus/admin_route.py`
- `scripts/eventbus/audit.py`
- scripts/eventbus/app.py (middleware name)
- `config/eventbus.toml`
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
- docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md (JSONL role only)
- `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
- `docs/10_adr/adr_01_index.md`
- `tests/eventbus/`

## Required Changes
- (no decision needed) Validate per-role token presence at config load, build each principal once, and remove the unreachable 500 branch.
- (no decision needed) Add separate audit event names for authorization changes, 409 conflicts, and TTL removals.
- (no decision needed) Rename the EventBus request-ID middleware and update its callers and tests.
- (no decision needed) Fix the ADR-013 formatting, decision references, Scope, and Implementation References; document the TTL baseline behavior and the `delivery: "replay"` value.
- (decision) Consumer identity: per-consumer tokens (recommended) or a recorded accepted risk.
- (decision) Role concentration in the shared `auth_token`: split it, or record the accepted risk.
- (decision) Publish: per-topic authorization, `producer` taken from the principal, and the role of the JSONL file.
- (decision) Add ADR-013 Invariants for generation compare-and-swap, the TTL bound, and the expiry sweep, each with a test.

## Constraints
- Do not change authorization behavior for a decision task before the decision is recorded.
- Before editing `docs/` or the middleware name, check `docs/24_eventbus/` and `tests/eventbus/` callers with `rg`.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- If per-consumer tokens are chosen, a token bound to consumer A gets 403 when it ACKs or NACKs as consumer B (test).
- A config without a token for a required role fails load (test).
- Each runtime behavior in `admin_route.py` and `authz_ttl.py` maps to an ADR-013 Invariant and a test.
- ADR-013 Decision and Ongoing Risks agree with the code.

## Testing Expectations
Unit and regression tests under `tests/eventbus/` for each behavior above; write the failing test first for each code task. Run mypy, ruff, bandit, import-linter, and the ADR checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-013 (Invariants, Scope, Implementation References, Ongoing Risks), the JSONL role in ADR-006, the DLQ semantics guide, and the Index matrix.

## Out of Scope
- Database schema or DDL changes.
- The subscribe route (not reviewed).

## Dependencies
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` blocks the new-Invariant task (pending-amendment form and approval record).
- `issues/20261117-123017_adrchk017_eventbus-task-supervision.md` edits `authz_ttl.py` and `auth.py`; fix the order with the owner.

## Unresolved Questions
- The subscribe route was not reviewed. Needs `scripts/eventbus/subscribe_route.py` (path assumed) and `scripts/eventbus/route_helpers.py`.

## AI Implementation Instruction
- Finish the no-decision tasks first. For each decision task, write an option table with risk and effort, and stop.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123002
- **Related target files**: `scripts/eventbus/auth.py`; `scripts/eventbus/config.py`; `scripts/eventbus/ack_route.py`; `scripts/eventbus/publish_route.py`; `scripts/eventbus/replay_route.py`; `scripts/eventbus/admin_route.py`; `scripts/eventbus/audit.py`; `scripts/eventbus/app.py (middleware name)`; `config/eventbus.toml`; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`; `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md (JSONL role only)`; `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`; `docs/10_adr/adr_01_index.md`; `tests/eventbus/`
