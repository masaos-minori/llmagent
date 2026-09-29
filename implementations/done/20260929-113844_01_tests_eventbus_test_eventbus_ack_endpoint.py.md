## Goal
Reorder `principal_client`'s `_TOKEN_PRINCIPAL_MAP["consumer-token"]` override to run
after `TestClient(eb_app.app)`'s `lifespan` startup, and fix the fixture's stale
comment (REQ-001; REQ-002).

## Scope
- **In-Scope**: The `principal_client` fixture in
  `tests/eventbus/test_eventbus_ack_endpoint.py` (lines 44-82) only — moving the
  existing override block and correcting one comment.
- **Out-of-Scope**: `scripts/eventbus/ack_route.py`, `scripts/eventbus/auth.py`,
  `scripts/eventbus/app.py` (investigation confirmed their authorization logic is
  correct; not modified); any other fixture or test in this file; the separate
  test-hygiene observation about dead-patch issues in an unrelated file's tests
  (out of this Plan's scope entirely).

## Assumptions
- `TestClient(eb_app.app).__enter__()` runs the `lifespan` startup handler
  synchronously before returning, so a mutation made immediately after entering the
  `with` block is guaranteed to run after `_populate_token_maps()`'s startup call
  (Plan Assumptions — standard, already-relied-upon `TestClient` behavior, not
  independently re-verified against the installed library's source here).
- No other test file imports/reuses `principal_client` in a way that depends on its
  current override timing (Plan UNK-01) — run `rg -l "principal_client" tests/`
  during this cycle's Step 4a verification to confirm before editing.

## Design decisions
- Reorder in place (move the existing override block) rather than introducing a new
  fixture parameter, monkeypatch, or FastAPI dependency-override mechanism — the existing
  `_TOKEN_PRINCIPAL_MAP` mutation approach already works correctly for the app's
  actual runtime dependency-injection path; the only defect is *when* it runs
  relative to `lifespan` startup (per `skills/python-design` — minimal, root-cause-scoped
  fix, no new abstraction needed for a two-block reorder).

## Alternatives considered
- Monkeypatch `_populate_token_maps` itself to skip resetting `consumer-token` —
  rejected: would diverge from testing the real startup path and could mask a future
  regression in `_populate_token_maps` itself.
- Add a second, later call to re-apply the override right before each request in the
  test bodies instead of the fixture — rejected: duplicates the override at every
  call site instead of fixing it once at its source (the fixture), and does not fix
  the stale comment (REQ-002).

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure
1. In the `principal_client` fixture, remove the `if "consumer-token" in
   _TOKEN_PRINCIPAL_MAP: ...` override block from its current position (before
   `with TestClient(eb_app.app) as c:`).
2. Re-insert the same override block immediately after `with TestClient(eb_app.app)
   as c:` is entered, before `c.headers["Authorization"] = "Bearer consumer-token"`.
3. Update the block's preceding comment to describe the current
   `_TOKEN_PRINCIPAL_MAP`-based mechanism instead of the stale `_TOKEN_CONSUMER_MAP`
   reference.

### Method
Direct text edit: move one existing code block (no new logic), edit one comment
line — no new imports, fixtures, or dependencies.

### Details
Current fixture body (confirmed via direct read, lines 44-82):
```
def principal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    ...
    cfg = EventBusConfig(...)
    _populate_token_maps(cfg)
    # Map consumer-token to a specific consumer ID for authorization testing
    from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal

    if "consumer-token" in _TOKEN_PRINCIPAL_MAP:
        _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
            roles=_TOKEN_PRINCIPAL_MAP["consumer-token"].roles,
            allowed_consumer_ids=frozenset({"consumer-A"}),
            allowed_topics=_TOKEN_PRINCIPAL_MAP["consumer-token"].allowed_topics,
            token_fingerprint=_TOKEN_PRINCIPAL_MAP["consumer-token"].token_fingerprint,
        )
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c
```

New fixture body — move the `_TOKEN_PRINCIPAL_MAP` override block to after
`TestClient` entry, and fix the comment:
```
def principal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    ...
    cfg = EventBusConfig(...)
    _populate_token_maps(cfg)
    monkeypatch.setattr(eb_app, "load_config", lambda path=None: cfg)
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "event_envelope.json"
    )
    monkeypatch.setattr(eb_app, "get_schema_path", lambda: schema_path)

    with TestClient(eb_app.app) as c:
        # Override consumer-token's allowed_consumer_ids for authorization testing.
        # Must run after TestClient entry: entering TestClient triggers the app's
        # `lifespan` startup handler, which calls _populate_token_maps() again and
        # would otherwise wipe out this override (see scripts/eventbus/app.py
        # lifespan(), scripts/eventbus/auth.py _populate_token_maps()).
        from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal

        if "consumer-token" in _TOKEN_PRINCIPAL_MAP:
            _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
                roles=_TOKEN_PRINCIPAL_MAP["consumer-token"].roles,
                allowed_consumer_ids=frozenset({"consumer-A"}),
                allowed_topics=_TOKEN_PRINCIPAL_MAP["consumer-token"].allowed_topics,
                token_fingerprint=_TOKEN_PRINCIPAL_MAP["consumer-token"].token_fingerprint,
            )
        c.headers["Authorization"] = "Bearer consumer-token"
        yield c
```

The `from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal` import moves down
with the block (it was already function-local, not module-level, so this is not a
new import-order concern). Do not change the `if "consumer-token" in
_TOKEN_PRINCIPAL_MAP:` guard's condition or the `Principal(...)` field values — only
their position and the comment above them.

## Compatibility considerations
N/A: test-only change, no production code, public interface, or schema affected.

## Security considerations
N/A: no production authorization logic is touched — see Plan Background; this fixes
test coverage for an existing, already-correct production check.

## Rollback considerations
Single-block revert via `git revert`/`git checkout` of this file if needed; no data
migration or fixture-shared state to unwind (each test gets a fresh `tmp_path`/fixture
instance).

## Validation plan
- `rg -l "principal_client" tests/` — confirm no other test file depends on the
  current override timing (Plan UNK-01) before/alongside the edit.
- `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v` — targeted; confirm
  `TestAckEndpoint::test_ack_event_principal_ownership_validation` now asserts
  `resp.status_code in (403, 409)` and passes, and no other test in the file regresses.
- `uv run pytest tests/eventbus/ -v` — regression across the eventbus test directory.
- `uv run pytest` — full suite, once, per `rules/toolchain.md`.

## Completion criteria
- `TestAckEndpoint::test_ack_event_principal_ownership_validation` passes.
- No other test in `tests/eventbus/test_eventbus_ack_endpoint.py` or `tests/eventbus/`
  regresses.
- The fixture's comment no longer references `_TOKEN_CONSUMER_MAP`.

## Out of scope
- Any change to `scripts/eventbus/ack_route.py`, `scripts/eventbus/auth.py`, or
  `scripts/eventbus/app.py`.
- The separate, unrelated `agent007` implementation procedure (different Plan/file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder the override block and fix the comment per Implementation > Procedure/Method/Details | Completed | 20260929-123411 | 20260929-123411 | Fixture override reordered per Procedure/Method/Details; stale_detector clean after rewording two false-positive backtick mentions |
| 2 | Run `rg` check for other `principal_client` users | Completed | 20260929-123411 | 20260929-123411 | rg -l principal_client tests/ found 3 other files with independently-defined (not shared) principal_client fixtures — no cross-file impact confirmed |
| 3 | Run targeted/regression/full-suite tests per Validation plan | Completed | 20260929-123411 | 20260929-123411 | Targeted: 10 passed (incl. test_ack_event_principal_ownership_validation). Regression tests/eventbus/: 315 passed, 1 skipped. Full suite: 7992 passed, 24 skipped, 5 failed - all pre-existing/unrelated (test_orchestrator.py::test_original_config_restored_even_on_error is agent007's own pending target; 4 test_memory_layer.py failures confirmed order-dependent/flaky via isolated non-randomized re-run, unrelated to this change). Pre-existing ruff/mypy/lint-imports/bandit findings recorded, not fixed (out of scope). |

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
- **Requirement ID**: REQ-001; REQ-002
- **Source issue**: issues/20260929-111108_eventbus001_ack-endpoint-authorization-bypassed-when-principal-allowed_consumer_ids-is-none.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260929-112600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-113844
- **Related target files**: tests/eventbus/test_eventbus_ack_endpoint.py