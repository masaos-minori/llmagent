# Plan: Report failure when /session rename cannot store the title

**Generated from**: `issues/20261026-225105_sess007_validate-session-rename-result.md`
**Date**: 2026-10-27
**Task classification**: Path A — small bounded fix (return contract of one method, one
command branch, tests)

## Goal

Make `set_title` report whether the title was actually persisted, and make the
`/session rename` branch print a validation error instead of a false success when there
is no active session row.

## Priority

Medium (inherited from the issue).

## Scope

**In scope:**

- REQ-1: `Session.set_title` returns `bool` — `True` when the UPDATE ran, `False` when
  `session_id is None` (the current silent no-op). DB errors keep raising `sqlite3.Error`
  as today.
- REQ-2: the `/session rename` branch maps `False` to `write_validation_error` output
  (existing pattern, L205) and suppresses the success line.
- REQ-3: regression tests for both outcomes; existing rename test stays green.

**Out of scope:**

- Auto-creating a session row on rename (issue Out of Scope).
- Title parsing, truncation rules, title generation/fallback logic (issue Constraints /
  Out of Scope).
- Other `set_title` call sites' behavior (they ignore the return value; no change needed,
  see Reference Files).

## Background

From a `python-code-review` pass (finding F-009). Verification against current source:

- Current behavior — `scripts/agent/session.py` `set_title` (L170-180): sets
  `_title_pending = False`; when `self.session_id is None` it `return`s silently (L173-174)
  — no DB row exists to update; otherwise UPDATE + commit, docstring notes
  `Raises sqlite3.Error on failure`.
- Current behavior — `scripts/agent/commands/cmd_session.py` rename branch (L202-213):
  after the empty-title validation error (L204-206), it calls
  `self._ctx.session.set_title(title)` (L209) and unconditionally writes
  `Session renamed: ...` (L210-212). The issue's claim is confirmed.
- Call-site audit (issue AI Instruction "check callers before changing the signature"):
  `scripts/agent/commands/session_title.py` L41 (+ its `sqlite3.Error` except at L44),
  `scripts/agent/services/conversation_service.py` L33, `scripts/agent/services/session_title.py`
  L59. All call `set_title` as a statement and discard the return value; changing `None`
  → `bool` keeps them source- and type-compatible.
- Related archived work (`issues/done/20261019-...sess002...`): truncation cap only; the
  no-session no-op is untouched — confirmed.
- Churn (90d commits / lines): `session.py` 8/115; `cmd_session.py` 10/114. Live files.
- Existing test: `tests/agent/commands/test_agent_cmd_session.py`
  `test_rename_updates_title` (L249-253) mocks `set_title` and asserts the "renamed" line.

## Problem

With `session_id is None` the user sees "Session renamed: 'x'" while nothing is
persisted; the next list/load shows the old title (issue Problem). False success
messages erode trust in all other success lines.

## Reason for Change

Explicit in issue: small fix removing a false-success path in a user-facing command.

## Implementation Intent

Storage layer reports the outcome (`set_title` returns bool — the issue's first of two
offered options; raising a new error would add an exception path to three call sites for
no benefit), command layer maps it to success vs validation-error output. No parsing or
truncation change.

## Requirements

| ID | Requirement | Issue Evidence | Reason It Solves It | Scope Decision | Basis |
|----|-------------|----------------|---------------------|----------------|-------|
| REQ-1 | `set_title` signals "no active session" explicitly via `False` return | Required Changes bullet 1 | The command can distinguish persisted from no-op | In | Explicit in issue |
| REQ-2 | rename branch prints validation error (usage hint), no success line, when `set_title` returns `False` | Required Changes bullet 2 | Removes the false-success path | In | Explicit in issue |
| REQ-3 | Regression tests: no-session rename → failure output, no success line; normal rename unchanged | Acceptance Criteria, Testing Expectations | Locks both branches | In | Explicit in issue |
| REQ-4 | Success message format for real renames unchanged; truncation rules unchanged | Constraints | Tests and users rely on the existing line | In (as constraint) | Explicit in issue Constraints |
| OUT-1 | Auto-creating a session row on rename | Out of Scope | — | Out | Explicit in issue |
| OUT-2 | Title generation/fallback logic changes | Out of Scope | — | Out | Explicit in issue |

## Implementation Target Files

**Freeze status**: Frozen (`issue-to-plan` Step 8 Implementation Target Files
Validation passed — structure check exit 0, all three target paths verified against
source; `session.py` overlap with turn001/undo002 Plans adjudicated Compatible, members
disjoint.)

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
implementation skill — including file paths inside inline code snippets — MUST reference
exactly these paths and no others: a skill MUST NOT create, split, merge, rename, or
otherwise introduce any file that is not a row in this table. When a discovered need
does not map onto any row, it is an unresolved question that reopens the Plan — not
something the skill may resolve by inventing a file.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/session.py | `set_title` returns `bool`: `False` on the `session_id is None` early exit, `True` after UPDATE/commit | Silent no-op at L173-174 makes the command's success line false | REQ-1 | Read: `set_title` L170-180 | tests/agent/commands/test_agent_cmd_session.py | Verified |
| scripts/agent/commands/cmd_session.py | rename branch captures the return; `False` → `write_validation_error("/session rename <title>")`, `True` → unchanged success line | L209-212 writes success unconditionally after the call | REQ-2, REQ-4 | Read: rename branch L202-213; existing validation-error pattern L204-206 | tests/agent/commands/test_agent_cmd_session.py | Verified |
| tests/agent/commands/test_agent_cmd_session.py | Add no-session rename case (validation-error output, no success line); existing success test stays green | No no-session test exists; `test_rename_updates_title` (L249-253) mocks success only | REQ-3, REQ-4 | Read: L249-253, L288, L325 | this file | Verified |

## Reference Files

These files are read-only for context and MUST NOT be modified; any change to them
requires reopening the Plan with an explicit decision recorded under Assumptions.

| Path | How to use it | Requirements |
|------|---------------|------------|
| `scripts/agent/commands/session_title.py` | call sites L41-44 (`set_title` + `sqlite3.Error` except) — verify they remain source/type-compatible with the `bool` return | REQ-1 |
| `scripts/agent/services/conversation_service.py` | call site L33 — same verification | REQ-1 |
| `scripts/agent/services/session_title.py` | call site L59 — same verification | REQ-1 |
| `scripts/agent/commands/cmd_session.py` | L204-206 existing `write_validation_error` usage pattern to reuse | REQ-2 |

## Acceptance Criteria

- REQ-1: `set_title` with `session_id is None` returns `False` and performs no DB write;
  with a session id it returns `True`; DB failures still raise `sqlite3.Error` (unchanged).
- REQ-2: `/session rename <title>` with `session_id is None` prints a validation error
  containing the usage hint and does NOT print `Session renamed:`.
- REQ-3: new tests green; existing `test_rename_updates_title` green.
- REQ-4: success line for real renames byte-identical to today:
  `Session renamed: {title[:32]!r}`.
- Static checks: `mypy`/`ruff` pass (issue Acceptance Criteria).

## Tests

| Test target | Tool | What it proves | Requirements |
|-------------|------|----------------|------------|
| `tests/agent/commands/test_agent_cmd_session.py` (new cases) | pytest | no-session rename → validation error, no success line; normal rename output unchanged | REQ-3, REQ-4 |
| `tests/agent/commands/test_agent_cmd_session.py -k rename` (existing) | pytest | existing success behavior | REQ-4 |
| `scripts/agent/session.py` unit-level check (new test in the same command test module or its existing session-level suite) | pytest | `set_title` return values on both paths | REQ-1, REQ-3 |
| full suite (`uv run pytest`) + `uv run mypy scripts/` | pytest / mypy | call-site compatibility, no regression | REQ-1 |

## Documentation Impact

- None required: the issue states docs are not required when the error message follows the
  existing validation-error pattern, which REQ-2 does (reuse of `write_validation_error`
  with the same usage hint string as L205). No docs target row.

## Assumptions

- bool return over raising an error: chosen because three existing call sites discard the
  return value and only the rename branch needs the outcome; an exception path would
  force error handling where it is not wanted (e.g. `(New Session)` title at
  `conversation_service.py` L33 is deliberately best-effort).
- `session.py` is also targeted by `plans/20261027-070403_turn001...` (turn-boundary
  persistence methods) and `plans/20261027-074657_undo002...` (`undo_last_turn`). This
  Plan changes only `set_title` (L170-180) — disjoint members from both; adjudicated
  Compatible per the target-file rules.
- A session with `session_id is None` at rename time is reachable (no active saved
  session), per the issue Problem statement; no attempt to make it unreachable.

## Constraints

- Keep success message format for real renames (issue Constraints).
- Do not change title truncation rules (`SESSION_TITLE_MAX_CHARS`, `title[:...]`) — issue
  Constraints.
- Do not auto-create sessions as a side effect of rename (issue AI Instruction).
- Never emit partial output.

## Unknowns

- None.

## Affected areas

| Area | Change | Blast radius | Requirements |
|------|--------|--------------|------------|
| session title persistence contract | `set_title` return type `None` → `bool` | 4 call sites audited; 1 consumes the value | REQ-1 |
| `/session rename` output | failure line for no-session case | command output only | REQ-2 |
| REPL command tests | 2-3 new test cases | test module only | REQ-3 |

## Design

Return-bool contract (issue offers bool-or-raise; bool chosen, see Assumptions). The
rename branch already owns a validation-error pattern (`write_validation_error` with the
usage hint, L204-206); REQ-2 extends that same pattern to the failed-store case, keeping
user-facing output consistent. No new exception types, no changes to
`SQLiteHelper`/`session_db`, no change to `_title_pending` bookkeeping (the flag is
cleared even on the no-op path today; behavior preserved).

## Implementation steps

1. `scripts/agent/session.py` (REQ-1): `def set_title(self, title: str) -> bool:` —
   `return False` at the `session_id is None` exit; `return True` after `db.commit()`.
   Update the docstring to state the return contract.
2. `scripts/agent/commands/cmd_session.py` (REQ-2, REQ-4): rename branch captures the
   return: falsy → `self._out.write_validation_error("/session rename <title>")` and
   return; truthy → unchanged `write_success(f"Session renamed: {title[:SESSION_TITLE_MAX_CHARS]!r}")`.
3. `tests/agent/commands/test_agent_cmd_session.py` (REQ-3, REQ-4): add (a) no-session
   rename test — session mocked with `session_id=None` behavior returning `False` —
   asserting a validation-error line and no "renamed" substring; (b) keep the existing
   success test asserting the exact renamed line.
4. Static gate: `uv run mypy scripts/` + `uv run ruff check .` (REQ validation per issue).

Step 1 → Step 2 → Step 3 (contract → consumer → tests).

## Validation plan

| Check | Command | Expected | Requirements |
|-------|---------|----------|------------|
| targeted tests | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rename` | all green | REQ-3, REQ-4 |
| call-site regression | `uv run pytest tests/` (title-related suites included) | green | REQ-1 |
| type/lint | `uv run mypy scripts/ && uv run ruff check .` | clean | REQ-1 |
| full suite | `uv run pytest` | green | REQ-1, REQ-2 |

## Risks

| Risk | Likelihood | Impact | Mitigation | Affected requirements |
|------|------------|--------|------------|-----------------------|
| A call site relied on `None` return typing (e.g. `assert set_title(...) is None` in tests) | Low | Low | grep audit found no such assertion; full suite run closes it | REQ-1 |
| Validation-error message confuses users expecting a different failure hint | Low | Low | Reuse the existing usage-hint pattern exactly (L205) | REQ-2 |

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `scripts/agent/session.py` `set_title` bool return contract (REQ-1) | In Progress | — | — | P1: return contract |
| 2 | `scripts/agent/commands/cmd_session.py` rename branch output mapping (REQ-2, REQ-4) | In Progress | — | — | P2: command mapping; after step 1 |
| 3 | `tests/agent/commands/test_agent_cmd_session.py` regression cases + static gate (REQ-3, REQ-4) | In Progress | — | — | P3: tests + static gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261028-001446_01_scripts_agent_session.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261028-001446_02_scripts_agent_commands_cmd_session.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261028-001446_03_tests_agent_commands_test_agent_cmd_session.py.md | 3 | Procedure | Pending | — | — |

## Traceability

- **Workflow phase**: `issue-to-plan`
- **Source issue**: `issues/20261026-225105_sess007_validate-session-rename-result.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the plan
- **Source implementation procedure**: N/A: not yet generated
- **Generated at**: 20261027-085735
- **Related target files**: `scripts/agent/session.py`, `scripts/agent/commands/cmd_session.py`, `tests/agent/commands/test_agent_cmd_session.py`

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261028-001446 -->