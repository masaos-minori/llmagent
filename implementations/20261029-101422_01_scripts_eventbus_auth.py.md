## Goal

Split the principal-map build out of `_populate_token_maps()` into a function that returns the map without publishing it, so the admin route can build the replacement generation before it publishes anything (`REQ-002`: map-returning build with unchanged startup behavior).

## Scope

Modify `scripts/eventbus/auth.py` only: extract the build half of `_populate_token_maps()` into a private helper and make `_populate_token_maps()` build then publish. No change to `Principal`, `Role`, `publish_principals()`, the token-to-role matrix, or the fail-closed errors. The admin route (seq 02) and the tests (seq 03) are separate documents.

## Assumptions

- Source claims re-verified this cycle: `_populate_token_maps` at `scripts/eventbus/auth.py:105` builds `new_map` (line 148) and publishes it via `publish_principals(new_map)` at line 206; `publish_principals` is defined at line 209. The function is the only place that derives principals from a config (callers: `scripts/eventbus/app.py:76`, `scripts/eventbus/admin_route.py:135`, and tests).
- `global _TOKEN_PRINCIPAL_MAP` at line 116 is only needed by code that assigns the module map; after the split no code in the moved body assigns it, so it is dropped from both functions.
- The helper name is private (`_`-prefixed), so the generated reference table (`docs/24_eventbus/eventbus_08_reference_api.md`) skips it (`tools/generate_reference_table.py` skips `_`-prefixed names); `tools/generate_reference_table.py --check` confirms.
- Sequencing: this is seq 01 on purpose; the admin route (seq 02) imports the helper this document creates, so it must run first. `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md` does not edit `auth.py`; no overlap with this row.

## Design decisions

- Pure move: the duplicate-token guard, the `_fingerprint` helper, the control-plane and per-role token blocks, and the consumer grants computation move unchanged into `_build_principal_map` (new); only the final `publish_principals(new_map)` call stays in `_populate_token_maps`.
- Keep `_populate_token_maps(config) -> None` as the startup and test entry point so every existing caller and test keeps working.

## Alternatives considered

- A generation object holding config and map: rejected, out of scope per the Plan (REQ-001 needs only an ordering fix).
- Making the helper public: rejected, it would add a row to the generated reference table for no caller outside the package.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Open `scripts/eventbus/auth.py` and locate `_populate_token_maps` (line 105).
2. Rename the existing function to `_build_principal_map` (new), change its return annotation to `dict[str, Principal]`, delete the `global _TOKEN_PRINCIPAL_MAP` statement (line 116), and replace the final `publish_principals(new_map)` (line 206) and its comment with `return new_map`.
3. Add a new `_populate_token_maps(config: Any) -> None` directly after the helper that calls `publish_principals(_build_principal_map(config))`.
4. Update both docstrings as described below; keep the existing comments inside the moved body.

### Method

Resulting shape (bodies abbreviated; the moved lines are unchanged):

```python
def _build_principal_map(config: Any) -> dict[str, Principal]:
    """Build the token-to-Principal map from config without publishing it.

    Builds the entire map into a fresh local dict. If building raises (e.g.
    consumer_token without consumer_authorization, or a duplicate token), the
    caller has published nothing and the previous generation stays in force.
    """
    ...  # unchanged: _fingerprint, duplicate-token guard, new_map construction
    return new_map


def _populate_token_maps(config: Any) -> None:
    """Populate the principal map from config at startup.

    Builds the whole map first and publishes it with one assignment through
    publish_principals(), so concurrent readers never observe an empty map and
    a build error leaves the previous generation in force.
    """
    publish_principals(_build_principal_map(config))
```

### Details

- `publish_principals` is defined later in the module (line 209); that is fine because it is resolved at call time.
- Keep the error messages byte-identical (`eventbus config duplicate token: ...`, `consumer_token is configured but consumer_authorization is missing...`); tests assert on them.
- Do not change line 22-25 style imports; no new import is needed.

## Compatibility considerations

Behavior of `_populate_token_maps()` is unchanged for startup and tests: same inputs raise the same errors before any publish, and success publishes the same map. The new helper is private and has no external caller until seq 02.

## Security considerations

Fail-closed behavior and token redaction are preserved: errors still name fields only and never interpolate token values; the SHA-256 fingerprint helper moves unchanged. Moving the build ahead of the publish cannot widen any grant.

## Rollback considerations

Revert the commit (single-file change); seq 02 depends on the helper, so revert both together.

## Validation plan

1. `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_eventbus_config.py tests/eventbus/test_eventbus_consumer_authorization.py -v` (existing atomic-publish and failed-rebuild tests stay green).
2. `uv run ruff check scripts/eventbus`; `uv run mypy --no-namespace-packages scripts/ tests/eventbus`; `uv run bandit -r scripts/eventbus -c pyproject.toml -ll`.
3. `uv run python tools/check_module_size.py` (file is 15596 B, gate 20480 B) and `uv run python tools/generate_reference_table.py --check`.
4. `uv run python tools/stale_detector.py implementations/20261029-101422_01_scripts_eventbus_auth.py.md`.

## Completion criteria

- `scripts/eventbus/auth.py` defines `_build_principal_map` (new) returning the map and `_populate_token_maps` calling it then `publish_principals`.
- No remaining `global _TOKEN_PRINCIPAL_MAP` in either function; error messages unchanged.
- Existing auth, config, and consumer-authorization tests pass; ruff, mypy, bandit, module-size and reference-table checks are clean.

## Out of Scope

- The admin route reorder (seq 02) and the regression tests (seq 03).
- Any change to `publish_principals()`, `Principal`, roles, or startup wiring in `app.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract `_build_principal_map` (new) and rewrite `_populate_token_maps` (Implementation > Procedure/Method/Details) | Pending | — | — | |
| 2 | Run the existing auth and config tests (Validation plan; no new test in this row) | Pending | — | — | New tests are in seq 03 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | No doc change; helper is private |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261029-090157_eventbus001_admin-authz-publish-order.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-091959_eventbus001_admin-authz-publish-order.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-101422
- **Related target files**: `scripts/eventbus/auth.py`
