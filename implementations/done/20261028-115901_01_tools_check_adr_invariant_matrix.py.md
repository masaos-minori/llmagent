# Procedure: validate cited nodes by AST and promote the body rules to errors

## Goal

Make the matrix checker verify that every cited `file.py::node` exists, in the index and in ADR bodies, and report body-evidence findings as errors (Plan REQ-003, REQ-004).

## Scope

- Modify only `tools/check_adr_invariant_matrix.py`.
- In scope: node validation, the body-citation scan, `_BODY_RULE_SEVERITY` and the docstring.
- Out of scope: the CI runner, the JSON output shape, tests (row 2), docs.

## Assumptions

- Ordering note: apply the corpus rows (seq 05-09) first; this row's severity promotion must not land while the live run still reports findings (AI instruction of the Issue).
- `.github/run_cited_adr_tests.py` imports the node-id regex from this module, so `_TEST_PATH_RE` keeps its name and shape.
- Cited nodes are plain classes and functions; AST name matching is sufficient (UNK-02 default).
- Overlap (compatible): `plans/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md` edits only the ADR-006 Implementation Notes, while this Plan edits ADR-006's Verification table. Any citation added by that Plan must resolve to an existing test node once the node validation of this Plan is in force.

## Design decisions

- AST scan (no imports, fast) in the checker; the CI runner keeps executing index citations with pytest.

## Alternatives considered

N/A: the Plan fixes the approach (see its Design section).

## Implementation

### Target file

`tools/check_adr_invariant_matrix.py`

### Procedure

- Add `_node_problem(file_part, node)` (new): parse the cited file with `ast` (cache the parsed name set per path), strip a trailing `()` and a `[...]` parameter id from each `::` segment, and return a message when any segment is not a class or function name defined in the file; return `None` otherwise.
- Extend `check_invariant_matrix_test_paths` so, after the existing file-existence check, a present file whose node is missing yields an `ERROR` Issue naming the node.
- Add `check_adr_body_citations(adr_file, lines)` (new) that scans the whole ADR body for backticked `_TEST_PATH_RE` matches (path-less citations fail the file check) and applies the same file and node checks; call it for every `docs/10_adr/adr_*.md` except the index from `collect_issues`.
- Change `_BODY_RULE_SEVERITY` from `"WARNING"` to `"ERROR"` and rewrite the module docstring to state that both body rules and node validation are errors that make the exit code non-zero.
- Keep the JSON keys and the exit-code logic (`1` when any ERROR) in `main`.

### Method

Add two functions and a cache dict; edit one constant and the docstring; no new third-party import (`ast` is standard library).

### Details

- The scan found five unresolved body citations before the corpus rows; after them the live run must report none.
- `tools/check_suppression_justification.py` applies to any new `# nosec` or `# noqa`; none is expected.

## Compatibility considerations

- Stricter gate: a stale citation, an empty evidence cell or a body/index disagreement now fails CI and pre-commit.

## Security considerations

- Read-only parsing with `ast.parse`; no code from cited files is executed or imported.

## Rollback considerations

- Revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/tools/test_check_adr_invariant_matrix.py -q` | Pass |
| 2 | `uv run ruff format tools/check_adr_invariant_matrix.py`; `uv run ruff check tools/check_adr_invariant_matrix.py`; `uv run mypy tools/check_adr_invariant_matrix.py`; `uv run bandit tools/check_adr_invariant_matrix.py` | No finding (`mypy` receives the path explicitly because `pyproject.toml` does not cover `tools/`) |
| 3 | `uv run python tools/check_tool_descriptions_sync.py` | No finding |

## Completion criteria

- A missing node or file in the index or an ADR body is an ERROR; empty cells and disagreements are ERRORs; `uv run python tools/check_adr_invariant_matrix.py` exits 0 on the cleaned corpus.

## Out of Scope

- Corpus edits, the reference checker, the CI runner.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-162007 | 20261028-162007 | Applied after corpus rows and markers; live run clean (exit 0); old HEAD corpus yields the 5 expected body findings |
| 2 | Add or update tests per Validation plan | Completed | 20261028-162007 | 20261028-162007 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261028-162007 | 20261028-162007 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261028-162007 | 20261028-162007 |  |

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
- **Requirement ID**: REQ-003, REQ-004 (node existence for index and ADR bodies; body rules at ERROR)
- **Source issue**: issues/20261027-155848_adrgate005_enforce-adr-evidence-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-093931_adrgate005_enforce-adr-evidence-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-115901
- **Related target files**: tools/check_adr_invariant_matrix.py