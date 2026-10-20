# Remove the unused obsolete read_json_file reader

## Priority
Medium

## Summary
Delete `read_json_file()` from `scripts/rag/ingestion/pipeline_utils.py` together with any helper that only it used, and update the two places that cite it as an example of an obsolete name that remains in source. The strict readers `read_chunk_json()` and `read_crawl_json()` stay as the only readers.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility candidates. It read documents only; the facts below were re-checked against the current code on 2026-10-20.
- `read_json_file(path)` reads a chunk file through the lenient helper `_read_chunk_json_raw()`, raises `ChunkFormatError` only when that helper returns nothing, and fills missing fields with defaults (empty title, language `en`, chunk index `0`, empty source file and chunk type, strategy `text`). It still requires `fetched_at`. (Explicit in code)
- The current production readers, `read_chunk_json()` and `read_crawl_json()`, are strict: they raise `ChunkFormatError` on any read, parse, or validation failure. (Explicit in code)
- A search of `scripts/`, `tests/`, and `tools/` finds no call to `read_json_file`. It appears only in the Glossary row for Obsolete in `docs/00_governance/governance_02_documentation-metadata.md`, in the description of the removed-name check in `docs/00_governance/governance_04_documentation-checks.md`, and in a comment in `tools/check_compat_shims.py`. (Explicit in code)
- `_read_chunk_json_raw`, `_get_str_with_default`, and `_get_int_with_default` are referenced only inside `pipeline_utils.py`; whether `read_json_file()` is their only caller was not verified and must be rechecked when it is removed. (Needs confirmation)
- The documentation example is about the removed-name check design: a name that remains in source but is no longer the current production path needs a context-aware check that is "not yet implemented (follow-up)". Removing the function removes that concrete example.

## Problem
A second, lenient chunk reader with different defaults and failure semantics sits beside the strict one and has no caller. A future change could pick it up by mistake and accept chunk files the strict readers reject. It is also the one concrete example the documentation gives of an obsolete name that stays in source.

## Reason for Change
Dead code with different validation semantics is a correctness hazard and misleads readers about which reader is current. Removing it leaves one reader contract and lets the obsolete-name documentation describe the rule in general terms instead of pointing at a function that exists only to be an example.

## Implementation Intent
- Remove `read_json_file()` and every helper that has no other caller after its removal; keep all other helpers.
- Do not make the strict readers lenient, and do not re-create the lenient defaults elsewhere.
- Replace the symbol-specific examples in `governance_04` and in the `tools/check_compat_shims.py` comment with a general description of the rule, so the documentation does not depend on a deleted name.
- Leave the Glossary row to `compat009`.

## Target Files or Areas
- `scripts/rag/ingestion/pipeline_utils.py` (remove `read_json_file()` and helpers that become unused)
- `tests/rag/ingestion/test_pipeline_utils_strict.py` (a test that the lenient reader is gone; read the existing tests for style)
- `docs/00_governance/governance_04_documentation-checks.md` (the removed-name check description)
- `tools/check_compat_shims.py` (the explanatory comment only; no behavior change)
- `docs/00_governance/governance_02_documentation-metadata.md` (Glossary row; owned by `compat009`)

## Required Changes
- Remove `read_json_file()` from `pipeline_utils.py`.
- Recheck `_read_chunk_json_raw`, `_get_str_with_default`, `_get_int_with_default`, and `ChunkJsonRaw`; remove those left without a caller and keep the rest.
- Add a test asserting that `pipeline_utils` no longer defines `read_json_file`.
- Reword the example in `governance_04` and the comment in `tools/check_compat_shims.py` so neither names the removed function; keep the described rule unchanged.
- Run the RAG ingestion tests and the documentation and tool checks.

## Constraints
- No change to the behavior or error handling of `read_chunk_json()` and `read_crawl_json()`.
- Do not change the logic of `check_compat_shims.py`, only its comment.
- Documentation follows the docs content policy: current specification only, no history of the removal; written in English.
- Follow `rules/coding.md`; do not use a suppression comment to keep an unused helper.

## Acceptance Criteria
- `pipeline_utils.py` does not define `read_json_file`, and no helper that only it used remains.
- A test fails if `read_json_file` is restored.
- `governance_04` and the comment in `tools/check_compat_shims.py` no longer name `read_json_file` and still describe the rule.
- The RAG ingestion tests, ruff, and `uv run mypy --no-namespace-packages` pass.
- `uv run python tools/check_compat_shims.py --check-removed-names` and the documentation checkers pass.

## Testing Expectations
- New regression test for the removed reader.
- `uv run pytest tests/rag/ingestion`, `uv run mypy --no-namespace-packages`, `uv run ruff check`, `uv run python tools/check_compat_shims.py --check-removed-names`, `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, and `uv run python tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. Reword the removed-name check description in `governance_04` without the deleted symbol (intent and constraints only). The Glossary row is handled by `compat009`.

## Out of Scope
- Changing the strict readers or the chunk file format.
- Implementing the context-aware check for names that remain in source (`compat007`).
- The Glossary row for Obsolete (`compat009`).
- The other items from the same investigation.

## Dependencies
- Related: `compat009` replaces the Glossary example, and `compat007` designs how obsolete names that remain in source are tracked; neither blocks this change, but the three edit overlapping governance text and should be merged in a consistent order.
- Sibling-issue check: no open issue under `issues/` touches `scripts/rag/ingestion/pipeline_utils.py`.

## Unresolved Questions
- Does any script outside the repository import `read_json_file`? The function is public in a package that is distributed, so the repository cannot rule it out. (Needs confirmation)
- Does anything beyond `read_json_file()` call `_read_chunk_json_raw`, `_get_str_with_default`, or `_get_int_with_default`? (Needs confirmation; recheck at removal)

## AI Implementation Instruction
- Remove only `read_json_file()` and the helpers that become unused; do not touch the strict readers.
- Keep the described rule in `governance_04` and the comment in `check_compat_shims.py`; change only the wording that names the removed function.
- If any caller of `read_json_file` turns up, stop and report it instead of deleting.
- Run the commands in Testing Expectations before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123044
- **Related target files**: `scripts/rag/ingestion/pipeline_utils.py`, `tests/rag/ingestion/test_pipeline_utils_strict.py`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/check_compat_shims.py`, `docs/00_governance/governance_02_documentation-metadata.md`
