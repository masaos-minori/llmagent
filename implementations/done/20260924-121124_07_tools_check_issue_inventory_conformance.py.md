## Goal
Add module-level `REPO_ROOT`/`DOCS_DIR`/`GOVERNANCE_DOC_PATH` constants to
`tools/check_issue_inventory_conformance.py` and switch `main()`'s default `doc_path`
to `GOVERNANCE_DOC_PATH`, so the tool resolves the governance document at its
post-move location instead of the flat pre-move path, implementing `REQ-003`.

## Scope
In scope: adding the 3 new module-level constants and replacing the inline default-path
expression inside `main()` with a reference to `GOVERNANCE_DOC_PATH`. Out of scope: any
other change to this file's parsing/validation logic, CLI argument handling, or output
format.

## Assumptions
- `main()`'s default `doc_path` currently computes
  `Path(__file__).parent.parent / "docs" / GOVERNANCE_DOC_NAME` inline, with no existing
  `REPO_ROOT`/`DOCS_DIR` module constant in this file — confirmed via `grep -n
  "^REPO_ROOT\|^DOCS_DIR"` (zero matches) and reading `main()`.
- This file was added 2026-09-17, before `docsreorg02`'s 2026-09-24 subfolder-aware
  refactor, and was not one of that Plan's 9 updated tools — confirmed via `git log
  --oneline --diff-filter=A -- tools/check_issue_inventory_conformance.py` and reading
  `plans/done/20260923-152824_plan.md`'s Requirements list.
- Sibling tools `tools/check_dependency_graph_cycles.py` (`GRAPH_DOC_PATH`),
  `tools/check_needs_confirmation_inventory.py` (`INVENTORY_DOC_PATH`), and
  `tools/check_known_deviation_sync.py` (`_GOVERNANCE_KNOWN_ISSUES_PATH`) already use
  the `DOCS_DIR / "00_governance" / <NAME>` pattern this row mirrors.

## Design decisions
- Reuse the existing `GOVERNANCE_DOC_NAME` constant (already defined as
  `"00_governance_03_issue-and-uncertainty-management.md"`) as the basename component of
  the new `GOVERNANCE_DOC_PATH` — do not introduce a second, differently-named constant
  for the same basename.
- Name the new constants `REPO_ROOT`, `DOCS_DIR`, `GOVERNANCE_DOC_PATH` to match the
  exact naming convention already used by `tools/check_dependency_graph_cycles.py` and
  `tools/check_needs_confirmation_inventory.py`, rather than inventing a new naming
  scheme for this file.

## Alternatives considered
- Keep the inline expression in `main()` and only change its literal string from
  `"docs"` to `"docs/00_governance"`: rejected — this would not produce a testable
  module-level constant, unlike the 3 sibling tools' pattern, and would make `REQ-004`'s
  real-repo-path regression test (seq 08) unable to import and assert against a stable
  symbol.
- Compute the path via `tools/check_docs_structure.py`'s basename-index resolution
  instead of a hardcoded subfolder constant: rejected — out of scope for this row (a
  much larger refactor of this tool's CLI contract), and inconsistent with how the 3
  sibling tools already solve the identical problem.

## Implementation
### Target file
`tools/check_issue_inventory_conformance.py`

### Procedure
1. In the "Document structure constants" section (immediately after the existing
   `GOVERNANCE_DOC_NAME` assignment), add:
   ```python
   REPO_ROOT = Path(__file__).resolve().parent.parent
   DOCS_DIR = REPO_ROOT / "docs"
   GOVERNANCE_DOC_PATH = DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME
   ```
2. In `main()`, replace:
   ```python
   doc_path = (
       Path(args.doc_path)
       if args.doc_path
       else Path(__file__).parent.parent / "docs" / GOVERNANCE_DOC_NAME
   )
   ```
   with:
   ```python
   doc_path = Path(args.doc_path) if args.doc_path else GOVERNANCE_DOC_PATH
   ```
3. Leave every other line of `main()` (document parsing, issue collection,
   `report_and_exit` call) unchanged.

### Method
Two localized edits: one constant-block addition, one expression replacement inside
`main()`. No change to `argparse` configuration, no change to any function signature.

### Details
- `Path` is already imported (`from pathlib import Path`) — no new import is required.
- Place the 3 new constants after `GOVERNANCE_DOC_NAME` and before
  `REMOVAL_PLACEHOLDER_RE`, matching the section's existing "Document structure
  constants" grouping comment.
- Do not rename or remove `GOVERNANCE_DOC_NAME` — it remains used elsewhere in this file
  (e.g. `DocFile(..., rel_path=GOVERNANCE_DOC_NAME, ...)` inside `main()`, and in test
  fixtures per seq 08's target file), so `GOVERNANCE_DOC_PATH` must be built from it,
  not replace it.
- An explicit CLI argument (`args.doc_path`) continues to take precedence over the
  default — this row does not change that precedence, only what the no-argument default
  resolves to.

## Compatibility considerations
`.github/workflows/governance-docs-consistency.yml`'s "Check issue inventory
conformance" step invokes `python tools/check_issue_inventory_conformance.py` with no
argument — after this change, that invocation resolves the moved file correctly instead
of raising `FileNotFoundError`. No caller currently passes an explicit `doc_path`
argument (confirmed via `grep` across `.github/workflows/` and `.pre-commit-config.yaml`
— this tool is CI-only, not a pre-commit hook), so no caller-side change is required.

## Security considerations
N/A: a path-constant change with no new file I/O target outside the repository, no new
external input, and no change to how untrusted input is handled.

## Rollback considerations
Revert the 2 edits via `git checkout -- tools/check_issue_inventory_conformance.py`, or
`git revert` the commit containing this change if already committed. A rollback of this
row without also reverting seq 01/03's `git mv` would leave the default pointing at the
now-nonexistent flat path again (the original bug); a rollback of this row while seq
01/03 remain landed would similarly reintroduce the `FileNotFoundError` this Plan exists
to fix — this row's rollback is only safe when seq 01, 03, and seq 08 (the regression
test) are rolled back together.

## Validation plan
- `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q` passes,
  including seq 08's new real-repo-path regression test (Plan `AC-6`).
- Manual smoke test: `uv run python tools/check_issue_inventory_conformance.py` (no
  argument) against the post-move repository tree, confirming it resolves
  `GOVERNANCE_DOC_PATH` and runs without `FileNotFoundError` (Plan `AC-6`).
- `uv run ruff format tools/check_issue_inventory_conformance.py`, `uv run ruff check
  tools/check_issue_inventory_conformance.py --fix`, then `uv run ruff check
  tools/check_issue_inventory_conformance.py` (confirm clean) — per `routing.md`
  "Adding a new tool"'s lighter `tools/*.py` validation sequence (this file lives under
  `tools/`, not `scripts/`, so `rules/toolchain.md`'s full sequence does not apply).
- `uv run mypy tools/check_issue_inventory_conformance.py` (pass the file path
  explicitly — `pyproject.toml`'s mypy `files` scope covers `scripts/` by default, not
  `tools/`).
- `uv run bandit tools/check_issue_inventory_conformance.py`.

## Completion criteria
`tools/check_issue_inventory_conformance.py` defines `REPO_ROOT`, `DOCS_DIR`, and
`GOVERNANCE_DOC_PATH` as module-level constants; `main()`'s default `doc_path` resolves
to `GOVERNANCE_DOC_PATH`; running the tool with no argument against the post-move
repository tree exits without `FileNotFoundError`; `ruff`/`mypy`/`bandit` report no new
findings for this file.

## Out of scope
Any change to this file's parsing logic (`PART1_*_VALUES`, entry-parsing helpers,
vocabulary/field-count/orphaned-bullet/closing-summary/referential-integrity checks);
any change to its CLI argument surface beyond the default-path resolution; any change to
`.github/workflows/governance-docs-consistency.yml` (the CI step itself needs no edit,
since it already invokes this tool with no argument).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `REPO_ROOT`/`DOCS_DIR`/`GOVERNANCE_DOC_PATH` constants; switch `main()`'s default `doc_path` to `GOVERNANCE_DOC_PATH` | Completed | 20260924-122736 | 20260924-122736 | Added REPO_ROOT/DOCS_DIR/GOVERNANCE_DOC_PATH constants; switched main()'s default doc_path to GOVERNANCE_DOC_PATH. ruff format/check, mypy, bandit all pass clean (bandit: 0 issues, 364 lines scanned). |
| 2 | N/A: test coverage for this change is seq 08's separate implementation procedure document | Completed | 20260924-122736 | 20260924-122736 | N/A: test coverage for this change is seq 08's separate implementation procedure document (existing 20 tests re-run below to confirm no regression from this row alone). |
| 3 | Run `ruff format`/`ruff check`/`mypy`/`bandit` against this file, then `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q` and the manual smoke test | Completed | 20260924-122736 | 20260924-122736 | uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q: 20 passed, no regression. Manual smoke test: uv run python tools/check_issue_inventory_conformance.py (no argument) now resolves GOVERNANCE_DOC_PATH and runs against the moved file -- no FileNotFoundError (AC-6 met). Exit code 1 with 61 findings is a pre-existing, unrelated governance-inventory content-quality condition (invalid Owner values, field-count mismatches, unresolved Related IDs) -- identical content to before the move, out of scope for this Plan per Step-Level Failure Triage, not fixed here. |
| 4 | N/A: no documentation update — this tool's docstring already describes its purpose without a path-specific claim | Completed | 20260924-122736 | 20260924-122736 | N/A: no docs/00_index.md task-scope mapping for tools/*.py; this tool's own docstring already describes its purpose without a path-specific claim needing an update. |

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
- **Requirement ID**: `REQ-003` (add `GOVERNANCE_DOC_PATH` and switch `main()`'s default)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: tools/check_issue_inventory_conformance.py