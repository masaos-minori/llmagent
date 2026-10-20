## Goal

Create a single authoritative definition of the session-title length maximum and reference it from `commands/session_title.py` instead of a local copy, so the fallback generator and `/session list` view resolve one constant (REQ-002).

## Scope

Modify `scripts/agent/commands/session_title.py` only:
- Replace the local `SESSION_TITLE_MAX_CHARS = 32` (module top) with a re-export `from agent.session import SESSION_TITLE_MAX_CHARS`.
- Keep `SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3` unchanged.

Reference Files are read-only and not modification targets.

## Assumptions

- `agent.session` (`AgentSession`) is the storage owner and canonical home of the constant.
- Importing `agent.session` from `commands/session_title.py` is cycle-free: `commands/session_title.py` already imports `agent.context` (line 9), and `context.py` imports `agent.session` (line 38); none of `agent.session`'s dependencies reach `agent.context` or any `commands/` module, so adding the direct edge `session_title.py → agent.session` is acyclic.

## Design decisions

- **Re-export, don't redefine.** Replace the local assignment with `from agent.session import SESSION_TITLE_MAX_CHARS`. This preserves the `SESSION_TITLE_MAX_CHARS` / `SESSION_TITLE_TRUNCATE_AT` names that `cmd_session.py::_session_list` imports (`from agent.commands.session_title import SESSION_TITLE_MAX_CHARS, SESSION_TITLE_TRUNCATE_AT`), so those callers need no change.
- **Display offset stays local.** `SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3` remains defined here as a display-layer concern; it still resolves to `29`.

## Alternatives considered

- Moving the constant to `shared/`: rejected — `shared/` has no domain-length constants and the storage owner (`AgentSession`) should own it (resolves UNK-02).
- Defining it in `commands/session_title.py` and importing INTO `session.py`: rejected — would form a cycle (`session.py` → `commands/session_title.py` → `agent.context` → `session.py`).

## Implementation

### Target file

`scripts/agent/commands/session_title.py` (modify)

### Procedure

1. At module top, replace the local definition line `SESSION_TITLE_MAX_CHARS = 32` with a re-export: `from agent.session import SESSION_TITLE_MAX_CHARS`.
2. Leave `SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3` as-is (it still resolves to `29`).

### Method

- Current (lines 14-15): `SESSION_TITLE_MAX_CHARS = 32` then `SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3`.
- After the change, `SESSION_TITLE_MAX_CHARS` is imported from `agent.session` (the canonical owner defined in `20261019-232337_01_scripts_agent_session.py.md`); `SESSION_TITLE_TRUNCATE_AT` keeps computing `MAX - 3` from it.
- The name `SESSION_TITLE_MAX_CHARS` continues to resolve via `from agent.commands.session_title import SESSION_TITLE_MAX_CHARS` for `_session_list` (cmd_session.py:80-81).

### Details

- Place the re-export where the old assignment was (module top, after imports) so the name is bound before `SESSION_TITLE_TRUNCATE_AT` uses it.
- No other references in this file change (`_generate_fallback` still uses both names at lines 36-37).

## Compatibility considerations

N/A: re-export only; the exported names and their values are unchanged, so `_session_list` and the fallback generator behave identically.

## Security considerations

N/A: no trust-policy change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `session_title.py` re-export | Fallback test still asserts `<= 32`; `_session_list` imports resolve | `uv run pytest tests/agent/commands/test_agent_cmd_session.py` | Rename flow works; fallback test asserts `<= 32` |
| Touched file (lint/type) | Static checks | `uv run ruff check scripts/agent/commands/session_title.py` and `uv run mypy scripts/agent/commands/session_title.py` | Clean (zero findings) |

## Completion criteria

- `session_title.py` re-exports `SESSION_TITLE_MAX_CHARS` from `agent.session` and defines `SESSION_TITLE_TRUNCATE_AT = SESSION_TITLE_MAX_CHARS - 3`.
- No local `SESSION_TITLE_MAX_CHARS = 32` definition remains; `ruff`/`mypy` clean; fallback + rename tests pass.

## Out of Scope

- Defining the constant in `session.py` (covered by `20261019-232337_01_scripts_agent_session.py.md`).
- The `/session rename` echo (`cmd_session.py`) and the boundary test (`test_agent_session.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-export `SESSION_TITLE_MAX_CHARS` from `agent.session`; keep `SESSION_TITLE_TRUNCATE_AT = MAX - 3` (REQ-002) | Completed | 20261020-115740 | 20261020-115740 | See UNK-02 (import cycle) Re-exported from agent.session (import cycle verified acyclic); SESSION_TITLE_TRUNCATE_AT = MAX-3 unchanged. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-115740 | 20261020-115740 | Fallback + rename tests (test_agent_cmd_session.py) 55 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261020-115740 | 20261020-115740 | ruff/mypy(438)/lint-imports(6/6)/bandit clean; combined Plan B suite 9613 passed. |
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
- **Requirement ID**: REQ-002 (re-export canonical maximum from `commands/session_title.py` so fallback/display reference one definition; keep `SESSION_TITLE_TRUNCATE_AT = MAX - 3`)
- **Source issue**: `issues/20261019-202130_sess002_set_title-truncation-cap-50-inconsistent-with-session_title_max_chars-32-used-by-fallback-and-list-display.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-215053_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-232337
- **Related target files**: `scripts/agent/commands/session_title.py`