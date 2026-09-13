## Goal
Fix `load_config()`'s misplaced validation checks (REQ-001) and resolve `UNK-01`.

## Scope
Only `scripts/eventbus/config.py`: `load_config()`'s validation block indentation.
No change to `_CONFIG_KEY_TYPES`, `_KNOWN_CONFIG_KEYS`, `_REQUIRED_CONFIG_KEYS`, or
any field default. **`EventBusConfig.__post_init__` is explicitly not modified** —
see Design decisions' Correction below.

## Assumptions
- `load_config()`'s two misplaced checks (lines 194-200, confirmed by reading the
  function) are nested one level too deep inside the `for key, expected_type in
  _CONFIG_KEY_TYPES.items():` loop (line 185) — the checks reference `data` directly
  (not `key`/`expected_type`), so de-indenting them out of the loop changes nothing
  about their own logic, only how many times they execute.
- `EventBusConfig.__post_init__` (lines 60-94, confirmed by reading the dataclass) has
  no per-role-token check today — only `auth_token` (line 71-72). Per the Correction
  below, this remains true after this document's change.

## Design decisions
**UNK-01 resolution: No** — `__post_init__` does **not** gain a per-role-token
check; that requirement stays exclusive to `load_config()`'s TOML-parsing path.

**Correction (found during Step 3e/Step 4 full-suite validation, reversing this
document's own original plan):** this document originally chose "Yes" (add the
check to `__post_init__` too, for TOML/direct-construction consistency) and it was
implemented and validated against this Plan's four `Implementation Target Files`
only. Running the full `tests/eventbus/` suite (per this document's own Validation
plan, "discover every `EventBusConfig(...)` call site broken by the new
`__post_init__` check") surfaced 114 errors + 22 new failures across 20+ test files
never listed in this Plan's `Implementation Target Files` — each constructs
`EventBusConfig` directly with only `auth_token` set, which the pre-existing
`__post_init__` already accepted. Per explicit user direction (asked because this
Blast Radius was far larger than this Plan's own "3 test files" estimate),
`__post_init__`'s change was reverted rather than re-scoping this Plan to touch 20+
additional files — see `plans/done/20260913-094809_plan.md`'s own Unknowns/Design
sections for the final, empirically-reached decision.

## Alternatives considered
- **Keep `__post_init__`'s per-role-token check (original "Yes" decision)**:
  reverted (see Correction) — the Blast Radius across untouched test files was
  judged disproportionate to REQ-001's actual intent (fixing `load_config()`'s
  indentation only) by explicit user direction, not a technical impossibility.
- **Add a separate classmethod/factory instead of extending `__post_init__`**: moot
  once "Yes" was reverted — not pursued.

## Implementation
### Target file
scripts/eventbus/config.py

### Procedure
1. In `load_config()`, de-indent the `auth_token`-non-empty check (current lines
   194-196) and the per-role-token-required check (current lines 198-200) so they sit
   after the `for key, expected_type in _CONFIG_KEY_TYPES.items():` loop (line 185),
   not inside its body — same condition and error message, executed once per call
   instead of once per `_CONFIG_KEY_TYPES` entry.
2. ~~In `EventBusConfig.__post_init__`, add a check mirroring `load_config()`'s
   per-role-token rule~~ — **reverted, see Design decisions' Correction.**
   `__post_init__` is unchanged by this document.

### Method
One mechanical change in this file: a de-indent (no logic change) to
`load_config()`. No change to `__post_init__` (see Correction).

### Details
- Do not change `_CONFIG_KEY_TYPES`, `_KNOWN_CONFIG_KEYS`, `_REQUIRED_CONFIG_KEYS`, or
  any field's default value — this is validation-logic-only, per Scope.
- `__post_init__` is not touched by this document (Correction) — no
  per-role-token-required check is added there; it keeps exactly its pre-existing
  `auth_token`-non-empty check.

## Compatibility considerations
`load_config()`'s de-indent changes iteration count only, not validation outcome — no
behavior change for the TOML-parsing path. `EventBusConfig.__post_init__` is
unchanged, so no direct-construction caller (test or production) is affected by this
document at all.

## Security considerations
No change to any check's strictness — `load_config()`'s existing checks still run,
just once instead of once per `_CONFIG_KEY_TYPES` entry. `__post_init__`'s checks are
unchanged.

## Rollback considerations
Single, small de-indent edit in one file — revert to roll back. No schema,
migration, or on-disk data impact.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_config.py -v` and confirm
  `load_config()`'s validation still rejects the same invalid inputs it did before
  (unknown keys, missing keys, wrong types, empty `auth_token`, missing per-role
  token) — the de-indent must not change which inputs are accepted or rejected.
- Run the full `uv run pytest tests/eventbus/ -q --timeout=30` once to confirm no new
  regression — per the Correction above, this document's final (reverted-to) form
  touches only `load_config()`'s iteration count, so no direct-construction caller
  should be affected.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `load_config()`'s `auth_token`-non-empty and per-role-token-required checks execute
  exactly once per call (AC-1), with no change to which TOML inputs pass or fail.
- `EventBusConfig.__post_init__` is unchanged (UNK-01 resolved to No — see Design
  decisions' Correction).
- The full `tests/eventbus/` suite shows no new failures caused by this document's
  change.

## Out of scope
- The `_ROUTE_ROLE_MAP` routing issue (eb001, already implemented), the `_dlq_loop`
  shutdown/segfault issue (eb003, already implemented), and the
  `require_consumer_identity` missing-default issue (eb004) — each tracked
  separately.
- The previously-undiscovered `_TOKEN_CONSUMER_MAP`/`require_consumer_identity`
  allowlist bug found during eb001's implementation (empty set should mean "any
  consumer_id" per its own comment, but the check rejects every consumer_id when the
  set is empty) — unrelated to this file, needs its own issue/plan.
- Adding `publisher_token`/`monitoring_token` to the per-role-token-required set —
  not requested by REQ-001/UNK-01; would change security requirements beyond this
  Plan's scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-142331 | 20260913-142331 | De-indented load_config()'s auth_token/per-role-token checks (REQ-001); UNK-01 resolved to No after reverting a broader __post_init__ change that broke 114+22 unrelated tests |
| 2 | Add or update tests per Validation plan | Completed | 20260913-142331 | 20260913-142331 | Added test_load_config_rejects_missing_per_role_token to cover load_config()'s per-role-token error path (diff-cover) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-142331 | 20260913-142331 | ruff/mypy/bandit/lint-imports/diff-cover(100%)/pre-commit all passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-142331 | 20260913-142331 | N/A: internal validation-logic fix only |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-093422_eb002_eventbus-per-role-token-validation-incomplete.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-094809_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-122501
- **Related target files**: scripts/eventbus/config.py