## Goal

Route the section builder reads through the shared primitives so startup and reload share one type-rule
implementation, keeping the existing reject-on-wrong-type behavior and the default-on-unset rule (REQ-001,
shared type rules; REQ-002, one builder for both paths).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- Verified against current source: `config_section_builders.py` reads values through
  `typed_validators._get_bool`, `_get_int`, `_get_float`, `_get_str` and its own `_or_default`,
  `_get_or_default` and `_get_str_or_default` helpers. The getters already raise
  `ConfigReloadValidationError` for a wrong-typed present value; the helpers fall back to the default
  only when the key is absent or the value is an explicit empty string. The module contains no
  `bool()`/`int()`/`float()` coercion (corrected during Step 3a: the Issue's coercive parsing is in
  `shared/mcp_config.py`, row 15, not here).
- The `memory` section example is `memory_min_importance`, which is not a registry entry, so its type
  rule comes from the builder path only, not from the reload registry.

## Design decisions
- The builders keep `typed_validators` as their read entry (row 2 delegates it to the shared
  primitives) and keep the `_or_default` unset rule — absent key or explicit empty string falls back to
  the default — so startup behavior is unchanged; `0` and `False` are values, not absence.
- The empty-string rejection in `strict_str` (row 1) applies to values the primitives receive
  directly (MCP parser, registry validators); the builder's unset fallback runs before the primitive
  call, which keeps startup and reload parity because both paths share this builder (OD-01).

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
- Executed result: no code change was needed in this file. Every field read already goes through
  `typed_validators._get_bool`/`_get_int`/`_get_float`/`_get_str`/`_get_list`/`_get_dict` with the key
  passed as the field path, and row 2 moved those getters behind the shared primitives, so the section
  builders now run the shared rules with no further edit. `grep` over the file for `bool(`, `int(`,
  `float(`, `str(` finds only `str(e)` inside `_build_model`'s error rewrap.
- One coercive read is deliberately left in place: `_build_diagnostics_config` turns a non-list
  `diagnostics.sensitive_fields` into an empty `frozenset` (`config_section_builders.py:290-292`). It is
  not in the Plan's `Newly rejected inputs` list, and `TestDiagnosticsSensitiveFieldsFallback` in
  `tests/agent/test_config_builders.py` pins it as intended behavior. Changing it is out of this Plan's
  scope.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125-153051 | no code change required: every read already goes through the typed_validators getters |
| 2 | Add or update tests per Validation plan | Completed | — | 20261125-153051 | row 30 covered by row 30 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125-153051 | ruff format+check, mypy, lint-imports 6 kept, generate_reference_table --check clean, full suite 14447 passed, diff-cover 100% |

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