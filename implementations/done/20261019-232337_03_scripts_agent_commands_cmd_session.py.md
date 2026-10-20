## Goal

Make the `/session rename` success echo report a title length equal to what is actually stored, by replacing the second magic `50` literal with the canonical maximum (REQ-003).

## Scope

Modify `scripts/agent/commands/cmd_session.py` only:
- In the `/session rename` branch, import the canonical maximum (`SESSION_TITLE_MAX_CHARS`).
- Change the success echo from `{title[:50]!r}` to `{title[:SESSION_TITLE_MAX_CHARS]!r}`.

Reference Files are read-only and not modification targets.

## Assumptions

- `SESSION_TITLE_MAX_CHARS` is canonically defined in `agent.session` (REQ-001) and re-exported from `agent.commands.session_title` (REQ-002); importing it from `commands/session_title.py` resolves to that single value (32).
- The rename branch's `set_title(title)` (line 201) already truncates storage to the canonical max, so echoing `{title[:SESSION_TITLE_MAX_CHARS]!r}` reports exactly the stored length.

## Design decisions

- **Lazy import matching `_session_list`.** `_session_list` imports the names lazily inside the method (lines 79-82: `from agent.commands.session_title import (SESSION_TITLE_MAX_CHARS, SESSION_TITLE_TRUNCATE_AT)`). The rename branch follows the same pattern to avoid any top-level import churn and to keep the acyclic contract.
- **Echo uses the canonical bound.** `{title[:SESSION_TITLE_MAX_CHARS]!r}` reports the stored length, removing the diverging `50` literal (resolves AC-3).

## Alternatives considered

- Importing `SESSION_TITLE_MAX_CHARS` at module top: rejected — `_session_list` uses a lazy import and the rename branch should match that established style; a top-level import is unnecessary and out step's minimal surface.

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py` (modify)

### Procedure

1. In the `/session rename` branch (`if sub == "rename":`, lines 196-203), add a lazy import of the canonical maximum directly before the `set_title` call (line 201): `from agent.commands.session_title import SESSION_TITLE_MAX_CHARS`.
2. Change the success echo on line 202 from `f"Session renamed: {title[:50]!r}"` to `f"Session renamed: {title[:SESSION_TITLE_MAX_CHARS]!r}"`.

### Method

- Current rename branch (lines 196-203): validates input, calls `self._ctx.session.set_title(title)` (line 201), echoes `{title[:50]!r}` (line 202).
- After the change, `SESSION_TITLE_MAX_CHARS` (32, re-exported from `commands/session_title.py`) bounds the echoed slice, so the reported length matches the stored length.
- The `set_title` call is unchanged; its storage truncation now uses the canonical max (REQ-001).

### Details

- Place the lazy import at the top of the `rename` branch body (after the empty-title guard, before line 201) so the name is bound before the echo.
- No other callers in this file change; `_session_list` keeps its own import.

## Compatibility considerations

N/A: display-echo constant swap only; no service behavior change. The rename flow and its success message format are unchanged except the reported slice bound.

## Security considerations

N/A: no trust-policy change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `cmd_session.py` rename echo | Rename flow still works; echo length matches stored length | `uv run pytest tests/agent/commands/test_agent_cmd_session.py` | Rename test passes; fallback test still asserts `<= 32` |
| Touched file (lint/type) | Static checks | `uv run ruff check scripts/agent/commands/cmd_session.py` and `uv run mypy scripts/agent/commands/cmd_session.py` | Clean (zero findings) |

## Completion criteria

- The `/session rename` branch imports `SESSION_TITLE_MAX_CHARS` and echoes `{title[:SESSION_TITLE_MAX_CHARS]!r}`.
- No magic `50` title-length literal remains in the rename echo; rename flow works; `ruff`/`mypy` clean.

## Out of Scope

- Defining the constant in `session.py` (`20261019-232337_01_scripts_agent_session.py.md`) and re-exporting in `session_title.py` (`20261019-232337_02_scripts_agent_commands_session_title.py.md`).
- The boundary test (`test_agent_session.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import canonical max in `/session rename` branch; change echo to `{title[:SESSION_TITLE_MAX_CHARS]!r}` (REQ-003) | Completed | 20261020-115740 | 20261020-115740 | Lazy import like `_session_list` Lazy-imported SESSION_TITLE_MAX_CHARS in /session rename branch; echo {title[:SESSION_TITLE_MAX_CHARS]!r}. |
| 2 | Add or update tests per Validation plan | Completed | 20261020-115740 | 20261020-115740 | Rename flow tests (test_agent_cmd_session.py) 55 passed. |
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
- **Requirement ID**: REQ-003 (replace second magic `50` in `/session rename` success echo with canonical maximum so reported length matches stored length)
- **Source issue**: `issues/20261019-202130_sess002_set_title-truncation-cap-50-inconsistent-with-session_title_max_chars-32-used-by-fallback-and-list-display.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-215053_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-232337
- **Related target files**: `scripts/agent/commands/cmd_session.py`