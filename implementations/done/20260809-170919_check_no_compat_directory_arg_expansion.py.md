## Goal
Fix `tools/check_no_compat.py`'s `main()` so that a directory passed as a positional file
argument is expanded into its contained `*.py`/`*.md` files instead of raising an unhandled
`IsADirectoryError`.

## Scope
In scope: the `args.files` branch of `main()` (currently lines ~215-221) — how `files: list[Path]`
is built when `args.files` is non-empty. Out of scope: the no-args `dirs_to_scan` branch,
`ROOT_DIR`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST`, and the `--help` text drift (tracked
separately in `issues/20260809-170451_risks.md`).

## Assumptions
- `check_all(content, filepath, allowlist)` / `check_compat_patterns(...)` take one already-read
  file's content plus its single `Path` — confirmed by reading their signatures at
  `tools/check_no_compat.py` lines ~149-170 — so this fix only needs to change how the `files`
  list is constructed, not those functions.
- The `no-compat-stubs` pre-commit hook (`.pre-commit-config.yaml`, `pass_filenames: false`)
  never passes `args.files`, so this branch is only reachable via manual CLI invocation —
  confirmed via `rg -n "check_no_compat" .pre-commit-config.yaml`.

## Design decisions
- Expand a directory argument using the same pattern as the existing no-args path —
  `.glob("**/*.py")` + `.glob("**/*.md")` — rather than inventing a new extension list, so
  directory-argument scans stay consistent with the tool's own default scan.
- Merge expanded-directory results with any plain file arguments in the same `args.files` list,
  then deduplicate with `sorted(set(...))`, mirroring the no-args path's existing convention
  exactly (same call shape, same ordering guarantee for deterministic output).
- Keep the change confined to the `else:` branch of `if not args.files:` — do not touch the
  no-args branch, so its behavior (and the pre-commit hook that depends on it) is provably
  unaffected.

## Alternatives considered
- **Explicit usage error on directory input** (reject with a clear message instead of
  expanding): rejected — the tool's default no-args mode already treats "scan this directory
  tree" as normal, useful behavior; failing on `python -m tools.check_no_compat <dir>` would be
  a less useful, more surprising interaction for something clearly meant to work like a scoped
  version of the default scan. This is a Low-priority internal dev tool, not a security-
  sensitive interface, so the more permissive/useful option is preferred here (see requirement
  and plan for full blast-radius reasoning).

## Implementation
### Target file
`tools/check_no_compat.py`

### Procedure
1. Locate the `else:` branch of `if not args.files:` inside `main()` (currently
   `files = [Path(f) for f in args.files]`, around line 215).
2. Replace it with logic that, for each `Path(f)` in `args.files`: if `.is_dir()`, extend the
   result with `.glob("**/*.py")` and `.glob("**/*.md")` from that directory; otherwise keep the
   path as-is (do not require `.is_file()` — preserve the existing behavior where a nonexistent
   path is silently skipped later by the `filepath.exists()` check at line ~219, so a typo'd
   plain filename still reports the same way it does today).
3. Deduplicate and sort the combined list with `sorted(set(...))`, matching the no-args path.
4. Do not modify `ROOT_DIR`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST`, or the `if not args.files:`
   branch's own body.
5. If pulling the file-collection logic (both branches) into one small named function
   materially simplifies testing the new directory-expansion behavior without widening the
   diff into unrelated code, do so; otherwise leave `main()`'s existing structure and let the
   test exercise it via `sys.argv` patching (see the companion test procedure document,
   `implementations/20260809-170919_test_check_no_compat_directory_arg_expansion.py.md`).

### Method
Direct, minimal edit to a single branch inside `main()`. No new dependencies, no new public
functions required unless step 5's extraction is chosen for testability.

### Details
- Reuse the literal glob pattern already present in the no-args branch — do not introduce a
  different glob syntax or additional extensions.
- Preserve the existing `filepath.exists()` guard in the per-file loop after this branch; it
  still serves its original purpose for the no-args path and for any nonexistent plain-file
  argument.

## Compatibility considerations
No public API or CLI flag signature changes — `files` remains a `nargs="*"` positional
argument. Existing manual invocations with only files (no directories) behave identically:
`Path.is_dir()` is false for a plain file, so it takes the unchanged "keep as-is" path.

## Security considerations
No new attack surface: this is a local developer CLI tool invoked manually or via pre-commit
(which never reaches this branch). Directory expansion only reads files already reachable to
the invoking user's filesystem permissions, same as the existing no-args scan.

## Rollback considerations
Single self-contained edit to one branch in one function. Revert via `git revert` of the
commit introducing this change; no data migration, no config, no deployed-service state
involved (`tools/` scripts are not part of `deploy/deploy.sh`'s copy list).

## Validation plan
- `uv run python -m tools.check_no_compat tools/` and `uv run python -m tools.check_no_compat scripts/` — must exit 0 or non-zero only from genuine findings, never `IsADirectoryError`.
- `uv run mypy tools/check_no_compat.py` — no new errors (baseline: 0 errors).
- `uv run ruff check tools/check_no_compat.py` — no new errors (baseline: 0 errors).
- `uv run pytest tests/tools/test_check_no_compat.py -v` — all existing 22 tests plus the new test(s) from the companion test procedure pass.
- `uv run pre-commit run --all-files` — `no-compat-stubs` hook still passes (confirms the no-args path is unaffected).

## Out of scope
- `ROOT_DIR`, `COMPAT_PATTERNS`, `DEFAULT_ALLOWLIST` (see `plans/20260807-100914_plan.md`).
- The no-args `dirs_to_scan` glob logic.
- The `--help` text drift for the `files` argument (see `issues/20260809-170451_risks.md`).

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260809-170033_plan.md
- Source implementation procedure: N/A
- Generated at: 20260809-170919
- Related target files: tools/check_no_compat.py
