## Goal

Update the one existing test that encodes the old `50` storage cap and add a boundary round-trip check, so `tests/agent/test_agent_session.py` asserts the new canonical maximum (32) instead of `50` (REQ-004).

## Scope

Modify `tests/agent/test_agent_session.py` only:
- Repurpose `TestSetTitle::test_truncates_to_50_chars` to assert the stored title length equals the agreed maximum (32) via `list_sessions`.
- Add a boundary round-trip check (store a long title, read it back via `list_sessions`, assert the stored length equals the maximum).
- Keep `test_no_op_when_session_id_none` and `test_updates_title` unchanged (preserve the `session_id is None` no-op guard and the success path).

Reference Files are read-only and not modification targets.

## Assumptions

- The `session` fixture yields a real `AgentSession` backed by `_FakeSQLiteHelper` (in-memory SQLite), so `set_title` writes and `list_sessions` reads exercise the real storage path.
- `test_truncates_to_50_chars` is the single existing test that encodes the old `50` value (the Plan's Risk table confirms this); all other `TestSetTitle` cases are value-agnostic.

## Design decisions

- **Repurpose, don't duplicate.** Rename `test_truncates_to_50_chars` to reflect the new bound and change the assertion from `== 50` to `== 32`, then extend it with a round-trip assertion (store a title longer than the max, read it back, assert the stored length equals the max). This keeps one boundary test rather than adding a parallel one.
- **Preserve out-of-scope behavior.** The `session_id is None` no-op guard (`test_no_op_when_session_id_none`) and `sqlite3.Error` propagation are explicitly left untouched and remain covered by existing cases.

## Alternatives considered

- Adding a brand-new test method and leaving `test_truncates_to_50_chars` as-is: rejected — the existing test asserts `== 50`, which would fail after the cap change; repurposing it is the minimal, correct update.

## Implementation

### Target file

`tests/agent/test_agent_session.py` (modify)

### Procedure

1. In `TestSetTitle`, rename `test_truncates_to_50_chars` to `test_stores_at_max_chars` and change its body:
   - Keep `session.start()` and `session.set_title("A" * 100)`.
   - Change the assertion from `assert any(len(r["title"] or "") == 50 for r in rows)` to `assert any(len(r["title"] or "") == 32 for r in rows)`.
   - Update the inline comment from "title is stored at max 50 chars" to "title is stored at the canonical max (32) chars".
2. Extend the same test with a round-trip assertion: after reading `rows`, assert the stored title length equals the maximum and does not exceed it — e.g. `stored = next(r["title"] for r in rows if r["title"])` then `assert len(stored) == 32` (a boundary check that a title longer than the max reads back at exactly the max).

### Method

- Current `test_truncates_to_50_chars` (lines 357-362): `session.start()` → `set_title("A" * 100)` → `list_sessions()` → asserts `any(len(r["title"] or "") == 50 for r in rows)`.
- After the change it asserts the stored length is exactly `32` (the canonical max from REQ-001) and adds the round-trip read-back.
- `test_no_op_when_session_id_none` (lines 364-365) and `test_updates_title` (lines 351-355) are unchanged, preserving the no-op guard and success-path coverage.

### Details

- The `session` fixture (real `AgentSession` + `_FakeSQLiteHelper`) makes `list_sessions` return the stored row, so the round-trip exercises the actual storage slice.
- Do not introduce a `== 50` reference anywhere in this file.

## Compatibility considerations

N/A: test-only update; the boundary test now locks the new 32-char behavior while existing cases keep passing.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `test_agent_session.py` (repurposed) | Boundary test asserts stored length == 32 via round-trip; no `== 50` remains | `uv run pytest tests/agent/test_agent_session.py` | New assertion passes; `test_updates_title` / `test_no_op_when_session_id_none` pass |
| Touched file (lint/type) | Static checks | `uv run ruff check tests/agent/test_agent_session.py` and `uv run mypy tests/agent/test_agent_session.py` | Clean (zero findings) |

## Completion criteria

- `test_truncates_to_50_chars` is repurposed to assert stored length == 32 with a `list_sessions` round-trip; no `== 50` reference remains.
- `test_no_op_when_session_id_none` still passes (no-op guard preserved); `ruff`/`mypy` clean.

## Out of Scope

- Changing `set_title`'s cap (covered by `20261019-232337_01_scripts_agent_session.py.md`).
- The fallback/rename regression guard in `tests/agent/commands/test_agent_cmd_session.py` (regression-checked there for REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repurpose `test_truncates_to_50_chars` to assert stored length == 32 via round-trip (REQ-004) | Completed | 20261020-115740 | 20261020-115740 | Preserve no-op guard Repurposed test_truncates_to_50_chars -> test_stores_at_max_chars: asserts stored length == 32 via list_sessions round-trip. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-115740 | 20261020-115740 | Boundary test passes; test_updates_title / test_no_op_when_session_id_none preserved. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-115740 | 20261020-115740 | ruff/mypy(scripts/438) clean; combined Plan B suite 9613 passed, 14 skipped. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020-115740 | 20261020-115740 | N/A N/A. |

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
- **Requirement ID**: REQ-004 (update `test_truncates_to_50_chars` to the agreed maximum and add a boundary round-trip check via `list_sessions`)
- **Source issue**: `issues/20261019-202130_sess002_set_title-truncation-cap-50-inconsistent-with-session_title_max_chars-32-used-by-fallback-and-list-display.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-215053_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-232337
- **Related target files**: `tests/agent/test_agent_session.py`