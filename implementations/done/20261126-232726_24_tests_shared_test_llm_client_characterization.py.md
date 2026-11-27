## Goal

Classify the module as `characterization` and correct the stale module docstring (REQ-003 — module marker;
REQ-007 — a characterization module MUST NOT present its assertions as normative).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Confirmed in Step 3a: `pytest` is not imported in this module, so the marker needs the import added.
- The docstring at `tests/shared/test_llm_client_characterization.py:1-8` cites `LLMClient.build_payload` and
  `request_with_retry`, which no longer exist in `scripts/shared/llm_client.py`, and line 4 ends with a dangling
  clause continued by the parenthetical at line 5.
- The module has no requirement citation, so it is `characterization` under REQ-002.

## Design decisions

- The docstring is rewritten to name only what the module actually covers (`build_llm_url` / `build_embed_url`
  edge cases) and keeps the sentence that states the tests lock observed behavior before a refactoring pass.
- Module-level `pytestmark` only: the module does not mix kinds.

## Alternatives considered

- Keeping the stale citation and only fixing the sentence — rejected by REQ-007: a characterization module must
  not present assertions against removed wrappers as normative.

## Implementation
### Target file
`tests/shared/test_llm_client_characterization.py`
### Procedure

- Add `import pytest` and `pytestmark = pytest.mark.characterization`.
- Rewrite the docstring: remove the reference to the removed wrappers, complete the truncated sentence, and keep
  the observed-behavior statement.

### Method

- No assertion is changed.

### Details

- The import goes with the existing standard-library imports, before the marker.
- Step 3b note (2026-11-27): verified against the current source, no change. `pytest` is not imported; the
  docstring's line 4 ends with the dangling clause "the" continued by the parenthetical at line 5;
  `build_llm_url` and `build_embed_url` exist at `scripts/shared/llm_client.py:29` and `:37`, while
  `build_payload` and `request_with_retry` do not exist in that module.

## Compatibility considerations

- The module is now selected by `-m characterization`; the full suite is unchanged.

## Security considerations

- N/A: no new disclosure surface.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/shared/test_llm_client_characterization.py -q`.
- Gate — `uv run python tools/check_test_taxonomy.py`.
- Sequence: lint → type → arch → security.

## Completion criteria

- The module carries exactly one taxonomy marker, its docstring names only sources that exist, and the checker
  reports no finding.

## Out of Scope

- The checker (document 02) and the authority-model wording (document 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker and correct the docstring per Procedure/Method/Details | Completed | 20261127-114755 | 20261127-114755 |  |
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
- **Requirement ID**: `REQ-003` (module marker), `REQ-007` (characterization module wording)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tests/shared/test_llm_client_characterization.py`