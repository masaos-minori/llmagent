## Goal

Replace the coercive reads in the section builders with the shared primitives, so a wrong-typed startup
value is rejected instead of coerced into a default (REQ-001, shared type rules; REQ-002, one builder
for both paths).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- Verified against current source: `config_section_builders.py` reads values through
  `typed_validators._get_bool`, `_get_int`, `_get_float` and its own `_get_or_default` and
  `_get_str_or_default` helpers, which apply a default when the value is missing but do not reject a
  wrong-typed value before the default is chosen.
- The `memory` section example is `memory_min_importance`, which is not a registry entry, so its type
  rule comes from the builder path only, not from the reload registry.

## Design decisions
- The builders call the shared primitives directly and keep their default behavior only for a missing
  key, not for a present-but-wrong-typed value.
- Truthiness defaults (`bool(value)` style) are removed; a `0` or `""` is a value, not an absence.

## Alternatives considered
- Keeping the local helpers and making them strict — rejected: that keeps two implementations of the
  same rule, which is the AC-1 defect.

## Implementation
### Target file
`scripts/agent/config_section_builders.py`

### Procedure
Replace the local coercive reads with the shared primitives for the llm, tool, memory, approval, and
diagnostics sections.

### Method
- Each field read passes the field path so the raised error names it.
- `allow_empty` is taken from the registry entry (row 4) for list-valued fields.

### Details
- Enum fields (`transport`, `startup_mode`, `tool_policy_mode`) keep their existing enum checks; only
  the type rule moves.

## Compatibility considerations
- Blast radius: every section is assembled here, so the strictness change affects startup as well as
  reload. The deployed configuration was parsed under the strict rules and reports no newly rejected
  value (UNK-01).

## Security considerations
- No raw value in the error text.

## Rollback considerations
- Revert the Phase 1 commit.

## Validation plan
- `uv run pytest tests/agent/test_config_builders.py -q`
- `uv run pytest tests/agent/services/test_config_reload_parity.py -q` (row 27)
- `uv run ruff check scripts tests`, `uv run mypy scripts`

## Completion criteria
- No section builder coerces a wrong-typed value, and the parity table shows the same accept and
  reject result on both paths.

## Out of Scope
- The registry `allow_empty` values (row 4, UNK-05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 30 |
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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-002 (reload candidate through the startup parser); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/config_section_builders.py`
