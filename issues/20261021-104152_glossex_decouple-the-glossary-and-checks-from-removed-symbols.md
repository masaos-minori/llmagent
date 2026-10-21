# Decouple the glossary and checks from removed symbols

## Priority
Medium

## Summary
Remove the remaining references to the deleted function `read_json_file()` from the governance documents and a tool comment, and stop the Glossary examples from stating the status of specific code symbols, so they cannot go stale with each removal.

## Background
`read_json_file()` and its private helpers were removed from `scripts/rag/ingestion/pipeline_utils.py` (commit `3d2dc8790`); the name no longer exists in source. It is still used as a live example in three places: the `Obsolete` row of the Glossary in `docs/00_governance/governance_02_documentation-metadata.md`, the description of the context-aware check in `docs/00_governance/governance_04_documentation-checks.md`, and a comment in `tools/check_compat_shims.py`. A name that is absent from source belongs to the other category those texts define, so each example now contradicts its own point. (Confirmed by code: `rg read_json_file docs tools scripts tests` finds exactly these three places)

The earlier work item `issues/done/20261020-123401_compat009_decouple-the-compatibility-glossary-examples-from-specific-code-symbols.md` asked for this and was moved to `issues/done/` by a rename-only commit (`79250e5c7`) with no content change, so the work was never done. Its Backward Compatibility half was handled by the `agent` package re-export removal, which reworded that row to a generic example. The rest remains.

The `Migration` row names `db/schema_sql.py::apply_workflow_migrations()`, which the open removal issue for the `workflow.sqlite` migrations deletes; that example will go stale the same way. The other symbol-specific examples (`Operational Fallback`, `Default`, `Lenient Parsing`) name symbols that currently exist. (Confirmed by code)

## Problem
Glossary rows define terms, but their examples state the current status of specific symbols. Status changes with every refactor, so the examples drift; one already contradicts the definition it illustrates. The governance check text and a tool comment repeat the same example.

## Reason for Change
Stale examples in the documents that define the project's vocabulary mislead readers and tooling that treat the Glossary as authoritative, and each future removal repeats the problem. Keeping status out of the Glossary removes the drift at its source.

## Implementation Intent
Keep the Glossary abstract: definitions plus examples that do not name a symbol whose status can change, and one sentence stating that the Glossary defines terms and is not a register of code status. Replace the `read_json_file` examples in the governance check text and the tool comment with a generic description of the category, since no real example of it is known today. Decide per remaining symbol-specific example between generalizing it and keeping it under an automated reference check; generalizing is the smaller change.

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md` (Glossary rows `Obsolete`, `Migration`, and the other symbol-specific examples; the scope sentence)
- `docs/00_governance/governance_04_documentation-checks.md` (the bullet about a name that remains in source but is no longer the current production path)
- `tools/check_compat_shims.py` (the comment that cites `read_json_file`; comment only)
- `tools/check_glossary_term_classification.py` and its tests (only if the owner chooses an automated reference check)

## Required Changes
- Rewrite the `Obsolete` example so it does not name `read_json_file()` or any specific symbol.
- Rewrite the `Migration` example so it does not depend on `apply_workflow_migrations()`.
- Review the `Operational Fallback`, `Default`, and `Lenient Parsing` examples and either generalize them or keep them under a check that verifies each referenced path and symbol exists.
- Replace the `read_json_file` example in the governance check text and in the tool comment with a description that names no symbol.
- Add one sentence to the Glossary stating that it defines terms and is not a register of code status.
- If a reference check is chosen, extend `tools/check_glossary_term_classification.py`, add tests, describe it in the governance check document, and keep `tools/TOOL_DESCRIPTIONS.md` in sync.

## Constraints
- Do not change any Term or Definition cell.
- The tool change, if any, is a comment edit: no behavior change in `tools/check_compat_shims.py`.
- Documentation stays in English and follows the content-policy check (no implementation-detail duplication).

## Acceptance Criteria
- `rg read_json_file docs tools scripts tests` returns no match.
- No Glossary example states the status of a specific code symbol, or each such example is verified by an automated check.
- The Glossary states its own scope in one sentence.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`, `check_glossary_term_classification.py`, and `check_compat_shims.py` pass; `ruff`, `mypy` (path passed explicitly), and `bandit` pass for any edited tool file.

## Testing Expectations
- Documentation inspection of the changed rows.
- Run the documentation checkers listed above, and `uv run python tools/check_tool_descriptions_sync.py` if a tool changed.
- If a check is added: unit tests, `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the tool file, `uv run bandit` on the tool file, and a smoke run against the real Glossary.

## Documentation Impact
Yes. The Glossary, the governance check description, and nothing else; state intent and category descriptions only, with no history of the removal.

## Out of Scope
- Term and Definition cells; the `Backward Compatibility` row (already reworded).
- Implementing the context-aware "is this presented as current" check that the governance check text calls a follow-up.
- Any other document or code change.

## Dependencies
- The open issue `issues/20261021-102049_rmwfmig_remove-the-workflow.sqlite-incremental-migrations.md` removes `apply_workflow_migrations()`; do this issue before it lands, or update the `Migration` example in the same change as the removal.
- Sibling-issue check: `issues/20261021-100252_gov004fu_decide-the-governance_04-follow-up-work-items-for-gv-009-gv-010-gv-011-gv-017.md` and `issues/20261021-100322_govcompress_decide-the-compression-policy-for-governance_01-and-governance_04.md` also edit `docs/00_governance/governance_04_documentation-checks.md`; apply the edits one after another and re-read the file before each. `issues/20261021-100336_compressverify_detect-enumeration-generalization-without-universal-wording-after-docs-compression.md` may add a rule to the same file. None of them covers this problem.

## Unresolved Questions
- Whether the remaining symbol-specific examples are generalized or kept under an automated reference check (the owner chooses); generalizing is recommended because it needs no tool change.
- Whether a real example of "a name that remains in source but is no longer the current production path" exists today; none is known, so the text should name none.

## AI Implementation Instruction
- Change only the rows, sentence, bullet, and comment named above; keep the diff minimal and do not rewrite other Glossary rows.
- Do not add an inventory of obsolete symbols to documentation.
- Do not change tool behavior; a comment edit only, unless the owner chose the reference check.
- Stop and report if an example turns out to be needed verbatim by another document or test.
- Write documentation in English.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-104152
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/check_compat_shims.py`
