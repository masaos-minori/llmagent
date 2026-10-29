## Goal

Make `make_eventbus_client()` rely on the production lifespan only: no hand-built `app.state`, no hand-written teardown, and no unused helper functions (`REQ-002`: lifespan-only helper with unchanged signature and callers; `REQ-004`: assertions keep their meaning).

## Scope

Modify `tests/eventbus/eventbus_helpers.py` only: `make_eventbus_client()` and its docstring, the helper functions `_init_state` and `_do_cleanup`, and the import that becomes unused. Signature, default `Authorization` header, token config, and the `principal_map()` helper are unchanged. No production code, no caller edits.

## Assumptions

- Source claims re-verified this cycle: `make_eventbus_client` (line 101) runs `_init_state` on a throwaway event loop (lines 137-143), builds `TestClient(eb_app.app)` without entering it (line 145), and attaches a hand-written `_cleanup` (lines 151-160); `_init_state` (line 164) and `_do_cleanup` (line 179) are the hand-built state and teardown.
- All 7 call sites enter the client with `with make_eventbus_client(...) as c` (`tests/eventbus/test_eventbus_publish.py:21`, `test_eventbus_crash_ack.py:52`, `test_eventbus_slow_consumer.py:21`, `test_eventbus_subscribe_transition.py:24`, `test_eventbus_concurrent.py:19`, `test_eventbus_auth.py:1502`, and `tests/deploy/test_setup_services_eventbus.py:343`), so the lifespan already overwrites the helper's state for them; no caller needs pre-startup `app.state` mutation (`rg -n "make_eventbus_client\("`).
- No module imports `_init_state` or `_do_cleanup` from this helper (`rg "eventbus_helpers import"` filtered for them returns nothing), and no caller uses the helper's `_cleanup` attribute; the other `_cleanup` assignments (`test_admin_topics_authorization.py:72`, `test_eventbus_auth.py:241`) belong to their own builders.
- `asyncio` is used only by the code removed here (lines 138-139, 152-153, 186), so `import asyncio` becomes unused and is removed; `Path`, `Any`, `pytest`, and `TestClient` stay used.
- Blast radius measured: `make_eventbus_client` appears in 9 files and 16 references including the definition; callers' usage is unchanged.
- Overlap: `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md` and `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` also edit this file (they add helpers); neither references `_init_state`, `_do_cleanup`, or `make_eventbus_client`. Judgment: compatible, sequencing (land after `ebresumetest004` or rebase). `plans/20261029-092617_eventbus004_test-requirement-id-cleanup.md` edits one docstring line in `eventbus_test_tokens`; compatible.

## Design decisions

- Remove, do not replace: since every caller already enters the client, a second lifecycle-based helper would only compete with the fixture that `ebresumetest004` adds.
- Document the contract in the docstring: the returned client must be entered as a context manager, which starts the app through the lifespan and stops it through `_shutdown_lifespan()`.

## Alternatives considered

- Entering the client inside the helper (returning an already-started client): rejected, it changes the callers' `with` usage and the exit semantics.

## Implementation

### Target file

`tests/eventbus/eventbus_helpers.py`

### Procedure

1. Open `tests/eventbus/eventbus_helpers.py` and locate `make_eventbus_client` (line 101).
2. Delete the `# Initialize app.state before creating TestClient` block that runs `_init_state` (lines 137-143) and the `# Store cleanup callback` block that defines `_cleanup` and assigns `client._cleanup` (lines 151-160), keeping the `TestClient` construction, the header assignment, and `return client`.
3. Delete `async def _init_state` (line 164) and `async def _do_cleanup` (line 179) in full.
4. Remove `import asyncio` (line 5).
5. Extend the docstring as shown in Method.

### Method

Resulting tail of the function and the docstring addition:

```python
    """...existing text...

    The returned client must be entered as a context manager
    (``with make_eventbus_client(...) as c``): the production lifespan then starts
    the application and its shutdown sequence stops it. The helper builds no app
    state itself.
    """
    ...  # config construction and the three monkeypatch.setattr calls unchanged

    client = TestClient(eb_app.app)
    client.headers["Authorization"] = eventbus_auth_headers(default_role)[
        "Authorization"
    ]
    return client
```

### Details

- After the edit `rg "_init_state|_do_cleanup|asyncio" tests/eventbus/eventbus_helpers.py` must return nothing (the word may remain only in a docstring if present; check).
- Do not edit `principal_map()` or `eventbus_test_tokens()`.

## Compatibility considerations

Callers keep working because each already enters the client: the lifespan builds the same state from the patched `load_config`. A future caller that does not enter the client would find no state; the docstring states the requirement.

## Security considerations

N/A: fixture tokens only; no change to the token set.

## Rollback considerations

N/A: revert the commit (single-file test change); callers are unaffected.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_publish.py tests/eventbus/test_eventbus_crash_ack.py tests/eventbus/test_eventbus_slow_consumer.py tests/eventbus/test_eventbus_subscribe_transition.py tests/eventbus/test_eventbus_concurrent.py tests/eventbus/test_eventbus_auth.py tests/deploy/test_setup_services_eventbus.py -v`.
2. `uv run pytest tests/eventbus`.
3. `uv run ruff check tests/eventbus`; `uv run ruff format --check tests/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`.
4. `uv run python tools/stale_detector.py implementations/20261029-101908_02_tests_eventbus_eventbus_helpers.py.md`.

## Completion criteria

- `make_eventbus_client()` builds no `app.state`, has no hand-written teardown, and keeps its signature and default header.
- `_init_state`, `_do_cleanup`, and `import asyncio` are gone from `tests/eventbus/eventbus_helpers.py`.
- All 7 callers' tests pass with no assertion change; ruff, format, and mypy are clean.

## Out of Scope

- The health fixture (seq 01), the lifecycle test (seq 03), other hand-built fixtures (`test_admin_topics_authorization.py`, `test_eventbus_auth.py` class fixtures; Plan UNK-02), and the test-client factory and prefix work of `ebtestdrift007`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the hand-built state, `_cleanup`, the two helper functions, and the unused import; update the docstring (Implementation > Procedure/Method/Details) | Completed | 20261029-131220 | 20261029-131220 |  |
| 2 | Run every caller's tests (Validation plan) | Completed | 20261029-131220 | 20261029-131220 | 7 call sites in 7 files |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-131220 | 20261029-131220 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Tests-only row |

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
- **Requirement ID**: `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261029-090402_eventbus003_test-lifecycle-production-path.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-092424_eventbus003_test-lifecycle-production-path.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101908
- **Related target files**: `tests/eventbus/eventbus_helpers.py`