## Goal

Build the four shutdown fields from configuration in the agent-config builder, so the values declared in `config/agent.toml` reach `AgentConfig` (REQ-002: one configurable global deadline; REQ-011: configurable second-signal behavior).

## Scope
**Release unit**: R1-budget-and-config (Phase 1)

- In scope: the scalar assembly in `_assemble_agent_config`.
- Out of scope: the fields themselves (row 17), the config file entries (row 19), and the production validator, which needs no edit because it derives its key set from the dataclass.

## Assumptions

- `_assemble_agent_config(cfg)` (`scripts/agent/config_builders.py:118-151`) builds the sub-configs and then the flat scalars through `_get_or_default` (`scripts/agent/config_builders.py:142-150`), which is where the four new fields are added.
- `build_agent_config` (`scripts/agent/config_builders.py:154-162`) resolves the source and registry (`scripts/agent/config_builders.py:83-98`) and runs production validation (`scripts/agent/config_builders.py:101-115`) before assembly; neither path needs a change because the validator's known keys come from the dataclass fields (row 17).

## Design decisions

- Use the existing `_get_or_default` helpers with the typed getters (`_get_float`, `_get_bool`) and the same defaults as the dataclass, so a missing key behaves identically whether the config file is present or not.
- No new builder function for four scalars: the neighboring scalars are assembled inline, and a dedicated function would add a layer with no shared logic.
- The defaults are repeated in the builder because `_get_or_default` requires one, and they must match the dataclass defaults exactly; row 44 asserts both agree.
- Compatibility impact: none for existing keys; unknown keys are unaffected because the accepted set grows through the dataclass.

## Alternatives considered

- read the values in the consumers directly from the config dict — rejected: the Plan's configuration boundary is that values become `AgentConfig` fields in the builder.

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
1. Add the four fields to the scalar block of `_assemble_agent_config` (`scripts/agent/config_builders.py:142-150`) using `_get_or_default` with `_get_float` for the three windows and `_get_bool` for the force-exit flag.
2. Keep the defaults identical to the dataclass defaults (45.0, 10.0, 2.0, false).
3. Leave `_resolve_config_source_and_registry` (`scripts/agent/config_builders.py:83-98`) and `_run_production_validation` (`scripts/agent/config_builders.py:101-115`) unchanged.

### Method
- One `_get_or_default` call per field, in the same order as the dataclass fields, so the diff is readable against row 17.

### Details
- The keys are read from the same flat config dict as `pending_timeout_minutes`, so no new section is introduced.

## Compatibility considerations

- Additive: existing keys and their defaults are untouched.
- Overlap: this file is also a target row of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`), which changes the reload path. `tools/plan_dependency_order.py` places this Plan first; the two changes touch different functions (`_assemble_agent_config` here, the reload commit path there), so they do not conflict, and the overlap must be re-checked before the cliplc005 row runs.

## Security considerations

- N/A: no new value is logged; production validation already reports unknown keys.

## Rollback considerations

- Revert this row's commit with rows 17, 19 and 44.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/config_builders.py` | Unit | `uv run pytest tests/agent/test_config_builders.py -q` | the four fields are read from configuration and default correctly |
| `scripts/agent/config_builders.py` | Unit | `uv run pytest tests/agent/test_production_config_validator.py -q` | production validation accepts the new keys (verification only) |

## Completion criteria

- A config file that sets the four keys produces an `AgentConfig` whose fields carry those values, and a config file that omits them produces the frozen defaults.

## Out of Scope

- The dataclass fields, the config file entries, and the shutdown sequence consumers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 44 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/agent/config_builders.py`, `tests/agent/test_config_builders.py`
