## Goal

Make `tools/check_workitem_structure.py` accept one or more paths after `--file` (REQ-001, single-path behavior unchanged) and add issue template-leftover detection (REQ-002) derived from `templates/issue.md` at run time.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The leftover rule is the measured Decision 4 set of the plan: 25 non-heading, non-bullet, non-table instruction lines, 5 fenced bullets holding a `{...}` placeholder, and the `# <Issue Title>` line, all matched verbatim after stripping surrounding whitespace.
- The 20261117 verification measured 0 hits on the 28 open issues and 1 hit on 1656 archived issues, so enabling the category breaks no open work item.
- `templates/issue.md` keeps one fenced `markdown` block; its extraction can reuse the module's existing `_FENCE_RE`.

## Design decisions

- `--file` keeps its name and gains `nargs="+"` so the flag stays the id anchor shared by gate, routing row, and hook (plan Decision 1); aggregation happens over the path list.
- The leftover rule is read from the template fence at run time — one source, no hard-coded copy — and applies to issues only (plans and procedures stay out per plan UNK-01).

## Alternatives considered

- A separate `--files` flag: rejected in plan Decision 1 (a second flag name forces a new routing row and hook mapping).
- A hard-coded leftover-line list in the checker: rejected; it drifts from `templates/issue.md`, which REQ-002 names as the single source.

## Implementation
### Target file
`tools/check_workitem_structure.py`

### Procedure

- Change the `--file` argument in `build_arg_parser` to `nargs="+"` and let `main` loop over the list, aggregating each path's findings; a single path must produce the same output as before (REQ-001 / AC-1).
- Add two module-level functions (new): an extraction function that builds the leftover rule from the `templates/issue.md` fence, and `find_template_leftovers` (new), which returns findings with category `template-leftover` (new), each naming the document and the matched line.

### Method

- Rule extraction: take the fenced block, then the title line, the bullets holding a `{...}` placeholder, and the instruction lines (skip headings, bullets, table rows, and fence markers).
- Matching: compare stripped document lines against the rule set verbatim; a document whose own content merely contains braces is not reported (plan Decision 5).
- Wire the findings into `collect_single_file_findings` (single-file mode) and `collect_findings` (directory-scan mode) for issue-kind documents only (REQ-002).

### Details

- Keep the new functions below radon complexity grade C (REQ-007); `find_release_unit_findings` stays untouched.
- Each finding must name the matched line so an author can reword a legitimately reused line (plan Risk mitigation).

### Companion test files
- `tests/tools/test_check_workitem_structure.py`
  - Procedure: add multi-path `--file` tests, an unfilled-scaffold exit-1 `template-leftover` test, a filled-issue exit-0 test, a brace-content-not-reported test, a title-line test, and clean plan/procedure skeleton tests, reusing `_write`, `_install_templates`, and the `ROOT_DIR` monkeypatch pattern.
  - Validation: `uv run pytest tests/tools/test_check_workitem_structure.py -v` passes (AC-1, AC-2, AC-3).

## Compatibility considerations

- `tools/amend_plan.py` passes one `--file` path; the list-typed argument must keep that behavior identical (REQ-001).
- The `--archived-status` subcommand and its baseline path stay unchanged.
- Gate, routing row, and hook id reconciliation lives in the seq 02/03/04 documents; this document changes no id-producing code.

## Security considerations

N/A: reads repository Markdown only; no eval, subprocess, or network access is added.

## Rollback considerations

- Revert the commit; safe to land alone because the gate row and hook land later in the plan's phase order.

## Validation plan

- `uv run pytest tests/tools/test_check_workitem_structure.py -v` (with the companion tests).
- `uv run python tools/check_workitem_structure.py` over the open work items: no `template-leftover` finding.
- Size gate: module stays under the 24576 B limit (currently 18168 B); ruff, mypy, bandit, and radon clean on the changed file (REQ-007 / AC-9).

## Completion criteria

- AC-1, AC-2, AC-3 hold as tests; the live scan reports nothing; single-path invocation output is byte-identical to before for the same document.

## Out of Scope

- Leftover rules for plans and procedures (plan UNK-01); generic `{...}` detection; checking `done/` documents; the gate row, hook, routing row, and tool description (other documents of this plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement multi-path `--file` and issue leftover detection | Completed | 20261117-164918 | 20261117-164918 | multi-path --file (nargs+), find_template_leftovers + _issue_template_leftover_lines added; live scan of open work items: 0 leftover findings |
| 2 | Add tests via the companion test file | Completed | 20261117-164918 | 20261117-164918 | 9 new tests in companion file; 46/46 pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-164918 | 20261117-170012 | targeted validators pass (ruff, mypy, bandit, size gate, radon: only pre-existing grade C find_release_unit_findings); full sequence at batch end full batch validation: pytest tests/ 12591 passed 7 skipped; diff-cover no measurable lines (tools/tests/docs only); drift 0 errors; hooks pass |

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
- **Requirement ID**: `REQ-001` (multi-path `--file`), `REQ-002` (issue leftover detection), `REQ-007` (size and complexity constraints)
- **Source issue**: `issues/20261117-123330_wftool001_gate-workitem-structure.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-124139_wftool001_gate-workitem-structure.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-151927
- **Related target files**: `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`