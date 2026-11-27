# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_index_state_consistency.py

## Goal

Create the coverage that filenames sharing a prefix or containing `LIKE` wildcards resolve to one
exact `index_state` key, and that a forced refresh followed by an incremental refresh leaves correct
state (REQ-003, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-003, REQ-004. Acceptance criterion: AC-2.

## Assumptions
- Full form: this is a new file and the only coverage of key identity, so the cases have to be defined
  here.
- The file does not exist; the only shared-prefix coverage today is the characterization test in
  `tests/mcp_servers/mdq/test_index_delete.py` (`TestIndexStateWildcardMatchIsCharacterizedAsIs`,
  lines 181-206), which pins the current over-match.
- This row gets its own document because no other row names it in `Related Tests`.
- The key form under test is the canonical `mtime:{path}` string produced by
  `scripts/mcp_servers/mdq/indexer.py` (line 316); no key-format change is introduced.

## Design decisions
- Test the delete boundary through the helper with an exact key, so the cases prove identity rather
  than pattern escaping.
- Keep the wildcard characters as data (`a.md%`, `a.md_bak`) so a future change back to a pattern
  match fails here.

## Alternatives considered
- Extend `tests/mcp_servers/mdq/test_index_delete.py` instead of creating a new file: rejected,
  because that file is the characterization companion of row 2 and the state-consistency cases span
  the forced-refresh path as well, which is row 3's boundary.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_index_state_consistency.py` (new)

### Procedure
- New file with the shared `tmp_path` service fixture used by the other mdq tests.
- Cases: `a.md` and `a.md.bak`; `a.md%` and `a.md_bak`; a path whose key is a literal prefix of
  another path's key.
- Case: forced refresh records state for each indexed file, then an incremental refresh reports no
  change.

### Method
- Assertions read `index_state` rows by exact key, so they do not depend on the delete statement form.

### Details
- One case per filename shape plus the forced-then-incremental sequence.

## Compatibility considerations
- `tests/mcp_servers/mdq/test_index_delete.py` keeps the shared-prefix case as the flip of its
  characterization (row 2's companion); this file covers the same boundary from the state side.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: delete the new file (single file, no confirmation needed).

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_index_state_consistency.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Deleting `a.md` cannot delete `a.md.bak` state, and forced refresh leaves correct incremental state
  (AC-2).

## Out of Scope
- The exact-key implementation (row 2); the transaction shape (rows 1, 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation in scope |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_index_state_consistency.py`
