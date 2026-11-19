## Goal

Regenerate the config-ownership fact manifest from the updated registry so the four security-relevant fields show their validators (REQ-004: manifest regenerated, never hand-edited).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 3, after the hot-reload-validation unit lands)

- In scope: `registry/manifests/config_ownership.yaml` via regeneration only.

## Assumptions
- The manifest is generated from `scripts/agent/services/config_field_registry.py` by `_MANIFEST_SOURCES` in `tools/generate_reference_table.py` (`:467`); regeneration order therefore must follow the seq 01 wiring and seq 02/03 behavior changes.
- `config_ownership.yaml` is a fact manifest with no document-backed domain (no guarded doc block, `tools/generate_reference_table.py:454-457`), so no other document changes with it.

## Design decisions
- N/A: no design content — regenerated artifact only.

## Alternatives considered
- N/A: hand editing is forbidden by the Plan's Out-of-Scope.

## Implementation
### Target file
`registry/manifests/config_ownership.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests`.
2. Inspect the diff: the four rows keep `hot_reloadable: true` and gain `validator:` names — `allowed_tools` → `validate_allowed_tools`, `approval_risk_rules` → `validate_approval_risk_rules`, `tool_safety_tiers` → `validate_tool_safety_tiers`, `allowed_root` → `validate_allowed_root` (the current rows at `:2-9,30-33,142-145` show `validator: null`).
3. Reject the change if the generator rewrites unrelated manifest rows beyond the four — that would mean the registry edit reached outside its scope; report instead of editing by hand.

### Method
- No manual edits to the YAML at any point.

### Details
- N/A.

## Compatibility considerations
- No guarded doc block or generated-document block consumes this manifest (Documentation Impact of the Plan).

## Security considerations
- The manifest is the operator-facing inventory of which fields a reload validates; a stale `validator: null` row hides the new gate.

## Rollback considerations
- Re-run the generator against the reverted registry, or revert the commit.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Drift check | `uv run python tools/generate_reference_table.py --check` | Exit 0, no drift |

## Completion criteria
- `--check` passes and the four rows name their validators (AC-003 wording: a `validator` name for each of the four fields).

## Out of Scope
- Any hand edit of `registry/manifests/*.yaml`; changes to the generator itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run `tools/generate_reference_table.py --manifests` after seq 01-04 land | Pending | — | — | |
| 2 | Run `--check` and inspect the four-row diff | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (manifest regenerated from the registry)
- **Source issue**: issues/20261117-123004_adrchk004_hot-reload-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-094759_adrchk004_hot-reload-validation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-101805
- **Related target files**: `registry/manifests/config_ownership.yaml`
