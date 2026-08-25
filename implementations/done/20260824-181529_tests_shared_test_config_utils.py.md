## Goal

Add a dedicated test file for `scripts/shared/config_utils.py::get_str()` covering its
full branch set. No production code change.

## Scope

- In scope: create `tests/shared/test_config_utils.py` with tests for all `get_str()`
  branches.
- Out of scope: `get_typed()` in the same file; `scripts/shared/json_utils.py` and
  `scripts/shared/llm_hot_config.py` (already covered by existing test files); any
  change to `scripts/shared/config_utils.py` itself.

## Assumptions

- `get_str()` (`scripts/shared/config_utils.py:18-25`) has two structural branches:
  `v is None` (covers both "missing key" and "value is `None`", since `dict.get(key)`
  returns `None` for both) → return `default`; and `not isinstance(v, str)` → raise
  `ValueError`. Otherwise returns `v` unchanged.
- No existing test in `tests/shared/` exercises `get_str()` — confirmed:
  `tests/shared/test_config_utils.py` does not exist, and `grep -rn "get_str\b"
  tests/shared/` returns no hits.
- No existing document under `implementations/` or `implementations/done/` targets
  `tests/shared/test_config_utils.py` — confirmed via
  `grep -rl "test_config_utils" implementations/ implementations/done/` (no matches).

## Design decisions

- Plain function-level unit tests, no fixtures — `get_str` takes a plain `dict`.
- Keep "missing key" and "`None` value" as two separate test cases even though they
  exercise the same `v is None` branch in the implementation (both start from
  `d.get(key)` returning `None`): they represent two distinct caller-observable input
  scenarios (absent key vs. explicit `None`), and keeping them separate documents both
  scenarios explicitly for future readers even though the code path is shared.

## Alternatives considered

- Collapsing "missing key" and "`None` value" into a single parametrized test case —
  rejected: keeping them separate is clearer for future readers even though it does not
  add branch coverage beyond the first case, since the intent (absent vs. explicit
  `None`) differs by input even where the code path does not.

## Implementation

### Target file

`tests/shared/test_config_utils.py` (new file)

### Procedure

1. `test_get_str_returns_string_value` — `get_str({"k": "v"}, "k")` returns `"v"`.
2. `test_get_str_raises_on_non_string_value` — `get_str({"k": 1}, "k")` raises
   `ValueError` whose message contains the key name (matches the f-string in the
   source: `f"Config key {key!r} must be str, got {type(v).__name__}"`).
3. `test_get_str_returns_default_on_missing_key` — `get_str({}, "k", default="x")`
   returns `"x"`.
4. `test_get_str_returns_default_on_none_value` — `get_str({"k": None}, "k",
   default="x")` returns `"x"`.
5. `test_get_str_default_is_empty_string_when_unset` — `get_str({}, "k")` returns `""`
   (the function's own default parameter value).

### Method

Import directly: `from shared.config_utils import get_str` (matches the module's own
docstring usage example).

### Details

`get_str()` (`scripts/shared/config_utils.py:18-25`):
```
v = d.get(key)
if v is None: return default
if not isinstance(v, str): raise ValueError(...)
return v
```
All 5 test cases map onto this exact 3-branch structure (default-return, type-error,
passthrough), as itemized in Procedure above.

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: pure in-memory dict input, no secrets, network, or filesystem access.

## Rollback considerations

Delete the new test file; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_utils.py` | Unit | `uv run pytest tests/shared/test_config_utils.py -v` | 5 tests pass |
| `tests/shared/` (full) | Regression | `uv run pytest tests/shared/ -v` | No new failures |
| `scripts/shared/config_utils.py` (untouched) | Static | `uv run ruff check scripts/shared/` + `uv run mypy scripts/shared/` | No new findings |

## Out of scope

`get_typed()`; `scripts/shared/json_utils.py`; `scripts/shared/llm_hot_config.py`; any
change to `scripts/shared/config_utils.py`.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` and `Source requirement: requires/20260726-121213_require.md` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/20260726-121213_require.md`
- **Source plan**: `plans/20260823-193335_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-181529
- **Related target files**: `tests/shared/test_config_utils.py`

## Adversarial verification notes (this cycle)

Re-verified the plan against current code:
- `scripts/shared/config_utils.py:18-25` confirms `get_str()` matches the plan exactly.
- Noted (non-blocking, documentation nuance only): the Design section describes
  "missing key" and "`None` value" as covering the branch "distinctly," but both inputs
  produce the same `v is None` result from `d.get(key)` — there are only 3 structural
  branches, not 4. This does not affect implementability or test validity (both remain
  legitimate, distinctly-named input scenarios); no plan edit was needed, and this is
  recorded here for the implementer's awareness rather than as a plan correction.
- Confirmed via `grep -rn "get_str\b" tests/shared/` that no existing test covers this
  function, and via `grep -rl "test_config_utils" implementations/ implementations/done/`
  that no duplicate implementation procedure document exists.
- No blocking unknowns or contradictions found. The plan's own "Adversarial
  verification notes" section (narrowing the original 3-module requirement to
  `config_utils.py` only) remains accurate.
