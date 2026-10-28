# Record request id and authenticated actor in privileged-action audit records

## Priority
Medium

## Summary
Make every privileged-action audit record carry the originating request id and a non-secret identifier of the authenticated principal, and stop emitting an empty `error_type` for successful actions.

## Background
Source: `memo-issue.md` item 06 (audit part), re-verified against current source on 2026-10-28.

- `log_privileged_action()` in `scripts/eventbus/audit.py` has three callers. `update_topics_authorization()` in `scripts/eventbus/admin_route.py` passes `consumer_id="admin"` and `request_id=""`. `dlq_requeue()` in `scripts/eventbus/dlq_route.py` and the replay handler in `scripts/eventbus/replay_route.py` pass `consumer_id=""` (rendered as `-`) with the real `request.state.request_id`. `Explicit in code`.
- No caller records which credential acted. `Principal.token_fingerprint` (a SHA-256 prefix of the token, never the token) already exists for audit use, and `log_auth_failure` callers carry `request.state.request_id`. `Explicit in code`.
- `log_privileged_action()` always builds the record with `error_type=""`; the module docstring defines `error_type` as a failure-mode identifier and tells callers never to emit an empty `detail`. `Explicit in code`.
- The admin update emits a record only for an effective change, with `detail="updated"`; it does not say what scope changed. `Explicit in code`.
- `tests/eventbus/test_admin_topics_authorization.py` patches `log_privileged_action` and asserts one call with redacted detail (`test_audit_emitted_on_effective_change`) and none for a no-op (`test_audit_not_emitted_on_noop`); it asserts no request id or actor. `Explicit in code`.
- Prior work: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md` addressed earlier metrics and health items; it does not cover audit correlation fields.

## Problem
A privileged action cannot be tied to the request that caused it (admin updates) or to the credential that performed it (all three actions), and successful records carry an always-empty failure field. An investigator cannot answer "which token changed the authorization mapping".

## Reason for Change
These are the highest-privilege operations on the bus (authorization changes, DLQ requeue, replay), and their audit trail is the only record of who did them. No incident is cited; severity is Medium (security-relevant observability gap, no demonstrated misuse).

## Implementation Intent
Pass the authenticated principal's fingerprint and the request id into each privileged-action record, define a documented value (or omit the field) for `error_type` on success, and add a short, non-sensitive summary of what changed for the authorization update. Never log a raw token.

## Target Files or Areas
- `scripts/eventbus/audit.py`
- `scripts/eventbus/admin_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`
- `scripts/eventbus/app.py` (the route wrappers that hold the principal)
- `tests/eventbus/test_admin_topics_authorization.py` and the DLQ and replay audit tests
- `docs/24_eventbus/` audit documentation, if it describes these records

## Required Changes
- Record `request.state.request_id` in the admin update record.
- Record the principal's `token_fingerprint` as the actor in all three privileged actions.
- Make `error_type` optional for successful events, or define one canonical non-empty success value; update the `AuditRecord` typing and docstring accordingly.
- For the authorization update, add a non-sensitive summary of the changed scope (which mappings changed and counts) and `persistent=false`.
- Update the callers' tests to assert the new fields.

## Constraints
- Never log raw tokens, topic names beyond what the current redaction allows, or consumer ids that are secret-like; keep the existing redaction behavior.
- Keep one JSON line per record and the existing field names so log parsers keep working (additive change).
- `docs/` edits follow `skills/DESIGN.md` Docs content policy.

## Acceptance Criteria
- Every privileged-action record contains a non-empty `request_id` and an actor fingerprint, and no raw credential.
- A successful record has no empty `error_type` (omitted or a documented value).
- The authorization update record states what changed without listing secrets.
- Tests assert the new fields for the admin update, DLQ requeue and replay.

## Testing Expectations
- Unit tests on `_build_audit_record`/`log_privileged_action` field shape.
- Route tests for each of the three actions asserting request id and actor, and that no token value appears in the captured log.
- `uv run pytest tests/eventbus`, mypy and ruff on changed files.

## Documentation Impact
Yes, small: describe the audit record fields (operational notes) in the EventBus docs if they list them; otherwise none.

## Out of Scope
- Authentication failure records (`log_auth_failure`).
- Audit log storage, rotation or shipping.
- Authorization model changes.

## Dependencies
- Coordinate with the archived `plans/done/20261028-092616_ebauth001_enforce-pairwise-consumer-authorization.md`: its pending procedure `implementations/20261028-114911_04_scripts_eventbus_app.py.md` edits the ACK/NACK wiring in `scripts/eventbus/app.py`; this issue edits the admin route wrapper in the same file. The regions differ; rebase when both are implemented.

## Unresolved Questions
- Should `error_type` be omitted on success or carry a fixed value such as `none`? `Needs confirmation` (design decision).
- Is the token fingerprint an acceptable actor identifier for operators, or is a configured token label wanted? `Needs confirmation`.

## AI Implementation Instruction
Keep the change additive and limited to the audit fields. Do not log token values and do not change authorization behavior. If passing the principal into a route requires a signature change beyond the wrapper, stop and report.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122415
- **Related target files**: `scripts/eventbus/audit.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/app.py`, `tests/eventbus/test_admin_topics_authorization.py`, `docs/24_eventbus/`
