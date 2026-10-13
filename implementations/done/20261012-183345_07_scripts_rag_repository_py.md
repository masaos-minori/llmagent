## Goal

Obtain the Sudachi dictionary argument for `_SudachiTokenizer` from the shared resolver instead of the hard-coded `dict="core"` literal, so a compiled binary uses the external dictionary. Implements `REQ-003` / AC-04.

## Scope

Modifies the single `Dictionary(...)` call site in `scripts/rag/repository.py` inside `_SudachiTokenizer._ensure_loaded`.

## Assumptions

- `_SudachiTokenizer` calls `_sd_dict.Dictionary(dict="core")` at line 55 (verified by grep).
- `repository.py` must not import from `agent` (`.importlinter` contract `rag-no-agent-or-mcp_servers`); importing from `shared.runtime_paths` is allowed because `shared` is a leaf.

## Design decisions

- Call `resolve_sudachi_dict_path()` once and pass its result as the `dict` argument: `Dictionary(dict=resolve_sudachi_dict_path())`. The function returns either a `Path` (env or compiled default) or the string `"core"` (uncompiled dev), which `Dictionary` accepts in both cases.

## Alternatives considered

- Passing the env var through from a config key: rejected — the RAG server is not restricted like the MCP servers, but the resolver centralizes the fail-fast semantics (AC-05) and the compiled default.

## Implementation

### Target file

`scripts/rag/repository.py`

### Procedure

Replace the `dict="core"` literal at the `Dictionary` call site with the resolver result.

### Method

1. Add `from shared.runtime_paths import resolve_sudachi_dict_path` to the imports.
2. In `_SudachiTokenizer._ensure_loaded`, replace `_sd_dict.Dictionary(dict="core")` with `_sd_dict.Dictionary(dict=resolve_sudachi_dict_path())`.

### Details

- Keep the call inside `_ensure_loaded` (lazy, once per tokenizer) rather than at module import, matching the current placement.
- Under `uv run` with no env set this returns `"core"`, so existing tokenization is unchanged.

## Compatibility considerations

- No signature or behavior change for callers of `_SudachiTokenizer`; the dictionary source now follows the resolver.

## Security considerations

- N/A: dictionary selection only; the fail-fast on a missing path prevents a silent fallback to an un-bundled dictionary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_repository.py` — resolver argument passed through; a patched `resolve_sudachi_dict_path` is used (a real tiny dictionary is not required).
- `rg 'dict="core"' scripts/rag/repository.py` — zero remaining literals.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run lint-imports` clean.

## Completion criteria

- The `Dictionary` call passes `resolve_sudachi_dict_path()`; no `dict="core"` literal remains in this file; the repository test passes.

## Out of scope

- The resolver (`runtime_paths.py`) and the splitter call site (`chunk_splitter.py`) are separate documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the resolved dictionary to `_SudachiTokenizer` | Completed | 20261012-183345 | 20261013-100326 |  |
| 2 | Update `tests/rag/test_rag_repository.py` | Completed | 20261012-183345 | 20261013-100326 |  |
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
- **Related target files**: scripts/rag/repository.py