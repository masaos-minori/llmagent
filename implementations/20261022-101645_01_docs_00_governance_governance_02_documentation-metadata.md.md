## Goal
Make the Glossary examples free of statements about the status of specific code symbols and add one scope sentence (REQ-001: `Obsolete`; REQ-002: `Migration`; REQ-003: `Operational Fallback`, `Default`, `Lenient Parsing`; REQ-004: scope sentence).

## Scope
- Rewrite the Example cell of five rows of the "Compatibility and Lifecycle Terminology" table and add one sentence to the glossary introduction.
- No Term or Definition cell changes; the `Backward Compatibility` and `Dead Code` rows are already generic.

## Assumptions
- `read_json_file()` no longer exists in source, and `apply_workflow_migrations()` is removed by the workflow-migration Plan, so those two examples are stale or about to be; the other three examples name symbols that currently exist but state status that can drift (confirmed by search).
- `tools/check_glossary_term_classification.py` reads the Term column only, so Example edits cannot change its result (verified in its docstring and tests).
- Docs content policy: no concrete symbols or counts needed; examples are descriptive.

## Design decisions
- Each Example describes a category in words and names no function, class, config key, or file.
- The scope sentence goes into the existing glossary introduction paragraph (not a new table row), so the table structure is unchanged.

## Alternatives considered
- Keeping symbol-specific examples under an automated reference check: rejected, generalizing is the smaller change and needs no tool change (Plan UNK-01).

## Implementation
### Target file
`docs/00_governance/governance_02_documentation-metadata.md`

### Procedure
1. `Obsolete`: example "A function that is still defined and callable but whose original purpose is now served by a different mechanism, so no current specification presents it as the production path."
2. `Migration`: example "Adding a column to an existing database table by an ordered, idempotent change that keeps the stored rows; a new database already has the column, so the change is a no-op."
3. `Operational Fallback`: example "A call to a remote service that falls back to in-process execution when the remote call fails; the decision is made per call at runtime."
4. `Default`: example "An optional integer configuration key that is absent from the configuration file is read as its declared default; a present value of the wrong type raises instead of using the default."
5. `Lenient Parsing`: example "A best-effort lookup run during a validation pass is skipped, not failed, when it raises an unexpected exception, because the lookup is not the contract being validated."
6. Append to the glossary introduction paragraph: "The glossary defines terms and is not a register of code status; its examples describe categories and name no specific symbol."

### Method
- Edit only the Example cells and the one sentence; keep table pipes and column count.
- Re-read the file before editing (high churn).

### Details
- After the edit run `rg "read_json_file|apply_workflow_migrations|call_rag_service|get_typed|production_config_validator" docs/00_governance/governance_02_documentation-metadata.md` (no match expected).

## Compatibility considerations
N/A: documentation only; Term and Definition cells are unchanged, so the glossary checker and any reader of the definitions are unaffected.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_glossary_term_classification.py --strict`, `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.

## Completion criteria
- No Example cell names a symbol or file whose status can change; the scope sentence exists once; Term and Definition cells are byte-identical to before; checkers pass.

## Out of Scope
- Other glossary rows and sections, and any tool change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the five Example cells and add the scope sentence | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (`Obsolete` example), `REQ-002` (`Migration` example), `REQ-003` (three more examples), `REQ-004` (scope sentence)
- **Source issue**: `issues/20261021-104152_glossex_decouple-the-glossary-and-checks-from-removed-symbols.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101645
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md
