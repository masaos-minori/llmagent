# Implementation Procedure: scripts/agent/tool_policy.py (shellprefix001)

## Goal
- Replace the bare prefix-name auto-approval of `shell_run` with a deny-by-default,
  per-executable safe-shape rule in `scripts/agent/tool_policy.py` (REQ-006 auto-approve
  only read-only-by-construction shapes, REQ-007 explicit allowed subcommands/flags per
  executable, REQ-008 one normalized executable name for both the prefix gate and the
  flag lookup).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Strict deny-by-default (Plan A7, owner-confirmed): an executable with no code-defined
  safe-shape rule returns `HIGH` even when a config prefix entry matches it; the config
  list is an operator gate, not sufficient for auto-approval.
- `tests/agent/test_tool_policy.py` is NOT a companion of this document (it is also cited
  by the `config/agent.toml` row, so it keeps its own procedure document:
  `implementations/20261103-072856_03_tests_agent_test_tool_policy.py.md`).
- Execute this document after the seq 03 red-test baseline (Plan Phase 1): the new
  regression tests must fail against the current code first.
- `shellrisk001` (`plans/20261101-142514_...`) is sequenced after this Plan; do not change
  `_check_positional_args` token parsing here (Plan A2).

## Design decisions
- Safe-shape rules live in code as a data-driven table (Plan A4, no new config key):
  extend `_UNSAFE_FLAGS` (L44-48) into a per-executable rule table `SAFE_SHELL_SHAPES`
  (new) so `_special_case_risk` stays a thin dispatcher (radon risk: it is already C(13)).
- Interpreters (`python`, `pytest`, `uv`) have no entry in the rule table — absence of a
  rule is the denial mechanism (REQ-006); no interpreter-specific code branch is needed.

## Alternatives considered
- Keeping `_UNSAFE_FLAGS` as a flag-only denylist and adding a separate subcommand check:
  rejected — REQ-007 explicitly asks to generalize the denylist into the per-executable
  rule, and two tables would drift.
- Config-side rule keys (new TOML structure): rejected per Plan A4 (no new config
  schema/validation surface).

## Implementation
### Target file
- `scripts/agent/tool_policy.py`

### Procedure
1. In `_special_case_risk` (L221-260), resolve the executable identity once after
   `shlex.split`: `exe = os.path.basename(argv[0])`; use `exe` for the safe-shape lookup
   and pass it to the flag/subcommand check instead of the raw `argv[0]` (REQ-008; today
   L256 calls `_unsafe_flag_denylist(argv[0], ...)` with the unnormalized token).
2. Keep `_match_executable_identity` (L129-151) unchanged as the operator/config gate.
3. After the gate matches, evaluate the per-executable safe-shape rule for `exe`; a
   missing rule or a rule violation returns `RiskLevel.HIGH` (REQ-006, REQ-007).
4. Keep the existing call order and fail-closed branches: metacharacter check (L240),
   `shlex.split` failure (L245), empty argv (L247), `_check_positional_args` (L253), then
   the safe-shape check replacing the `_unsafe_flag_denylist` call (L256), then return the
   match.

### Method
- Replace `_UNSAFE_FLAGS` with `SAFE_SHELL_SHAPES` (new): `dict[str, ShellShapeRule]`
  where `ShellShapeRule` (new) is a small frozen dataclass with `allowed_subcommands:
  frozenset[str] | None` (None = no subcommand semantics) and `deny_flags: frozenset[str]`
  plus `deny_flag_prefixes: frozenset[str]` (token-prefix denylist such as `--output=`).
- Table content (REQ-007, preserving current `none`-asserted behavior for read-only
  executables per Plan A3):
  - `ls`, `pwd`, `echo`, `cat`: no subcommand semantics, `deny_flags=∅` (path checks stay
    in `_check_positional_args`); `cat` had an empty denylist today (L46) — unchanged.
  - `grep`: `deny_flags={"-r", "-R"}` (unchanged from L47).
  - `find`: `deny_flags={"-exec", "-delete", "-ok"}` (unchanged from L45).
  - `git`: `allowed_subcommands={"log", "status", "show", "diff", "branch"}`; `branch`
    accepts list-only forms only — deny `-D`, `-d`, `-M`, `-m`, `-c`, `--delete`,
    `--move`, `--copy` when the subcommand is `branch`; `diff` denies any token starting
    with `--output` (`--output=<file>` form; the space-separated `--output <path>` form is
    already caught by `_check_positional_args` seeing `<path>` as positional).
  - No entry for `python`, `pytest`, `uv`, `python3`: absence → `HIGH` (REQ-006).
- Add a module-private `_safe_shape_violation(exe: str, argv: list[str]) -> bool` (new)
  implementing the lookup and per-rule evaluation; `_special_case_risk` calls it as
  `if _safe_shape_violation(exe, argv[1:]): return RiskLevel.HIGH` in place of the
  `_unsafe_flag_denylist` call. Remove `_unsafe_flag_denylist` (its only call site is
  L256; it has no other callers in `scripts/` or `tests/` — verified 20261103).

### Details
- Subcommand detection: `argv[1]` (if present) is the git subcommand; tokens starting with
  `-` are flags. A git invocation with a subcommand outside `allowed_subcommands`
  (`checkout`, `push`, `branch -D ...` handled via the branch deny flags) → `HIGH`.
- Executable identity for the gate is still basename-matched per token (existing
  `_match_executable_identity`), so a full-path invocation of `git` (basename `git` from
  any directory) applies the rule to the `log` subcommand (AC-3 full-path read-only form
  stays `none`).
- REQ-008 acceptance: full-path `find` with `-delete` → gate matches basename `find`; the
  rule lookup now uses the same normalized `find` and `-delete` violates it → `HIGH`
  (today the denylist lookup with the raw token silently skips, the root-cause bug).
- Preserve the docstring/inline REQ annotations style: this file already carries
  `REQ-001`..`REQ-005` matching-mechanism annotations (Plan D1); annotate the new code
  with `REQ-006`..`REQ-008`.

## Compatibility considerations
- `classify_risk` public signature and return values unchanged; changed functions are
  module-private (verified: `_match_executable_identity` / `_unsafe_flag_denylist` have no
  external callers).
- Behavior change is escalation-only: commands previously `none` may become `high`; no
  command becomes less risky (metacharacter/path/parse fail-closed branches untouched).
- `TestPrefixCollision` synthetic-prefix tests for executables with no rule (`c`, `Cat`,
  `\$HOME`) will flip to `high` — migrated in the seq 03 document (Plan A7).

## Security considerations
- Fail-closed default: unknown executables, unknown git subcommands, denied flags,
  metacharacters, parse failures, empty argv all route to `HIGH` (approval prompt).
- The change removes the interpreters/test-runners auto-approval that let arbitrary code
  execute without the human-in-the-loop prompt (Plan Background/Reason for Change).

## Rollback considerations
- Revert the single commit for this row; `config/agent.toml` (seq 02) and tests (seq 03)
  revert independently per Plan phase, but reverting only this document restores the
  pre-change fail-open behavior — revert all three to a consistent state.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py` — all green, incl. migrated
  `TestPrefixCollision` cases (AC-1, AC-2, AC-3, AC-5).
- `uv run pytest tests/agent -k "tool_policy or tool_approval"` — no caller regression.
- `uv run ruff check scripts/agent/tool_policy.py` and `uv run mypy --no-namespace-packages
  scripts/agent/tool_policy.py` — clean.
- `radon cc scripts/agent/tool_policy.py -s` — no new blocker-grade function;
  `_special_case_risk` must not exceed its current rank (Plan Risk).

## Completion criteria
- The seq 03 red baseline tests pass; interpreter invocations (`python -c ...`, `pytest`,
  `uv run ...`), `git branch -D ...`, `git diff --output=...` classify `high`; `git status`,
  `git log --oneline`, `git diff`, `git show`, list-only `git branch` classify `none`;
  full-path `find` with `-delete` classifies `high` and full-path `git log --oneline`
  stays `none`.
- Static checks and radon constraint pass; the three A7 pins are `high` (migrated in seq 03).

## Out of Scope
- `_check_positional_args` token extraction (`--flag=value`) — owned by
  `plans/20261101-142514_shellrisk001_...` (Plan A2, sequencing dependency).
- `config/agent.toml` prefix list edits — seq 02 document.
- Test additions/migrations — seq 03 document; docs updates — seq 04/05 documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement safe-shape rule table + normalized executable lookup (Procedure 1-4) | Pending | — | — | Execute after seq 03 red-test baseline (Plan Phase 1) |
| 2 | Run the validation sequence (`rules/toolchain.md`) incl. radon | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (deny-by-default auto-approval), `REQ-007` (per-executable
  allowed subcommands/flags), `REQ-008` (single normalized executable name)
- **Source issue**: `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-145910_shellprefix001_safe-prefix-approves-code.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-072856
- **Related target files**: `scripts/agent/tool_policy.py`
