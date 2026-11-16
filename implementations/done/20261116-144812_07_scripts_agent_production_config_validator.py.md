## Goal

Register the six new artifact-retention keys in `ProductionConfigValidator`'s valid-keys set so they are not classified as unknown keys at startup (REQ-001, AC-1).

## Scope
**Release unit**: retention-sweeps-and-drill-lifecycle

- In scope: extend the `valid_keys.update({...})` set literal in `_get_valid_production_keys`.
- Out of scope: value-range validation of these keys (the `0`/negative/bool semantics live in `ArtifactRetentionConfig`/`_non_negative_int`, row 1).

## Assumptions
- Anchors re-verified 2026-11-16. `_get_valid_production_keys` builds `valid_keys`; the `valid_keys.update({...})` set literal at `production_config_validator.py:186-201` already lists `sqlite_corrupt_archive_max_age_days`, `sqlite_corrupt_archive_max_files`, `sqlite_retention_max_age_days`, `sqlite_retention_max_sessions`, etc. Unknown-key classification against this set is exercised via `startup_validation.py:72-93` (reference).
- The six key names are fixed in the Plan REQ-001: sqlite_archive_max_files, sqlite_archive_max_age_days, sqlite_drill_artifact_max_files, sqlite_drill_artifact_max_age_days, sqlite_quarantine_max_files, sqlite_quarantine_max_age_days.

## Design decisions
- Register the keys only (no per-key validator branch), matching how the existing `sqlite_retention_*` and `sqlite_corrupt_archive_*` keys are handled — value enforcement stays in the config layer.

## Alternatives considered
- N/A: registration-only, consistent with the landed sibling keys.

## Implementation
### Target file
`scripts/agent/production_config_validator.py`

### Procedure
1. Add the six key names to the `valid_keys.update({...})` set literal at `:186-201`, kept alphabetically consistent with the existing `sqlite_*` entries.

### Method
- No change to `_VALID_PRODUCTION_KEYS` caching, the file-name-derived keys, or any other branch.

### Details
- These names must match exactly what `ArtifactRetentionConfig.from_config` (row 1) reads and what `config/agent.toml` (row 8) sets.

## Compatibility considerations
- Purely additive to the valid-keys set; no key is removed and existing validation behavior is unchanged.

## Security considerations
- N/A: name registry only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent -v` (existing validator/unknown-key tests; a seeded config carrying the six keys must produce no unknown-key finding); `uv run ruff check`, basedpyright (CI form).

## Completion criteria
- A production config containing the six new keys validates with no unknown-key classification; a config without them still validates (defaults apply).

## Out of Scope
- Value semantics for the keys (row 1); adding them to the deployed `agent.toml` (WI-008-1, operator).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the six keys to the valid-keys set | Completed | 20261116-194502 | — |  |
| 2 | Add/update validator tests per Validation plan | Completed | 20261116-194502 | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116-194502 | — |  |
| 4 | Update docs only if in scope (see row 11) | Completed | 20261116-195856 | 20261116-195856 | no docs change owned; keys documented in row 11 |

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
- **Requirement ID**: REQ-001 (register the six retention keys in the validator)
- **Source issue**: issues/20261114-092857_dbreview008_artifact-retention-gaps.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-054021_dbreview008_artifact-retention-gaps.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-144812
- **Related target files**: `scripts/agent/production_config_validator.py`