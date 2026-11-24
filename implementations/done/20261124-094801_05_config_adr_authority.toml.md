## Goal
Add only the necessary supplemental authority entries between ADR-006 and ADR-008 so ADR-006 stays the primary authority for EventBus persistence, delivery, replay, and retention and ADR-008 stays the primary authority for store separation and lifecycle policy (REQ-008).

## Scope
**Release unit**: adr-amendment

- Edits only `config/adr_authority.toml`. The ADR front matter `related` lists and the `adr_edge` rows (ADR-008 Governs ADR-006; ADR-006 Reference ADR-008) already exist and stay unchanged.

## Assumptions
- Each decision target keeps exactly one `primary_adr`; only `supplemental_adrs` entries are added, each with a `limit` text.
- If a checker shows an entry is redundant, the row is reduced through an approved Plan amendment (Plan Risks); this document does not add a speculative edge.

## Design decisions
- `eventbus.persistence` gains `{ adr = "ADR-008", limit = ... }` for separation and lifecycle policy (backup, restore, schema mismatch, capacity monitoring) of `eventbus.sqlite` as one of six stores; `db.recovery-separation` gains `{ adr = "ADR-006", limit = ... }` for EventBus retention, replay-floor, and DLQ state semantics.

## Alternatives considered
N/A: adding a third decision target or a new `adr_edge` row is not needed because the edges already cover both directions.

## Implementation
### Target file
`config/adr_authority.toml`

### Procedure
1. Edit the `[[authority]]` block of `decision_target = "eventbus.persistence"`: append the ADR-008 supplemental entry to `supplemental_adrs` (the existing ADR-013 entry stays).
2. Edit the `[[authority]]` block of `decision_target = "db.recovery-separation"`: replace `supplemental_adrs = []` with one ADR-006 entry.

### Method
- Use the existing inline-table style `{ adr = "ADR-0NN", limit = "..." }` of neighboring blocks, with a limit text that names the narrow scope.

### Details
- Do not change `primary_adr` values, `adr_edge` rows, or `[[assumption]]` entries.
- After editing, run `uv run python tools/generate_adr_authority.py` (index document 03 owns the guarded-block refresh) and the authority checkers.

## Compatibility considerations
N/A: configuration is read only by the ADR checkers and generator; no runtime consumer exists (no match under `scripts/` or `deploy/`).

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit and regenerate the index blocks.

## Validation plan
- `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_reference.py`, `uv run python tools/generate_adr_authority.py --check`.
- `uv run pytest tests/tools/test_adr_authority.py tests/tools/test_generate_adr_authority.py -q`.

## Completion criteria
- Both targets still have one primary ADR, no cycle is reported, and the generated index blocks match the file.

## Out of Scope
- Changing primary owners or `adr_edge` rows; any runtime configuration; deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two supplemental entries per Implementation | Completed | 20261124-095609 | 20261124-095942 | Changed: config/adr_authority.toml |
| 2 | Run the authority, reference, and generator checks per Validation plan | Completed | 20261124-095942 | 20261124-100816 | Release unit adr-amendment Blocked: file outside procedure scope - tools/check_docs_structure.py (size ceilings) and registry/manifests/invariant_coverage.yaml (stale generated manifest) ADR checkers, generator, DB-separation, cited ADR tests (75) pass. Fallout approved by user: tools/check_docs_structure.py size ceilings, registry/manifests/invariant_coverage.yaml regenerated |

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
- **Requirement ID**: REQ-008 (supplemental authority edges)
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-094324_adrdoc001_adr-eventbus-memory-amendment.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-094801
- **Related target files**: `config/adr_authority.toml`