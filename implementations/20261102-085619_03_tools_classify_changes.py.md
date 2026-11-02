## Goal
- Create the read-only classifier that groups changed paths into pathspec lists, keeps both names of every rename together, marks untracked paths, and flags partly staged paths (`REQ-003`: read-only porcelain classifier).

## Scope
- In scope: a new module `tools/classify_changes.py` with `main()`, a pure parser and classifier, and the CLI in the shared contract. Out of scope: staging, unstaging, committing, commit-type selection, registration (rows 05 to 07), tests (row 04).

## Assumptions
- Step 3a verification: `tools/classify_changes.py` and `tests/tools/test_classify_changes.py` do not exist (`ls` checked), `tools/` and `tests/tools/` exist, and `tools/TOOL_DESCRIPTIONS.md` lists no such tool. Existing tools use `from __future__ import annotations`, `argparse`, a module docstring headed by the path, `ROOT_DIR`, and `main(argv) -> int` with `sys.exit(main())` (`tools/check_plan_target_overlaps.py`); git is run as `subprocess.run([...], capture_output=True, check=False)` with a static list (`tools/run_validation_gates.py::_git_diff_name_only`).
- A5 (Plan): `--porcelain=v1 -z` entries are XY, a space, then the path, then NUL; for a rename or copy (`R`/`C` in X or Y) the entry is followed by one more NUL-terminated token, the original path (to-path first, then from-path in `-z` mode). Falsifiable by a path the parser mishandles; tests cover spaces, quotes, and non-ASCII names.
- Interpretation decisions recorded here (the Plan states the requirements, not these details): the pathspec list holds only paths with a staged change (index column not blank and not `?`), so unstaged edits of other sessions are never swept into a split commit; working-tree-only changes are reported on an `unstaged:` line; `--verify-pathspec` is the concrete way "refuse to split a pair" is exercised; exit code 1 on `partly-staged` or `unmerged`.
- A3 (Plan): the group table and the cross-group rename rule (grouped under the new name, reported as a `NOTE`).
- Needs confirmation (non-blocking): whether the owner wants the extra `--group` and `--verify-pathspec` options; they add no write capability. Recorded here; proceed.
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`, judged and recorded): no other Frozen Plan targets this new file. Judged compatible; see the Plan's Assumptions A6, A6b, and A7.
- Tool contract (shared by rows 01, 03, 04, 06, 07; row 03 owns the implementation):
  - Command: `uv run python tools/classify_changes.py [--status-file <path>] [--group <name> | --verify-pathspec <path> ...]`.
    Input is `git status --porcelain=v1 -z` bytes: read from `--status-file <path>` (`-` means stdin), otherwise obtained by running that exact git command in the current directory.
  - Groups, first match wins, in this print order: `artifacts` (`issues/`, `plans/`, `implementations/`, including `done/`), `code` (`scripts/`, `config/`, `deploy/`), `tests` (`tests/`), `tools` (`tools/`), `docs` (`docs/`, `skills/`, `rules/`, `templates/`, `prompts/`, `routing.md`, `AGENTS.md`, `CLAUDE.md`), `other`.
  - Default output, one block per non-empty group: `[<group>]`, then `pathspec: <shell-quoted staged paths, rename pairs adjacent as new name then old name>`, then optional `unstaged: <paths with a working-tree-only change>` and `untracked: <paths>` lines (neither is part of the pathspec). A `warnings:` section follows when needed, with `WARN partly-staged: <path>`, `WARN unmerged: <path>`, and `NOTE cross-group-rename: <old> -> <new> (grouped under <new>)`.
  - Exit codes: 0 normal; 1 when any `partly-staged` or `unmerged` warning exists (or, with `--verify-pathspec`, when a candidate pathspec names only one name of a staged rename); 2 for a usage error or a failed git call.
  - `--group <name>` prints only that group's pathspec line value (empty output when the group is empty); `--verify-pathspec` reads the candidate paths and prints `split-rename: <path> needs <partner>` for each half-named pair.

## Design decisions
- Pure core, thin shell: `parse_porcelain_z(raw: bytes) -> list[Change]`, `classify(changes) -> Classification`, `render(classification) -> str`, `verify_pathspec(changes, paths) -> list[str]`, and `main()` do the I/O. A rename is one `Change` record holding both names, so no code path can emit half of a pair.
- Group lookup is a fixed ordered tuple of `(group, prefixes, exact names)`; `other` is the fallback. Paths are shell-quoted with `shlex.quote` in output only.

## Alternatives considered
- Parse `git status --short` (non-`-z`): rejected, quoting of unusual names and the rename arrow are ambiguous (A5).
- Use GitPython: rejected, the other tools that read status use plain git and the `-z` form is simplest and dependency-free.

## Implementation
### Target file
`tools/classify_changes.py` (new)

### Procedure
1. Create `tools/classify_changes.py` (new) with the module docstring (purpose, usage, exit codes, never writes), constants for the group table, and a frozen dataclass `Change` (`index: str`, `worktree: str`, `path: str`, `orig_path: str | None`) with `is_staged` (new), `is_untracked` (new), `is_partly_staged` (new), and `is_unmerged` (new) properties.
2. Implement `parse_porcelain_z` (new), `classify`, `render`, `verify_pathspec` (new), `_read_status` (new), and `main`.
3. Run the tool lint sequence from `routing.md` "Adding a new tool" and a smoke test against the live repository.

### Method
- `parse_porcelain_z` (new): split on NUL, drop the trailing empty token, iterate with an index; each entry needs at least 4 characters (XY plus space plus path) else raise `ValueError` (main maps it to exit 2); if `X` or `Y` is `R` or `C`, consume the next token as `orig_path` (new). `??` entries are untracked; `!!` entries are skipped.
- Unmerged: `(X,Y)` in `DD AU UD UA DU AA UU`.
- `classify`: for each change compute the group from `path` (new name); a staged rename or copy whose `orig_path` (new) maps to a different group adds a cross-group note; the group's pathspec holds staged paths in input order, a rename contributing `path` then `orig_path` (new); `unstaged` holds tracked paths with a worktree-only change; `untracked` holds `??` paths; `partly staged` means a staged column in the letters M, A, D, R, C together with a worktree column in the letters M, D (a worktree-only rename does not exist).
- `verify_pathspec` (new): for each staged rename or copy, return a message when exactly one of its two names appears among the candidate paths.
- `_read_status` (new): `--status-file -` reads `sys.stdin.buffer`, a path reads the file bytes, otherwise `subprocess.run(["git", "status", "--porcelain=v1", "-z"], capture_output=True, check=False)`; a non-zero return code raises `RuntimeError` (exit 2). Add `# nosec B603 B607 — static argument list, no user input` per `rules/coding.md`.
- `main`: argparse with `--status-file`, and a mutually exclusive `--group` choice among the six names or `--verify-pathspec` with `nargs="+"`; return the exit codes of the shared contract.

### Details
- Never import or call anything that writes to the repository; the only subprocess is the status read.
- Output is plain text to stdout, errors to stderr; no color, no emoji.
- Keep the module small (well under the 20480 B size gate, which applies to `scripts/` only).

## Compatibility considerations
- New file; nothing imports it. The CLI is the contract consumed by row 01 text, row 04 tests, and rows 06 and 07 registration, so its flags and output block names MUST match the shared contract.

## Security considerations
- Paths are data, never executed; the only subprocess uses a static argv list (no shell). Output quoting uses `shlex.quote` so a name with spaces or shell metacharacters is safe to paste into a pathspec.

## Rollback considerations
N/A: new read-only file; revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_classify_changes.py -v` (row 04): all pass.
- Per `routing.md` "Adding a new tool": `uv run ruff format tools/classify_changes.py`; `uv run ruff check tools/classify_changes.py --fix` then without `--fix`; `uv run mypy tools/classify_changes.py`; `uv run bandit tools/classify_changes.py`.
- Smoke test on live data: run the tool in this repository and confirm renames under `plans/done/` appear in the `artifacts` group with both names.

## Completion criteria
- The tool matches the shared contract, is read-only, keeps both names of every rename in one group, refuses a half-named pair under `--verify-pathspec`, marks untracked and unstaged paths, flags partly staged paths, and passes ruff, mypy, bandit, and its tests (`AC-3`, `AC-4`).

## Out of Scope
- Staging, unstaging, or committing; commit message or type generation; registration (rows 05 to 07); skill text (rows 01, 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tools/classify_changes.py` per Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan (row 04 owns `tests/tools/test_classify_changes.py`) | Pending | — | — | executed by row 04 |
| 3 | Run ruff format and check, mypy, bandit on the file, and the live smoke test | Pending | — | — |  |

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
- **Requirement ID**: `REQ-003`; acceptance `AC-3`, `AC-4`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: tools/classify_changes.py
