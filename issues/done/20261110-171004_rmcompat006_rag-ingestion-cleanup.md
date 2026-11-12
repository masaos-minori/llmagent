# Clean up the RAG ingestion tools: duplicate-module suppressions, tolerant reads, and stale names

## Priority
Medium

## Summary
Remove or justify the `# type: ignore` comments that blame a duplicate module path, replace the tolerant `getattr` reads and the duplicate import in the crawler entry point, and make the ingestion docstrings and comments describe the current files, CLI, and configuration model.

## Background
- Source: `memo-issue.md` item M-01 (consolidated version), re-checked against current source on 2026-11-10.
- `Explicit in code`: four `# type: ignore[no-any-return]` comments (in `scripts/rag/ingestion/ingester.py`, `chunk_preparation.py`, `chunk_splitter.py`, and `crawler.py`) say mypy loses a correct return type "across the rag.* vs scripts.rag.* dual module-path resolution" and point to `scripts/shared/tool_constants.py`. A search of `scripts/` and `tests/` found no import of the form `scripts.rag...` in Python code, and `scripts/shared/tool_constants.py` contains no mention of a duplicate module name, so the cross-reference is dangling and the claimed dual import path is not visible in the code.
- `Verified by test` (measured 2026-11-10): with the CI invocation, `mypy` passes as committed; with the four `# type: ignore[no-any-return]` comments removed it reports four `no-any-return` errors ("Returning Any from function declared to return ..."), one per comment. The suppressions are therefore needed today, and the callers import the callees as `rag.ingestion...`, so the stated cause (a dual module path) is not supported by the code; the actual cause of the `Any` is `Needs confirmation`.
- `rules/toolchain.md` and `rules/coding.md` say mypy must be run as `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, because without the flag mypy resolves `scripts/` modules under two names and judges ignore comments differently; `pyproject.toml` sets `mypy_path = "scripts"` and `warn_unused_ignores = true`.
- `Explicit in code`, in `scripts/rag/ingestion/crawler.py`: `main()` reads `getattr(args, "targets_file", None)` twice although `--targets-file` is always added to the parser; `ConfigLoader` is imported at module top and again inside the `__main__` block; the module docstring names `Crawler.py`, `ChunkSplitter.py`, and `RagIngester.py`, which do not exist (the modules are `crawler.py`, `chunk_splitter.py`, `ingester.py`); `chunk_splitter.py` and `ingester.py` repeat the old names in their docstrings.
- `Explicit in code`: comments in `crawler.py` and `ingester.py` say their DB settings are stored "explicitly to bypass build_db_config() / agent.toml" (or "bypasses build_db_config"). Under ADR-002 each tool reads its own configuration file (`config/ingester.toml`, `config/crawler.toml`), so this is the normal design, not a bypass.

## Problem
- If the suppressions are not needed under the CI mypy invocation, they hide real typing errors (`warn_unused_ignores` would flag them only when they are unused); if they are needed, the stated reason is not verifiable and its reference is dangling.
- A tolerant `getattr` read turns a renamed CLI argument into a silent `None` instead of a failure.
- Docstrings that name files that do not exist tell readers to run commands that fail; "bypass" wording makes the normal configuration model look unusual.

## Reason for Change
- The current-only policy (`compatrm001`) and the suppression rules in `rules/coding.md` require a justified, verifiable reason for each suppression. No external deadline; the wrong file names in the docstrings are the only item that can lead a reader to a failing command.

## Implementation Intent
- Each ingestion module is imported by one name, and no suppression rests on an unverifiable claim.
- The ingestion tools' code, docstrings, and comments describe the current modules, CLI, and configuration model.
- Keep ingestion and crawling behavior unchanged.

## Target Files or Areas
- `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_preparation.py`
- `scripts/shared/tool_constants.py` (the dangling cross-reference target)
- `pyproject.toml` and the import-linter contract only if a missing rule is found necessary
- `tests/rag/ingestion/` tests that cover the crawler entry point

## Required Changes
- Find why mypy sees `Any` at the four call sites (for example an untyped attribute or a callee resolved as untyped) and fix that cause so the four suppressions can be removed.
- If the cause cannot be fixed within these files, keep the suppression with the verified reason instead of the dual-path claim; remove the dangling cross-reference either way.
- If a second import name for `rag` modules is found while investigating, choose one import root, update imports, and add a lint rule (import-linter or ruff) that rejects the other.
- Replace `getattr(args, "targets_file", None)` with `args.targets_file`, and remove the second `ConfigLoader` import.
- Update the module docstrings to the real module names and commands.
- Reword the "bypass" comments to say that the settings come from `ingester.toml` / `crawler.toml` (ADR-002).

## Constraints
- Do not add a new suppression without an error code and justification (`rules/coding.md` Suppression governance).
- Do not change the mypy invocation used by CI and pre-commit.
- `scripts/rag/ingestion/ingester.py` is also edited by `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`; implement that issue first or keep the edits non-overlapping.

## Acceptance Criteria
- `rg -n "rag\.\* vs scripts\.rag\.\*|getattr\(args|Crawler\.py|ChunkSplitter\.py|RagIngester\.py|bypasses? build_db_config" scripts/rag/ingestion/` returns nothing.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` passes with no new suppression and no `unused-ignore` error.
- `scripts/shared/tool_constants.py` is not cited as the explanation for a suppression unless it contains that explanation.
- If a dual import path was found, the lint rule rejecting the second path passes and fails on a deliberate bad import in a test.
- Existing ingestion and crawler tests pass.

## Testing Expectations
- Run `tests/rag/ingestion/` and the crawler entry-point tests; add a test that `--url` together with `--targets-file` still exits with the parser error.
- Run `rules/toolchain.md` validation (ruff, mypy with `--no-namespace-packages`, import-linter, bandit, pytest) and `uv run python tools/check_suppression_justification.py`.

## Documentation Impact
- Documentation does not need a content change unless a `docs/21_rag/` document names the old file names or the "bypass" model (found by search; then fix it in the same change). Run the `docs/` checkers in `routing.md` if a document changes.

## Out of Scope
- The RAG delegation leftovers and the ingester lifecycle (`issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md`).
- Changing ingestion, chunking, or crawling behavior.
- The unrelated "bypass this helper" wording in `scripts/rag/ingestion/document_manager.py`.

## Dependencies
- Depends on `issues/20261110-170632_rmcompat001_rag-delegation-leftovers.md` for ordering (same `scripts/rag/ingestion/ingester.py`).
- Blocks the history-comment sweep issue in this batch (`issues/20261110-171040_rmcompat007_history-comment-sweep.md`).

## Unresolved Questions
- `Needs confirmation`: the actual cause of the `Any` at the four call sites (the four suppressions are needed today; the dual-path claim is unsupported).
- `Needs confirmation`: whether a lint rule is worth adding if no second import name is found (acceptance covers only the case where one is found).

## AI Implementation Instruction
- Measure first: determine with the CI mypy invocation whether each suppression is needed before editing.
- Change only the ingestion modules, `tool_constants.py` (the dangling reference), and their tests.
- Do not alter runtime behavior; stop and report if removing a suppression exposes a real typing error that needs a code change outside these files.
- Keep comments and log text in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261110-171004
- **Related target files**: `scripts/rag/ingestion/crawler.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/ingestion/chunk_preparation.py`, `scripts/shared/tool_constants.py`
