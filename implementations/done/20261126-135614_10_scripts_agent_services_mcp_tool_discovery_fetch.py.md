## Goal
- Validate `config_dependent` strictly as a bool in the discovery fetch layer so a non-bool entry value rejects the entry with a finding (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the entry validation path in this file only.
- Out of scope: the runtime schema gate in `scripts/shared/resource_scope.py` (reference file, not modified); the test file is covered by seq 26.

## Assumptions
- Verified in Step 3a: `validate_tool_schema_v2` in `resource_scope.py` has no `config_dependent` check; `_validate_entry()` (`mcp_tool_discovery_fetch.py:94-118`) checks name and schema-2.1 fields but not `config_dependent`; the producer declares it as `Required[bool]` (`scripts/mcp_servers/models.py:244`).
- The per-server request timeout at `:54` already uses `get_effective_health_timeout(cfg)` and stays; after seq 02 the resolver always returns a positive float.
- Corrected in Step 3b: the check is added to `_entry_optional_field_error()`, the helper `_validate_entry()` already calls after the schema gate, so the message keeps the existing
  `tool {name!r} has invalid {field} {value!r} (expected bool)` shape rather than a new branch in `_validate_entry()`.
- Corrected in Step 3b: an absent `config_dependent` is not rejected. REQ-007 rejects a value that is not an actual `bool`; the producers emit the field on every entry
  (`scripts/mcp_servers/cicd/cicd_tools.py:87` and the other tool modules), while the discovery test fixtures do not build it, so requiring presence would reject valid entries. Seq 11 must read the
  value with a default (`entry.get("config_dependent", False)`) rather than `entry["config_dependent"]`.

## Design decisions
- Add the check in `_validate_entry()` (the fetch layer), not in `resource_scope.py`, per the frozen target table.

## Alternatives considered
- N/A: single-function change, no public-contract impact.

## Implementation
### Target file
`scripts/agent/services/mcp_tool_discovery_fetch.py`

### Procedure
1. In the entry validation path (`_entry_optional_field_error()`, called by `_validate_entry()` after the schema gate), require a present `entry["config_dependent"]` to be an actual `bool`;
   otherwise return a warning finding naming the entry and the got type, in the same `_warning_entry` shape as the existing field checks.

### Method
- Use `isinstance(value, bool)` strictly (no truthy coercion), consistent with the existing `_entry_optional_field_error` style.

### Details
- The validated value then travels unchanged to the registry builder (seq 11), which reads it with a default because an absent field is not rejected here.

## Compatibility considerations
- Producers already emit a bool, so no production entry is rejected; only malformed entries change behavior.

## Security considerations
- N/A: no credential handling here; the token reaches the request only through `auth_headers()`.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/services/test_mcp_tool_discovery.py` (strict-bool cases added by seq 26); `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- A non-bool `config_dependent` entry is rejected with a finding; a bool entry passes; tests pass. The strict-bool cases themselves are added by seq 26, so this cycle only confirms the existing
  discovery tests are unchanged by the check.

## Out of Scope
- The `RuntimeTool` field itself (seq 12) and the test file (seq 26).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the strict bool check | Completed | 20261126-182024 | 20261126-182024 | config_dependent added to the strict typed-field tuple in _entry_optional_field_error() (the helper _validate_entry() calls after the schema gate); a present non-bool value is rejected with the existing warning shape. An absent field is not rejected (recorded as a Step 3b correction); seq 11 reads it with a default. File size 9510 B < 24576. |
| 2 | Tests are covered by the test-file procedure (seq 26) | Completed | 20261126-182024 | 20261126-182024 | No test change in this cycle: the test file is seq 26's target and the strict-bool cases are added there. Existing tests unchanged: 87 passed; the 6 failures are the seq 09 capability-proof fallout pending seq 26. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-182024 | 20261126-182024 | ruff format/check pass; mypy clean; lint-imports 6 contracts kept; bandit pass; check_docstrings, check_mock_patch_targets, check_module_size pass. Full suite pending at end of batch. |

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
- **Requirement ID**: `REQ-007` (strict `config_dependent` parse from the discovery entry)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/services/mcp_tool_discovery_fetch.py`