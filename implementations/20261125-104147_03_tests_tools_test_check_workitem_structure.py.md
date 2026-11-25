## Goal
Cover companion-kind detection and checking in the structure checker's test file: filename detection, kind inference, discovery and `--kind` selection, a passing and a malformed companion per template, the real producer skeleton, and regression of the existing kinds (`REQ-005`; evidence for `REQ-001` to `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- This document is a standalone row, not a companion: two code rows name the test file in `Related Tests`, so the companion condition "exactly one other row" fails (`skills/plan-to-implementation-procedure/SKILL.md`).
- In scope: the fixture template list and new tests in `tests/tools/test_check_workitem_structure.py`.

## Assumptions
- The code from the `seq` 01 and `seq` 02 procedures exists when these tests run: `companion_kind`, `COMPANION_TEMPLATES`, and the wired checker.
- The tests monkeypatch `cwis.ROOT_DIR` to `tmp_path` and install copies of the real templates, as the existing tests do (`tests/tools/test_check_workitem_structure.py:49-65`); loading the companion specs requires the two companion templates to be installed there too, so `_TEMPLATE_NAMES` must be extended before any test runs `load_template_specs`.
- `cwis.collect_findings` is called with explicit kind sets in the existing tests (lines 131, 145, 480, 643, 721, 893, 929, 937), so the default-set change does not affect them.

## Design decisions
- Reuse `_write`, `_install_templates`, and `monkeypatch.setattr(cwis, "ROOT_DIR", tmp_path)`; derive each companion document's headings from `cwis._extract_template_headings` so the tests follow the templates.
- Test through the public checker functions (`infer_kind`, `discover_documents`, `collect_single_file_findings`, `collect_findings`, `main`) plus `companion_kind` directly.

## Alternatives considered
A separate test file for the new module was rejected: the plan's single test row keeps the companion cases next to the checker's other kind tests.

## Implementation
### Target file
`tests/tools/test_check_workitem_structure.py`

### Procedure
1. Extend `_TEMPLATE_NAMES` (`:49`) with `unknowns-issue.md` and `risks-issue.md`.
2. Add `companion_kind` tests: parametrized accepted forms (`{ts}_unknowns.md`, `{ts}_02_unknowns.md`, `{ts}_risks.md`, `{ts}_01_risks.md`, a one-digit and a three-digit sequence, and an `issues/done/` path) and rejected forms (`{ts}_gate001_unknowns.md`, `{ts}_x_foo-unknowns.md`, `{ts}_unknowns.txt`, a non-numeric sequence, a `plans/` path, a deeper path).
3. Add `infer_kind` cases for companion paths under `issues/` and `issues/done/`, and the unchanged `plan`, `implementation`, and `None` results.
4. Add per-template checks: a document with every heading of the template yields no finding; removing one heading yields exactly that `missing required section` finding; the verbatim fenced skeleton of the real template, saved under the companion filename, yields no finding.
5. Add selection tests: `discover_documents` with the default kinds returns the companion kinds for companion files and `issue` for an ordinary Issue; `{"issue"}` excludes companions; `{"unknowns"}` returns only unknowns files; `main(["--kind", "unknowns"])` accepts the choice.
6. Add a live-repository check that `collect_findings` over the companion kinds reports no `missing required section` for files present under `issues/`.

### Method
Follow the existing helper style and naming (`test_<behavior>`); keep each test independent; use `pytest.mark.parametrize` for the filename tables; assert on `finding["detail"]` text for the missing heading, as the existing tests do.

### Details
- The malformed case removes a heading that exists only in the companion template (`Evidence Missing` for unknowns, `Suggested resolution` for risks) so the finding cannot come from the issue template.
- After the tests pass, temporarily disable `companion_kind` in `infer_kind` (revert afterwards) and confirm the new cases fail.

## Compatibility considerations
Test-only change; existing tests keep their assertions apart from the fixture template list.

## Security considerations
N/A: tests write only under `tmp_path`; nothing touches the real `issues/`, `plans/`, or `implementations/`.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_workitem_structure.py -q` and `uv run pytest tests/tools -q -n logical` (the unrelated `test_generated_agent_index_stays_within_the_document_ceiling` failure pre-exists).
- `uv run ruff format --check tests/tools/test_check_workitem_structure.py`, `uv run ruff check tests/tools/test_check_workitem_structure.py`, `uv run mypy tests/tools/test_check_workitem_structure.py`.

## Completion criteria
- All new cases pass, fail when companion detection is removed, and the existing cases still pass.

## Out of Scope
- Tests for other tools; changes to the unrelated failing test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend the fixture template list and add the detection, inference, and selection tests | Pending | — | — | |
| 2 | Add the per-template pass, malformed, and skeleton tests and the live check | Pending | — | — | |
| 3 | Run the tests, the mutation check, ruff, and mypy | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (tests), evidence for `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: issues/20261125-091717_gate001_workitem-structure-companion-kinds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-102213_gate001_workitem-structure-companion-kinds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-104147
- **Related target files**: `tests/tools/test_check_workitem_structure.py`
