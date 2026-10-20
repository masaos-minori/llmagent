# Decouple the compatibility glossary examples from specific code symbols

## Priority
Low

## Summary
Make the "Compatibility and Lifecycle Terminology" glossary in `docs/00_governance/governance_02_documentation-metadata.md` define terms only, and stop it from being the de facto register of which code is obsolete. Replace the symbol-specific examples with either general examples or examples whose references an automated check keeps valid. Where a specific obsolete item must be tracked, track it in the compatibility manifest of `compat007`, not in the glossary.

## Background
- Source: an investigation of the design documents dated 2026-10-20 that listed backward-compatibility features. It read documents only; the facts below were re-checked against the current documents on 2026-10-20.
- The glossary table has seven terms: Backward Compatibility, Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, and Dead Code. Six of the seven examples name a specific file, function, or docstring; only the Dead Code example is generic. (Explicit in code: read from the document)
- The Backward Compatibility example quotes the module docstring of `scripts/agent/__init__.py`; the Obsolete example names `read_json_file()` in `scripts/rag/ingestion/pipeline_utils.py`. These two are the only places in the glossary that state the status of a specific item. (Explicit in code)
- `tools/check_glossary_term_classification.py` checks only that glossary terms are project-specific words (GV-015). It does not check that an example still refers to something that exists. (Explicit in code)
- No document, rule, or skill defines a "Compatibility Inventory"; a search for the term finds nothing. (Explicit in code: absence verified by search)
- `compat003` and `compat005` remove the two items the glossary currently cites, which would leave both examples stale.

## Problem
A glossary is meant to define words. Here two examples double as the only statement of which code is a compatibility layer or obsolete, so the glossary becomes the register of obsolete code by accident, and it silently goes stale when that code is deleted or changed.

## Reason for Change
Definitions change rarely; the status of a specific symbol changes with every refactor. Mixing them guarantees drift. Keeping status in a machine-checked manifest and keeping the glossary abstract removes the drift and gives obsolete items one authoritative place.

## Implementation Intent
- Keep the term definitions as they are.
- For each example, prefer a general description of the kind of thing the term names. Keep a specific reference only when an automated check verifies that the referenced path or symbol still exists.
- Do not move the status of specific obsolete items into another prose document; they belong in the manifest introduced by `compat007`.
- Describe the glossary's role in one sentence: definitions, not a register of current code status.

## Target Files or Areas
- `docs/00_governance/governance_02_documentation-metadata.md` (the glossary examples and a one-sentence statement of the glossary's scope)
- `docs/00_governance/governance_04_documentation-checks.md` (only if a new check is added; GV-015 and its neighbors)
- `tools/check_glossary_term_classification.py` and its test (only if the owner chooses to verify example references)
- Read for evidence: `docs/00_governance/governance_01_documentation-policy.md`

## Required Changes
- Decide, per example, between a general description and a reference kept valid by a check.
- Rewrite the Backward Compatibility and Obsolete examples so that they do not depend on `scripts/agent/__init__.py` or `read_json_file()`.
- Review the other four symbol-specific examples (Operational Fallback, Default, Lenient Parsing, Migration) and either generalize them or keep them under an automated reference check.
- If references are kept, extend the glossary check to verify that each referenced path and symbol exists, and add tests.
- Add one sentence stating that the glossary defines terms and is not a register of code status.

## Constraints
- Do not change the definitions of the terms.
- Do not copy the manifest or an inventory into the glossary.
- Documentation follows the docs content policy: no implementation-detail inventory, no history; written in English.
- If a check is added, it follows the existing report-only default and `--strict` convention of the glossary check.

## Acceptance Criteria
- No glossary example states the status of a specific code symbol, or each such example is verified by an automated check.
- The glossary no longer cites `scripts/agent/__init__.py`'s docstring or `read_json_file()`.
- The glossary states its own scope in one sentence.
- If a check was added, it has tests and is described in the governance check document.
- The documentation checkers pass, including `check_glossary_term_classification.py` and `check_tool_descriptions_sync.py` when a tool changed.

## Testing Expectations
- Documentation inspection of the changed rows.
- If a check is added: unit tests, `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the tool with the path passed explicitly, `uv run bandit` on the tool, and a smoke run against the real glossary.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py --strict`, and `uv run python tools/check_glossary_term_classification.py`.

## Documentation Impact
Yes. Rewrite the glossary examples and add the one-sentence scope statement (intent and boundaries). No history of the removed examples is recorded.

## Out of Scope
- Changing the term definitions or adding new terms.
- Creating a prose Compatibility Inventory; tracking belongs to `compat007`.
- Removing the obsolete code itself (`compat003`, `compat005`).

## Dependencies
- Should be done before `compat003` and `compat005`, so that neither removal leaves a stale glossary example behind; if done after, those issues must update the rows themselves.
- Related: `compat007` provides the manifest that replaces the glossary as the register of specific items.
- Sibling-issue check: no open issue under `issues/` touches `governance_02` or the glossary check.

## Unresolved Questions
- Should the remaining symbol-specific examples be generalized, or kept under an automated reference check? (Needs confirmation; the owner chooses)

## AI Implementation Instruction
- Do not change any term definition.
- Do not create an inventory in documentation; if a specific item needs tracking, point to `compat007` instead.
- Change only the glossary rows, the scope sentence, and, if chosen, the glossary check with its tests and descriptions.
- Run the commands in Testing Expectations before finishing.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261020-123401
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`, `docs/00_governance/governance_04_documentation-checks.md`, `tools/check_glossary_term_classification.py`
