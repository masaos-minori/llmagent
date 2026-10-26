## Goal

Remove the empty-map window and partial-population-on-raise defect in
`_populate_token_maps()` (`scripts/eventbus/auth.py`) by publishing a fully built principal
map together with the new config in one atomic reference swap, so every request observes
exactly one authorization generation.

## Scope

- Modify only `scripts/eventbus/auth.py`: `_populate_token_maps()` (lines 97-186) and the
  module global `_TOKEN_PRINCIPAL_MAP` publication.

## Assumptions

- A single module-level assignment is atomic under the GIL, so `_TOKEN_PRINCIPAL_MAP =
  new_map` is observed whole by concurrent readers.
- `_populate_token_maps()` stays the single population entry point; its callers
  (`admin_route.py`, `app.py` lifespan) are unchanged in signature.
- `_TOKEN_PRINCIPAL_MAP` remains a module global (82 test references depend on the name).

## Design decisions

- **Build-new-then-swap.** Build the entire new map into a fresh local dict, then publish
  it with one module-level assignment. If building raises (e.g. `consumer_token` configured
  but `consumer_authorization` missing, auth.py:137-141), the previous generation is
  already in force — the clear happens only after the new map is fully built.
- **Publish helper.** Extract `publish_principals (new)` in auth.py that both the startup
  lifecycle (app.py) and the admin handler call, so there is one publish entry point.

## Alternatives considered

- Clearing then repopulating in place (current): rejected — concurrent requests see an
  empty map (401s) and a raise leaves a half-populated map.
- Publishing via a `dataclasses.replace` on a holder object: adds indirection over a plain
  module assignment; the plain assignment is sufficient under the GIL.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. At the top of `_populate_token_maps(config)`, build the new map into a fresh local dict
   (call it `new_map (new)`); do NOT call `_TOKEN_PRINCIPAL_MAP.clear()` yet.
2. Populate the fresh dict from `config` using the existing population logic moved inside
   the fresh-dict body (preserve every existing key/branch; only the target container
   changes).
3. After the fresh dict is fully built, publish it: call `publish_principals (new)` instead
   of the in-place clear+repopulate.
4. Add the helper:
   ```python
   def publish_principals(new_map: dict[str, Principal]) -> None:
       global _TOKEN_PRINCIPAL_MAP
       _TOKEN_PRINCIPAL_MAP = new_map
   ```
5. Refactor `app.py` lifespan (line 74) and `admin_route.py` (line 109) to call
   `_populate_token_maps()` unchanged (they already do); the publish now happens inside it.
6. Keep `resolve_principal()` (auth.py:201) and `require_consumer_identity()` (auth.py:279)
   fail-closed; no change to their contracts.

### Method

Move the population body to build into a fresh dict; insert the publish call at the end. No
signature changes for callers.

### Details

- Do not expose `publish_principals (new)` beyond the module unless app.py/admin_route.py need it;
  they currently go through `_populate_token_maps()`, so a module-private helper suffices.
- Preserve the exact raise semantics at the former lines 137-141; the raise now occurs
  during fresh-dict construction, before any swap.

## Compatibility considerations

- `_TOKEN_PRINCIPAL_MAP` stays a module global; the 82 test references remain valid. Tests
  that mutate it directly (`test_eventbus_crash_ack.py`) are updated separately (seq 10).

## Security considerations

- Removing the empty-map window closes a window where concurrent requests received 401
  mid-update (REQ-001). Fail-closed resolution is preserved (INV-01).

## Rollback considerations

- Revert the commit; the previous in-place behavior is restored.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_auth.py` — assert atomic publish and that a
  failed rebuild leaves the previous generation intact.
- `uv run pytest tests/eventbus/` — full suite passes; no `_TOKEN_PRINCIPAL_MAP` direct
  mutation remains where the plan requires (seq 10 handles crash_ack).
- `uv run radon cc scripts/eventbus/auth.py`; keep `require_consumer_identity` at or below
  B (9). `uv run vulture`, `uv run bandit scripts/eventbus/ -c pyproject.toml`.
- `PYTHONPATH=scripts uv run lint-imports` — `eventbus-is-isolated` KEPT.
- `uv run mypy`, `uv run ruff`.

## Completion criteria

- `_populate_token_maps()` publishes a fully built map via one atomic assignment; a raise
  during build leaves the previous generation in force; no in-place `.clear()` window
  remains.

## Out of Scope

- Changing `resolve_principal()`'s 401/500 fail-closed contract beyond atomic publishing.
- Direct test-side mutation of `_TOKEN_PRINCIPAL_MAP` (handled in seq 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement build-new-then-swap publish in `_populate_token_maps()` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `scripts/eventbus/auth.py`
