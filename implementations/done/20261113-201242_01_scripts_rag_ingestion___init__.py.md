## Goal

`REQ-001`: add `scripts/rag/ingestion/__init__.py` as a regular package marker following the convention of `scripts/rag/__init__.py`, so `rag.ingestion` resolves under the CI mypy invocation and `[tool.setuptools.packages.find]`.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/rag/__init__.py` (Reference Files) is the convention: a `#!/usr/bin/env python3` shebang plus a one-line docstring naming the path and purpose.
- The containing directory `scripts/rag/ingestion/` exists.
- An empty-body package marker changes how mypy and setuptools see `rag.ingestion` but not runtime imports (the directory was already importable as a namespace subpackage of `rag`; UNK-03).

## Design decisions
- Empty body: no symbol is exported from the package root; the marker only makes `rag.ingestion` a regular package.
- Header mirrors `scripts/rag/__init__.py` so `tools/check_docstrings.py` and `tools/fix_docstring_paths.py` accept it.

## Alternatives considered
- N/A: the file must exist for this fix; only its header shape is a choice, fixed by the sibling convention.

## Implementation
### Target file
`scripts/rag/ingestion/__init__.py` (new)

### Procedure
Create the file with the two-line header from `scripts/rag/__init__.py`, adapted to this path.

### Method
1. Line 1: `#!/usr/bin/env python3`
2. Line 2: `"""scripts/rag/ingestion/__init__.py — RAG ingestion package."""`
3. Leave the remainder of the file empty (no imports, no re-exports).

### Details
- The docstring names the file path and that it is the RAG ingestion package, matching `scripts/rag/__init__.py` (`"""scripts/rag/__init__.py — RAG pipeline package."""`).
- Do not import or re-export any submodule; the marker carries no runtime behavior.

## Compatibility considerations
N/A: a package marker changes how mypy and setuptools resolve `rag.ingestion`; runtime imports through `sys.path = scripts/` are unchanged (UNK-03).

## Security considerations
N/A: no request handling, network, or permission change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- After this document and the companion suppression-removal (docs 02–05) and `http_fetcher.py` fix (doc 06) execute, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` passes with no new suppression and no `unused-ignore` (AC-1).
- Adding this marker alone surfaces the four `unused-ignore` (from docs 02–05) and two `arg-type` (doc 06) errors; that is expected and recorded in the Plan Background.
- `uv run python tools/check_docstrings.py` and `tools/fix_docstring_paths.py`: no finding.
- `lint-imports`: the 6-contract baseline unchanged.

## Completion criteria
- `scripts/rag/ingestion/__init__.py` exists with the shebang and a one-line path/purpose docstring.
- `scripts/rag/ingestion/` is now the only former package directory under `scripts/` carrying a marker; no new mypy error is introduced by the marker itself.

## Out of Scope
The four suppression removals (docs 02–05) and the two `http_fetcher.py` typing fixes (doc 06); the mypy invocation itself; the corpus identity change (rmcompat003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-201242 | 20261113-204236 | package marker created per Method |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-201242 | 20261113-204236 | mypy 0 errors (561 files); pytest 353 passed; ruff format clean; lint-imports 0 broken; bandit 0 high/medium; docstrings no new finding |

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
- **Requirement ID**: `REQ-001` (regular package marker for `rag.ingestion`)
- **Source issue**: issues/20261110-171004_rmcompat006_rag-ingestion-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-121532_rmcompat006_rag-ingestion-cleanup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-201242
- **Related target files**: `scripts/rag/ingestion/__init__.py`
