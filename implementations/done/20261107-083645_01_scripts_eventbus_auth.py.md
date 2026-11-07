## Goal

- Make `_CURRENT_GENERATION` the only module-level authentication state in `scripts/eventbus/auth.py`: delete the `_TOKEN_PRINCIPAL_MAP` compatibility alias and rewire `resolve_principal()` to `current_generation()`, and rename `_populate_token_maps()` to `build_and_publish_generation()` (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- The Plan states no release unit: Phase 1 is a single atomic cutover; production rename and test redesign land in one commit so no intermediate state has two sources of truth (Plan Design "Atomicity").

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `70391b306` (no target-file changes since the Plan freeze at `1b2dded66`).
- `_CONSUMER_ID_ALLOWLIST` (auth.py:90) is consumer-ID allowlist state, not a principal map; it stays out of this row (Plan Scope: only the principal alias is removed).
- Overlap with plan001 document implementations/20261107-081028_23_tests_deploy_test_setup_services_eventbus.py.md: plan001 edits the workflow-schema fixture lines (25, 133) of the companion file `tests/deploy/test_setup_services_eventbus.py`; this Plan's companion edits the populate call at line 334 of the same file — disjoint regions. Re-verified at HEAD `70391b306` on 2026-11-07: the deploy-test anchor shifted 339 -> 334 (db_conn restores now 332-333) when `70391b306` changed that file (Plan Assumptions).
- UNK-01 (indirect auth-state construction via `make_eventbus_client` lifespan) is covered by the conftest generation-restore fixture (sibling document 05) and verified by the full-suite run (Plan Unknowns, Blocking? = False).

## Design decisions

- `None` generation means "no principals": `resolve_principal()` looks up an empty view and falls into the existing 401 authentication-failure path (audit-logged, no token echo) — this is the fail-closed behavior REQ-001 requires, with no new exception type.
- `build_and_publish_generation` (new) is a public module-level name because `scripts/eventbus/app.py` imports it cross-module (Plan Assumptions). No alias for the old name is left behind (REQ-002).
- `_build_principal_map()` keeps its name and contract (build-only helper used by `admin_route.py`/`authz_ttl.py`); `\bprincipal_map\b` cannot match it (Plan Assumptions).

## Alternatives considered

- Keeping the alias but wrapping it in `MappingProxyType`: rejected — REQ-001 deletes the alias; immutability hardening is out of scope (Plan Assumptions).
- Raising a dedicated "no generation published" error in `resolve_principal()`: rejected — the existing 401 path is already the fail-closed contract the Constraints require (Plan Design).

## Implementation
### Target file
`scripts/eventbus/auth.py`

### Procedure
1. Delete the alias comment block (lines 92-95) and the `_TOKEN_PRINCIPAL_MAP` definition (line 96).
2. Reword the `_build_principal_map()` comment at line 173: "do NOT touch _TOKEN_PRINCIPAL_MAP yet" -> "do NOT touch the published generation yet".
3. Rename `_populate_token_maps` (def at line 234) to `build_and_publish_generation` (new); keep its body and docstring (they already describe build-then-publish semantics).
4. In `publish_generation()` (def at 258, docstring 259-265, global block 266-268): drop the alias sentence from the docstring; body becomes `global _CURRENT_GENERATION` + `_CURRENT_GENERATION = new_generation` only (delete line 268).
5. In `resolve_principal()`: after the `get_auth_token(config)` fail-closed block, add `generation = current_generation()` and `principals = generation.principals if generation is not None else {}`; replace `token not in _TOKEN_PRINCIPAL_MAP` (line 310) with `token not in principals` and `_TOKEN_PRINCIPAL_MAP[token]` (line 326) with `principals[token]`. An unpublished generation therefore takes the existing 401 path at lines 311-323 (audit `log_auth_failure`, no token echo).
6. Confirm `grep -n "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" scripts/eventbus/auth.py` returns nothing.

### Method
- Current state (HEAD `1a13653e8`): alias def auth.py:96 with the "Compatibility alias (owner-approved 2026-11-01)" comment; rebinding in the same global block at 266-268; reads at 310/326; `_populate_token_maps` def at 234 (docstring already documents publish-after-build semantics); `current_generation()` unchanged.
- Production importers of the renamed function: `scripts/eventbus/app.py` only (sibling document 02). `admin_route.py` and `authz_ttl.py` import `_build_principal_map`/`current_generation`/`publish_generation` only — unaffected (Plan Background).
- `AuthzGeneration` (auth.py:55-67: `generation`, `config`, `principals`, `effective_at`) and `publish_generation`'s publish-only contract stay as-is (REQ-004).

### Details
- No persisted data is touched; auth state lives in process memory only (Plan Implementation steps Phase 3 deploy note).

### Companion test files
- `tests/eventbus/test_eventbus_auth.py`
  - Procedure (regions re-verified at HEAD `70391b306` on 2026-11-07):
    1. Rename all 29 `_populate_token_maps` references (comment 92; imports/calls at 262/265, 816/833, 923/940, 953/974, 1014/1035, 1063/1084, 1503/1517, 1597/1614, 1626/1648, 1675/1703, 1731/1748/1755, 1775/1792/1810; docstring 1729 and comment 1751 text updated in the same sentences) to `build_and_publish_generation` (new).
    2. Replace the `principal_map` import (line 25) with `current_principals` (new) (sibling document 04) and all 27 `principal_map()` calls (101-103, 819, 840, 844-845, 926, 942-943, 959, 979, 990, 1001-1002, 1021, 1036, 1051-1052, 1070, 1085, 1107-1108, 1649, 1652, 1655-1656) with it.
    3. Replace the direct-alias injection blocks (import at 862 with inject at 869 and `finally: _TOKEN_PRINCIPAL_MAP.pop(token, None)` at 883; second block import 890 / inject 897 / pop 911) and the `_snapshot`/`_restore` helper pairs (1582-1585 / 1588-1592 and 1716-1719 / 1722-1726) with generation discipline: snapshot `auth.current_generation()`, inject via the helpers-module publish helper (sibling document 04), read via `auth.current_generation().principals`.
    4. Convert the concurrent-reader assertions (atomic-swap test 1728-1769: map-emptiness/count assertions at 1749, 1754-1756, 1764-1765; failed-rebuild test 1771-1819: assertions at 1793-1794, 1813-1815) to generation-based reads of the same properties.
    5. Rework the two tail tests of `TestAtomicPublishAndFailedRebuild` (1821-1840): both read a generation published by an earlier test, which the conftest per-test rollback no longer preserves — make each self-contained (`build_and_publish_generation(cfg)` first). For `test_published_generation_principals_is_the_map_resolve_principal_consults`: drop the alias phrase from the docstring and delete the object-identity assertion (`assert generation.principals is auth._TOKEN_PRINCIPAL_MAP`); assert instead that `resolve_principal()` resolves from `current_generation().principals`, that a failed rebuild keeps `current_generation() is gen1`, and that a successful rebuild publishes `gen1.generation + 1` with a new principals map (Plan Design "Test discipline"). Also add `assert auth.current_generation() is gen_before` to `test_failed_rebuild_preserves_previous_generation` (AC-004 object identity, not just content).
  - Validation: `uv run pytest tests/eventbus/test_eventbus_auth.py` green after Method; `grep -c "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" tests/eventbus/test_eventbus_auth.py` -> 0.
- `tests/eventbus/test_authz_generation_ttl.py`
  - Procedure: swap the `principal_map` import (line 23, from `tests.eventbus.eventbus_helpers`) for `current_principals` (new) (new, sibling document 04) and update its calls at lines 122, 136, 209, 229, and 244 (re-verified at HEAD `70391b306`: 5 calls, not 3); `map_before = principal_map()` (229) and `assert principal_map() is map_before` (244) become `map_before = current_principals()` / `assert current_principals() is map_before` — the failed-rebuild case (232-244) keeps asserting the previous generation stays in force (REQ-004 / AC-004).
  - Validation: `uv run pytest tests/eventbus/test_authz_generation_ttl.py` green; failed-rebuild assertions (`current_generation() is granted`) unchanged.

## Compatibility considerations

- Every test caller of `_populate_token_maps` is renamed in the same commit by sibling documents 02, 07-14; the suite is only green with all Phase 1 documents landed (Plan Implementation steps Phase 1 atomicity).
- The lifespan baseline audit (`app.py` `current_generation()` read after publication, `log_privileged_action` with `target="authz_baseline"`) keeps working: the rename does not change generation semantics (ADR-013 restart baseline, ADR line 109, updated by sibling document 18).

## Security considerations

- `resolve_principal()` keeps the no-token-echo rule: the 401 path logs `detail=""` and never includes the raw bearer token (REQ-004 / AC-006); fail-closed on unpublished generation uses this same path.

## Rollback considerations

- Revert the single atomic commit restores auth.py, app.py, config.py, the helpers/conftest, all converted test files, the checker patterns, and the ADR wording together (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_auth.py tests/eventbus/test_authz_generation_ttl.py` (Plan Validation row 1).
- `uv run pytest tests/eventbus/ -q` — whole suite in order, cross-file leakage detection (Plan Validation row 2).
- `grep -rn "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" scripts/ tests/ docs/` and a `\bprincipal_map\b` word-boundary grep — zero references outside `tools/check_compat_shims.py` and its test data (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- `_TOKEN_PRINCIPAL_MAP` and `_populate_token_maps` have no definition or reference in `scripts/eventbus/auth.py` or its companion tests (AC-001).
- `resolve_principal()` reads only `current_generation()` and fails closed (401) when no generation is published (AC-002).
- Failed construction leaves the previous generation in force; concurrent readers never observe a partial generation (AC-004).

## Out of Scope

- Updating `scripts/eventbus/app.py` and `scripts/eventbus/config.py` — sibling documents 02, 03.
- Redesigning `tests/eventbus/eventbus_helpers.py` and `tests/eventbus/conftest.py` — sibling documents 04, 05.
- Converting the remaining eight EventBus test files and the deploy test — sibling documents 07-14.
- Adding `COMPAT_PATTERNS` entries — sibling document 17. ADR wording — sibling document 18.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `scripts/eventbus/auth.py` (delete alias, rewire `resolve_principal`, rename to `build_and_publish_generation` (new)) — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | Atomic cutover: suite green only with all Phase 1 documents landed auth.py alias removed, resolve_principal via current_generation, rename landed |
| 2 | Convert companion tests `test_eventbus_auth.py` and `test_authz_generation_ttl.py` — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | test_eventbus_auth.py + test_authz_generation_ttl.py converted; 59 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Completed | 20261107-152722 | 20261107-152722 | full suite 11784 passed diff-cover 100pct |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `scripts/eventbus/auth.py`, `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_authz_generation_ttl.py`