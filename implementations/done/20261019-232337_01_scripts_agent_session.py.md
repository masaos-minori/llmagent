## Goal

Establish a single authoritative session-title length maximum so that storage (`AgentSession.set_title`) agrees with the fallback/display convention (REQ-001). Replace the lone magic `50` in `set_title` with a canonical constant equal to 32.

## Scope

Modify `scripts/agent/session.py` only:
- Add `SESSION_TITLE_MAX_CHARS = 32` near `set_title`.
- Change the storage slice from `title[:50]` to `title[:SESSION_TITLE_MAX_CHARS]`.
- Update the `set_title` docstring from "truncated to 50 chars" to "truncated to 32 chars".

Reference Files (`context.py`, `tests/agent/commands/test_agent_cmd_session.py`) are read-only and not modification targets.

## Assumptions

- The value 32 is intended: `SESSION_TITLE_MAX_CHARS=32` is the dominant convention (fallback generator, `/session list` display, and the existing fallback test all use it); the `50` in `set_title` is the sole outlier.
- LLM titles are ~8 words (well under 32), so storage truncation is rare in practice.
- Defining the constant at module level in `session.py` is cycle-free (`context.py` imports `agent.session`; `session.py` need not import anything from `commands/`).

## Design decisions

- **Owner = `AgentSession`.** `set_title` is the storage owner of the `title` field, so it owns the storage cap. A module-level `SESSION_TITLE_MAX_CHARS = 32` placed near `set_title` is referenced by the slice `title[:SESSION_TITLE_MAX_CHARS]`.
- **Value = 32 (resolves UNK-01).** Unify storage with the established `SESSION_TITLE_MAX_CHARS` convention; the `50` is removed as the sole outlier.

## Alternatives considered

- Keeping `set_title` at 50 and lowering fallback/display to 50: rejected — 32 is the dominant convention and 50 is the lone outlier; reversing would widen the inconsistency.

## Implementation

### Target file

`scripts/agent/session.py` (modify)

### Procedure

1. Add a module-level constant `SESSION_TITLE_MAX_CHARS = 32` immediately before the `AgentSession.set_title` method (line 160).
2. Change the storage slice in `set_title` from `(title[:50], self.session_id)` (line 168) to `(title[:SESSION_TITLE_MAX_CHARS], self.session_id)`.
3. Update the `set_title` docstring (line 161) from "(truncated to 50 chars)" to "(truncated to 32 chars)".

### Method

- Current `set_title` (lines 160-170): guards `session_id is None` (line 163), opens a write `SQLiteHelper("session")`, and updates `sessions SET title = ?` with `title[:50]`. Only the bound literal and the docstring change.
- The `sqlite3.Error` propagation and the `session_id is None` no-op guard are preserved exactly (out of scope).

### Details

- No new imports; the constant is module-level so the method references it directly.
- Storage keeps its no-ellipsis `title[:N]` semantics; display (`commands/session_title.py`) still uses `SESSION_TITLE_TRUNCATE_AT = N - 3` + `"..."`, unchanged.

## Compatibility considerations

Behavior-preserving except for the cap value: titles longer than 32 chars are now truncated to 32 on write instead of 50. Existing `TestSetTitle` cases (`test_updates_title`, `test_no_op_when_session_id_none`) keep passing unchanged.

## Security considerations

N/A: no auth/trust-policy change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `session.py` cap -> canonical | `TestSetTitle` stores a long title, reads it back at the maximum; existing cases unchanged | `uv run pytest tests/agent/test_agent_session.py` | Stored length == 32; existing cases pass |
| Touched file (lint/type) | Static checks | `uv run ruff check scripts/agent/session.py` and `uv run mypy scripts/agent/session.py` | Clean (zero findings) |

## Completion criteria

- `SESSION_TITLE_MAX_CHARS = 32` is defined in `session.py` and `set_title` slices `title[:SESSION_TITLE_MAX_CHARS]`.
- The `set_title` docstring states "truncated to 32 chars".
- No magic `50` title-length literal remains in `session.py`; `test_updates_title` / `test_no_op_when_session_id_none` still pass; `ruff`/`mypy` clean.

## Out of Scope

- Re-exporting the constant from `commands/session_title.py` (covered by `20261019-232337_02_scripts_agent_commands_session_title.py.md`).
- The `/session rename` echo (`cmd_session.py`) and the boundary test (`test_agent_session.py`).
- `set_title`'s signature, `sqlite3.Error` propagation, or `session_id is None` no-op guard.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define `SESSION_TITLE_MAX_CHARS = 32`; change `set_title` slice to `title[:SESSION_TITLE_MAX_CHARS]`; update docstring (REQ-001) | Completed | 20261020-115740 | 20261020-115740 | See UNK-01 Module-level SESSION_TITLE_MAX_CHARS=32; set_title slice title[:SESSION_TITLE_MAX_CHARS]; docstring -> 32 chars. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-115740 | 20261020-115740 | Own TestSetTitle cases pass; boundary test repurposed by sibling proc 06 (REQ-004). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-115740 | 20261020-115740 | ruff/mypy(438)/lint-imports(6/6)/bandit clean; combined Plan B suite 9613 passed, 14 skipped. |
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
- **Requirement ID**: REQ-001 (single authoritative title-length maximum; `set_title` truncates stored title to it instead of magic `50`)
- **Source issue**: `issues/20261019-202130_sess002_set_title-truncation-cap-50-inconsistent-with-session_title_max_chars-32-used-by-fallback-and-list-display.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-215053_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-232337
- **Related target files**: `scripts/agent/session.py`