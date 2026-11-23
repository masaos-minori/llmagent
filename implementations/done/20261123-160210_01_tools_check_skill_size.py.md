## Goal

Create the size-budget tool for the pipeline instruction files, mirroring `tools/check_module_size.py`: default limit, baseline ceilings, stale entries, shrunk-file advisory, and the update and no-baseline modes.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the new tool only. It reuses `load_baseline` and `write_baseline` from `tools/check_module_size.py` and keeps its own `main` small (the model's `main` is complexity D (30)).

## Assumptions

- Verified: `check_module_size.py` exposes `load_baseline(path)` (skips blank and `#` lines, reports malformed lines on stderr) and `write_baseline(path, entries)` (sorted `<relpath>\t<size>` lines); tools import siblings by module name (as `generate_reference_table.py` imports `_agent_config_migration`).
- Covered files: `skills/**/*.md`, `rules/*.md`, `prompts/*.md`, `templates/*.md`, `routing.md`, `AGENTS.md`, `CLAUDE.md` (71 files, 827,660 B on 2026-11-23; 18 over 16,384 B). Implementation procedures and plans are work items and are excluded.
- The default limit 16,384 B is a judgment recorded as UNK-01 in the Plan; it is one constant.

## Design decisions

- Helpers: `collect_covered(root) -> list[tuple[str, int]]` (sorted relpath and byte size), `evaluate(sizes, baseline, limit) -> Evaluation` (a frozen dataclass with `violations`, `stale`, `shrunk` lists of readable messages), and a thin `main(argv)`.
- Semantics (same as the module gate): a file over the limit and absent from the baseline is a violation; a baselined file larger than its ceiling is a regression violation; a baseline entry whose file is gone or is at or under the limit is stale and fails; a baselined file smaller than its ceiling is advisory (`shrunk`) and does not change the exit status.
- Options: `--root PATH`, `--limit BYTES` (default 16384), `--baseline PATH` (default `tools/check_skill_size_baseline.txt`), `--no-baseline`, `--update-baseline` (rewrite from the current over-limit files and exit 0), `--top N` (advisory). Exit 0 clean, 1 on a violation or stale entry, 2 on a usage error (missing root).

## Alternatives considered

Rejected: extending `check_module_size.py` with a markdown mode (it would grow past its own complexity and size baseline); rejected: copying the baseline helpers (a second parser for the same file format).

## Implementation
### Target file
`tools/check_skill_size.py` (new)

### Procedure
1. Create the module with the docstring, constants (`DEFAULT_LIMIT = 16384`, the covered glob list, `DEFAULT_BASELINE`), and the two helpers `collect_covered` (new) and `evaluate` (new).
2. Implement `main` with argparse and the mutually exclusive `--no-baseline` and `--update-baseline`, calling the helpers and printing one line per finding.
3. Print the advisory `shrunk` lines on stdout with a hint to run `--update-baseline`; print violations and stale entries on stderr.

### Method
Resolve the repository root as the parent of `tools/`; collect with `Path.glob` on each covered pattern and `Path.stat().st_size`; sort by relpath for deterministic output.

### Details
- Messages name the file, its size, and the limit or ceiling, and state the remedy: move the branch to an edge-case file, or lower the ceiling with `--update-baseline` after a reduction.
- No file is modified except by `--update-baseline`.
- Keep the module well under 24,576 B and `main` under complexity C.

## Compatibility considerations

New tool; nothing imports it. The sibling import requires `tools/` on `sys.path`, which `tests/conftest.py` and direct execution already provide.

## Security considerations

N/A: reads file sizes only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/tools/test_check_skill_size.py -q` (procedure 02)
- `uv run ruff check tools/check_skill_size.py` and `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run radon cc tools/check_skill_size.py -s` shows no function above B
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` stays clean

## Completion criteria

- The tool reports violations, regressions, stale entries, and shrunk files as described, supports the two update modes, and exits with the documented codes.

## Out of Scope

Gate, CI, and inventory wiring (procedures 03-06) and the baseline file (procedure 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-160632 | 20261123-161116 | Created tools/check_skill_size.py; radon: main B (8), evaluate B (9) |
| 2 | Add or update tests per Validation plan | Completed | 20261123-161116 | 20261123-161116 | Tests are in procedure 02 (18 unit tests plus the live-repository test) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-161116 | 20261123-161116 | ruff, ruff format, mypy (609 files), lint-imports, module size, docstring check, validation gates pass; full suite 13572 passed, 2 failed in tests/db/test_schema_validation_per_database.py (mcp_dedup stamp 2 vs user_version=1, caused by the concurrent mcpdl004 schema bump, unrelated); diff-cover reports no covered lines because the new tool is an untracked file, measured coverage of tools/check_skill_size.py is 97 percent from its own tests |

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
- **Requirement ID**: `REQ-001` (baseline-gated size check)
- **Source issue**: issues/20261123-155457_skillsize001_compress-skill-workflows.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-155813_skillsize001_compress-skill-workflows.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-160210
- **Related target files**: `tools/check_skill_size.py`
