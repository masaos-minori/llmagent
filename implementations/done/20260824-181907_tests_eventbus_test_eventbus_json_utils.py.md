## Goal

Add dedicated unit tests for `scripts/eventbus/json_utils.py` (`dumps`, `now_iso`) —
the eventbus-local duplicates created to satisfy the `eventbus-is-isolated`
import-linter contract. No production code change.

## Scope

- In scope: create `tests/eventbus/test_eventbus_json_utils.py` covering `dumps()`
  and `now_iso()`.
- Out of scope: any further import/dependency change (`lint-imports` already reports
  "5 kept, 0 broken"); the pragma test for `_apply_eventbus_pragmas()`, which belongs
  to `tests/eventbus/test_eventbus_db_migration.py` (separate target file, separate
  implementation procedure document).

## Assumptions

- `scripts/eventbus/json_utils.py` exists as an eventbus-local duplicate of
  `shared.json_utils`'s `dumps`/`now_iso` — confirmed by reading the file in full this
  cycle: `dumps()` wraps `orjson.dumps(obj, option=option).decode()` with
  `OPT_SORT_KEYS` as the default `option`; `now_iso()` returns
  `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`.
- No existing test file at `tests/eventbus/test_eventbus_json_utils.py` — confirmed via
  file-existence check this cycle.
- `PYTHONPATH=scripts uv run lint-imports` currently reports "Contracts: 5 kept, 0
  broken" including `eventbus must not import from agent, mcp_servers, rag, db, or
  shared` — re-confirmed this cycle; this test addition must not change that.

## Design decisions

- Plain function-level unit tests, no fixtures needed — both functions are pure
  (no I/O, no shared state).
- Assert `dumps()`'s return type is `str` (not `bytes`) explicitly, since the whole
  point of the eventbus-local wrapper is the `.decode()` call `orjson.dumps()` itself
  does not perform.

## Alternatives considered

- Testing `dumps()`/`now_iso()` indirectly through a higher-level eventbus module that
  calls them — rejected: direct unit tests are simpler, faster, and isolate failures to
  the actual function under test, matching the plan's Design intent.

## Implementation

### Target file

`tests/eventbus/test_eventbus_json_utils.py` (new file)

### Procedure

1. `test_dumps_returns_str` — `dumps({"a": 1})` returns a `str`, not `bytes`.
2. `test_dumps_sorts_keys_by_default` — `dumps({"z": 1, "a": 2})` produces `a` before
   `z` in the output string (matches `OPT_SORT_KEYS` as the default `option`).
3. `test_now_iso_format` — `now_iso()` matches
   `r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"`.

### Method

Import directly: `from scripts.eventbus.json_utils import dumps, now_iso` — matches the
import pattern already used by other `tests/eventbus/test_eventbus_*.py` files.

### Details

Current code (verified this cycle), `scripts/eventbus/json_utils.py`:
```python
OPT_SORT_KEYS: int = orjson.OPT_SORT_KEYS

def dumps(obj: object, option: int | None = OPT_SORT_KEYS) -> str:
    return orjson.dumps(obj, option=option).decode()

def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
```
All 3 tests map directly onto this implementation.

## Compatibility considerations

Test-only addition; no production code, schema, or public interface changes.

## Security considerations

N/A: pure in-memory function calls, no secrets, network, or filesystem access.

## Rollback considerations

Delete the new test file; no other rollback steps required.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_json_utils.py` | Unit | `uv run pytest tests/eventbus/test_eventbus_json_utils.py -v` | 3 tests pass |
| `scripts/eventbus/` (isolation) | Architecture | `PYTHONPATH=scripts uv run lint-imports` | 5 contracts kept, 0 broken |
| `tests/eventbus/` (full) | Regression | `uv run pytest tests/eventbus/ -v` | No new failures |
| `tests/eventbus/test_eventbus_json_utils.py` | Static | `uv run ruff check tests/eventbus/test_eventbus_json_utils.py` + `uv run mypy tests/eventbus/test_eventbus_json_utils.py` | Clean |

## Out of scope

Any further import/dependency change; the pragma test (belongs to a separate target
file / separate implementation procedure document); restoring the
eventbus-implementation-forbidden policy text (a separate, deliberate policy decision,
not part of this test-coverage gap).

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
- **Source issue**: N/A: not applicable in this phase (the source plan's own Traceability records `Source issue: N/A` and `Source requirement: requires/20260726-121812_require.md` — this plan predates the issue-to-plan pipeline merge)
- **Source requirement**: `requires/20260726-121812_require.md`
- **Source plan**: `plans/20260823-194101_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260824-181907
- **Related target files**: `tests/eventbus/test_eventbus_json_utils.py`

## Adversarial verification notes (this cycle)

- Re-verified `scripts/eventbus/json_utils.py`'s full content against the plan's
  Design/Assumptions — matches exactly.
- Re-ran `PYTHONPATH=scripts uv run lint-imports` — confirmed "Contracts: 5 kept, 0
  broken" including `eventbus-is-isolated`, matching the plan's claim.
- Confirmed `routing.md`'s Event Bus row currently routes implementation work to
  `skills/python-implementation/` (not an implementation-forbidden policy), and that
  `AGENTS.md` contains no "Global Rule 8"/"implementation forbidden" text — consistent
  with the plan's Adversarial verification notes describing this correction as already
  applied in a prior review pass.
- Confirmed no existing test file at this target path and no duplicate implementation
  procedure document for this plan/target pair. No blocking unknowns or contradictions
  found.
