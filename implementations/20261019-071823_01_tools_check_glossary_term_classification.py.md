## Goal

Create a new standalone checker `tools/check_glossary_term_classification.py` that parses the
"Compatibility and Lifecycle Terminology" glossary table in
`docs/00_governance/governance_02_documentation-metadata.md` and flags entries whose term is a
general/common English word rather than a project-specific identifier. Non-blocking, `Warning`-level.
This closes the documented `Partial` gap for GV-015.

## Scope

- **In-Scope**:
  - Parse the glossary term table in `governance_02_documentation-metadata.md`.
  - Classify each entry as project-specific or general/common using conservative signals.
  - Flag general/common-word entries at `Warning`.
  - Add unit tests with project-specific and general-term fixtures; confirm no false positives on
    the current canonical term set.
- **Out-of-Scope**:
  - Altering the glossary content, term definitions, or usage rules in `governance_02`.
  - Extending to other tables.

## Assumptions

- The checker is `Warning`-level and non-blocking, consistent with GV-015's existing gate.
- The dominant `tools/check_*.py` convention is string severity (`Issue(severity: str)` with
  `"WARNING"`/`"ERROR"`); follow it (the `Severity` HIGH/MEDIUM/LOW enum is used only by
  `check_canonical_source_conflicts.py`).
- "General/common English word" is detected with conservative signals only (lowercase term, absence
  of a project-specific marker such as a domain prefix, acronym, or camelCase/PascalCase form), so
  the current canonical term set is not flagged.

## Design decisions

- New standalone CLI following the `tools/check_*.py` convention (argparse, `Issue` results, string
  `Warning`/`ERROR` severities, `main() -> int` + `sys.exit(main())`).
- Parse the glossary table by locating the "Compatibility and Lifecycle Terminology" section header
  and reading the following Markdown table rows.
- Classify per term with conservative signals; fail safe toward not flagging ambiguous terms.

## Alternatives considered

- Hardcoding the list of canonical project-specific terms — rejected: REQ-002 requires dynamic
  classification from the parsed table; hardcoding would drift as the glossary changes.

## Implementation

### Target file

`tools/check_glossary_term_classification.py`

### Procedure

1. Scaffold the module following an existing `tools/check_*.py` (e.g. `check_docs_content_policy.py`):
   argparse CLI, `Issue` results with string severity, `main() -> int` ending in `sys.exit(main())`.
2. Implement glossary parsing (UNK-01): locate the "Compatibility and Lifecycle Terminology" section
   header in `governance_02_documentation-metadata.md` and read the following Markdown table rows;
   extract the term column.
3. Implement conservative classification (UNK-02): for each term, apply conservative signals — a
   term that is entirely lowercase, lacks a project-specific marker (domain prefix, acronym,
   camelCase/PascalCase, or a known project token), and matches a common-English heuristic is
   classified as general/common. Otherwise project-specific.
4. Implement flagging: emit a `Warning` finding for each general/common entry (REQ-003).
5. Corpus guard: assert zero findings on the current canonical term set (REQ-004).
6. Report `Warning`-only; preserve the non-blocking contract.

### Method

- **CLI.** Mirror `check_docs_content_policy.py`: `argparse.ArgumentParser`, optional `--root`
  (default repo root), `def main(argv=None) -> int` ending in `sys.exit(main())`.
- **Parsing.** Find the "Compatibility and Lifecycle Terminology" header (case-insensitive substring
  match), then parse subsequent table rows (`| ... |`) into cells; take the first cell as the term.
  Fail safe if the section/table is missing.
- **Classification (UNK-02).** Apply conservative signals only:
  - Lowercase-only term → candidate general/common.
  - Presence of a project-specific marker (camelCase/PascalCase, acronym/all-caps, domain prefix like
    `gv-`, or a token from a small project-vocabulary allowlist) → project-specific.
  - Otherwise fail safe (not flagged).
- **Exclusions.** Treat the documented American-spelling exceptions (`Authorization`, `Behavior`,
  `Standardization`) as project-specific (they are capitalized and canonical), so they are not
  flagged.

### Details

- `REQ-001`: the glossary term table is parsed from `governance_02_documentation-metadata.md`.
- `REQ-002`: classification is derived dynamically from the parsed table (no hardcoded term list).
- `REQ-003`: a general/common-word entry is flagged at `Warning`.
- `REQ-004`: the current canonical term set yields zero false positives.
- **UNK-01:** define the glossary input precisely — the "Compatibility and Lifecycle Terminology"
  section's table; document it in-code.
- **UNK-02:** use conservative signals only; fail safe toward not flagging ambiguous terms.

## Compatibility considerations

New CLI entry point only; no external callers. `Warning`-only findings preserve the non-blocking
contract.

## Security considerations

N/A: reads local `docs/`; applies read-only parsing; executes no user input.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_glossary_term_classification.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_glossary_term_classification.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_glossary_term_classification.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_glossary_term_classification.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_glossary_term_classification.py` | Unit + corpus | `uv run pytest tests/tools/test_check_glossary_term_classification.py` then corpus run | General/common flagged; canonical set clean |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | No new failures |

## Completion criteria

- The checker parses the glossary table, classifies terms conservatively, and flags general/common
  word entries at `Warning`.
- Unit tests cover project-specific and general-term fixtures plus a corpus run with zero false
  positives.
- The GV-015 matrix row reports the validation as automated with the follow-up note cleared.

## Out of scope

Changing the glossary content, term definitions, or usage rules in `governance_02`, and extending
to other tables.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | REQ-001/002/003; UNK-01/02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (new checker: parse glossary table, classify terms, flag general/common words at `Warning`)
- **Source issue**: `issues/done/20261018-173410_gov015_automate-glossary-term-classification-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-182535_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-071823
- **Related target files**: `tools/check_glossary_term_classification.py`
