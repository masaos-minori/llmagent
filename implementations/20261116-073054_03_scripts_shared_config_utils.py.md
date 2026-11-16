## Goal
- Harden `get_typed` in `scripts/shared/config_utils.py` so a `bool` is rejected when `expected_type` is `int` or `float` (REQ-002), with `tests/shared/test_config_utils.py` as companion pinning the type matrix (REQ-007 part).

## Scope
**Release unit**: retention-input-validation (Phases 1-3 of the plan; lands with `20261116-073054_01`, `_02`, `_04`, `_05`)

- In scope: the bool guard + docstring in `get_typed` (`:54-76`); companion test class in `tests/shared/test_config_utils.py`.
- Out of scope: the call-site switch to `get_typed` in `maintenance.py`/`config.py` (procedures `20261116-073054_01`/`_04`); `scripts/mcp_servers/git/git_models.py` `_optional_real` local helper — stays as-is per the scope rule (plan Reference Files).

## Assumptions
- Verification finding (2026-11-16, re-confirmed against source): `get_typed` (`:54-76`) does `if not isinstance(value, expected_type)` only — `isinstance(True, int)` is `True`, so `bool` passes today for int/float keys.
- Companion eligibility for `tests/shared/test_config_utils.py`: plan table row 7 under `tests/`, named in exactly one other row's Related Tests (this row), fully prescribed tests, same plain-unit-test harness — no design decision of its own (SKILL.md companion conditions 1-4).
- Existing consumers pass TOML-typed ints (`web_search`, `file` models); a bool there now fails closed at server config load — intended behavior (Plan Assumptions).

## Design decisions
- Reject `bool` before the `isinstance` check rather than adding a coercion or a new helper: the Issue's AI Instruction forbids new coercion mechanisms; the existing shared helper is hardened and reused (Plan Design).
- Keep `bool` valid for `expected_type=bool` (REQ-002 exception).

## Alternatives considered
- Per-call-site bool checks: rejected — 9 mcp_servers + eventbus consumers would each need the check; the shared helper is the boundary.
- Changing `scripts/mcp_servers/git/git_models.py:_optional_real` to delegate: rejected — its "left untouched" comment records an author decision; scope rule keeps it as-is.

## Implementation
### Target file
`scripts/shared/config_utils.py`

### Procedure
1. In `get_typed`, insert before the `isinstance` check (`:71` region): `if expected_type in (int, float) and isinstance(value, bool): raise ValueError(f"'{key}' must be {type_label}, got bool: {value!r}")` (REQ-002).
2. Docstring: add one sentence — `bool` is rejected for `int`/`float` expected types because `isinstance(True, int)` would otherwise pass; `bool` remains valid when `expected_type=bool`.

### Companion test files
- `tests/shared/test_config_utils.py`
  - Procedure: add a `get_typed` test class: `get_typed({"k": True}, "k", int, "an integer")` raises `ValueError` matching `bool`; same for `float`; float-for-int and str-for-int raise stay pinned; `get_typed({"k": True}, "k", bool, "a bool")` passes through; absent-key default behavior stays pinned. The 5 existing `get_str` tests are untouched.
  - Validation: `uv run pytest tests/shared/test_config_utils.py -v` → AC-3 asserted.

### Method
- Two-line-scale edit in the existing function; no new imports (plan Design: no new mechanism).

### Details
- radon baseline: `config_utils.py` top A — the guard adds 1 branch and keeps the module low (plan Baseline Consistency).
- Blast radius: eventbus + 9 mcp_servers consumers of `get_typed`/`get_str` (plan Affected areas); behavior change only for bool-for-int values, which no shipped config uses.

## Compatibility considerations
- Fail-closed change: a config that previously accepted `True` for an int key now raises at load naming key and got-type `bool` (AC-3). No shipped config uses bools for int keys (verified Step 2).

## Security considerations
- Net improvement: prevents `True` silently becoming `1` in retention/timeout limits (the Issue's original off-by-value class); bandit baseline unchanged.

## Rollback considerations
- `git checkout` revert of the unit commit; part of release unit retention-input-validation — reverting this alone makes the `_01`/`_04` call sites weaker (bool would flow through `get_typed` again), so revert together with `_01`, `_02`, `_04`, `_05`.

## Validation plan
- `uv run pytest tests/shared/test_config_utils.py -v` → companion class passes (AC-3).
- `uv run pytest tests/ -n auto` → no regressions across eventbus + mcp_servers config loaders (plan Validation plan).
- `uv run ruff check scripts/shared/config_utils.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` (CI form per `rules/toolchain.md`).

## Completion criteria
- `get_typed` raises `ValueError` naming the got-type `bool` for `int`/`float` expected types; accepts `bool` for `bool`; all other behaviors byte-identical; companion tests and full suite green.

## Out of Scope
- `maintenance.py`/`config.py` call-site changes (procedures `20261116-073054_01`/`_04`).
- `scripts/mcp_servers/git/git_models.py` `_optional_real` (stays as-is).
- `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` update (plan Phase 3 step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `get_typed` bool guard + docstring (plan Phase 1) | Pending | — | — | REQ-002; batch order 006 -> 007, no code dependency on 006 |
| 2 | Companion tests in `tests/shared/test_config_utils.py` (plan Phase 3) | Pending | — | — | REQ-007 (config-utils part) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (get_typed bool rejection), REQ-007 (companion get_typed matrix tests)
- **Source issue**: issues/20261114-092855_dbreview007_retention-input-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050559_dbreview007_retention-input-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-073054
- **Related target files**: `scripts/shared/config_utils.py`, `tests/shared/test_config_utils.py`
