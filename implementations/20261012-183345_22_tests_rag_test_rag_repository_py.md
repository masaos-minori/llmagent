## Goal

Update `tests/rag/test_rag_repository.py` so the `_SudachiTokenizer` dictionary argument comes from the resolver, verifying the resolver argument is passed through. Implements `REQ-003` / AC-04.

## Scope

Modifies `tests/rag/test_rag_repository.py`: assert that `_SudachiTokenizer` obtains its `dict` argument from `resolve_sudachi_dict_path()` rather than the hard-coded `"core"` literal.

## Assumptions

- `repository.py` calls `Dictionary(dict=resolve_sudachi_dict_path())` (see its row).
- A real tiny Sudachi dictionary is not required; the resolver can be patched.

## Design decisions

- Patch `shared.runtime_paths.resolve_sudachi_dict_path` to return a sentinel `Path` and assert the `Dictionary` call receives it (argument-passing verification).
- Alternatively assert that with `LLMAGENT_SUDACHI_DICT` unset and uncompiled, the tokenizer uses `"core"`.

## Alternatives considered

- Using a real dictionary: rejected — unnecessary; the resolver returns a path or `"core"`, fully unit-testable.

## Implementation

### Target file

`tests/rag/test_rag_repository.py`

### Procedure

Add/adjust a case verifying the resolver argument is passed to `Dictionary`.

### Method

1. Patch `shared.runtime_paths.resolve_sudachi_dict_path` to return a temp `Path` and assert `_SudachiTokenizer` constructs `Dictionary` with that argument.
2. Add a case asserting the uncompiled, unset default yields `"core"`.

### Details

- Use `monkeypatch` to patch the resolver on the module the test imports from.

## Compatibility considerations

- Preserve existing repository cases.

## Security considerations

- N/A: dictionary selection only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_repository.py` — resolver argument passed through; `"core"` default case passes.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` clean.

## Completion criteria

- `test_rag_repository.py` verifies the resolver argument is passed to `Dictionary`; the suite passes.

## Out of scope

- The resolver (`scripts/shared/runtime_paths.py`) and the splitter call site (`chunk_splitter.py`) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the resolver argument is passed to `Dictionary` | Pending | — | — | |
| 2 | Add the `"core"` default case | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260717-171259_nuitka_onefile_packaging_proposal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-104451_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183345
- **Related target files**: tests/rag/test_rag_repository.py
