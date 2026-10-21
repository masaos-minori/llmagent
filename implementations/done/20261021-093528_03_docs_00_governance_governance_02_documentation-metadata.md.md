## Goal
Reword the Example cell of the `Backward Compatibility` Glossary row so it no longer quotes the removed `scripts/agent/__init__.py` docstring and does not state the status of a specific code symbol (REQ-006).

## Scope
- In: `docs/00_governance/governance_02_documentation-metadata.md`, the Example cell of the `Backward Compatibility` row (line 122).
- Out: the Term and Definition cells; every other row, including the `Obsolete` row naming `read_json_file()` (a different, already removed symbol); any Glossary tool.

## Assumptions
- Row 01 removes the docstring being quoted; this edit lands in the same change.
- `tools/check_glossary_term_classification.py` inspects Glossary terms (first cell), not Example text.

## Design decisions
- The new Example is a generic description with no file path, symbol name, or "current status" claim, so it cannot drift with a refactor.

## Alternatives considered
N/A: keeping a file-specific example was rejected because `compat009` aims to decouple Glossary examples from code symbols.

## Implementation
### Target file
`docs/00_governance/governance_02_documentation-metadata.md`

### Procedure
1. Edit only the Example cell of the `Backward Compatibility` row.
2. Run the docs checkers named in Validation plan.

### Method
- New Example text (English, no file path or symbol): "A package `__init__.py` that re-exports names from its submodules so that callers' old import statements keep working after the modules are reorganized."
- Docs are written in English (`skills/DESIGN.md` Output language); keep the table row on one line and keep the pipe-delimited structure intact.

### Details
- Follow `skills/python-documentation/SKILL.md` for this docs edit; no history of the removal is written (Current-Specification-Only Policy).

## Compatibility considerations
N/A: documentation only; Term and Definition unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`, `check_glossary_term_classification.py`, `check_compat_shims.py`.
- `rg "Exports all component classes" docs scripts tests tools` returns no match.

## Completion criteria
- The Example cell contains no quote of the removed docstring and no path or symbol status; Term and Definition cells are byte-identical to before (AC-5).
- All listed checkers pass.

## Out of Scope
- The `Obsolete` row and its `read_json_file()` example; `governance_04_documentation-checks.md`; `tools/check_compat_shims.py` comment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the Example cell of the `Backward Compatibility` row (REQ-006) | Completed | 20261021-095319 | 20261021-095419 | Changed: docs/00_governance/governance_02_documentation-metadata.md (Example cell only; Term/Definition unchanged) |
| 2 | Run the documentation checkers named in Validation plan | Completed | 20261021-095419 | 20261021-095419 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_japanese, check_glossary_term_classification, check_compat_shims all exit 0; no leftover quote of the removed docstring. Docs-only change: no test run in this cycle. |

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
- **Requirement ID**: `REQ-006` (Glossary row no longer quotes the removed docstring)
- **Source issue**: `issues/20261020-122918_compat003_remove-the-agent-package-re-exports-kept-for-backward-compatibility.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-235040_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-093528
- **Related target files**: `docs/00_governance/governance_02_documentation-metadata.md`