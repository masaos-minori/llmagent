## Goal

Mark the requirement-cited assertions as `contract` and the characterization section as `characterization`
(REQ-003 — a module that mixes both kinds carries per-test markers).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is already imported; the module cites REQ-005 at `:257`, REQ-011 at `:309`,
  REQ-002/AC-3 at `:370`, and mcpdl003 REQ-002 at `:395`.
- The characterization section is `:658-737`, introduced by the heading that states these tests lock behavior
  the refactor of `scripts/agent/config_builders.py` must preserve.
- Those tests assert observed behavior with no requirement source, so they cannot be presented as normative.

## Design decisions

- Module-level `pytestmark = pytest.mark.contract` for the requirement-cited part, with per-test
  `@pytest.mark.characterization` on the tests in the section at `:658-737`.

## Alternatives considered

- Marking the whole module `characterization` — rejected: most assertions are traceable to recorded
  requirements, so the module mixes kinds.

## Implementation
### Target file
`tests/agent/test_config_builders.py`
### Procedure

- Add `pytestmark = pytest.mark.contract` after the imports.
- Add `@pytest.mark.characterization` to each test in the section at `:658-737`.

### Method

- No assertion is changed.

### Details

- The section heading already separates the two parts; the markers make the split machine-readable.
- Step 3b correction (2026-11-27): the labeled block is the heading at `:658` plus the four classes it names —
  `TestDiagnosticsSensitiveFieldsFallback` (667), `TestToolRegistryFailureConversion` (688),
  `TestProductionValidationWarningPath` (714), `TestEmptyStringFallbackIdioms` (736). Its tests run to `:764`,
  not `:737`: 670, 677, 684, 691, 702, 717, 739, 743, 758, 761, 764.
- Step 3b finding (2026-11-27, resolved by owner decision): `TestBuilderExceptionTypeUniformity` at `:771`
  (tests 779, 783) is under a separate heading, "Builder exception type (P22)", and carries no requirement
  citation. The marker set is the labeled block only, so this block stays unmarked. The same decision applies to
  the uncited tests outside the labeled blocks in documents 19, 22, 23, and 25: the labeled block named by the
  plan is the operational marker set, because `tools/check_test_taxonomy.py` cannot judge per-test traceability.

## Compatibility considerations

- The module appears in both `-m` selections; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_config_builders.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`: the mixed module is detected through its per-test
  markers.
- Sequence: lint → type → arch → security.

## Completion criteria

- Every test in the module resolves to exactly one kind, the `contract` part carries a citation, and the
  checker reports no finding.

## Out of Scope

- The checker (document 02) and the authority-model wording (document 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the markers per Procedure/Method/Details | Completed | 20261127-114755 | 20261127-114755 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-114755 | 20261127-114755 | this row is the test itself this row is the test itself |

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
- **Requirement ID**: `REQ-003` (per-test markers for a mixed module)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/agent/test_config_builders.py`