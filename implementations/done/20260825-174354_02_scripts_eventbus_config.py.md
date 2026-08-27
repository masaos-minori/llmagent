## Goal

`REQ-001`: make explicit and test-locked the invariant that EventBus's `load_config()`
only ever reads the single path returned by `get_config_path()`, without importing
`shared.config_loader.ConfigLoader` (which would violate the `.importlinter`
`eventbus-is-isolated` contract).

## Scope

- **In-Scope**: document the single-path invariant in `load_config()`'s docstring; add a
  regression test locking the invariant that `scripts/eventbus/app.py` always calls
  `load_config(get_config_path())` (never a different path, never bare `load_config()`
  relying on the `path=None` default).
- **Out-of-Scope**: adding runtime guard code inside `load_config()` itself that rejects
  a caller-supplied `path` not equal to `get_config_path()` — see Assumptions for why this
  was rejected after investigation.

## Assumptions

- `.importlinter`'s `eventbus-is-isolated` contract (`.importlinter:57-67`) forbids
  `eventbus` from importing `agent`, `mcp_servers`, `rag`, `db`, or `shared` — so
  `shared.config_loader.ConfigLoader` cannot be imported here; this Requirement must be
  satisfied without it.
- **Critical finding (resolves the source Plan's UNK-01)**: `load_config(path: Path |
  None = None)` (`scripts/eventbus/config.py:72`) is called with an explicit
  `tmp_path`-derived path by four existing tests in `tests/eventbus/test_eventbus_config.py`
  (`test_load_config_rejects_stray_poll_interval_ms` and three others, lines 62-120).
  Adding a runtime check inside `load_config()` that rejects any `path` not equal to
  `get_config_path()` would break all four of these tests, since none of them pass
  `get_config_path()`'s value. Therefore the guard must live at the call-site level
  (`scripts/eventbus/app.py`), not inside `load_config()`.
- Confirmed both production call sites already pass `get_config_path()` explicitly:
  `scripts/eventbus/app.py:58` (`app.state.config = load_config(get_config_path())`) and
  `scripts/eventbus/app.py:198` (`cfg = load_config(get_config_path())`).
- Noted but out of scope for this Requirement: `load_config()`'s own default
  (`p = path or _DEFAULT_CONFIG_PATH`, line 74) does not consult the
  `EVENTBUS_CONFIG_PATH` environment variable the way `get_config_path()` does — a caller
  relying on the bare default (`load_config()` with no argument) would silently bypass
  the env var. This is currently harmless because no production call site relies on the
  default (see previous bullet), but is noted here for visibility; changing it is not
  part of REQ-001's scope (the source Plan does not request it).

## Design decisions

- Keep `load_config()`'s signature and body unchanged — add only a docstring line stating
  the invariant ("Callers must always pass `get_config_path()`'s return value; this
  function does not itself enforce that — see the `app.py` call-site regression test.").
- Lock the invariant with a regression test at the `app.py` call-site level: assert (via
  `inspect.getsource` or an equivalent static check, or by monkeypatching `load_config`
  and asserting the argument it was called with) that both `app.py` call sites pass
  exactly `get_config_path()`'s return value.

## Alternatives considered

- Runtime guard inside `load_config()` rejecting `path != get_config_path()`: rejected —
  breaks four existing tests that pass arbitrary `tmp_path` values (see Assumptions).
- Wrapping `load_config()` in a new function that enforces the path and replacing all
  callers: rejected as unnecessary indirection for a two-call-site invariant; a
  call-site-level regression test achieves the same guarantee with less code to maintain.

## Implementation

### Target file
`scripts/eventbus/config.py`

### Procedure
1. In `scripts/eventbus/config.py`, update `load_config()`'s docstring (currently `"""Load
   and validate the EventBus TOML configuration file."""`, line 73) to state the
   single-path invariant explicitly, e.g.: `"""Load and validate the EventBus TOML
   configuration file. Callers must always pass get_config_path()'s return value —
   this function does not itself restrict which path is read; see
   tests/eventbus/test_eventbus_config.py for the call-site regression test that locks
   this invariant."""`
2. Add a new test to `tests/eventbus/test_eventbus_config.py` that reads
   `scripts/eventbus/app.py`'s source (or imports `eventbus.app` and inspects the two
   call sites via `inspect.getsource(eb_app)`) and asserts both occurrences of
   `load_config(` are followed by `get_config_path()`, not a literal path or a bare call.
3. Do not modify `EventBusConfig`, `_is_public_host`, or any other symbol in
   `scripts/eventbus/config.py`.

### Method
Docstring-only change to `config.py`; new regression test added to the existing test
file (no changes to the four existing tests, which remain valid exercises of
`load_config()`'s `path` parameter for unit-level testing).

### Details
- The regression test's purpose is to catch a future edit to `app.py` that passes a
  different path (or omits the argument) to `load_config()`, not to constrain
  `load_config()`'s own parameter contract.

## Compatibility considerations

- No behavior change to `load_config()` or any caller — docstring-only edit plus an
  additive test. The four existing tests in `test_eventbus_config.py` are unaffected.

## Security considerations

- Establishes a test-enforced guarantee (rather than a runtime one) that the EventBus
  process only ever reads its own declared config path, consistent with ADR-002's
  INV-01/INV-02 intent, without importing `shared.config_loader` and without breaking
  `.importlinter`'s `eventbus-is-isolated` contract.

## Rollback considerations

- Revert the docstring line and remove the added test; no other state changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/config.py` | N/A: docstring-only, no behavior to unit-test directly | N/A | N/A |
| `tests/eventbus/test_eventbus_config.py` | Integration (call-site regression) | `PYTHONPATH=scripts uv run pytest tests/eventbus/test_eventbus_config.py -v` | All existing tests plus the new call-site regression test pass |
| Repository-wide | Architecture | `PYTHONPATH=scripts uv run lint-imports` | Unchanged: same contracts kept/broken as before this change (no new import added to `eventbus/`) |

## Completion criteria

- `load_config()`'s docstring states the single-path invariant.
- A new test in `tests/eventbus/test_eventbus_config.py` fails if either `app.py` call
  site stops passing `get_config_path()`'s return value to `load_config()`.
- `uv run lint-imports` shows no new violation of `eventbus-is-isolated`.

## Out of scope

- Any runtime guard code inside `load_config()` (see Assumptions/Alternatives).
- The `path=None` default's env-var inconsistency noted in Assumptions — not requested
  by the source Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `load_config()` docstring with the single-path invariant | Pending | — | — | |
| 2 | Add call-site regression test to `tests/eventbus/test_eventbus_config.py` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to `scripts/eventbus/` and `tests/eventbus/`, including `lint-imports` | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope for this file — see companion `docs/adr/ADR-002-config-isolation.md` implementation procedure document for REQ-003 |

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
- **Requirement ID**: `REQ-001` — lock the EventBus single-config-path invariant without importing `ConfigLoader`
- **Source issue**: `issues/20260822_ci_eventbus_bypasses_restrict_to.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-131854_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-174354
- **Related target files**: `scripts/eventbus/config.py`
