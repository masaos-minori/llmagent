# docs010: `check_docs_structure.py` prints "All checks passed" when its glob matches zero files

## Priority
Medium

## Summary
Make `tools/check_docs_structure.py` fail (or at minimum warn) when the glob it is given resolves to
no files, so a mistyped pattern cannot produce a green result.

## Background
Found while converting `plans/20261023-072425_plan.md` into implementation procedures on 2026-10-24.
The Plan cited a size finding for the generated agent reference table, and reproducing it with the
pattern as written in the Plan produced a pass because the pattern matched nothing:
- `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` → exit 0, `All checks passed`
- the same run with `"docs/23_agent/agent_13_*.md"` checked the file (it reported
  `agent_13_reference-api-generated.md: size 24961 bytes exceeds 24576 byte limit` at HEAD
  `6fcbb7e0c`, before the `SIZE_EXCEPTIONS` entry that `BLK-001` added)

Measured on 2026-10-24: `Path(".").glob("23_agent/agent_13_*.md")` matches 0 files,
`Path(".").glob("docs/23_agent/agent_13_*.md")` matches 1, `docs/**/*.md` matches 172. The checker
resolves each pattern against `ROOT_DIR` (`tools/check_docs_structure.py:480-483`) and then prints
`All checks passed` to stderr and returns 0 (`:521-525`) with no count of how many files were checked.

`parser.add_argument("globs", nargs="*", ...)` documents the patterns as "Glob patterns relative to
repo root (default: docs/**/*.md)" (`tools/check_docs_structure.py:455-459`, inside `main()` at `:451`),
which is the form that works; the `docs/`-less form is a silent no-op. `tools/TOOL_DESCRIPTIONS.md:34`
and `:114` describe the tool as validating "structural conventions of `docs/*.md`" without stating that
an empty match set is accepted.

## Problem
Any caller that writes the pattern relative to `docs/` instead of the repo root gets exit code 0 and
"All checks passed" while checking nothing. CI passes `docs/**/*.md`
(`.github/workflows/governance-docs-consistency.yml:89` and `:95`), so CI is not affected today; the
failure mode is local runs, procedures, and ad-hoc commands copied from documents — which is exactly
how this was discovered.

## Reason for Change
The checker is the gate several procedures and plans cite as evidence. A green run that checked zero
files is indistinguishable from a green run that checked 300, so the evidence is not trustworthy
unless the empty-match case is refused.

## Implementation Intent
Count the files the resolved globs match. If the count is zero, print a distinct message naming the
patterns and return a non-zero exit code. Keep everything else about the current behavior identical.

## Target Files or Areas
- `tools/check_docs_structure.py` (glob resolution and `main()` `:450-472`)
- `tests/tools/test_check_docs_structure.py`
- `tools/TOOL_DESCRIPTIONS.md` (`:34`, `:114`)

## Required Changes
- Resolve every supplied glob, collect the matched set, and fail with a message such as
  `no files matched the given glob(s): {patterns}` when the set is empty.
- Add a test for the empty-match case (expect non-zero exit and the message) and a test that a normal
  single-file glob still passes.
- State the behavior in the `tools/TOOL_DESCRIPTIONS.md` entry for `check_docs_structure.py`.

## Constraints
- CI already relies on the current exit-code contract with `docs/**/*.md`; a non-empty run must keep
  the same exit codes and output format.
- `tests/tools/test_check_docs_structure.py:22` imports `SIZE_EXCEPTIONS` and `MAX_SIZE` directly, and
  `TestCheckSizeExceptions` uses `next(iter(SIZE_EXCEPTIONS.items()))`; the empty-match change must not
  perturb those tests.
- Do not add glob normalization that silently rewrites `23_agent/*` into `docs/23_agent/*`; the point
  is to make the mistake visible, not to hide it.

## Acceptance Criteria
1. `uv run python tools/check_docs_structure.py "23_agent/agent_13_*.md"` exits non-zero and reports
   that no file matched.
2. `uv run python tools/check_docs_structure.py "docs/**/*.md"` keeps its current behavior and reports
   no findings at HEAD.
3. `uv run pytest tests/tools/test_check_docs_structure.py -q` passes, including the new empty-match case.
4. `uv run python tools/check_tool_descriptions.py` reports no drift after the description update.

## Testing Expectations
- Unit tests in `tests/tools/test_check_docs_structure.py` for: zero-match globs, one valid file, and a
  mix of a valid and an invalid glob (the run must still fail on the valid file's findings, and must
  report the unmatched pattern).
- Run `uv run ruff check tools/check_docs_structure.py` and `uv run ruff format --check tools/check_docs_structure.py`.

## Documentation Impact
Required, small: the `tools/TOOL_DESCRIPTIONS.md` entry for `check_docs_structure.py` must say that an
empty match set is an error. No `docs/` chapter describes this checker's exit behavior.

## Out of Scope
- Changing `MAX_SIZE` or any `SIZE_EXCEPTIONS` entry.
- Changing which checks the tool performs, or adding new checks.
- Changing the CI workflow invocation.
- Lazy loading of the Step 0 mandatory-load set — no action required: the fixed load is absorbed by the prompt cache (user decision 2026-10-24).

## Unresolved Questions
- Should a partially-matching set (some globs match, some do not) fail, or only warn? The issue assumes
  the same failure treatment for consistency; confirm.
- Should `docs/**/*.md` remain the implicit default when no glob is given? (Current behavior,
  `tools/check_docs_structure.py:455-457`.)

## Dependencies
- N/A: none. Independent of `plans/20261023-072425_plan.md`; that Plan's rows were corrected to use the
  `docs/`-prefixed glob form.

## AI Implementation Instruction
Change only glob resolution and the exit path in `tools/check_docs_structure.py`. Do not alter any
individual check. Add the empty-match test first, then implement. Update the tool description in the
same change so `check_tool_descriptions.py` stays consistent.

## Traceability
- **Workflow phase**: `plan-to-implementation-procedure` (validation-reliability gap found while reproducing a Plan's cited checker finding)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md` (`## Validation plan`)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `tools/check_docs_structure.py`, `tests/tools/test_check_docs_structure.py`, `tools/TOOL_DESCRIPTIONS.md`
