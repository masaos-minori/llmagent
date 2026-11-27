## Goal
- Add a repeatable `--plan PATH` option to `tools/check_plan_target_overlaps.py` that keeps only findings naming a given Plan, in every output format, with default output and exit code unchanged (`REQ-001`, `REQ-003`); its tests are the companion `tests/tools/test_check_plan_target_overlaps.py`.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: argument handling and a post-filter of the finding list in `main`. Out of scope: `find_cross_plan_target_overlaps` and every other detection function.

## Assumptions
- Verified in Step 3a: findings are dicts with `category`, `file`, `detail`; `detail` has the form `targeted by N Frozen Plans at once: p1, p2 -- verify their designs do not contradict each other before/while implementing` (`tools/check_plan_target_overlaps.py:139-163`); `main` (lines 207-226) discovers, finds, renders by `--format`, and returns 0.
- `tools/amend_plan.py:516-527` runs this tool by subprocess and filters its lines itself; it does not pass `--plan`, so its behavior is unchanged.
- The module is 7831 B, well under the 24576 B gate.

## Design decisions
- Filter by exact path membership: take the text between `: ` and ` -- ` of `detail`, split on `, `, and test whether any of the requested Plan paths is in that list, so a path that is a prefix of another never matches.
- A requested path is normalized to the repository-relative POSIX form that `PlanDocument.rel_path` uses (resolve, then `relative_to(ROOT_DIR)`; an absolute path outside the repository keeps its POSIX string and matches nothing).

## Alternatives considered
- Filtering inside `find_cross_plan_target_overlaps`: rejected, the Issue forbids changing detection logic.

## Implementation
### Target file
`tools/check_plan_target_overlaps.py`

### Procedure
1. Add `filter_findings_by_plans(findings: list[dict[str, str]], plans: list[str]) -> list[dict[str, str]]` (new): return the findings whose detail's Plan list contains any of the normalized paths; with an empty `plans` list return the findings unchanged.
2. Add a helper `normalize_plan_path(value: str) -> str` (new) as described above.
3. In `build_arg_parser` add `--plan` with `action="append"`, `default=None`, `metavar="PATH"`, help "Keep only findings that name this Plan (repeatable)".
4. In `main`, before discovery: for each `--plan` value that is not an existing file print `error: not a file: {value}` to standard error and return 2; after `find_cross_plan_target_overlaps` apply the filter, then render in the chosen format as before; return 0.
5. Update the module docstring Usage block with `--plan`.

### Method
- `main` keeps its structure; the only new lines are the validation, the normalization, and one filter call, so `--format json`, `--format csv`, and text all filter identically.

### Details
- Type annotations on every new function; line length 88; English comments.

### Companion test files
- `tests/tools/test_check_plan_target_overlaps.py`
  - Procedure: add tests with two synthetic Frozen Plans sharing one target: `--plan` of either keeps the finding in text, JSON, and CSV; a third Plan prints the empty form; repeating `--plan` keeps the union; an absolute and a relative path match alike; a path that is a prefix of a listed Plan path does not match; an unknown path returns exit 2; without `--plan` the output is unchanged.
  - Validation: `uv run pytest tests/tools/test_check_plan_target_overlaps.py -q`, then ruff and mypy on the file.

## Compatibility considerations
- The default call and `--format` output are unchanged; the only caller (`tools/amend_plan.py`) passes no new option.

## Security considerations
- N/A: read-only; the new option only reads existing paths.

## Rollback considerations
- Revert the commit; no other file depends on the option.

## Validation plan
- `uv run ruff format tools/check_plan_target_overlaps.py` then `uv run ruff check ... --fix` and confirm; `uv run mypy tools/check_plan_target_overlaps.py`; `uv run bandit tools/check_plan_target_overlaps.py`.
- `uv run pytest tests/tools/test_check_plan_target_overlaps.py -q` (existing tests unchanged and passing).
- Default-output parity: run the tool before and after on the repository and compare the saved outputs.

## Completion criteria
- `--plan` output contains only findings naming a given Plan in all three formats; an unknown path exits 2; the default output and exit code are unchanged; lint, type, bandit, and tests pass.

## Out of Scope
- Detection logic, Frozen-Plan discovery, adoption of the option in skill texts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `--plan`, the filter, and the parser change per Procedure | Completed | 20261127-110934 | 20261127-111040 | Changed: tools/check_plan_target_overlaps.py (--plan, filter_findings_by_plans, normalize_plan_path); defaults byte-identical in text, JSON, CSV |
| 2 | Add the tests listed under Companion test files | Completed | 20261127-111040 | 20261127-111055 | Changed: tests/tools/test_check_plan_target_overlaps.py (companion; 7 tests added, 11 pass) |
| 3 | Run ruff, mypy, bandit and the default-output parity comparison | Completed | 20261127-111055 | 20261127-111704 | ruff, mypy, bandit pass; text, JSON, CSV default output byte-identical to the saved pre-change output End-of-batch full suite: 15994 passed, 4 failed: 3 pre-existing in tests/mcp_servers/git (same on a clean HEAD) and tests/eventbus/test_eventbus_dlq_outbox.py::test_restart_with_pending_rows, a timing flake under parallel load (passes alone 3/3; unrelated to tools/); diff-cover N/A: no scripts/ change |

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
- **Requirement ID**: `REQ-001` (the `--plan` filter), `REQ-003` (defaults unchanged)
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104530_wfeff008_gate-output-filters.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-105933
- **Related target files**: `tools/check_plan_target_overlaps.py`, `tests/tools/test_check_plan_target_overlaps.py`