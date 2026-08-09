## Goal
Fix `tools/check_no_compat.py`'s `files` argparse `help=` string so it accurately lists all
four directories scanned by the no-args default path (`scripts/`, `docs/`, `tests/`,
`tools/`), instead of omitting `tools/`.

## Scope
In scope: the `help=` string literal on the `files` positional argument (currently
`"Files to check (default: scripts/, docs/, tests/)"`, line ~186). Out of scope: `dirs_to_scan`,
`ROOT_DIR`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST`, and the directory-expansion logic in the
`args.files` branch (added separately in `implementations/done/20260809-170919_check_no_compat_directory_arg_expansion.py.md`).

## Assumptions
- No existing test asserts on the exact `--help` text — confirmed via `grep -n
  "help\|argparse\|--help" tests/tools/test_check_no_compat.py`, no matches — so no test needs
  updating alongside this change.
- Zero behavior change: this only affects the string shown by `--help`, not any scanning logic,
  argument parsing, or default values.

## Design decisions
- Update the help string to explicitly list all four directories (`scripts/`, `docs/`, `tests/`,
  `tools/`) rather than deriving it programmatically from `dirs_to_scan` at argparse-setup time
  — `dirs_to_scan` is a local variable built inside `main()`, not available at module level
  where `parser.add_argument` is called, so a dynamic reference would require restructuring
  code purely for a help string, which is unjustified scope widening for a one-line text fix.

## Alternatives considered
- **Rephrase to avoid enumerating directories at all** (e.g. "Files to check (default: scans
  the repository's standard source/doc/test directories)"): considered, but rejected in favor
  of keeping the explicit list — the requirement's acceptance criteria calls for the four
  directories to be visible in `--help` output, and an explicit list is more useful to someone
  invoking the tool manually than a vague description.

## Implementation
### Target file
`tools/check_no_compat.py`

### Procedure
1. Locate the `files` argument's `parser.add_argument(...)` call (currently line ~183-187).
2. Change `help="Files to check (default: scripts/, docs/, tests/)"` to
   `help="Files to check (default: scripts/, docs/, tests/, tools/)"`.
3. Do not modify any other argument, the `dirs_to_scan` list, `ROOT_DIR`, `COMPAT_PATTERNS`,
   `DEFAULT_ALLOWLIST`, or the `args.files` branch's directory-expansion logic.

### Method
Single string-literal edit inside an existing `parser.add_argument(...)` call.

### Details
None beyond the string change itself — this is a one-line, self-contained edit.

## Compatibility considerations
No behavior, argument name, or signature change — `files` remains a `nargs="*"` positional
argument. Purely cosmetic to `--help` output.

## Security considerations
N/A — text-only change to a CLI help string, no new attack surface.

## Rollback considerations
Single-line string edit; revert via `git revert` of the commit with no other side effects, no
data or config involved.

## Validation plan
- `uv run python -m tools.check_no_compat --help` — visually confirm the `files` help text now
  lists `scripts/`, `docs/`, `tests/`, `tools/`.
- `uv run mypy tools/check_no_compat.py` — no new errors (baseline: 0 errors).
- `uv run ruff check tools/check_no_compat.py` — no new errors (baseline: 0 errors).
- `uv run pytest tests/tools/test_check_no_compat.py -v` — all 25 existing tests still pass (no
  test asserts on help text, so none require updating).

## Out of scope
- `dirs_to_scan`, `ROOT_DIR`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST`.
- The positional-directory-argument expansion logic (see
  `implementations/done/20260809-170919_check_no_compat_directory_arg_expansion.py.md`).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260809-173020_plan.md
- Source implementation procedure: N/A
- Generated at: 20260809-173855
- Related target files: tools/check_no_compat.py
