## Goal
- Report a `plain-path-citation` finding for each plain citation of an active Plan from `tools/check_workitem_structure.py`, without outgrowing the 24576 B gate (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one import, two call sites, and a docstring tightening that offsets their size; the companion test file. Out of scope: archived Plans, any baseline file, the `procedure-length` advisory logic, and other findings.

## Assumptions
- Verified in Step 3a: the file is 24465 B (gate 24576 B, no baseline entry); the active-only guards are `if kind in ("plan", "implementation") and not _is_archived(doc_path):` at lines 436 (`collect_single_file_findings`) and 462 (`collect_findings`), and in both the plan branch calls `find_plan_leftover_findings`.
- Procedure 01 provides `find_plan_citation_findings(doc_path, root)`, shaped like `find_plan_leftover_findings(doc_path, root, ...)`, so the call needs no new wrapper function.
- Test conventions (read in Step 3a): tests monkeypatch `cwis.ROOT_DIR` to a `tmp_path` tree, install the real templates with `_install_templates(root)`, write documents with `_write(dir, name, content)`, and call `cwis.collect_single_file_findings(path)` or `cwis.collect_findings({"plan"}, include_done=...)`.

## Design decisions
- The finding is not advisory (it is not in `ADVISORY_CATEGORIES`): exit 1 like the other Plan findings.
- Size: the added import (about 70 B) and two calls (about 170 B including ruff's wrapping) are offset by replacing the `--file` paragraph of the module docstring with the shorter text below (saves 220 B measured), net about +20 B.

## Alternatives considered
- A wrapper function named _citation_findings, like `_length_findings`: about 300 B more, over the headroom. Moving a function to a helper module with `module_nodes.py`: only if the measured size still exceeds the gate (Plan UNK-03).

## Implementation
### Target file
`tools/check_workitem_structure.py`

### Procedure
1. Record `wc -c` (24465 expected) and run `uv run pytest tests/tools/test_check_workitem_structure.py`.
2. Write the companion tests and confirm the new ones fail.
3. Add `from tools._workitem_citation_check import find_plan_citation_findings` after the `_workitem_companion_kinds` import (keep isort order for ruff).
4. In `collect_single_file_findings`, in the `if kind == "plan":` branch after the `find_plan_leftover_findings(doc_path, ROOT_DIR)` call, add `findings.extend(find_plan_citation_findings(doc_path, ROOT_DIR))`; do the same in `collect_findings` (after its `find_plan_leftover_findings(...)` call, same branch).
5. Replace the `--file` paragraph of the module docstring (the six lines from "`--file` checks one or more documents" to "`--file` check.") with: "`--file` checks the given documents (kind inferred from the top-level directory)" newline "and ignores `--kind`/`--include-done`, so a repository-wide scan's legacy-template" newline "findings never block a check of the documents a workflow step just produced."
6. Run `wc -c` again: the size MUST be at most 24576. If not, tighten another docstring paragraph; if that is not enough, stop and report (fallback: extract a function with `module_nodes.py`, a decision to report).

### Method
- No other line of the file changes.

### Details
- Run `uv run python tools/check_workitem_structure.py --kind plan` afterwards: the active Plans report no finding.

### Companion test files
- `tests/tools/test_check_workitem_structure.py`
  - Procedure: add tests with the real templates: an active plan with plain `File Path` and step citations gives `plain-path-citation` findings through `collect_single_file_findings` (category, file, detail naming the path and the normalizer command) and through `collect_findings`; the same plan after `wrap_plain_citations` gives none; the same text under `plans/done/` gives none with `include_done=True`; the findings make the exit code 1 (`main` with `--file`).
  - Validation: the new tests fail before the hook exists; the existing tests of the file still pass.

## Compatibility considerations
- The finding applies to active Plans only; the five Plans in `plans/` have no plain citation (checked in Step 3), so no existing document starts failing.

## Security considerations
- N/A: read-only checker.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py`; ruff format and check; mypy (CI invocation); `uv run bandit tools/check_workitem_structure.py -c pyproject.toml`; `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`; the active-Plan scan above.

## Completion criteria
- The finding appears for a plain active Plan and not for archived or normalized ones; the file is at most 24576 B; no new finding on the repository's active Plans.

## Out of Scope
- The detector (procedure 01), the normalizer (procedure 03), and the documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test file(s) first, then confirm they fail before and pass after | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261126-151438_wfeff003_plan-path-citations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-172913_wfeff003_plan-path-citations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-173805
- **Related target files**: `tools/check_workitem_structure.py`, `tests/tools/test_check_workitem_structure.py`
