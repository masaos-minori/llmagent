## Goal

Add unit tests to the new checker's test module `tests/tools/test_check_glossary_term_classification.py`:
a general/common-word entry is flagged at `Warning`, a project-specific entry is not, and the
current canonical term set yields no false positives.

## Scope

- **In-Scope**: general/common and project-specific fixtures; confirm no false positives on the
  current canonical term set; regression assertion on existing `test_check_docs_content_policy.py`.
- **Out-of-Scope**: changing the checker's behavior.

## Assumptions

- Tests exercise the checker's public functions or invoke its CLI against fixture inputs.
- A small temp directory standing in for `docs/00_governance/` can supply a fixture glossary file.

## Design decisions

- Follow the patterns of existing `tests/tools/*` so the new tests fit the suite.

## Alternatives considered

N/A: mirroring existing test patterns is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_glossary_term_classification.py`

### Procedure

1. Scaffold the module following an existing `tests/tools/*` pattern.
2. Project-specific fixture: a capitalized, domain-prefixed term (e.g. `GV-015`) → assert no finding
   (REQ-003).
3. General/common fixture: a lowercase common English word (e.g. `behavior`) → assert a `Warning`
   finding (REQ-003).
4. Exception fixture: the documented American-spelling exceptions (`Authorization`, `Behavior`,
   `Standardization`) → assert no finding (they are canonical, capitalized).
5. Corpus run: run the checker against the current `governance_02_documentation-metadata.md` → assert
   zero false positives (REQ-004).
6. Regression: confirm existing `test_check_docs_content_policy.py` still passes.

### Method

- Reuse the sibling test module's conventions (how it builds fixtures, how it invokes the checker,
  how it asserts on `Issue.severity`).
- Assert `issue.severity == "WARNING"` for the general/common case.
- For the corpus run, ensure the canonical term set (including the capitalized American-spelling
  exceptions) is not flagged.

### Details

- `REQ-001`: the parser reads the glossary term table from `governance_02`.
- `REQ-002`: classification is derived from the parsed table (no hardcoded term list).
- `REQ-003`: a general/common-word entry is flagged; a project-specific entry is not.
- `REQ-004`: corpus run yields zero false positives.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_glossary_term_classification.py` | Unit | `uv run pytest tests/tools/test_check_glossary_term_classification.py` | General/common flagged at Warning; project-specific/corpus clean |

## Completion criteria

- One test each covering the passing and failing path for REQ-003.
- A corpus run proving zero false positives (REQ-004).
- The existing `test_check_docs_content_policy.py` suites pass unchanged.

## Out of scope

Changing the checker's behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-150438 | 20261019-150438 | REQ-001/002/003 |
| 2 | Add or update tests per Validation plan | Completed | 20261019-150438 | 20261019-150438 | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-150438 | 20261019-150438 | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-150438 | 20261019-150438 | REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit + corpus coverage for the glossary term classification checker)
- **Source issue**: `issues/done/20261018-173410_gov015_automate-glossary-term-classification-validation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-182535_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-071823
- **Related target files**: `tests/tools/test_check_glossary_term_classification.py`