## Goal

Make the doc-quality rule's description name the command it sanctions after the rename, so the rule does not tell an author to use a name the corrected documents no longer contain (REQ-007: name matches behavior).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the `stale_db_rag_slash_commands` rule description at `config/doc_quality_rules.json:30-34`.

## Assumptions

- The `pattern` is unchanged: it matches removed `/db` and `/rag` command forms, not the RAG vector subcommand. Only the description text lists the sanctioned alternatives.
- `check_docs_quality.py` reports the description as part of the finding, so a stale description produces a finding that reads as a wrong instruction.

## Design decisions

- Only the description changes; the pattern, severity, and rule name stay as they are. Changing the rule name or severity is outside this row.

## Alternatives considered

- Adding the retired name to the pattern so the rule would catch it — rejected: the retired name is not a removed `/db` or `/rag` form, and `tests/agent/commands/test_removed_commands.py` (row 50) already enforces that it stays unregistered.

## Implementation
### Target file
`config/doc_quality_rules.json`

### Procedure
1. Replace `/session rag-rebuild-vec` in the description at `:33` with the renamed form.
2. Leave the `pattern`, `severity`, and key unchanged.

### Method

- Single string change in a JSON value; no schema change.

### Details

- The description must name only registered commands, consistent with the documents it sanctions (rows 29-34).

### Companion test files

- `tests/tools/test_check_docs_consistency_checks.py` (row 64 is this row's companion test, covered by this document)
  - Procedure: update the expectation that reads the rule description so it names the renamed command.
  - Validation: `uv run pytest tests/tools/test_check_docs_consistency_checks.py -q` (REQ-007; AC-8, AC-9).

## Compatibility considerations

- Every document that names the command is corrected in the same release unit; a corrected rule with uncorrected documents fails `tools/check_docs_quality.py`.

## Security considerations

- N/A: configuration data.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `config/doc_quality_rules.json` | Checker | `uv run python tools/check_docs_quality.py` | No finding; description names the registered command |
| Same file | Unit | `uv run pytest tests/tools/test_check_docs_consistency_checks.py -q` | Rule expectations pass with the renamed command |

## Completion criteria

- The rule description names only registered commands, and the whole document set passes the checker in one run.

## Out of Scope

- The rule pattern, the documents it sanctions, the code rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the rule description | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) done: the rule description names /session rag-prune-vec; pattern, severity and key unchanged. |
| 2 | Update the companion test per Validation plan | N/A | — | — | Covered by this document Deviation: no test reads the rule description - tests/tools/test_check_docs_quality.py:640,649 exercise only the pattern - so the procedure's companion-test expectation is a stale assumption. Validation is the live corpus check, which reports no finding. |
| 3 | Run the validation sequence (`rules/tool-gates.md`) | Completed | 20261125-002740 | 20261125-002740 | Phase 6 part: check_docs_quality reports no finding over 176 files; tests/tools/test_check_docs_quality.py and test_check_docs_consistency_checks.py pass (101). |

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
- **Requirement ID**: REQ-007 (name matching behavior), REQ-010 (documentation reflects the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `config/doc_quality_rules.json`, `tests/tools/test_check_docs_consistency_checks.py`