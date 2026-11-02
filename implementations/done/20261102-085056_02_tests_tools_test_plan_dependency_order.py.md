## Goal
- Add unit tests for `tools/plan_dependency_order.py` covering the structured line, the prose fallback, graph order, cycles, and readiness (`REQ-001`, `REQ-002`).

## Scope
- In scope: the new test module with fixture Plans written under `tmp_path`.
- Out of scope: tests for `manage_workitem_stage.py` (row 04) and the live smoke run (row 01 validation).

## Assumptions
- Row 01 creates `tools/plan_dependency_order.py` and its functions (`parse_dependencies`, `load_plans`, `resolve_dependency`, `find_cycles`, `recommended_order`, `readiness`, `main`); this module imports them and exists only after row 01 runs, which `code-implementation` guarantees by `seq` order.
- Step 3a verified: `tests/tools/` holds one test module per tool and imports as `import tools.<module> as alias`; `tests/tools/test_check_plan_target_overlaps.py` writes fixture Plans through a `_write` helper and a `_plan_text` factory, the pattern reused here.
- Overlap (Step 2): no other Plan targets this new file.
- Names that only the row 01 procedure creates (`parse_dependencies`, `load_plans`, `resolve_dependency`, `recommended_order`) will exist when `code-implementation` executes the rows in `seq` order.

## Design decisions
- Fixtures build a tiny repository under `tmp_path` (`plans/`, `plans/done/`, `issues/`, `issues/done/`) and call the functions with `root=tmp_path`; no test touches the live `plans/`.

## Alternatives considered
- N/A: a single plain pytest module matches the repository convention.

## Implementation
### Target file
`tests/tools/test_plan_dependency_order.py` (new)

### Procedure
- Add a `_plan(tmp_path, name, scope_lines, targets, status_rows)` helper (new) that writes a minimal Plan with `## Scope`, `## Implementation Target Files` (`Frozen`), and `### Execution Status`.
- Add the test cases below, each named for the behavior.

### Method
- Parser: a structured `**Depends on**` bullet yields path, phase, reason, no warning; `N/A: none` yields nothing; a prose `Dependencies` sentence naming a `plans/` path yields phase `all` plus a `prose-dependency` warning; a structured bullet wins over prose in the same Plan.
- Readiness (parametrized): dependency on an Issue in `issues/` is `gated` naming the path; Issue in `issues/done/` is `ready`; Plan in `plans/` with the named phase row `Pending` is `gated` with the phase; same row `Completed` is `ready`; Plan in `plans/done/` is `ready`; a missing path is reported `Needs confirmation` and the Plan is not silently `ready`-without-notice.
- Order: three Plans in a chain are ordered dependency first; independent Plans are ordered by filename timestamp; a Plan outside any edge keeps its timestamp position.
- Cycle: two Plans depending on each other, and a three-Plan loop, are each reported with the cycle path; the tool still exits 0.
- Overlap: two Frozen Plans sharing a target appear as an `overlap` note and add no edge.
- Read-only and CLI: `main(["--root", str(tmp_path)])` leaves the fixture directory byte-identical (compare a hash of every file before and after) and the header contains `owner decides`; `--plan` for a missing path returns 1; `--format json` output parses with `json.loads`.

### Details
- Use `pytest.mark.parametrize` for the readiness matrix; use `capsys` for `main` output.
- Do not mock `check_plan_target_overlaps`; run it against the fixture directory so the reuse is exercised.

## Compatibility considerations
- N/A: new test module, no shared fixtures or conftest changes.

## Security considerations
- N/A: tests write only under `tmp_path`. One case asserts a dependency path escaping the root (`../x.md`) is reported `Needs confirmation` and not read.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_plan_dependency_order.py -v`, then the targeted tools suite `uv run pytest tests/tools -q`.
- `uv run ruff format tests/tools/test_plan_dependency_order.py`; `uv run ruff check tests/tools/test_plan_dependency_order.py`.

## Completion criteria
- Every case above exists and passes; the module covers parser (both forms), readiness (open Issue, open Plan phase, closed, missing), order, cycles, overlap notes, and the read-only property.

## Out of Scope
- Tests of the order view (row 04) and of skill text (rows 07, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the tests described in Implementation > Procedure/Method/Details | Completed | 20261102-101500 | 20261102-101710 | Files: tests/tools/test_plan_dependency_order.py (34 tests). No procedure correction needed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-101710 | 20261102-101710 | Run the validation sequence ruff format/check clean, mypy on the file clean, check_mock_patch_targets clean; check_suppression_justification reports 2 pre-existing findings in other files. Full suite deferred to plan end |

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
- **Requirement ID**: REQ-001, REQ-002 (parser, fallback, graph, cycle, readiness tests)
- **Source issue**: issues/20261030-191144_flowimp003_plan-dependency-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080134_flowimp003_plan-dependency-gate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085056
- **Related target files**: tests/tools/test_plan_dependency_order.py