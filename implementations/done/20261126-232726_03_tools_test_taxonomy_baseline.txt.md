## Goal

Record the modules that are not yet classified so the checker can exempt them while the suite is migrated
incrementally (REQ-003 — a module not yet classified is tracked in a baseline).

## Scope
**Release unit**: taxonomy mechanism

## Assumptions

- Confirmed in Step 3a: 90 modules under `tests/agent` and `tests/shared` carry neither `pytestmark` nor a
  requirement citation; `tests/tools/` and `tests/mcp_servers/` modules are outside that count, so the
  baseline lists only the counted modules.
- Step 3b correction (2026-11-27, owner decision): the baseline holds every module in the classified areas
  that carries no taxonomy marker, so it is 240 entries, not 90. The 90 figure counted only modules with
  neither marker nor citation; REQ-003's marker obligation covers all 253 modules in `tests/agent` and
  `tests/shared`, and the checker cannot exempt a module that has a citation but no marker without dropping
  the marker obligation. See document 02's Step 3b note for the same decision.
- Step 3b correction (2026-11-27): `tests/agent/memory/test_memory_vec_session.py` carries
  `pytestmark = pytest.mark.skipif(...)` (`:32`), which is not a taxonomy marker, so under the rule it is
  unclassified and is a baseline entry; the earlier assumption that it is "reported as classified" does not
  hold.
- The first tranche (the Plan's test rows) is excluded from the baseline because those rows classify them in
  the same commit.
- `tests/agent/memory/test_memory_vec_session.py` already carries a `pytestmark` and is not one of the
  tranche rows, so it is reported as classified, not as a baseline entry.

## Design decisions

- One entry per module path, `<path><TAB><reason>`, following `tools/known_test_failures_baseline.txt`'s
  header policy: the reason names the owning issue, and an entry is removed when its module is classified.

## Alternatives considered

- N/A: the Plan fixes the baseline as the mechanism for incremental migration.

## Implementation
### Target file
`tools/test_taxonomy_baseline.txt` (new)
### Procedure

- Write the header stating the entry format and the removal rule, then the 90 module paths, excluding the
  Plan's first-tranche rows.

### Method

- Generate the list from the same scan the checker uses, so the baseline and the checker cannot disagree at
  creation time.

### Details

- Sorted by path for a stable diff.

## Compatibility considerations

- The baseline shrinks as modules are classified; the gate fails on any changed module that is not
  classified, so the baseline cannot grow silently.

## Security considerations

- N/A: data file.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Gate — `uv run python tools/check_test_taxonomy.py`: reports only baseline modules as unclassified, exit 0.
- Unit — `uv run pytest tests/tools/test_check_test_taxonomy.py -v` (the checker's test row, document 08).

## Completion criteria

- Every module the checker reports as unclassified is in the baseline, and no first-tranche module is in it.

## Out of Scope

- Classifying the 90 baseline modules (incremental, owned by later changes).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the baseline file per Procedure/Method/Details | Completed | 20261127-111354 | 20261127-111354 | 240 entries, owner decision A |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-111354 | 20261127-111354 | checker reads the baseline; baseline lines parse |

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
- **Requirement ID**: `REQ-003` (baseline for modules not yet classified)
- **Source issue**: `issues/20261119-145310_cliplc012_characterization-test-split.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-215529_cliplc012_characterization-test-split.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-232726
- **Related target files**: `tools/test_taxonomy_baseline.txt`