## Goal

Make `ReplInputLoop.run()` own no persistence step (REQ-002): drop the
`persister_callback` parameter, its type union, and the persist `finally`, so the
persist step lives only in `AgentREPL.run()`'s outer `finally` (row 1). And make
one error raised inside `run()` produce exactly one operator-facing line
(REQ-007), resolving the duplicate report the plan measures.

## Scope

Production behavior change to `scripts/agent/repl_input_loop.py` only. Reference
reads: `scripts/agent/repl.py` (row 1, where the persist step now lives),
`scripts/agent/session_persister.py` (row 3, the gate). Dependent tests:
`tests/agent/test_repl.py` (rows 4/5).

## Assumptions

- `persister_callback` has exactly one caller — the second positional argument of
  `self._input_loop.run(...)` at `repl.py:154-157` (row 1 deletes it). No other
  caller exists (`grep -rn "persister_callback" scripts/` returns only these three
  lines — confirm before editing).
- `Coroutine` (imported at `:11`) appears only in the removed type union (`:80`);
  removing the parameter makes it unused, so the import must be trimmed to avoid
  ruff `F401`.
- `asyncio` is used throughout the file (`:61`, `:67`, `:136`, `:148`, `:158`,
  `:160`, `:162`, `:173`, `:179`, `:236`, `:254`, `:259`, `:260`, `:282`, `:288`),
  so removing `asyncio.iscoroutine` (`:114`) does not make the import unused.
- `sqlite3` is used only in the `except sqlite3.Error` handler (`:95`); whether it
  stays imported depends on the REQ-007 choice below.

## Design decisions

- **Drop the parameter and the finally (REQ-002).** Remove the
  `persister_callback` parameter and its three-way type union from `run()`'s
  signature (`:76-82`), leaving only `banner_callback: Callable[[], None]`. Delete
  the persist `finally` at `:111-115`. Keep every other statement, including the
  session-start handlers and `_repl_loop`, byte-for-byte.
- **Trim the import.** Remove `Coroutine` from `from collections.abc import
  Callable, Coroutine` (`:11`), becoming `from collections.abc import Callable`.
  Keep `asyncio` and `sqlite3` unless the REQ-007 choice below removes the last
  `sqlite3` use.
- **Single report (REQ-007 / UNK-01).** The current shape double-reports:
  - `SchemaMissingError` (`session.py:19` is a `RuntimeError`) is printed by the
    inner `except SchemaMissingError` (`:89-91`) and again by the outer
    `except RuntimeError` (`:108-110`) when re-raised.
  - `sqlite3.Error` is printed by the inner handler (`:95-101`) and then a new
    `RuntimeError` is raised and printed by the outer handler (`:108-110`).
  UNK-01 decides which side is the single reporter. Both options preserve the
  messages `test_repl.py:773-775` and `:803-806` assert. Implement the chosen
  option as step 4.

## Alternatives considered

- Keeping `persister_callback` as a plain `Callable[[], None]` — rejected: the
  bound value is always the same coroutine method (`repl.py:104-107`), so the
  `iscoroutine` branch (`:113-115`) is dead weight, and the persist step should
  not live in this component at all (REQ-002, Design → invariant).
- Resolving UNK-01 by deleting the outer `except RuntimeError` entirely — too
  aggressive: the outer handler also nets errors raised by `_repl_loop()`
  (`:107`); deleting it would drop those reports. The two options below keep the
  net when it is needed.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. **Remove the `persister_callback` parameter** from `run()`'s signature
   (`:76-82`). Replace lines `76-82`:
   ```python
   async def run(
       self,
       banner_callback: Callable[[], None],
       persister_callback: Callable[[], None]
       | Callable[[], "Coroutine[Any, Any, None]"]
       | None = None,
   ) -> None:
   ```
   with:
   ```python
   async def run(self, banner_callback: Callable[[], None]) -> None:
   ```
2. **Delete the persist `finally`** at `:111-115`:
   ```python
   finally:
       if persister_callback is not None:
           result = persister_callback()
           if asyncio.iscoroutine(result):
               await result
   ```
   The method body now ends after the `except RuntimeError` handler (`:108-110`)
   with no `finally`.
3. **Trim the import** at `:11` from
   `from collections.abc import Callable, Coroutine` to
   `from collections.abc import Callable` (`Coroutine` was only in the removed
   union). Confirm `asyncio` and `sqlite3` are still used elsewhere before
   touching them.
4. **Apply the REQ-007 single-report rule** by resolving UNK-01 (see Details).

### Method

Read-only reference reads of `repl.py` (row 1) and `session_persister.py` (row 3)
confirm the persist step's new home and gate; no edit there belongs to this row.

### Details

- **UNK-01 decision (step 4).** Choose one and implement it:
  - Option (a) — inner handlers are the only reporters: give each inner handler
    (`:89-91`, `:92-94`, `:95-101`) its single `write_fatal` + `raise`, and turn
    the outer handler (`:108-110`) into a bare re-raise:
    ```python
    except RuntimeError as e:
        raise
    ```
    Smallest diff; removes the catch-all that re-renders errors it did not
    produce. Risk: it drops the net for errors raised by `_repl_loop()` (`:107`).
  - Option (b) — outer handler is the single reporter: strip the `write_fatal`
    calls from the inner handlers, leaving them to `raise` only, and keep the
    outer handler's `write_fatal` + `raise` as the one reporter. Keeps the net but
    widens the diff.
  - Decide by running the existing tests (`test_repl.py`,
    `test_repl_error_handling.py`). If no test depends on the outer net catching a
    `_repl_loop()` error, option (a) is safe and preferred; otherwise choose (b).
    Record the choice in the Blocker Log.
- Under either option the `except sqlite3.Error` clause remains, so `sqlite3`
  stays imported. Only if a chosen option removes that clause would `sqlite3`
  need trimming — neither option does.
- The `run()` docstring ("Run the main REPL loop.") needs no change.

## Compatibility considerations

### Corrections found while implementing

- REQ-007 resolved with a local `reported` flag in `run()` (not option a/b as written): the inner session-start handlers report once and set the flag; the outer `except RuntimeError` reports only unreported errors (e.g. `_repl_loop()` not bound). `Coroutine` and `Any` imports were removed (ruff F401). `StdinReader`/bounded-wait changes that landed after this procedure do not interact.


- `ReplInputLoop.run()` loses one parameter; no other signature changes. The single
  remaining caller (`repl.py:154-157`, row 1) drops its second argument. In
  `test_repl.py` the 18 `mock_persister` fixtures and their paired call-site
  arguments are deleted (rows 4/5), which is also what keeps ruff `F841` from
  firing on the now-unused assignments.
- `_repl_loop`, `_read_input`, `_GRACEFUL_TIMEOUT_S` (`:55`) and the signal race
  (`:255-305`) are untouched.

## Security considerations

- N/A: no auth, secret, or permission change.

## Rollback considerations

- Single logical commit; `git checkout -- scripts/agent/repl_input_loop.py`
  restores HEAD. Reversible; touches no config or DB.

## Validation plan

- `grep -rn "persister_callback" scripts/ tests/` → empty (AC-5).
- `uv run ruff check scripts/agent/repl_input_loop.py tests/agent/test_repl.py`
  (no `F401`/`F841` left behind), `uv run mypy --no-namespace-packages
  scripts/agent/repl_input_loop.py`, `uv run vulture
  scripts/agent/repl_input_loop.py --min-confidence 80`.
- `uv run pytest tests/agent/test_repl.py tests/agent/test_repl_error_handling.py
  -q` (AC-6 once strengthened; AC-7).
- Radon: `ReplInputLoop.run` at or below B (9) after losing a parameter and a
  `finally` (AC-9).

## Completion criteria

`run()` takes one parameter (`banner_callback`), owns no persist `finally`, and one
error raised inside it produces one operator-facing line (UNK-01 resolved);
`persister_callback` is gone from signature, call site, and tests; AC-5/AC-6 hold.

## Out of Scope

- The persist step's new home in `AgentREPL.run()` — row 1. The write-or-skip gate
  and containment in `session_persister.py` — row 3. Docs — rows 6/7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop `persister_callback` parameter + type union from `run()` signature | Completed | 20261023-150346 | 20261023-150346 | REQ-002 implemented; full suite 9879 passed |
| 2 | Delete the persist `finally` (:111-115) | Completed | 20261023-150346 | 20261023-150346 | REQ-002 |
| 3 | Trim `Coroutine` from the import (F401) | Completed | 20261023-150346 | 20261023-150346 | REQ-002 |
| 4 | Apply REQ-007 single-report rule (UNK-01 decides) | Completed | 20261023-150346 | 20261023-150346 | REQ-007 |
| 5 | Run validation sequence (`rules/toolchain.md`) | Completed | 20261023-150346 | 20261023-150346 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1-4 | Shared file with `repl001` (`plans/20261022-030840_plan.md`): implement it first; this Plan owns `:76-82`, `:89-91`, `:95-101`, `:108-115` — different regions than `repl001`'s mid-turn cancellation branch (`:255-305`) and `_GRACEFUL_TIMEOUT_S` (`:55`) | No | — |
| 4 | UNK-01 (which handler is the single reporter) is open; decide during Phase 3 per the plan. Blocking: no. Blocks: step 4. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 4 | Uncertainty | Open | implementer | Phase 3 |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-007
- **Source issue**: `issues/20261021-093421_shutdown002-session-persistence-skipped-on-startup-failure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-071052_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-093504
- **Related target files**: `scripts/agent/repl_input_loop.py`