## Goal

Create `tools/generate_issue_batch.py` (new): one call that reads a Markdown spec of issue
blocks, validates every block, allocates strictly increasing timestamps, writes each issue
atomically (or previews with `--dry-run`), and runs the structure/leftover checker once over
all created paths.

## Scope
**Release unit**: N/A: not part of a release unit

Single-file procedure for row 1 of the plan's frozen `Implementation Target Files` table:
`tools/generate_issue_batch.py` (REQ-001 to REQ-006 spec parsing, collision-safe allocation,
reference tokens, `Generated at`, atomic writes and post-write check, REQ-008 the tool stays
under the size gate, AC-1 to AC-6, AC-8). The companion test module is listed under
Companion test files.

## Assumptions
- UNK-01 open: the maintainer must confirm the Decision 1 spec format before the first code
  step (plan Phase 1); a different format changes only the parser and its tests.
- The wftool001 dependency is satisfied: `tools/check_workitem_structure.py --file` already
  accepts several paths and carries leftover detection (verified against source, commit
  4f5a6d73e).
- The imported helpers read `ISSUES_DIR` at call time, so tests can redirect it with
  `monkeypatch` exactly as `tests/tools/test_generate_workitem.py` does.

## Design decisions
- New CLI, not a flag on `tools/generate_workitem.py`: the generator is 28930 bytes against
  the 24576-byte gate and its baseline entry may only shrink (Decision 2).
- Timestamps from one clock read in strictly increasing one-second steps in spec order
  (Decision 3); the tool sets only `Generated at` (Decision 4) and resolves `{{issue:<id>}}`
  to the allocated path (Decision 5).
- Whole-spec validation before the first write; a mid-run write failure reports created
  files and deletes none (Decision 6).

## Alternatives considered
- YAML or JSON spec (rejected in Decision 1: escaping and quoting pitfalls, authors must
  write Markdown anyway); `--batch-spec` on the generator (rejected in Decision 2: size
  gate); per-issue clock reads (rejected in Decision 3: same-second name collisions).

## Implementation
### Target file
`tools/generate_issue_batch.py` (new)
### Procedure
Follow the plan's Phase 1-3 in order: write the companion tests first (they fail), then the
pure functions (parse, validate, resolve references, allocate), then the preflight, atomic
writes, `--dry-run`, failure report, post-write checker call, exit codes, and `main`.
### Method
- Parse the spec into blocks each starting with `<!-- issue: {id} {slug} -->` followed by a
  document in the `templates/issue.md` shape: `{id}` matches `[a-z0-9]+` with at least one
  letter, `{slug}` matches `[a-z0-9_-]+` with at most four words, ids unique in the spec;
  any violation exits `2` before any write (REQ-001).
- Import from `tools/generate_workitem.py`: `issue_output_path`, `check_collision`,
  `GenerationError` (all exist); call `check_collision` for every allocated path in `issues/`
  and `issues/done/` before the first write (REQ-002).
- Replace `{{issue:<id>}}` tokens with the allocated repository-relative path; an unknown id
  exits `2` (REQ-003). Set only the `Generated at` value to the allocated timestamp
  (REQ-004).
- Write through `tools/_atomic_write.py` (`atomic_write_text`, `stage_write`,
  `add_dry_run_argument`); `--dry-run` prints each planned path and writes nothing; a
  mid-run failure reports the created paths and deletes none (REQ-005).
- After writing, run `uv run python tools/check_workitem_structure.py --file <p1> <p2> ...`
  once and report per-file results; exit `0` clean, `1` findings, `2` usage/validation
  error; entry point `main(argv: list[str] | None = None) -> int` (REQ-006).
### Details
Keep every function below radon grade C (REQ-008); no function reaches the generator's
complexity. Do not touch `tools/generate_workitem.py` (AC-8: `git diff --stat` on it is
empty).

### Companion test files
- `tests/tools/test_generate_issue_batch.py` (new)
  - Procedure: cover parsing/validation, allocation order, collision in both directories,
    reference tokens, `Generated at` equality, dry run, simulated write failure, atomic
    write, the checker call, and exit codes (plan Tests section); redirect the issue
    directory into `tmp_path` with `monkeypatch` following `tests/tools/test_generate_workitem.py`.
  - Validation: `uv run pytest tests/tools/test_generate_issue_batch.py -v` passes; AC-1 to AC-6 map to these tests.

## Compatibility considerations
New tool and new spec format; no existing caller changes. The single-issue path of
`skills/issue-creator` stays valid (its documentation rows are separate target rows).

## Security considerations
No network; the only subprocess is the local structure-checker command run as an argv list
(no shell), per `tools/` CLI convention.

## Rollback considerations
N/A: revert the commit; the tool creates no state outside `issues/` files it wrote itself.

## Validation plan
- `uv run pytest tests/tools/test_generate_issue_batch.py -v` — tests pass.
- `uv run radon cc tools/generate_issue_batch.py -s -n C` — reports nothing.
- `uv run bandit tools/generate_issue_batch.py` — clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — passes; the new file is not added to the baseline.
- `git diff --stat -- tools/generate_workitem.py` — empty.
- Smoke run (plan Tests): `--dry-run` on a two-issue spec against the real repository, then a real run whose created files are removed afterwards by single-path deletes.

## Completion criteria
AC-1 to AC-6 and AC-8 hold: three-block spec parses in order and bad specs exit `2` writing
nothing; timestamps strictly increase and a pre-existing path refuses the run before any
write; reference tokens resolve; documents equal their spec blocks except `Generated at`;
`--dry-run` changes nothing; the checker runs once over all paths; the generator has no diff
and the size and complexity gates pass.

## Out of Scope
Batch generation of plans, procedures, or Unknown/Risk files; posting to GitHub; any change
to `tools/generate_workitem.py` or the size baseline; the documentation rows (separate
target rows, seq 03 to 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the Decision 1 spec format with the maintainer, then write the companion tests (they fail first) | Pending | — | — | plan Phase 1; UNK-01 |
| 2 | Implement parse, validation, reference resolution, timestamp and path allocation (pure functions) | Pending | — | — | plan Phase 2 |
| 3 | Implement preflight, atomic writes, `--dry-run`, failure report, post-write checker call, exit codes, `main` | Pending | — | — | plan Phase 3 |
| 4 | Run the validation sequence (`rules/toolchain.md`), size gates, complexity, bandit, and the smoke runs | Pending | — | — | plan Phase 5 |

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
- **Requirement ID**: `REQ-001` to `REQ-006` (spec batch generation), `REQ-008` (size and complexity limits)
- **Source issue**: issues/20261117-123334_wftool005_workitem-batch-generate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-125502_wftool005_workitem-batch-generate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-200906
- **Related target files**: `tools/generate_issue_batch.py`, `tests/tools/test_generate_issue_batch.py`
