# mutmut cannot run: missing `[mutmut]` `source_paths` configuration

## Priority
Medium

## Summary
`mutmut` is installed in the dev environment but fails on every invocation because the
installed version resolves its mutation target exclusively from a `[mutmut]` section in
`setup.cfg`/`pyproject.toml`, which does not exist in this repo. This blocked the mutation-testing
gate in `prompts/04_refactor.md` Step 4/10 across every one of the ~45 file-level refactor cycles
run against `scripts/mcp_servers/{git,file,web_search,shell}/` (2026-08-14 through 2026-08-16).

## Reason for Change
`prompts/04_refactor.md`'s completion gate requires "`mutmut` has no unresolved surviving
mutations in changed paths." This gate could not be evaluated at all (not "0 survivors" but
"tool did not run") for any file in the sweep, which weakens the behavior-lock evidence the
refactor procedure is designed to produce. The gap is a one-time config fix that unblocks the
gate for all future refactor cycles.

## Implementation Intent
Add a `[mutmut]` section (in `pyproject.toml` or `setup.cfg`, whichever the installed `mutmut`
version prefers) with `source_paths` pointing at `scripts/`. Confirm the exact key name and
section format against the installed `mutmut` version's own docs/`--help` output, since the
error message references `setup.cfg` specifically.

## Target Files or Areas
- `pyproject.toml` or `setup.cfg` (new `[mutmut]` section)
- Unknown: exact required key names for the installed `mutmut` version (confirm via
  `uv run mutmut run --help` and package docs before editing)

## Required Changes
- Add a `[mutmut]` config section with `source_paths = ["scripts"]` (or the correct key name).
- Run `uv run mutmut run --paths-to-mutate scripts/mcp_servers/git/git_security.py` (or any
  small already-refactored file) as a smoke test to confirm the tool now executes.
- Confirm mutation results are produced (killed/surviving counts), not just "no error."

## Acceptance Criteria
- `uv run mutmut run` (or a path-scoped invocation) executes without the
  `FileNotFoundError: Could not figure out where the code to mutate is` error.
- At least one smoke-test run against a small module produces a mutation report with
  killed/surviving/equivalent counts.
- No unrelated `pyproject.toml`/`setup.cfg` sections are modified.

## Testing Expectations
Manual verification only: run `mutmut` against 1-2 small, already-tested modules and confirm a
report is produced. No code behavior changes, so no regression test suite run is required.

## Documentation Impact
None required for this fix itself. If `rules/toolchain.md`'s "Additional static analysis"
section is later extended to include a canonical `mutmut` invocation example, update it there —
out of scope for this issue.

## Out of Scope
- Do not add mutation-testing steps to CI/pre-commit as part of this issue.
- Do not change any production code behavior.

## AI Implementation Instruction
Confirm the installed `mutmut` version's expected config location/key by reading its own
`--help` output and installed package docs before writing the config section — do not guess the
key name. Keep the change to the config file only; do not touch any file under `scripts/`.
