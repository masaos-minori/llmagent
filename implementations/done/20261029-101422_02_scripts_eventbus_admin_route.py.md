## Goal

Reorder `update_topics_authorization()` so the replacement config and the replacement principal map are both built successfully before either is published (`REQ-001`: publish only after every build step succeeded; `REQ-004`: response contract and no-op behavior unchanged).

## Scope

Modify `scripts/eventbus/admin_route.py` only: the publish block of `update_topics_authorization()` and its import line. No change to validation, the no-op detection, the audit call, the log line, or the response shape. The map-returning helper is created by seq 01; the tests are seq 03.

## Assumptions

- Source claims re-verified this cycle: the handler assigns `request.app.state.config` at `admin_route.py:131` and calls `_populate_token_maps(config)` at lines 134-135, after the assignment; the import is at line 11 (`from eventbus.auth import _populate_token_maps`); `log_privileged_action` is called at lines 141-147 and the response is returned at line 149.
- Name created by an earlier row: `_build_principal_map` is created by seq 01 (`scripts/eventbus/auth.py`), which `code-implementation` executes first (earlier `seq`), so it exists when this row runs.
- No test patches `eventbus.admin_route._populate_token_maps` (checked with `rg` over `tests/` and `scripts/` this cycle); the existing patches in `tests/eventbus/test_admin_topics_authorization.py` target `eventbus.admin_route.log_privileged_action` only.
- Overlap (`tools/check_plan_target_overlaps.py`): `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` also edits this file, at the audit call (lines 139-147); this row edits lines 125-135. Judgment: compatible, with a sequencing dependency (land the audit plan first or rebase); the Plan's `Scope` Dependencies already record it. `ebaudit005` has no procedure documents yet, so no conflicting instruction exists today.

## Design decisions

- Build config, then principal map, then publish both back to back; with no `await` between the two publishes, coroutines never observe a mixed generation.
- Import `publish_principals` (public, existing) and the private helper from seq 01; drop the now-unused `_populate_token_maps` import.

## Alternatives considered

- Wrapping the publish in try/except with a rollback: rejected, building first makes rollback unnecessary and a handler is out of scope (the route returns 500 on an unhandled build error).

## Implementation

### Target file

`scripts/eventbus/admin_route.py`

### Procedure

1. Open `scripts/eventbus/admin_route.py`.
2. Change the import at line 11 to `from eventbus.auth import _build_principal_map, publish_principals`.
3. Replace the two consecutive `if changed:` blocks (lines 125-135) with the single block shown in Method.
4. Leave the logging, audit, and return statements unchanged.

### Method

```python
    if changed:
        # EventBusConfig is a frozen dataclass — build a replacement instance
        # rather than mutating the existing one. Build the replacement principal
        # map from it before publishing anything, so a failed build leaves the
        # previous config and principal generation fully active.
        config = dataclasses.replace(config, **replacements)
        new_principals = _build_principal_map(config)
        request.app.state.config = config
        publish_principals(new_principals)
```

### Details

- The `await request.json()` at the top of the handler is the last `await`; the block above is synchronous, so the two publishes are not interleaved with other coroutines.
- A no-op update (`changed` false) executes neither build nor publish, as today.
- Keep the existing explanatory comment about the frozen dataclass; only the sequencing sentence is added.

## Compatibility considerations

Request and response contract (`status`, `persistent`, `changed`), the 422 and 401/403 behavior, runtime-only persistence, and the audit record are unchanged. The only behavior change is on a principal-map build error: previously the new config stayed published; now nothing is published and the unhandled error yields a 500.

## Security considerations

A failed update can no longer leave a new authorization config next to the old principal map. No token values are logged or returned; the build helper's errors name fields only (unchanged).

## Rollback considerations

Revert the commit; seq 01's helper can stay in place because nothing else calls it.

## Validation plan

1. `uv run pytest tests/eventbus/test_admin_topics_authorization.py -v` (existing tests unchanged; new tests are added by seq 03).
2. `uv run pytest tests/eventbus` once seq 03 has landed.
3. `uv run ruff check scripts/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/eventbus -c pyproject.toml -ll`; `uv run python tools/check_module_size.py`.
4. `uv run python tools/stale_detector.py implementations/20261029-101422_02_scripts_eventbus_admin_route.py.md`.

## Completion criteria

- `update_topics_authorization()` builds the replacement config and principal map before assigning `app.state.config` and calling `publish_principals()`; the old `_populate_token_maps` call and import are gone.
- Existing admin tests pass unchanged; ruff, mypy, bandit, and module-size checks are clean.

## Out of Scope

- Audit call content (`ebaudit005`), serializing concurrent updates, a generation object, and any change to `auth.py` beyond seq 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder the publish block and update the import (Implementation > Procedure/Method/Details) | Completed | 20261029-112901 | 20261029-113618 | Needs seq 01 first Changed: scripts/eventbus/admin_route.py. stale check: clean (after seq 01) |
| 2 | Run the admin tests; regression tests are added by seq 03 (Validation plan) | Completed | 20261029-112901 | 20261029-113618 | targeted: 106 passed (admin, auth, config tests); regression tests are added by seq 03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261029-112901 | 20261029-113618 | ruff, mypy (475 files), lint-imports, bandit, module-size, reference-table clean; full suite 10391 passed 8 skipped 15 deselected; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261029-113618 | 20261029-113618 | No doc states the old order N/A: no docs/00_index.md row maps this change to a doc; no doc states the old publish order (checked earlier in plan) |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: `issues/20261029-090157_eventbus001_admin-authz-publish-order.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-091959_eventbus001_admin-authz-publish-order.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101422
- **Related target files**: `scripts/eventbus/admin_route.py`