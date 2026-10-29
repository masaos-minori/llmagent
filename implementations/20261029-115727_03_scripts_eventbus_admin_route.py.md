## Goal

Give the admin topics-authorization audit record the real request id, the acting principal's fingerprint, a non-sensitive scope-change summary and `persistent=false` (`REQ-001`, `REQ-002`, `REQ-004`; AC-1, AC-3).

## Scope

Modify `scripts/eventbus/admin_route.py` only: the `update_topics_authorization` signature, the audit call at lines 141-147, and a new module-level helper that counts changed mapping entries. Validation, no-op detection, the log line and the response shape are unchanged.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): the handler is `async def update_topics_authorization(request: Request) -> dict[str, Any]` at `admin_route.py:74`; the single audit call is at `:141-147` with `consumer_id="admin"`, `request_id=""`, `target="topics_authorization"`, `detail="updated"`; the response with `"persistent": False` is returned at `:150`; the effective-change boolean is computed just before the call.
- `request.state.request_id` is set by the auth middleware (`auth.py:417`) for every route; the handler already holds the `Request`.
- Sequencing: `implementations/20261029-101422_02_scripts_eventbus_admin_route.py.md` (archived plan `plans/done/20261029-091959_eventbus001_admin-authz-publish-order.md`) reorders the publish block at lines 125-135 of this file and adds a `_build_principal_map` (new) import. Land that procedure first, then re-anchor the audit-call line numbers here; the two edits touch disjoint regions.
- UNK-03 format fixed here: `detail` is a semicolon-joined `key:count` summary of the provided mappings that actually changed, followed by `persistent:false`, e.g. `consumer_authorization:1;persistent:false`. Mappings with zero changed entries are not listed.

## Design decisions

- New helper `_changed_count(old: dict[str, list[str]], new: dict[str, list[str]]) -> int` counts keys whose topic lists differ plus added/removed keys: `sum(1 for k in set(old) | set(new) if old.get(k) != new.get(k))`.
- The handler captures the previous `consumer_authorization` / `topic_authorization` mappings before the config replacement, computes a count per provided mapping, and builds the detail string only for the changed mappings; the no-op case (no effective change) emits no record, as today.
- `actor=principal.token_fingerprint` is passed to `log_privileged_action` (seq 01 signature); the new `principal: Principal` parameter is added after `request` and app.py passes it (seq 02).

## Alternatives considered

- Recording counts inside `persistent` as a record key: rejected; the record API (seq 01) only adds `actor`, and the Plan allows the `persistent` marker inside `detail` (UNK-03 decision above).
- Dumping the changed mapping keys themselves: rejected; only counts are needed to answer "what changed", and counts minimize topic disclosure.

## Implementation
### Target file

`scripts/eventbus/admin_route.py`

### Procedure

1. Add `principal: Principal` to the `update_topics_authorization` signature (after `request`) and extend the import at line 11 to `from eventbus.auth import Principal, _populate_token_maps` (adjusted to whatever the landed 101422_02 state is for `_populate_token_maps`/`_build_principal_map` (new)).
2. Add the module-level helper `_changed_count` (new) (typed, one-liner body) near the other helpers.
3. Before publishing the new config, capture the old mappings and compute `counts: dict[str, int]` for the provided mappings.
4. Replace the audit call arguments: `request_id=request.state.request_id`, `detail` built as `";".join([f"{name}:{count}" for name, count in changed entries] + ["persistent:false"])`, `actor=principal.token_fingerprint`; keep `consumer_id="admin"` and `target="topics_authorization"`.

### Method

Direct edits inside the handler; no new imports beyond `Principal`.

### Details

- Keep the `if changed:` guard so the no-op path emits nothing (existing tests pin this).
- `detail` for the common single-mapping case is e.g. `consumer_authorization:1;persistent:false`; for both mappings changed: `consumer_authorization:2;topic_authorization:1;persistent:false`.

## Compatibility considerations

- `detail` value changes from `updated` to the summary string; existing tests asserting `detail == "updated"` are updated by seq 07 in the same plan batch.

## Security considerations

- The summary contains only mapping names and integer counts plus the constant `persistent:false`; no token, topic list, or consumer id appears. `actor` is the non-secret fingerprint.

## Rollback considerations

- Revert this file to restore `request_id=""` / `detail="updated"`; seq 02/07 must be reverted together with this row (signature and test coupling).

## Validation plan

- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` (extended tests in seq 07 assert request id non-empty, actor equals the admin token fingerprint, detail shape, no-op silence).
- `uv run ruff check scripts/eventbus/admin_route.py` and `uv run mypy scripts/eventbus/admin_route.py`.

## Completion criteria

- Effective-change audit record carries non-empty `request_id`, non-empty `actor`, a `key:count` summary and `persistent:false` in `detail`; no-op still emits nothing; static gates clean.

## Out of Scope

- The publish-order reordering (101422_02), validation logic, response body, and the audit helper itself (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land after 101422_02 and after seq 01/02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are seq 07 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Doc rows are seq 10 |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004 (AC-1, AC-3); UNK-03 format decision recorded here
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: scripts/eventbus/admin_route.py
