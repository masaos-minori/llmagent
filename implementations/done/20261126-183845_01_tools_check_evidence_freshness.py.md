## Goal
- Create `tools/check_evidence_freshness.py`, a read-only tool with two subcommands: `check` reports which files a Plan or procedure cites that changed, are uncommitted, or are unrecorded since the Plan's recorded `Evidence revision`; `record` prints the line to write and refuses while a cited file is uncommitted (REQ-001, REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the tool and its companion test file. Out of scope: writing the field into a Plan (the phase pastes it), the template and rule text (procedures 03 to 07), and any hook, gate, or CI step.

## Assumptions
- The recording format of Plan D-1 (one `Evidence revision` line, derived file set) was proposed in the Plan for the owner's confirmation (Plan UNK-01); the owner's request to generate these procedures is taken as that confirmation, and the report says so.
- Verified in Step 3a (experiments on this repository): `git diff --name-only <sha> HEAD -- <paths>` lists committed changes including added and deleted files; `git status --porcelain=v1 --untracked-files=all -- <paths>` lists working-tree, staged, and untracked changes and nothing for ignored files; `git cat-file -e <sha>^{commit}` fails with `Not a valid object name` for an unknown SHA. Two `git` calls cover any number of paths.
- `tools/amend_plan.py` shows the accepted way to start `git` from a tool: `subprocess.run` with a fixed argv list, no shell, and `# nosec B404` / `# nosec B603` comments with a justification after the dash; `tools/compare_test_baseline.py` is the model of the CLI shape (text report, exit codes 0, 1, 2, `main(argv)`, the `sys.path` guard).
- Plan overlap check (Step 2): no other Frozen Plan targets these files.

## Design decisions
- CLI: `check_evidence_freshness.py {check,record} DOC [--also PATH ...] [--root DIR]`; `--root` (default: the repository root) is the directory `git -C` runs in, so tests use a temporary repository.
- Cited paths: every backticked token of the document, with a trailing `:LINE` or `:LINE-LINE` removed, that matches `^[\w.-]+(?:/[\w.-]+)+$` (so globs, placeholders with braces, commands, and `::` pytest ids are excluded), in first-seen order and unique; the document's own repository-relative path is excluded.
- Revision: the first line `- **Evidence revision**: <40 lowercase hex>` of the document; when the document has none, its `- **Source plan**: <path>` value is followed once (a `plans/<name>` path is tried under `plans/` and then `plans/done/`). No revision, an unreadable document, or a SHA that `git cat-file -e <sha>^{commit}` rejects is an input error (exit 2), so the phase verifies in full.
- `check`: classify each cited path and each `--also` path: `changed` when it appears in `git diff --name-only <sha> HEAD -- <paths>`; `uncommitted` when it appears in the `git status` output; `unrecorded` when it is an `--also` path the document does not cite. A path can be both `changed` and `uncommitted`. Output: one `<status>: <path>` line per reported path (sorted by path), then `unchanged: N; changed: X; uncommitted: Y; unrecorded: Z (revision <12 hex>)`. Exit 1 when any path is reported, 0 otherwise.
- `record`: take the cited paths of a Plan; when any is uncommitted print `uncommitted: <path>` lines and return 1; otherwise print `- **Evidence revision**: <HEAD sha>` and return 0. It writes nothing.
- Path handling: paths come from the document and are passed after `--` so a path starting with `-` is never an option.

## Alternatives considered
- A per-claim file list in the Plan: rejected (Plan D-1). Per-path `git log -1` calls: rejected, two batched calls are faster and simpler.

## Implementation
### Target file
`tools/check_evidence_freshness.py` (new)

### Procedure
1. Write the companion tests first and confirm they fail because the module does not exist.
2. Create the module with the docstring style of `tools/compare_test_baseline.py` (file path line, purpose, usage, exit codes), `from __future__ import annotations`, and the `sys.path` guard.
3. Implement, in this order: `InputError`, `cited_paths` (new), `read_revision` (new), `_git`, `classify`, `render`, `main`.
4. Run the companion tests, ruff, mypy, and bandit on the file.

### Method
- Data: `Freshness(changed: frozenset[str], uncommitted: frozenset[str], unrecorded: frozenset[str], total: int)` as a frozen dataclass; `classify(root, sha, paths, also) -> Freshness`.
- `_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]` runs `["git", "-C", str(root), *args]` with `capture_output=True`, `text=True`, `check=False`; the callers inspect `returncode`; `git` missing is an `InputError`.
- Parse `git status --porcelain=v1` lines as `line[3:]`; for a rename (`old -> new`) take the new path; paths git quotes (special characters) are compared after stripping the quotes.

### Details
- The exit code is 1 for any reported path, including `unrecorded`, so a caller cannot read an incomplete check as clean.
- Documented dry run (Plan AC-09): copy an archived Plan to a scratch directory outside the repository, add an `Evidence revision` line holding an older commit SHA, run `check` against it, and record the unchanged share in this procedure's Execution Status Notes.

### Companion test files
- `tests/tools/test_check_evidence_freshness.py` (new)
  - Procedure: build a temporary git repository in `tmp_path` (`git init`, commits with `-c user.name=t -c user.email=t@example.com -c commit.gpgsign=false`), write a Plan under `plans/` citing files in backticks, and call `main` with `--root`; cover: all files unchanged (exit 0, summary counts); a file changed in a later commit; a staged change and an unstaged change; an untracked cited file; a deleted file (committed and uncommitted); a file created after the revision; a cited file that does not exist at the revision and still does not (unchanged); an `--also` path the Plan does not cite (`unrecorded`, exit 1) and one it cites; `:LINE` and `:LINE-LINE` suffixes removed, globs and `{filename}` placeholders and commands ignored, the document's own path excluded; a procedure document resolved through `Source plan` under `plans/` and under `plans/done/`; no `Evidence revision`, an unknown SHA, and an unreadable document (exit 2); `record` printing the HEAD line, and refusing with `uncommitted:` lines when a cited file is dirty.
  - Validation: `uv run pytest tests/tools/test_check_evidence_freshness.py` fails before the module exists and passes after.

## Compatibility considerations
- N/A: a new standalone tool with no importer.

## Security considerations
- `git` is started with a fixed argv list and no shell; document-derived paths follow `--` and cannot become options; the two `nosec` comments carry that justification (`tools/check_suppression_justification.py` checks them). The tool writes nothing.

## Rollback considerations
- N/A: revert the commit; the rule text of procedures 04 to 07 refers to the tool and reverts with it.

## Validation plan
- `uv run pytest tests/tools/test_check_evidence_freshness.py`; ruff format and check; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit tools/check_evidence_freshness.py -c pyproject.toml`; `uv run python tools/check_suppression_justification.py`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; the documented dry run.

## Completion criteria
- The tests fail first and then pass for AC-01, AC-02, AC-03, AC-04, and AC-05; the validators pass; the dry run is recorded in the Notes.

## Out of Scope
- Registration (procedure 08), the field in the template (procedure 03), and the rule and workflow text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-185118 | 20261126-185118 | wfeff004: full suite 15778 passed, 3 failed (known tests/mcp_servers/git failures); dry run on a scratch copy of the wfeff003 Plan at revision 27a17cb51: unchanged 15, changed 9 |
| 2 | Add the companion test file first, then confirm it fails before and passes after | Completed | 20261126-185118 | 20261126-185118 | wfeff004: full suite 15778 passed, 3 failed (known tests/mcp_servers/git failures); dry run on a scratch copy of the wfeff003 Plan at revision 27a17cb51: unchanged 15, changed 9 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-185118 | 20261126-185118 | wfeff004: full suite 15778 passed, 3 failed (known tests/mcp_servers/git failures); dry run on a scratch copy of the wfeff003 Plan at revision 27a17cb51: unchanged 15, changed 9 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261126-151439_wfeff004_evidence-sha-carryover.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-182520_wfeff004_evidence-sha-carryover.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-183845
- **Related target files**: `tools/check_evidence_freshness.py`, `tests/tools/test_check_evidence_freshness.py`
