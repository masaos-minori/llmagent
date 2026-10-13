## Goal

Obtain the Sudachi dictionary argument for the chunk splitter from the shared resolver instead of the hard-coded `dict="core"` literal, so a compiled binary uses the external dictionary. Implements `REQ-003` / AC-04.

## Scope

Modifies the single `Dictionary(...)` call site in `scripts/rag/ingestion/chunk_splitter.py` (line 81).

## Assumptions

- The splitter constructor calls `sd_dict = sudachi_dict.Dictionary(dict="core")` at line 81 (verified by grep).
- `chunk_splitter.py` already imports `from shared.config_loader import ConfigLoader` and `from sudachipy import dictionary as sudachi_dict`; it may additionally import from `shared.runtime_paths` (leaf package).

## Design decisions

- Replace `dict="core"` with `dict=resolve_sudachi_dict_path()`, reusing the same resolver as `repository.py` so both call sites share identical precedence and fail-fast behavior (AC-04).

## Alternatives considered

- Reading the dictionary path from a config key: rejected — the resolver centralizes the compiled-default and missing-path semantics; keep the call site thin.

## Implementation

### Target file

`scripts/rag/ingestion/chunk_splitter.py`

### Procedure

Replace the `dict="core"` literal at the `Dictionary` call site with the resolver result.

### Method

1. Add `from shared.runtime_paths import resolve_sudachi_dict_path` to the imports.
2. In the splitter constructor, replace `sd_dict = sudachi_dict.Dictionary(dict="core")` with `sd_dict = sudachi_dict.Dictionary(dict=resolve_sudachi_dict_path())`.

### Details

- Keep the call where it currently is (constructor) so the dictionary is bound per splitter instance, matching current behavior.
- Under `uv run` with no env set this returns `"core"`, so existing splitting is unchanged.

## Compatibility considerations

- No constructor-signature change; the dictionary source now follows the resolver.

## Security considerations

- N/A: dictionary selection only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — resolver argument passed through; a patched `resolve_sudachi_dict_path` is used.
- `rg 'dict="core"' scripts/rag/ingestion/chunk_splitter.py` — zero remaining literals.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- The `Dictionary` call passes `resolve_sudachi_dict_path()`; no `dict="core"` literal remains in this file; the splitter test passes.

## Out of scope

- The resolver (`runtime_paths.py`) and the repository call site (`repository.py`) are separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the resolved dictionary to the splitter | Completed | 20261012-183345 | 20261013-100326 |  |
| 2 | Update `tests/rag/ingestion/test_chunk_splitter.py` | Completed | 20261012-183345 | 20261013-100326 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261012-183345 | 20261013-100326 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261012-183345 | 20261013-100326 | N/A |

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
- **Related target files**: scripts/rag/ingestion/chunk_splitter.py