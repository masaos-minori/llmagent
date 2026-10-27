# Implementation Procedure: Rename fixtures and add the new-key/old-key regression test in `tests/rag/test_config_resolution.py`

## Goal

Rename the two fixture occurrences of the old key spelling and add the Plan's one new
regression test that pins the rename contract: the renamed key resolves from a config dict and
the old spelling is ignored as an unknown field (stays `None`) (REQ-004, AC-2).

## Scope

- Rename two occurrences (verified 2026-10-27): the `_ALL_FIELDS`-style base dict entry at L29
  and the keyword occurrence at L77.
- One new test function `test_renamed_key_resolves_and_old_key_is_ignored` (new).
- No assertion or logic edits to existing tests (AC-6).

## Assumptions

- Phase 3 row: the scripts declaration renames (Plan rows `20261027-154619_01`-`_07`) land
  first; this file asserts against the renamed `resolve_rag_config` contract.
- The module's existing fixtures build the raw config dict via a base dict with
  `base.update(overrides)` (verified around L22-47) and a `mock_validator` fixture that patches
  `RagConfigValidator` (verified at L50+); the new test reuses both.
- Overlap with the rag002 Plan on this file: none.

## Design decisions

- The new test pins the documented "ignored as unknown field" behavior per Plan Design "no
  alias/back-compat": old spelling in a config dict must yield the `None` default, not an error
  (fail-safe = no delegation).

## Alternatives considered

- Asserting an error for the old key — rejected: the ignore-extras filter is the designed
  contract (Plan Design); the test documents, not changes, it.

## Implementation
### Target file

`tests/rag/test_config_resolution.py`

### Procedure

1. Rename the base-dict entry `"rag_service_url": None` (L29, verified) to the new spelling
   `rag_query_service_url` (new), value `None` unchanged.
2. Rename the keyword occurrence at L77 (verified) to the new spelling.
3. Add `test_renamed_key_resolves_and_old_key_is_ignored` (new):
   - Case A: build the base dict with `{"rag_query_service_url": "http://x"}` override; call
     `resolve_rag_config` with `mock_validator`; assert the resolved config's
     `rag_query_service_url == "http://x"` (AC-2 first half).
   - Case B: build a dict carrying the old spelling `{"rag_service_url": "http://x"}` (not in
     `_ALL_FIELDS` after the rename); assert the resolved value stays `None` (AC-2 second
     half). Case B must not pass the renamed key.

### Method

Two fixture token renames plus one new test function modeled on the existing resolution tests
(dict override + `mock_validator`).

### Details

- Case B's dict must be constructed literally (a stray dict entry, not the renamed base), so
  the test stays valid even after every other rename row lands.
- Type note: the resolved object is `RagConfigImpl`; access the renamed attribute directly.

## Compatibility considerations

- Test-only change; existing test semantics untouched (AC-6).

## Security considerations

- N/A: the new test pins the fail-safe default for stray old-spelling keys.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_config_resolution.py` — renamed fixtures and the new test pass
  after Phase 2 rows land (Plan Validation row for this file).
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — no
  matches once all rename rows land (AC-1).

## Completion criteria

- AC-2: both cases of the new test pass; AC-1: no standalone old-spelling occurrence remains
  in this file (the new test's Case-B dict entry is the single intentional literal, allowed by
  AC-1's scope of production code; it is written as a quoted dict key, not an identifier).

## Out of Scope

- All other test-file renames (own procedure documents) and the scripts-side declaration
  renames.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 row; land after Phase 2 rows 01-07 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document includes the new test itself |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: tests/rag/test_config_resolution.py
