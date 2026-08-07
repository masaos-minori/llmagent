# `tools/check_no_compat.py`'s `ROOT_DIR` resolves one directory too high, so the no-compat-stubs check silently scans nothing

## Priority
Medium

## Summary
`tools/check_no_compat.py` computes `ROOT_DIR = Path(__file__).resolve().parent.parent.parent`,
which resolves to the parent of the repository root (e.g. `/home/masaos` instead of
`/home/masaos/llmagent`) given the file's current location at `tools/check_no_compat.py`. As a
result, `main()`'s default scan (`ROOT_DIR / "scripts"`, `"docs"`, `"tests"`, `"tools"`) points at
directories that do not exist, every `d.exists()` guard is `False`, the files list stays empty, and
the tool always reports `All checks passed` with exit code `0` — even though it performs zero
actual scanning. This defeats the `no-compat-stubs` pre-commit hook, which invokes this tool with
`pass_filenames: false` (i.e. always via the default, directory-based scan).

## Reason for Change
This tool exists specifically to catch backward-compatibility leftovers (stale import paths,
re-export stubs, `_cfg` cache references, etc.) before they land — see its own docstring and
`COMPAT_PATTERNS`. A silently-broken check is worse than no check: it gives false confidence that
compatibility-leftover patterns are being caught in every commit and in `pre-commit run --all-files`,
when in fact this hook has been a no-op (unconditionally passing, having scanned zero files) since
some prior move of the file to its current path. This was discovered incidentally while
implementing an unrelated requirement (`requires/done/`, see the sibling
`tools/check_suppression_justification.py` implementation cycle) and was explicitly deferred as a
separate concern rather than fixed inline, to avoid unrelated scope creep in that change.

## Evidence
- Current computation (confirmed by direct read, `tools/check_no_compat.py` line 21):
  `ROOT_DIR = Path(__file__).resolve().parent.parent.parent`.
- The file's own docstring still reads `"""scripts/checks/check_no_compat.py`, a stale header from
  before the file was moved to its current location, `tools/check_no_compat.py` — this is the
  likely origin of the extra `.parent` level (the file used to live one directory deeper, at
  `scripts/checks/check_no_compat.py`, where three `.parent` calls would have correctly reached the
  repo root; the depth was not updated when the file moved).
- Live reproduction:
  ```
  python3 -c "
  from pathlib import Path
  p = Path('tools/check_no_compat.py').resolve()
  root = p.parent.parent.parent
  print('ROOT_DIR resolves to:', root)
  print('exists scripts/:', (root / 'scripts').exists())
  print('exists docs/:', (root / 'docs').exists())
  "
  ```
  prints `ROOT_DIR resolves to: /home/masaos` and `exists scripts/: False` / `exists docs/: False`
  (repository root is `/home/masaos/llmagent`).
- `uv run python -m tools.check_no_compat` (default scan, no file args — matching exactly how
  `.pre-commit-config.yaml`'s `no-compat-stubs` hook invokes it, `pass_filenames: false`) prints
  `All checks passed` and exits `0`, despite scanning zero files (confirmed via the reproduction
  above: every `dirs_to_scan` entry fails its `d.exists()` guard, so `files` stays empty and
  `total_issues` never leaves `0`).
- A sibling module in the same directory, `tools/check_suppression_justification.py`, correctly
  uses `ROOT_DIR = Path(__file__).resolve().parent.parent` (two levels, since `tools/` is one level
  below the repo root) — this is the correct depth for a file living directly under `tools/`.

## Implementation Intent
Fix the path depth so `ROOT_DIR` resolves to the actual repository root, matching the pattern
already used correctly in `tools/check_suppression_justification.py`. Also correct the stale
`scripts/checks/check_no_compat.py` docstring header to reflect the file's real current path, since
that header is the apparent root cause of the depth mismatch and would mislead the next person who
copies this file as a template. After fixing the depth, re-run the tool against the current
repository and address (fix or explicitly, individually allowlist per existing convention) whatever
compatibility-leftover findings newly surface, since the check has apparently not scanned anything
for an unknown period — do not silently re-allowlist everything in bulk without reviewing each
finding.

## Target Files or Areas
- `tools/check_no_compat.py` (the `ROOT_DIR` computation and docstring header)
- Possibly `DEFAULT_ALLOWLIST` in the same file, if newly-surfaced findings are legitimate
  pre-existing matches that need individual allowlisting per `rules/coding.md` suppression
  governance conventions
- `tests/test_check_no_compat.py` (if it exists at the currently-documented path referenced inside
  `check_no_compat.py`'s own `DEFAULT_ALLOWLIST` — verify this test actually exercises the real
  `main()` default-scan path, not just the individual `check_*` functions with synthetic content,
  since the latter would not have caught this regression)

## Required Changes
- Change `ROOT_DIR = Path(__file__).resolve().parent.parent.parent` to
  `ROOT_DIR = Path(__file__).resolve().parent.parent` in `tools/check_no_compat.py`.
- Update the module docstring's first line from `"""scripts/checks/check_no_compat.py` to the
  file's actual path, `"""tools/check_no_compat.py`.
- Re-run `uv run python -m tools.check_no_compat` (default scan) after the fix and triage any
  newly-surfaced findings: fix genuine leftovers, or add them to `DEFAULT_ALLOWLIST` individually
  with a clear reason if they are confirmed intentional/historical exceptions.
- If `tests/test_check_no_compat.py` only tests individual `check_*` functions against synthetic
  `tmp_path` content and never exercises `main()`'s real default-scan/`ROOT_DIR` path, add a
  regression test that would have caught this (e.g. asserting `ROOT_DIR` resolves to a directory
  that actually contains `scripts/`, `docs/`, `tests/`, and `tools/`).

## Acceptance Criteria
- `ROOT_DIR` in `tools/check_no_compat.py` resolves to the actual repository root (verifiable via
  `(ROOT_DIR / "scripts").exists()` returning `True` in a quick manual check or a test).
- `uv run python -m tools.check_no_compat` (no file args) scans a non-empty file list and reports
  a real result (either `All checks passed` after genuine triage, or a nonzero exit with concrete
  findings) — not a silent, zero-file `All checks passed`.
- `uv run pre-commit run no-compat-stubs --all-files` passes against the current, correctly-triaged
  repository state.
- The module docstring's path header matches the file's actual location.
- Any newly-surfaced compatibility-leftover findings are either fixed or individually allowlisted
  with a documented reason — not bulk-suppressed.

## Testing Expectations
- Run `uv run pytest tests/test_check_no_compat.py -v` (or wherever its test file actually lives —
  confirm the real path) after the fix; all existing cases must still pass.
- Add a regression test asserting `ROOT_DIR` resolves correctly (see Required Changes) so a future
  file move cannot silently reintroduce this bug.
- Run the standard lint/type sequence from `rules/toolchain.md` (`ruff check`, `mypy`) against the
  changed file.
- Run `uv run pre-commit run --all-files` once triage is complete to confirm the hook is both
  functional and passing.

## Documentation Impact
No `docs/*.md` update is expected to be strictly required, since this tool is not currently
documented in any `docs/*.md` page (confirmed absent during a related prior investigation).
If the fix's triage step surfaces and fixes genuine compatibility-leftover code, follow whatever
documentation convention already applies to that specific fix (unrelated to this issue itself).

## Out of Scope
- Any change to `COMPAT_PATTERNS` or the detection regexes themselves — this issue is about the
  path-resolution bug, not detection logic.
- Bulk-allowlisting all newly-surfaced findings without individual review.
- Changes to `tools/check_suppression_justification.py` or any other unrelated `tools/` module —
  it is referenced here only as a correct-depth precedent, not part of this fix's scope.

## AI Implementation Instruction
Fix only `tools/check_no_compat.py`'s `ROOT_DIR` depth and its stale docstring header. After the
fix, run the tool for real and treat whatever it newly reports as first-class findings to triage
(fix or allowlist individually) — do not assume the previous "all checks passed" history was
meaningful, since it was never actually scanning anything. Do not widen scope into unrelated
`tools/` modules or into `COMPAT_PATTERNS` changes. Stop and report if the newly-surfaced findings
are numerous or ambiguous enough to require a product/judgment decision, rather than silently
allowlisting them.
