# Implementation Procedure: scripts/agent/tool_policy.py (shellrisk001)

## Goal
- Make `_check_positional_args()` treat the value of a long `--flag=value` token as a path
  candidate for the protected-path and `allowed_root` checks (REQ-001), leaving every other
  behavior unchanged (REQ-002). The REQ-003 regression tests live in the sibling procedure
  document `implementations/20261103-073729_02_tests_agent_test_tool_policy.py.md` (not a
  companion: this test file is also a target row of the shellprefix001 Plan, so it keeps
  documents of its own in both Plans).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Sequencing (Plan Assumptions, UNK-01 resolved): execute only after the shellprefix001
  procedures (`implementations/20261103-072856_*`) are implemented. Re-read
  `_check_positional_args` at execution time: the shellprefix001 Plan states it does not
  touch this function and keeps the call `_check_positional_args(cfg, argv, match)` in
  `_special_case_risk`, but the function body may have moved lines.
- Reconciliation the Plan requires (its ordering bullet): after shellprefix001, `python`
  and `pytest` commands are no longer auto-approval candidates and `git diff
  --output=<file>` is rejected by the git safe-shape rule, so the Plan's REQ-003 example
  executables are
  partially redundant. Primary escalation cases must use commands that still reach this
  check: `cat --file=/etc/shadow`, `grep --include=/etc/shadow x`, `ls --ignore=/etc`
  (read-only executables with path-taking flags). Keep `git diff --output=/etc/x` as a
  high-pin regression (it will pass through the git rule, not through this fix). Record
  the deviation from the Plan example set in the implementation cycle notes.
- The extension only adds `HIGH` escalations; it never lowers a risk (Plan Assumptions).

## Design decisions
- Candidate extraction in one small module-private helper ahead of the unchanged loop
  (Plan Design approach): `_iter_path_candidates(argv: list[str]) -> list[str]` (new) —
  keeps `_check_positional_args` from exceeding its current radon rank C (11).

## Alternatives considered
- Extract from any token containing `=` regardless of leading dashes — rejected per Plan
  Design (would treat `-X key=value` operands and `VAR=value` as paths; UNK-02 out of
  scope).
- Per-executable path-taking-flag tables — rejected per Plan Design (owned by
  shellprefix001's safe-shape rule, now implemented).

## Implementation
### Target file
- `scripts/agent/tool_policy.py`

### Procedure
1. Add `_iter_path_candidates` (new): for each token in `argv[1:]` — a bare token not
   starting with a dash yields the token; a token starting with a double dash and
   containing an equals sign yields the text after the first equals sign when non-empty;
   everything else (long flags without a value, the end-of-options marker, short flags,
   long flags with an empty value) yields nothing.
2. In `_check_positional_args` (currently L154-179), replace the filter line
   `positional = [a for a in argv[1:] if not a.startswith("-")]` (L163) with a call to
   `_iter_path_candidates(argv)`; the empty-list early return now tests the candidate
   list (Plan Design). Keep the loop body (protected-path check, `allowed_root`
   resolution, `ValueError` and `OSError` fail-closed branch), the `base == HIGH` early
   return, thresholds, and `_UNSAFE_FLAGS` semantics untouched (REQ-002).

### Method
- Extraction rule is mechanical and executable-agnostic; `_UNSAFE_FLAGS` note: after
  shellprefix001 this table is generalized into the safe-shape rule table — this Plan's
  REQ-002 "entries untouched" constraint is satisfied because this document changes
  neither the rule table nor its lookup, only candidate extraction.

### Details
- Annotate the new code with this Plan's inline style (`REQ-001`).
- NUL-containing values must still escalate through the existing `ValueError` branch
  (`Path.resolve()` raises on embedded NUL) — covered by the seq 02 NUL test, no new
  branch needed.

## Compatibility considerations
- `_check_positional_args` is module-private; signature `(cfg, argv, base)` unchanged (Plan
  Design Path A).
- User-visible behavior change: non-path `--flag=value` values (e.g. `--since=yesterday`)
  now resolve as paths and can escalate when the agent cwd is outside `allowed_root` —
  fail-closed parity with bare positional tokens (Plan Assumptions/Risks; pinned by the
  in-root and non-path tests).

## Security considerations
- Closes the `--flag=value` bypass of the protected-path/allowed_root guard on the
  auto-approved shell path (Plan Reason for Change); the extension adds escalations only.

## Rollback considerations
- Revert the single commit; the seq 02 tests revert with it (single-target change).

## Validation plan
- `uv run pytest tests/agent/test_tool_policy.py` — existing + new tests pass (AC-1 to AC-4).
- `uv run pytest tests/agent -k "tool_policy or tool_approval"` — no caller regression (AC-2).
- `uv run ruff check scripts/agent/tool_policy.py tests/agent/test_tool_policy.py` and
  `uv run mypy scripts/agent/tool_policy.py` — no findings.
- `radon cc scripts/agent/tool_policy.py -s` — `_check_positional_args` does not exceed
  rank C; `uv run bandit -r scripts/agent/tool_policy.py -c pyproject.toml` — no findings.
- `rules/toolchain.md` section 7 diff-cover sequence (baseline run without `--fail-under`
  first, then at the threshold).

## Completion criteria
- `--flag=value` values under protected prefixes or outside `allowed_root` classify
  `high`, identical to the space-separated form; in-root values, non-path values, bare
  long flags, the end-of-options marker, short flags, and empty values keep the
  pre-change result; NUL values escalate; the whole `test_tool_policy.py` suite and
  callers' classification tests are
  green; radon/bandit constraints hold (AC-1 to AC-4).

## Out of Scope
- Attached short-flag values (-c/etc/x.ini, -I/etc) and `key=value` operands — Plan
  UNK-02, needs owner follow-up issue.
- The safe-shape rule table, config prefixes, docs — shellprefix001 scope (already
  covered by its procedures).
- Regression tests — `implementations/20261103-073729_02_tests_agent_test_tool_policy.py.md`.
- Docs: Plan Documentation Impact is N/A.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `_iter_path_candidates` + candidate wiring (Procedure 1-2) | Pending | — | — | Execute after the seq 02 red-baseline tests land (Assumptions); re-read function body first (UNK-01) |
| 2 | Run the validation sequence incl. radon/bandit/diff-cover | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (`--flag=value` path candidates), `REQ-002` (unchanged
  behavior), `REQ-003` (regression tests; covered by the seq 02 document)
- **Source issue**: issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142514_shellrisk001_shell-risk-check-misses-flag-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-073729
- **Related target files**: `scripts/agent/tool_policy.py`
