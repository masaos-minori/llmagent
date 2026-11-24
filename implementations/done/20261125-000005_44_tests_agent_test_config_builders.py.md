## Goal

Add the four shutdown configuration fields to the builder tests, so the fields, their defaults, and the values read from configuration are pinned (REQ-002: one configurable global deadline; REQ-011: configurable second-signal behavior).

## Scope
**Release unit**: R1-budget-and-config (Phase 1)

- In scope: the config-surface cases in this file.
- Out of scope: the dataclass (row 17), the builder (row 18), and the config file (row 19).

## Assumptions

- This file is the config-surface test the builder change is measured against, and it enumerates the fields the builder produces.
- The defaults asserted here must match both the dataclass defaults (row 17) and the entries declared in `config/agent.toml` (row 19), because the builder's `_get_or_default` fallback and the file's declared value must be the same number.

## Design decisions

- Assert three things per field: the default when the key is absent, the value when the key is present, and the type (`float` for the three windows, `bool` for the force-exit flag).
- Assert the builder default equals the dataclass default in one case, which is the check that keeps rows 17 and 18 from drifting apart.
- Keep the existing field enumeration cases and extend them rather than rewriting them.
- Compatibility impact: none outside this file.

## Alternatives considered

- rely on `tests/agent/test_production_config_validator.py` — rejected: that file validates key acceptance, not the values the builder produces, and it is not a target row.

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
1. Add cases for `shutdown_deadline_seconds` (new), `shutdown_settle_seconds` (new), `shutdown_termination_confirm_seconds` (new) and `shutdown_force_exit_on_second_sigint` (new): absent key yields the frozen default, present key yields the configured value.
2. Add one case asserting the builder defaults equal the `AgentConfig` defaults.
3. Extend the existing field-enumeration cases so the four new fields are included.

### Method

- Table-style cases over the four keys, reusing the file's existing config-dict fixtures.

### Details

- The boolean case asserts `false` is honored, not only `true`, because the default is the safe value (REQ-011).

## Compatibility considerations

- Overlap: this file is also a target row of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`), which changes the config surface through shared typed primitives and adds no `AgentConfig` field. `tools/plan_dependency_order.py` places this Plan first; re-run `tools/check_plan_target_overlaps.py` after each lands.

## Security considerations

- N/A: no secret or path is asserted.

## Rollback considerations

- Revert this row's commit with rows 17, 18 and 19.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_config_builders.py` | Unit | `uv run pytest tests/agent/test_config_builders.py -q` | the four fields build with the frozen defaults and honor configured values |

## Completion criteria

- Each of the four keys has an absent-key case and a present-key case, and the builder-vs-dataclass default equality is asserted.

## Out of Scope

- The dataclass fields, the builder implementation, and the config file entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125-074347 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261125-074347 | this row is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-074347 | 20261125-075448 |  |

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
- **Requirement ID**: REQ-002 (one configurable global deadline), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `tests/agent/test_config_builders.py`, `scripts/agent/config_builders.py`