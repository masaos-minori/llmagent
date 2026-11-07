## Goal

- Delete `principal_map()` from `tests/eventbus/eventbus_helpers.py` and provide generation-based helpers, so no test reads or mutates a module-level principal dictionary (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Helper redesign for the whole EventBus test suite; the two new helpers are consumed by sibling documents 07-14 and the companion conversions in documents 01/02. Part of the Plan's single atomic Phase 1 cutover.

## Assumptions

- `principal_map()` def verified 2026-11-07 at HEAD `1a13653e8`: lines 216-230 (def line 216), falling back to `auth._TOKEN_PRINCIPAL_MAP` when no generation is published (Plan Background, corrected line range).
- Importers of `principal_map` at HEAD: `test_eventbus_auth.py` (line 25), `test_eventbus_config.py` (line 12), `test_admin_topics_authorization.py` (line 23), `test_authz_generation_ttl.py` (line 23) — each updated by a sibling/conpanion document in the same commit (grep-verified 2026-11-07).

## Design decisions

- New helpers (both new names, no alias for the removed one):
  - `current_principals() -> dict[str, Principal]` — returns `auth.current_generation().principals`, or `{}` when no generation is published (mirrors the production fail-closed read).
  - `publish_derived_generation(overrides: dict[str, Principal], removed: frozenset[str] = frozenset()) -> AuthzGeneration` — builds the next complete generation from the current one (`generation + 1`, same `config`, `principals = {**current, **overrides}` minus `removed`, `effective_at = time.time()`) and publishes it through `auth.publish_generation()`; this is the plan's "small helpers-module function that wraps `publish_generation(AuthzGeneration(generation=current+1, ...))`" for injection tests (Plan Design "Test discipline").
- Restoration is not the helpers' job: `tests/eventbus/conftest.py::_reset_auth_state` (sibling document 05) republishes the snapshotted generation after every test, replacing every `clear()/update()`/`pop()` restore block.
- `AuthzGeneration.principals` stays a plain dict; publish-only discipline is enforced by the helpers and conftest, not by `MappingProxyType` (Plan Assumptions).

## Alternatives considered

- Keeping `principal_map()` as a wrapper over `current_generation()`: rejected — REQ-003 and AC-001 require the name to have no definition anywhere, and the fallback read to the alias is exactly the bypass being removed.

## Implementation
### Target file
`tests/eventbus/eventbus_helpers.py`

### Procedure
1. Delete `principal_map()` (lines 216-230).
2. Add `current_principals()` and `publish_derived_generation()` (both new) per the Design decisions; import `AuthzGeneration` and `publish_generation` from `eventbus.auth` locally inside the functions (same lazy-import style the deleted helper used at line 226).
3. Keep every other helper in the module (client factories, header builders, topic-authorization helpers) unchanged.

### Method
- Current helper body (verified HEAD `1a13653e8`): looks up `auth.current_generation()`, returns `generation.principals` if published else `auth._TOKEN_PRINCIPAL_MAP`. After deletion, no helper in the module touches the alias.
- `publish_derived_generation` (new) raises `RuntimeError` (new, deterministic message "no generation published to derive from") when `current_generation()` is `None` — injection tests must run after the lifespan baseline is published; no partial/empty publication window is possible because the whole dict is built before `publish_generation()` (REQ-004 / AC-004).

### Details
- Helpers never mutate the current generation's dict in place: `{**current, **overrides}` copies (REQ-003).

## Compatibility considerations

- The four `principal_map` importers are updated in the same commit (documents 01 companion, 08, 14, and 01 companion for the TTL file); the module exports no removed name, so the `\bprincipal_map\b` pattern from document 17 stays clean — the new names contain no matchable word boundary (`current_principals` (new), `publish_derived_generation` (new)).

## Security considerations

- Helpers take/return Principal objects only; tests must not log raw bearer tokens — token strings stay as the existing test constants and never enter assertion messages (REQ-004 / AC-006).

## Rollback considerations

- Revert of the single atomic commit restores `principal_map()` and all its call sites together.

## Validation plan

- `uv run pytest tests/eventbus/ -q` — whole suite green with the new helpers (Plan Validation row 2).
- `grep -rn "\bprincipal_map\b" tests/eventbus/` — no matches outside this module's deletion diff (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- `principal_map()` has no definition or import anywhere in the repository (AC-001).
- Test injection goes exclusively through `publish_derived_generation()` / `build_and_publish_generation()`; no test mutates a global principal dict (AC-003).

## Out of Scope

- Converting each consuming test file — sibling documents 01 (companion), 07-14.
- The conftest autouse fixture — sibling document 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `principal_map()` (216-230); add `current_principals()` and `publish_derived_generation()` — Plan Phase 1 | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Pending | — | — | consumers land in the same commit |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tests/eventbus/eventbus_helpers.py`
