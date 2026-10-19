## Goal

Add unit tests for the new checker `tools/check_canonical_document_prose.py`: positive
(unregistered/duplicate canonical claim) and negative (benign/incidental/negation)
fixtures, plus a corpus run confirming zero benign false positives (`REQ-004`), and a
regression guard that the existing canonical-tool tests still pass.

## Scope

- **In-Scope**: tests for REQ-001/002/003/004 and a regression assertion on
  `test_check_canonical_source_conflicts.py` / `test_check_canonical_source_registry.py`.
- **Out-of-Scope**: changing the checker's behavior or the existing canonical-tool tests.

## Assumptions

- Tests import the checker's public functions/patterns and feed them fixture strings, or run
  the CLI against a temp `docs/` tree.
- The registry TOML at `config/documentation_canonical_sources.toml` can be used as-is for
  overlap fixtures, or a small inline fixture registry can be constructed.

## Design decisions

- Mirror the structure/style of `test_check_canonical_source_conflicts.py` (fixture layout,
  assertions on finding severity/blocking status) so the new tests fit the suite.

## Alternatives considered

N/A: mirroring the sibling test module is the lowest-risk approach.

## Implementation

### Target file

`tests/tools/test_check_canonical_document_prose.py`

### Procedure

1. Import the new checker's scan/extract/match functions (or invoke its CLI).
2. Positive fixture: a prose line asserting canonical status for a registered
   `source_paths`/`decision_target` → assert a WARNING finding (REQ-002).
3. Duplicate fixture: two prose lines asserting canonical status for the same subject →
   assert WARNING finding(s) (REQ-003).
4. Negative fixtures: a negated mention ("not treated as the top canonical source") and an
   incidental "canonical" mention → assert no finding (REQ-001/004).
5. Corpus run: run the checker against the current `docs/` and assert zero benign
   false positives (REQ-004).
6. Regression: confirm `test_check_canonical_source_conflicts.py` and
   `test_check_canonical_source_registry.py` still pass.

### Method

- Reuse the sibling test module's conventions (how it builds fixtures, how it asserts on
  finding severity/blocking status, how it invokes the tool).
- For overlap fixtures, reuse a real registered subject from
  `config/documentation_canonical_sources.toml` (e.g. a `decision_target` or `source_paths`
  entry) so the match is against live registry data.
- For the duplicate case, emit two distinct prose sentences sharing one subject token.
- For negatives, include the actual negation sentence from `governance_01_documentation-policy.md`
  referenced by ACC-004.
- Assert on the finding's severity/blocking-status being non-blocking and the message
  indicating a canonical-prose overlap.

### Details

- `REQ-001`/`REQ-002`: canonical assertion for a registered subject flagged; negation /
  incidental mention not flagged.
- `REQ-003`: two overlapping prose claims flagged.
- `REQ-004`: corpus run yields zero WARNINGs on benign mentions.
- Regression: existing canonical-tool suites unchanged.

## Compatibility considerations

N/A: test-only change; does not affect production code or the CI exit contract.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_canonical_document_prose.py` | Unit | `uv run pytest tests/tools/test_check_canonical_document_prose.py` | Positive flagged; negatives/corpus clean |
| Whole suite | Regression | `uv run pytest` | Existing canonical-tool tests still pass |

## Completion criteria

- One test each covering the passing and failing path for REQ-001 through REQ-003.
- A corpus run proving zero benign false positives (REQ-004).
- The existing canonical-tool suites pass unchanged.

## Out of scope

Changing the checker's behavior or the existing canonical-tool tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019-110037 | 20261019-110037 | REQ-001/002/003 |
| 2 | Add or update tests per Validation plan | Completed | 20261019-110037 | 20261019-110037 | REQ-001/002/003/004 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019-110037 | 20261019-110037 | all REQs |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019-110037 | 20261019-110037 | REQ-005 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (unit + corpus coverage for the new checker)
- **Source issue**: `issues/20261018-173010_gov009_detect-duplicate-canonical-document-specification-in-unregistered-prose.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-180319_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-064745
- **Related target files**: `tests/tools/test_check_canonical_document_prose.py`