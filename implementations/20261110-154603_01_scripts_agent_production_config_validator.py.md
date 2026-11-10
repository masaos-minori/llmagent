## Goal

Make `ProductionConfigValidator` strict-only: drop the `*_strict` required keys and the `security_profile` handling, reject an empty or absent `allowed_root`, and keep the `allowed_tools=[]` error (REQ-001 strict-only, REQ-003 `allowed_root` required, REQ-007 no profile key).

## Scope
**Release unit**: strict-only-startup

Edit `scripts/agent/production_config_validator.py` only. Tests for it belong to the Plan row for `tests/agent/test_production_config_validator.py`; callers (`config_builders.py`) are separate rows.

## Assumptions

- Sequencing: the Plan's Phases 1-4 can land in any order within this file; the strict-key removal (Phase 1) ships in the `strict-only-startup` release unit, the `security_profile` removal is Phase 3 and the `allowed_root` rejection is Phase 4.
- Removed keys are rejected as unknown keys by the existing `_check_unknown_production_keys` path: `_get_valid_production_keys()` derives its set from dataclass fields, so deleting the dataclass fields (`config_dataclasses.py` row) and the explicit `valid_keys.add("security_profile")` line is what makes `tool_definitions_strict`, `routing_drift_strict` and `security_profile` unknown. No separate deny-list is added.
- Depends on the `config_dataclasses.py` and `config_builders.py` rows only for the final green run; this file can be edited first because `validate()` reads a plain mapping.
- `ProductionConfigValidator.validate()` callers outside `config_builders.py` were not found by `rg` (the other user is `validate_against_registry`, unchanged); if one passes `security_profile=`, report an additional-target discovery.

## Design decisions

- `allowed_root` is checked in `validate()` on the raw mapping: absent, non-string, or blank is an error, so a typo or unresolved variable cannot disable the path jail; the section builder (`config_section_builders.py` row) rejects the same condition for the reload path.
- The `allowed_tools=[]` error stays and its message states that every tool is denied (not allowed), matching REQ-002.

## Alternatives considered

Keeping `_REQUIRED_STRICT_KEYS` as a tuple that only checks key absence was rejected: the keys must not exist at all (Plan Design). Rejecting `allowed_root` only in the builder was rejected because the validator is the single place that reports every production error in one list.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`

### Procedure
1. Remove the `SecurityProfile` `TYPE_CHECKING` import (line 19), `_get_security_profile()` (lines 24-29) and the profile check at the start of `validate()` (lines 233-244, including its early return).
2. Remove the `security_profile` parameter from `ProductionConfigValidator.validate()` (signature at line 223) and its docstring mention.
3. Delete `_REQUIRED_STRICT_KEYS` (lines 31-35) and the strict-key loop in `validate()` (lines 246-250). Keep `_REQUIRED_NOT_FALSE_KEYS` and its loop (an empty tuple today) untouched.
4. Delete `valid_keys.add("security_profile")` in `_get_valid_production_keys()` (line 187) and its comment line.
5. Add an `allowed_root` check in `validate()` after the `allowed_tools` check: record an error when `config.get("allowed_root")` is not a non-blank `str`.
6. Reword the `allowed_tools=[]` message (line 299) to say every tool is denied.
7. Update the class docstring ("Checks strict mode flags ...") to drop the strict-flag wording.

### Method
- Use the existing `self._record(errors, warnings, msg)` helper for the new error so it flows through `_format_error_or_warning` (always an error).
- Check `isinstance(root, str) and root.strip()`; do not resolve the path or test that it exists (existence is a deployment concern, out of scope).
- Run `rg -n "SecurityProfile|security_profile|_REQUIRED_STRICT|_strict" scripts/agent/production_config_validator.py`; the result must be empty after the edit.

### Details
- Error text for `allowed_root` names the key and the effect, e.g. `allowed_root is empty or absent (the path jail would be disabled; set an absolute directory)`; do not include config values.
- The `validate()` return type and the `known_tools` parameter are unchanged.
- Line numbers are from the current file and shift as edits land; edit by symbol.

## Compatibility considerations

Breaking by design: a config that sets `tool_definitions_strict`, `routing_drift_strict` or `security_profile` now fails validation as an unknown key, and one without a non-blank `allowed_root` fails. The shipped `config/agent.toml` loses the two strict keys in the same release unit and keeps `allowed_root`.

## Security considerations

Removes the "strict can be false" configuration path and closes the empty-`allowed_root` hole at the validation boundary (ADR-004 Decision Group 1: a safety boundary must not depend on a value being non-empty). No weakening: every error that is reported today is still reported.

## Rollback considerations

`git revert` of the commit; no persisted state is involved.

## Validation plan

- `uv run pytest tests/agent/test_production_config_validator.py -v` (updated by its own Plan row: removed-key rejection cases, empty `allowed_root` case).
- `uv run ruff format scripts/agent/production_config_validator.py` and `uv run ruff check scripts/agent/production_config_validator.py`; `uv run mypy --no-namespace-packages scripts/`.
- `rg -n "security_profile|SecurityProfile|_strict" scripts/agent/production_config_validator.py` returns nothing.

## Completion criteria

- `validate()` has no `security_profile` parameter and no strict-key logic.
- An empty, blank, or absent `allowed_root` yields an error; `allowed_tools=[]` still yields an error.
- The three removed keys are reported by the unknown-key check.

## Out of Scope

- Test edits (own Plan row) and the builder/dataclass edits (own rows).
- Any change to `validate_against_registry` or the `tool_safety_tiers` checks.
- Checking that `allowed_root` exists on disk.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the profile import, helper, parameter and check; delete the strict-key tuple and loop; delete the `security_profile` valid key | Pending | — | — | REQ-001, REQ-007 |
| 2 | Add the `allowed_root` error and reword the `allowed_tools=[]` message | Pending | — | — | REQ-003, REQ-002 |
| 3 | Run ruff, mypy and `tests/agent/test_production_config_validator.py` (after the test row lands) | Pending | — | — |  |
| 4 | Run `uv run python tools/check_suppression_justification.py` if any suppression changed; otherwise record N/A | Pending | — | — | Expected N/A |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-007`
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `scripts/agent/production_config_validator.py`
