## Goal

Run one value table through both the startup builder and `/reload` and assert identical accept and
reject results, which is the only way to show AC-1 holds rather than being asserted (REQ-001, shared
strict type rules; REQ-002, reload candidate through the startup parser; REQ-004, strict MCP parsing).

## Scope
**Release unit**: R2-typed-registry

## Assumptions
- The parity table is written before the registry gains `field_type` and `allow_empty` (rows 3, 4), per
  the Plan's Phase 2 order (tests first).
- The tests reuse `tests/agent/_config_test_defaults.py` so production validation does not fail for
  unrelated reasons (Plan `Reference Files`).
- Startup-side expectations must match `tests/agent/test_startup_validation.py`, which is not modified
  here.

## Design decisions
- One table, two runners: each row is a value plus the expected result, and both paths are run against
  the same row, so a divergence is a test failure rather than a documented difference.
- The newly rejected inputs are recorded in the test as the published review surface for the strictness
  change (UNK-01).

## Alternatives considered
- Comparing the two implementations by reading the code — rejected: it proves nothing at runtime.

## Implementation
### Target file
`tests/agent/services/test_config_reload_parity.py` (new)

### Procedure
Write the parity table before the registry gains `field_type` and `allow_empty`, per the Plan's Phase 2
step 1: one value table run through both the startup builder and the reload path.

### Method
- Each table row runs the startup builder and the reload path and compares the accept or reject result.
- The `allow_empty` value chosen for each list entry is pinned here (UNK-05, decided in row 4).
- The deployed MCP tables and `config/agent.toml` are checked against the strict rules (UNK-01).

### Details
- The table includes every input in the Plan's `Newly rejected inputs` list and the already-rejected
  inputs, so a regression in either direction is visible.

## Compatibility considerations
- `tests/agent/test_config_effective_snapshot.py` pins the registered-field inventory; the parity test
  must agree with it or the inventory is re-measured (UNK-04).

## Security considerations
- N/A: the tests assert accept and reject results, not output.

## Rollback considerations
- Revert the Phase 2 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_parity.py -q`
- `uv run pytest tests/agent/test_config_effective_snapshot.py -q`

## Completion criteria
- Every table row produces the same result on both paths, and the recorded newly rejected inputs match
  the Plan's list.

## Out of Scope
- The registry entry shape (row 4).
- The MCP parser tests (row 15's companion).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-154000 | 20261125-163000 | tests written before rows 3, 4 tests/agent/services/test_config_reload_parity.py created: reject parity, accept and allow_empty parity, startup-only reporting, shipped config checks; 100 passed |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-154000 | 20261125-163000 | tests/agent/test_config_effective_snapshot.py still passes: 2 passed, registered-field inventory unchanged |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-002 (reload candidate through the startup parser), REQ-004 (strict MCP server parsing); AC-1, AC-6
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/services/test_config_reload_parity.py`