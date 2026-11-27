## Goal
- Create `tools/generate_repeated_procedures.py`, which writes one implementation procedure document per listed Plan row from one body template and refuses rows whose `Change Responsibility` differs (`REQ-001` generate; `REQ-002` refusals before any write; `REQ-003` own Traceability block; `REQ-004` structure check and `--dry-run`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module. Tests, the inventory row, and the skill pointer are separate documents; `tools/generate_workitem.py` is read-only here (28930 B, baselined at that size).

## Assumptions
- Reused as a library from `tools/generate_workitem.py`, imported as a module so tests can patch its directory constants: `extract_target_file_rows` (line 312), `find_or_record_pass_timestamp` (283), `implementation_procedure_output_path` (235), `check_collision` (265), `IMPLEMENTATIONS_DIR` (99). Verified in Step 3a: the path function reads the module-level `IMPLEMENTATIONS_DIR`, so a test points it at `tmp_path` with `monkeypatch.setattr`.
- `extract_target_file_rows` returns paths only; this tool parses the second (`Change Responsibility`) and fourth (`Related Requirement / Acceptance Criterion`) cells itself, with the same table rules (first `|` table of the `## Implementation Target Files` section).
- The marker comment appended to the Plan by `find_or_record_pass_timestamp` is the one Plan write, as for `generate_workitem.py`; it happens only after every refusal check passed and never with `--dry-run`.
- The module must stay at or below 24576 B (`check-module-size-tools`).
- The tool does not run `tools/stale_detector.py`: names the template introduces still need `(new)` marking, which the Plan for `tools/finalize_procedures.py` (wfeff006) automates.

## Design decisions
- Pure functions: `parse_rows(plan_text)` returning `PlanRow(path, responsibility, requirement)` items, `normalize_change(responsibility, path)`, `check_request(rows, listed, template, timestamp)` (corrected in code-implementation Step 3b: the collision check needs only the pass timestamp, which is looked up without writing the marker, `root` is not needed) returning a list of refusal messages, `render_document(template, row, seq, timestamp, source_issue, plan_rel)`.
- `normalize_change` (new): replace the row's own path and its base name with the literals `{path}` and `{name}` (longest first), collapse whitespace, lowercase nothing; two rows are alike when the results are equal.
- The template body must not contain a `## Traceability` heading (the tool appends it) and may use only the placeholders `{path}`, `{name}`, `{seq}`, `{timestamp}`; any other lowercase `{identifier}` is refused as unknown.

## Alternatives considered
- Extend `tools/generate_workitem.py` with a `--body` option: rejected, it is at its baselined size ceiling.
- Let the template include its Traceability: rejected, those values are mechanical and per row.

## Implementation
### Target file
`tools/generate_repeated_procedures.py` (new)

### Procedure
1. Module docstring (usage, exit codes: 0 success, 1 refusal or failed structure check, 2 usage error), `from __future__ import annotations`, the `sys.path` fix when `__package__` is empty, `import tools.generate_workitem as gw`, `from tools._atomic_write import atomic_write_text`.
2. `parse_rows`: reuse the table location rules (section `## Implementation Target Files`, first `|` table, skip the header and separator), return rows with their cells.
3. `check_request` (new) collects every refusal without stopping at the first: a listed path that is not a Plan row, a duplicate in `--rows`, an existing output (`gw.check_collision` on the computed path, which also covers `done/`), a template with a `## Traceability` heading or an unknown placeholder, and rows whose normalized change texts are not all equal (naming the first differing row and both texts).
4. If any refusal exists print each as `refused: {message}` to standard error and return 1 before any write.
5. Otherwise call `gw.find_or_record_pass_timestamp(plan_path, now_stamp, dry_run)` (once), then for each listed row in table order compute `seq = f"{index:02d}"` (the 1-indexed position in the Plan table), render the document and write it with `atomic_write_text` (a dry run prints the path and writes nothing).
6. Run `check_workitem_structure.py --file {document}` for every created document (`sys.executable`, stdin closed), print the result under the document path, and return 1 when any exits non-zero; print `created {n} document(s)` and a reminder that `tools/stale_detector.py` is still to be run.
7. `main(argv: list[str] | None = None) -> int` with `argparse` (`plan`, `--rows` with `nargs="+"`, `--body-template`, `--root`, `add_dry_run_argument`); `__main__` calls `sys.exit(main())`; a missing Plan or template returns 2.

### Method
- `render_document`: apply the four placeholder replacements to the template, strip trailing blank lines, then append the Traceability block with the same field names and order as `templates/implementation-procedure.md`: Workflow phase `plan-to-implementation-procedure`; Requirement ID the row's fourth cell; Source issue from the Plan's `- **Source issue**:` line; Source requirement and Source implementation procedure as in the template; Source plan the Plan's repository-relative path; Generated at the pass timestamp; Related target files `` `{path}` ``.
- Sequence and timestamp are never recomputed locally: the `seq` rule is the one `gw.generate_all_rows` uses, and the timestamp comes from `find_or_record_pass_timestamp`.

### Details
- Type annotations on every function; English comments; line length 88.
- A row whose `Change Responsibility` mentions another row's path stays "different" after normalization, so it is refused (safe side).

## Compatibility considerations
- New file; no caller. It depends on five public names of `tools/generate_workitem.py`; renaming one fails the new tests at once.

## Security considerations
- Writes only new files under `implementations/` plus the one marker append to the named Plan; the template is read as text and never evaluated; fixed argv for the structure check, no shell.

## Rollback considerations
- Revert the commit and delete the generated documents of an unwanted run (they are new files named by the pass timestamp); the Plan's marker line stays valid for later runs.

## Validation plan
- `uv run ruff format tools/generate_repeated_procedures.py`, `uv run ruff check ... --fix`, then confirm `uv run ruff check`.
- `uv run mypy tools/generate_repeated_procedures.py`; `uv run bandit tools/generate_repeated_procedures.py`.
- `uv run python -m tools.check_module_size --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`.
- Comparison with `generate_workitem.py` (Plan `REQ-001`, AC-2): in a scratch copy of a Plan, the filenames written by this tool for all rows equal those of `--kind implementation-procedure --all-rows --dry-run`.

## Completion criteria
- Ten identical rows give ten documents in one call; every refusal case writes nothing; documents carry the Traceability block; the structure check result is printed and decides the exit code; lint, type, bandit, and the size gate pass.

## Out of Scope
- Changing `tools/generate_workitem.py`, the one-document-per-row rule, or the lightweight-fill criteria.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tools/generate_repeated_procedures.py` per Procedure/Method/Details | Completed | 20261127-101605 | 20261127-101627 | Changed: tools/generate_repeated_procedures.py (new, 9.9 KB); ruff, mypy, bandit pass; check_request signature corrected in the procedure |
| 2 | Run `tests/tools/test_generate_repeated_procedures.py` (written by its own procedure) | Completed | 20261127-101728 | 20261127-101728 | Needs the procedure for seq 02 |
| 3 | Run ruff, mypy, bandit, and the tools size gate on the file | Completed | 20261127-101728 | 20261127-102301 | ruff, mypy, bandit, tools size gate pass; End-of-batch full suite: 15950 passed, 3 failed (tests/mcp_servers/git, pre-existing, same 3 fail on a clean HEAD); diff-cover N/A: no scripts/ change |
| 4 | Compare filenames with the `--all-rows --dry-run` output of `tools/generate_workitem.py` on a scratch Plan | Completed | 20261127-101728 | 20261127-101728 | AC-2 parity covered by test_filenames_equal_those_of_generate_workitem_all_rows: ten files, same names as gw.generate_all_rows |

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
- **Requirement ID**: `REQ-001`..`REQ-004` (generate, refusals, Traceability block, structure check and dry run)
- **Source issue**: issues/20261126-151442_wfeff007_repeated-row-procedures.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095809_wfeff007_repeated-row-procedures.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100500
- **Related target files**: `tools/generate_repeated_procedures.py`