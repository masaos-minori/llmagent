## Goal

Put the shutdown timing on `AgentConfig` as four typed fields, so the deadline, the settle window, the termination confirm window, and the force-exit opt-in are configuration rather than module constants (REQ-002: one configurable global deadline; REQ-011: second-signal behavior is configurable; AC-1).

## Scope
**Release unit**: R1-budget-and-config (Phase 1)

- In scope: the four fields and their defaults on `AgentConfig`.
- Out of scope: reading them from the config file (row 18), declaring them in `config/agent.toml` (row 19), and every consumer (rows 1, 7, 8, 10, 11, 12).

## Assumptions

- The fields belong in the flat top-level scalar block next to `agent_memory_max_startup_snippets`, `pending_timeout_minutes` and `approval_grant_ttl_seconds` (`scripts/agent/config_dataclasses.py:395-397`), not in a sub-config: they are sequence-wide settings, not settings of one subsystem.
- Production validation derives its known-key set from these dataclass fields (`scripts/agent/production_config_validator.py:146-205`), so adding a field extends the accepted keys without editing the validator, and the membership assertion at `tests/agent/test_production_config_validator.py:351-387` is what confirms it.
- The defaults are the values the Plan's Owner decision OD-03 and OD-04 froze: `shutdown_deadline_seconds` (new) 45.0, `shutdown_settle_seconds` (new) 10.0, `shutdown_termination_confirm_seconds` (new) 2.0, `shutdown_force_exit_on_second_sigint` (new) false.

## Design decisions

- Four flat fields rather than a nested shutdown sub-config: the existing flat scalars are the pattern the builder and the validator already handle, and a sub-config would add a nesting level for four values.
- The fields carry their defaults in the dataclass, so a config file that omits them yields today-equivalent behavior for the confirm window and no forced exit.
- `shutdown_force_exit_on_second_sigint` (new) is a boolean opt-in, defaulting to false, which keeps `os._exit` unreachable unless configured (REQ-011).
- Compatibility impact: additive fields; no existing field changes type or default.

## Alternatives considered

- reuse the existing 30 s constants as the defaults — rejected: the Plan's OD-03 chose a configurable 45 s total precisely because the current windows are per-step and unbounded in sum.

## Implementation
### Target file
`scripts/agent/config_dataclasses.py`

### Procedure
1. Add `shutdown_deadline_seconds` (new) `float = 45.0`, `shutdown_settle_seconds` (new) `float = 10.0`, `shutdown_termination_confirm_seconds` (new) `float = 2.0`, and `shutdown_force_exit_on_second_sigint` (new) `bool = False` to `AgentConfig` in the flat scalar block (`scripts/agent/config_dataclasses.py:395-397`).
2. Leave `__post_init__` unchanged: there is no cross-field rule between these four values, and no cross-field rule is invented here.

### Method
- Plain typed fields with defaults, matching the style of the neighboring scalars, so the builder and the validator treat them like any other scalar key.

### Details
- The field names are the configuration key names: the validator derives keys from the fields, so a rename here renames the key.

## Compatibility considerations

- Additive: existing `AgentConfig` construction and every existing key are untouched.
- Overlap: `scripts/agent/config_builders.py` (row 18) is also a target of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`); `tools/plan_dependency_order.py` places this Plan first, so these fields land before that Plan's builder change.

## Security considerations

- N/A: configuration fields only; no value is logged by this row.

## Rollback considerations

- Revert this row's commit with rows 18, 19 and 44: the field, the builder, the file entry and the test expectations are one unit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/config_dataclasses.py` | Unit | `uv run pytest tests/agent/test_config_builders.py -q` | the four fields are built with their defaults |
| `scripts/agent/config_dataclasses.py` | Unit | `uv run pytest tests/agent/test_production_config_validator.py -q` | the derived key set accepts the four new keys (verification only, no test edit) |

## Completion criteria

- `AgentConfig` exposes the four fields with the frozen defaults, and the production validator accepts them as known keys.

## Out of Scope

- Reading the keys from configuration, declaring them in the config file, and using them in the shutdown sequence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125-074347 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261125-074347 | row 44 |
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
- **Related target files**: `scripts/agent/config_dataclasses.py`, `tests/agent/test_config_builders.py`