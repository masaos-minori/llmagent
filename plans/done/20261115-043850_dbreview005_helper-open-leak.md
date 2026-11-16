## Goal
- Make `SQLiteHelper.open` leak-free on every failure path (post-connect exceptions, vec-load exceptions other than `OperationalError`, re-open over an existing connection) and turn an explicit `load_vec=True` without a configured `sqlite_vec_so` into an immediate `ValueError` instead of a silent skip.

## Priority
Medium (Issue Priority)

## Scope
- **In-Scope**: exception-safe `open` with single-owner close responsibility; closing a previously open connection on non-reuse re-open; explicit-`load_vec=True` guard; unit tests for each path.
- **Out-of-Scope**: the `read_only` open mode (`plans/20261115-041859_dbreview004_integrity-probe-side-effects.md`, lands first); the default pragma set (Issue Out of Scope); `check_same_thread` design (Issue Out of Scope); config-level `sqlite_vec_so` validation (already implemented in `scripts/db/config.py:66-69`).
- **Dependencies**: none per the Issue.
  - **Depends on**: plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | phase all | sequencing only: 004 modified the same `open`/`_connect`/pragma region of `scripts/db/helper.py` (added `read_only`); 005 landed after 004 and its procedures target the post-002/004 code shapes. No behavioral dependency. (004 landed 2026-11-15 in commit `693f71679`; re-verified this cycle.)

## Background
From the Source Issue (F-005), re-verified against the post-004 tree (2026-11-15; Plan 004 landed in commit `693f71679`). All three leak claims hold in `scripts/db/helper.py`: `open` (:280-333) creates the connection at `:315` and stores `self.conn` only at `:329`; the existing `try/except Exception` at `:316-326` closes the connection only when `read_only=True` (`:321-325`), so any exception from `_configure_connection` (`:317-319`) — vec load or pragmas — leaves the raw connection unclosed on the write path. `_load_vec_extension` (`:247-260`) closes the connection only on `sqlite3.OperationalError` (`:257-260`, close at `:258`); an `AttributeError` from `enable_load_extension` (`:254`) leaks it. A non-reuse `open()` over an already-open helper overwrites `self.conn` at `:329` and drops the previous connection.

Two Issue claims are retired by upstream work (batch MID-PULL, commit era of `4543c2aa4`):
- The silent-skip consequence ("callers fail later with `no such module: vec0`, reported as corruption") is already defused: `build_db_config()` rejects an empty/absent `sqlite_vec_so` (`scripts/db/config.py:66-69`, tests `tests/db/test_sqlite_helper.py:397-433`), so `self._vec_so` (`helper.py:132`) is never empty in production; an empty value is only reachable through patched-config tests. The missing vec0 condition is also mapped honestly as `verification_unavailable` (`scripts/db/recovery.py:387-402`) by the Plan 001-related upstream fix. The helper-level guard requested by the Issue remains as a defensive contract at the boundary the Issue names.
- The unreachable `ValueError` guard in `_load_vec_extension` (`helper.py:249-252`) stays in place; the new guard moves to `open` where the explicit intent is known — the silent skip currently sits in `_configure_connection` (`:243-244`, `if use_vec and self._vec_so`).

Existing frozen behaviors this Plan must not break: default-`load_vec=None` skip with empty vec_so under a patched config (`tests/db/test_sqlite_helper.py:338-356`), `OperationalError` at open leaving `helper.conn is None` (`:358-369`), workflow ignoring vec config (`:371-395`), `reuse_connection` semantics (`:262-290`, Issue Constraint), and `open(load_vec=True)` with a configured path invoking the load (`:305-335`).

## Problem
A leaked connection keeps file locks and WAL readers alive (holding the helper object alive keeps the socket open indefinitely under reference cycles or module-level references), which can block checkpoints and the maintenance operations this package performs. A silent `load_vec=True` skip defers a configuration error to a confusing downstream failure.

## Reason for Change
Resource lifecycle correctness: the helper is the single connection gateway for every DB component, so its failure paths determine whether locks are released. Making explicit intent explicit (load_vec=True must load or fail) is the fail-closed contract used elsewhere in this package.

## Implementation Intent
Give `open` a single owner for connection teardown: every step after `_connect` runs inside a `try/except BaseException` that closes the connection and re-raises. `_load_vec_extension` drops its own `conn.close()` (single-owner teardown; close is also safe on an already-closed connection). A non-reuse re-open closes the previous `self.conn` (with a debug log) before connecting. `open` raises `ValueError` when `load_vec=True` is passed explicitly and `self._vec_so` is empty; `load_vec=None` (instance default) is untouched.

## Requirements
- `REQ-001`: post-connect failure in `open` closes the connection and re-raises the original exception with `self.conn` still `None` (AC-1).
- `REQ-002`: `_load_vec_extension` no longer closes the connection itself; teardown for its `OperationalError` (and any other exception, e.g. `AttributeError`) is `open`'s single-owner handler; the exception type propagating out of `open` is unchanged (AC-1, AC-2).
- `REQ-003`: calling `open(reuse_connection=False)` on a helper with `self.conn` set closes the previous connection before the new one is created; `reuse_connection=True` semantics unchanged (AC-3).
- `REQ-004`: `open(load_vec=True)` with empty `self._vec_so` raises `ValueError` naming `sqlite_vec_so` before any connection is created; `load_vec=None` default behavior unchanged (`AC-4`).
- `REQ-005`: tests cover each path: leaked-lock proof, `AttributeError` vec failure with `conn` closed and `helper.conn is None`, re-open closing the first connection, explicit-`load_vec` `ValueError` (AC-1..AC-4).

## Implementation Target Files
**Freeze status**: Frozen (validated in Step 8: every row exists, requires modification, has supporting evidence recorded this cycle, and links to a Requirement).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/db/helper.py | Modify | `open` single-owner teardown (`try/except BaseException`), re-open close-before-connect, explicit-`load_vec` guard; `_load_vec_extension` drops its `conn.close()` | REQ-001..REQ-004 / AC-1..AC-4 | `helper.py:315` connect, `self.conn` stored only at `:329`; `try/except Exception` at `:316-326` closes only on the `read_only` branch (`:321-325`); `_load_vec_extension` `:257-260` closes only on `OperationalError` (close at `:258`); silent skip `use_vec and self._vec_so` in `_configure_connection` `:243-244` (re-verified 2026-11-15 against the post-004 code) | tests/db/test_sqlite_helper.py | Verified |
| tests/db/test_sqlite_helper.py | Modify | Add leak/lock, AttributeError-vec, re-open, explicit-`load_vec` ValueError tests | REQ-005 / AC-1..AC-4 | No existing test asserts connection teardown on pragma failure or re-open (`grep` of `reuse_connection`/`close` usages, Step 3; `:358-369` covers only the OperationalError outcome) | tests/db/test_sqlite_helper.py | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/config.py | `sqlite_vec_so` validation (`:66-69`) establishes the production-unreachable status of the empty-path guard; **no edit required** | scripts/db/helper.py / REQ-004 |
| plans/20261115-041859_dbreview004_integrity-probe-side-effects.md | Defines the `read_only` branch of `open`/`_connect`/pragmas that this Plan's teardown wrapper must target (lands first) | scripts/db/helper.py / REQ-001 |
| tests/db/test_sqlite_helper.py frozen-behavior tests `:262-290`, `:305-335`, `:338-395` | Constraint behaviors that must stay green (reuse semantics, explicit override, default skip) | scripts/db/helper.py / REQ-003, REQ-004 |

## Acceptance Criteria
- AC-1 (`REQ-001`, `REQ-002`, `REQ-005`): After a failing `open` (pragma failure or vec-load failure of any exception type), no connection to the file remains — proven by the helper's captured connection being closed and by a second connection acquiring what the leaked one would have held.
- AC-2 (`REQ-002`): `test_unloadable_vec_so_raises_at_open` (`:358-369`) stays green — same exception type, `helper.conn is None`.
- AC-3 (`REQ-003`, `REQ-005`): A re-open closes the first connection (subsequent use of the first connection raises `sqlite3.ProgrammingError`) and `reuse_connection=True` tests stay green.
- AC-4 (`REQ-004`, `REQ-005`): `open(load_vec=True)` with empty `sqlite_vec_so` raises `ValueError` naming `sqlite_vec_so` before connecting; default-None skip tests stay green.

## Tests
- `REQ-001/REQ-005` (AC-1): with a temp DB and a stubbed `_apply_connection_pragmas` that raises, capture the raw connection (patch `_connect`) and assert `conn.closed` is True after `open` raises and `helper.conn is None`.
- `REQ-002/REQ-005` (AC-1, AC-2): stub `enable_load_extension` to raise `AttributeError`; assert the connection was closed, `helper.conn is None`, and the `AttributeError` propagates.
- `REQ-003/REQ-005` (AC-3): open, capture conn A, call `open()` again (non-reuse), assert A raises `sqlite3.ProgrammingError` on use (closed) and the helper now holds a fresh connection.
- `REQ-004/REQ-005` (AC-4): patched config with `sqlite_vec_so=""`, `helper.open(load_vec=True)` raises `ValueError` matching `sqlite_vec_so`; the same helper with `load_vec=None` still opens without the extension (pattern of `:338-356`).

## Documentation Impact
No. The Issue states documentation is not required beyond the `open` docstring, which is updated in the code row. No `docs/*.md` change; `tools/check_docs_consistency.py` is still run in Phase 2 as part of the standard gate set.

## Baseline Consistency (Step 5)
| Dimension | Baseline Value | Source (exact command) | Recorded |
|---|---|---|---|
| radon CC targets | `helper.py` top `open` B(9) (post-004) | `uv run radon cc scripts/db/helper.py -s` (re-run this cycle) | 2026-11-15 |
| vulture targets | No `scripts/db` findings repo-wide | `uv run vulture scripts/ --min-confidence 80` (run this cycle) | 2026-11-15 |
| bandit targets | 45 low / 0 medium / 0 high | `uv run bandit -r scripts/ -c pyproject.toml` (run this cycle) | 2026-11-15 |
| coverage targets | project total 95%; tree clean at recording | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (run this cycle) | 2026-11-15 |
| operational check | no process holds `/opt/llm/db/rag.sqlite` or `/opt/llm/db/session.sqlite` (`fuser` empty, exit 1); dev-host only | `fuser /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite` (run this cycle, recorded under Plan 002 Step 3) | 2026-11-15 |

## Assumptions
- `sqlite3.Connection.closed` (Python 3.13) is a sufficient leak assertion; the Issue's exclusive-lock technique is additionally used in one integration test (AC-1) to validate the assumption behaviorally (checked in Step 3 as mechanism).
- Double `close()` on a connection is a no-op, so the single-owner teardown wrapper is safe even if a callee already closed (`helper.py:258` removal is not required for safety, only for single-owner clarity).
- No production caller relies on a leaked-but-unclosed connection after a failed `open` (grep in Step 3 found no `try: open() except: ... conn` patterns outside the helper).
- Empty `_vec_so` is production-unreachable due to `config.py:66-69`; the `ValueError` guard is a boundary contract, not a production-path fix (checked in Step 2).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any third-party or notebook-style caller depends on `open` silently discarding an old connection (re-open semantics) | No such caller found in this repo (Step 3 grep of `.open(` call sites) | Close-with-log chosen (backward compatible); if a real caller reports a regression, reconsider a `RuntimeError` refusal | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/db/helper.py | Modify | High (every DB component opens through this Helper) | 3 | High (single author, >70%) | not applicable (rsynced) |
| tests/db/test_sqlite_helper.py | Modify | Low (test-only) | 0 | High (single author, >70%) | not applicable (rsynced) |

## Cross-Plan Target Overlap Scan

- Re-run with all plans frozen so far (`tools/check_plan_target_overlaps.py`, 2026-11-15): new findings — `scripts/db/helper.py` (004+005) and `tests/db/test_sqlite_helper.py` (004+005). Judgment: **sequencing** — fixed batch order 004 → 005; 004 added the `read_only` branch to `open`/`_connect`/pragmas, and 005 wraps the resulting post-connect body in the teardown handler and adds disjoint tests. 004 has landed (commit `693f71679`); 005's Phase 1 re-reads 004's landed code shape before editing. No behavioral interaction: 004's probes use `read_only` opens; 005's teardown applies to every open regardless of mode.

## Design
- **Single-owner teardown**: `open` wraps `_configure_connection` + row_factory + conn assignment in `try/except BaseException: conn.close(); raise`. The current `:316-326` handler closes only on the `read_only` branch; the write path must gain the same teardown. `_load_vec_extension` loses its own `conn.close()` so exactly one site decides teardown (mutation-safe for `OperationalError` outcome — AC-2 keeps the existing test green). Rejected alternative: per-callee cleanup — every current callee would need its own teardown and any future callee added to `open` re-introduces the leak class.
- **Re-open close-before-connect**: at the top of `open` (after the reuse short-circuit at `:310-311`), if `self.conn is not None`: close it with a debug log. Chosen over refusal because existing callers (Step 3 grep) never treat a second non-reuse `open()` as an error, and closing preserves their behavior while removing the leak.
- **Explicit-`load_vec` guard**: in `open`, `if load_vec is True and not self._vec_so: raise ValueError("load_vec=True requested but sqlite_vec_so is not configured")` placed before `_connect` so no connection is created for a doomed open. `load_vec=None` keeps `_default_load_vec` behavior verbatim (Issue Constraint), so `:338-356` and `:371-395` stay green.
- **Complexity control** (radon baseline `open` B(9), post-004): the post-verification body (vec + pragmas + row_factory + teardown wrapper) is extracted into a private `_prepare_connection(conn, *, write_mode, row_factory, use_vec)` so `open`'s CC drops back to B or below; `_prepare_connection` carries the try/except. Rejected alternative: inline try/except in `open` — adds CC to an already-B(9) function.
- **Architecture check** (Step 3): no new import edges; `lint-imports` reported 6 contracts kept this cycle; `helper.py` keeps its layer (imported by `db.recovery`, services).
- **Persisted schema check**: N/A — connection lifecycle only.

## Implementation steps
1. **Phase 1: Single-owner teardown and re-open close** (REQ-001..REQ-003; `scripts/db/helper.py`)
   - [ ] Extract post-connect preparation into `_prepare_connection` with `try/except BaseException` close-and-reraise; remove `conn.close()` from `_load_vec_extension` (REQ-001, REQ-002; scripts/db/helper.py)
   - [ ] Close an existing `self.conn` (debug log) on non-reuse re-open before `_connect` (REQ-003; scripts/db/helper.py)
2. **Phase 2: Explicit-`load_vec` guard and tests** (REQ-004, REQ-005; `scripts/db/helper.py`, `tests/db/test_sqlite_helper.py`)
   - [ ] Add the `load_vec=True` + empty-path `ValueError` guard before `_connect` (REQ-004; scripts/db/helper.py)
   - [ ] Add the four tests of the Tests section (REQ-005; tests/db/test_sqlite_helper.py)
   - [ ] Run `uv run pytest tests/db` and full suite `-n auto` (AC-1..AC-4)
3. **Phase 3: Validation & deployment hand-off**
   - [ ] Run ruff, mypy (CI form), bandit `-ll`, `lint-imports`, `tools/check_docs_consistency.py --domain db`
   - [ ] diff-cover on the branch diff reaches 90% per `rules/toolchain.md`
   - [ ] Deployment hand-off to `skills/deploy/SKILL.md` after commit+push; deploying is the user's decision

### Release units
**Unit**: helper-leak-safety | **Phases**: 1, 2 | **Reason**: the teardown wrapper and re-open close change existing helper behavior (double-open callers, vec-load teardown site); Phases 1-2 are one semantic change validated by the same test run; splitting them leaves the leak class half-fixed.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/db/helper.py | Leak unit tests (closed flag) + lock integration test | `uv run pytest tests/db/test_sqlite_helper.py -v` | AC-1, AC-3 asserted |
| scripts/db/helper.py (regression) | Existing helper suite incl. frozen reuse/vec behaviors `:262-395` | `uv run pytest tests/db -v` | No regressions; `:358-369` same exception, conn None |
| scripts/ (regression) | Full DB + service suites (helper is the shared gateway) | `uv run pytest tests/ -n auto` | No regressions |
| scripts/db/helper.py (radon) | Complexity guard | `uv run radon cc scripts/db/helper.py -s` | Baseline top `open` B(9); keep ≤B via `_prepare_connection` extraction |
| scripts/db/helper.py (vulture) | Dead code guard | `uv run vulture scripts/db/helper.py --min-confidence 80` | No new findings after `_load_vec_extension` close removal |
| branch diff | Coverage gate | `uv run coverage run -m pytest tests/` → `coverage xml` → `uv run diff-cover coverage.xml --compare-branch=master` (`--fail-under=90`) | Baseline recorded this cycle (95%); branch diff ≥ 90% |

## Risks
- **Risk**: closing a previous connection on re-open breaks a caller that intentionally left a connection open while re-opening → **Mitigation**: Step 3 grep found no such caller in-repo; UNK-01 records the residual external risk; close-with-log keeps observable behavior (log line) for diagnosis.
- **Risk**: `except BaseException` in `open` also catches `KeyboardInterrupt`/`SystemExit` paths → **Mitigation**: it re-raises unchanged after closing the connection; teardown on interrupt is desirable and the exception contract is preserved.
- **Risk**: overlapping edits with Plan 004 in `open`/`_connect` → **Mitigation**: strict order 004 → 005 recorded in both Plans; 005 targets the post-004 shapes.
- **Risk**: helper is the gateway for every DB component, so a teardown defect could close a connection callers still hold → **Mitigation**: `self.conn` is only exposed through the helper after successful open; AC-2 regression test keeps the successful-open path byte-identical.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Single-owner teardown and re-open close (scripts/db/helper.py) | In Progress | — | — | procedure doc 20261115-232225_01 generated |
| 2 | Explicit-`load_vec` guard and tests (scripts/db/helper.py, tests/db/test_sqlite_helper.py) | In Progress | — | — | procedure docs 20261115-232225_01/_02 generated |
| 3 | Validation & deployment hand-off | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261115-232225_01_scripts_db_helper.py.md | 1 | Procedure | Created | — | — |
| implementations/20261115-232225_02_tests_db_test_sqlite_helper.py.md | 2 | Procedure | Created | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261114-092853_dbreview005_helper-open-leak.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-043850
- **Related target files**: scripts/db/helper.py, tests/db/test_sqlite_helper.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem bullets 1; Required Changes bullet 1 | scripts/db/helper.py | Phase 1 | AC-1 | Leak unit + lock tests | Explicit in code (Step 2 re-verified this cycle: helper.py:315-329, teardown only on read_only branch `:321-325`) |
| REQ-002 | Problem bullet 2; Required Changes bullet 1 | scripts/db/helper.py | Phase 1 | AC-1, AC-2 | AttributeError-vec test; `:358-369` regression | Explicit in code (Step 2 re-verified this cycle: helper.py:257-260) |
| REQ-003 | Problem bullet 3; Required Changes bullet 2; Constraint (reuse semantics) | scripts/db/helper.py | Phase 1 | AC-3 | Re-open ProgrammingError test | Explicit in code (Step 2 re-verified this cycle: helper.py:329) |
| REQ-004 | Problem bullet 4; Required Changes bullet 3; Constraint (default behavior) — production path retired by config.py:66-69, boundary contract kept | scripts/db/helper.py | Phase 2 | AC-4 | ValueError test; `:338-356` stays green | Explicit in code (Step 2 re-verified this cycle: helper.py:243-244) + Step 2 retirement note |
| REQ-005 | Required Changes bullet 4; Testing Expectations | tests/db/test_sqlite_helper.py | Phase 2 | AC-1..AC-4 | New tests | Verified by test (gap confirmed in Step 3) |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261115-232225 -->