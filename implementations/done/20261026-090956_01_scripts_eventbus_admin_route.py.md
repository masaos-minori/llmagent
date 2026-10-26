## Goal

Make `update_topics_authorization()` (`scripts/eventbus/admin_route.py`) publish the new
config and the token→principal map as one auditable generation, report whether the update
is runtime-only or persistent, reject or explicitly report empty/no-op bodies, and emit a
redacted privileged-action audit record for every effective change — without changing the
fail-closed `resolve_principal()` contract.

## Scope

- Modify only `scripts/eventbus/admin_route.py`, `update_topics_authorization()`
  (current lines 73-112).

## Assumptions

- `app.state.config` is read per request via `get_config(request)`; the swap is a single
  reference assignment visible atomically to other handlers under the GIL.
- `_populate_token_maps()` (auth.py:97) is kept as the single population entry point; the
  admin handler drives it through the same production path the startup lifecycle uses.
- The owner decision on UNK-01 (runtime-only default) and UNK-02 (empty/no-op handling) is
  recorded before this row is executed; this procedure implements the plan's recommended
  branches and flags the alternative in Design decisions.
- `log_privileged_action()` (audit.py:129) is reusable as-is; its convention is
  `log_privileged_action(consumer_id, request_id, route, target, detail="")` per
  dlq_route.py:72 / replay_route.py:38.

## Design decisions

- **One generation.** Build the new principal map completely and publish it together with
  the new config via one ordered sequence so no request observes a mixed or empty
  generation. Build-and-publish the map first, then commit the config swap; roll back the
  config swap if the publish raises, so a failed rebuild leaves the previous generation in
  force (REQ-001; Acceptance 1, 5).
- **Effective-change gating.** Only emit `log_privileged_action` when `replacements` is
  non-empty and actually changes state; a no-op emits nothing (REQ-003, REQ-004; INV-05).

## Alternatives considered

- Publishing the map and config as two independent swaps inside one lock: rejected because
  a concurrent request between the two swaps observes a mixed generation.
- Returning `{"status": "ok", "changed": false}` for empty bodies vs. rejecting with
  422/400: the plan records this as UNK-02; this procedure rejects (see Assumptions).

## Implementation

### Target file

`scripts/eventbus/admin_route.py`

### Procedure

1. In `update_topics_authorization()`, after building `replacements` (lines 95-99), keep
   the `if replacements:` guard (line 101) as the effective-change test.
2. Inside the guard, reorder so the principal map is published before the config swap:
   call `_populate_token_maps(config)` (currently line 109) first, then perform
   `dataclasses.replace(...)` + `request.app.state.config = config` (currently lines 106-107).
   Wrap the publish in a try/except that rolls back `request.app.state.config` to the
   pre-update value if `_populate_token_maps()` raises.
3. After a successful publish+swap, emit
   `log_privileged_action(consumer_id="", request_id=request.state.request_id,
   route="/admin/topics/authorization", target="topics_authorization", detail="<redacted summary>")`
   before returning (REQ-003). No token values are passed (INV-05).
4. Change the return at line 112 from `{"status": "ok"}` to include the persistence flag
   and a change indicator, e.g. `{"status": "ok", "persistent": <bool>, "changed": true}`.
5. For the empty-body case (`{}` or body equal to current value, i.e. `replacements` empty),
   return `{"status": "ok", "changed": false}` WITHOUT repopulating the map and WITHOUT
   emitting an audit record (REQ-004). Do not fall through to the bare success path.
6. Keep the function raising `ValueError` on validation failures unchanged.

### Method

Edit `update_topics_authorization()` in place; no new module-level symbols required unless
the rollback needs a captured pre-update config snapshot (a local variable suffices).

### Details

- Capture `previous_config = request.app.state.config` at function entry for the rollback.
- The redacted `detail` summarizes the changed authorization fields without token values,
  e.g. `"consumer_authorization=<set>"`.
- `_populate_token_maps()` remains the sole population entry point; the handler does not
  touch `_TOKEN_PRINCIPAL_MAP` directly (supports REQ-006 at the admin layer).

## Compatibility considerations

- The response gains two fields (`persistent`, `changed`); existing consumers that read
  `status` are unaffected. No `scripts/` caller exists under the repo (plan Assumptions).

## Security considerations

- The audit record must never carry token values (INV-05, REQ-008); the detail string is
  redacted.
- The build-before-swap ordering removes the empty-map window that let concurrent requests
  see 401 mid-update (REQ-001).

## Rollback considerations

- Revert the commit; the rollback restores the previous generation because the config swap
  is reverted on publish failure.

## Validation plan

- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` — assert one-generation
  publish (no empty-map window), the `persistent` field, empty/no-op not reported as
  success, and audit emission only on effective change.
- `uv run pytest tests/eventbus/` — full EventBus suite passes; no behavior regression.
- `uv run radon cc scripts/eventbus/admin_route.py`; keep `update_topics_authorization` at
  or below B (6). `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- An effective update publishes the map and config atomically, returns `persistent`/`changed`,
  and emits exactly one redacted audit record; an empty/no-op body returns `changed: false`
  without repopulating the map or emitting an audit record.

## Out of Scope

- Changes to `resolve_principal()`'s fail-closed contract (auth.py).
- The persistence default itself (UNK-01) — implement the recorded owner decision; if
  unresolved, stop and ask the owner before executing this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the atomic, audited admin handler in `admin_route.py` | Pending | — | — | UNK-01/UNK-02 owner decisions must be confirmed before execution |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation (ADR-013) if in scope | Pending | — | — | Covered by seq 11 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | UNK-01 (runtime-only vs persistent) and UNK-02 (empty/no-op status) are owner decisions | Partially — classified non-blocking 2026-10-25; concrete values still needed | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `scripts/eventbus/admin_route.py`
