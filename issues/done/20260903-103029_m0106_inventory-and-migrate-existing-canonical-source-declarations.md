# Inventory and migrate existing canonical-source declarations

## Priority
Medium

## Summary
Inventory all existing canonical-source declarations, map them to decision targets and claim types, and migrate validated mappings into the Canonical Source Registry.

## Background
Existing canonical ownership is distributed across governance policy, area guides, ADR indexes, Specifications, References, Operations documents, templates, and informal phrases such as `authoritative`, `primary`, and `source of truth`.

## Problem
The migration must not mechanically convert every Primary document into a canonical source. Each declaration must be assigned to a specific decision target and claim type.

## Reason for Change
The registry (`M-01-04`) and its validator (`M-01-05`) have no value until the repository's actual canonical-source declarations are inventoried and migrated into them — until then, the old hand-maintained area tables remain the de facto system of record.

## Implementation Intent
Produce a complete migration inventory, resolve unambiguous mappings, and explicitly report conflicts or missing information without inventing ownership.

### Required inventory columns

- Decision target
- Claim type
- Current source path
- Current authority wording
- Proposed canonical source
- Owning area
- Conflict status
- Required action
- Manual review required
- Migration status

### Repository search scope

Search active files for at least:

- `canonical`
- `canonical source`
- `authoritative`
- `authority`
- `primary`
- `secondary`
- `source of truth`
- `ultimate authority`
- `most recently reviewed`
- `latest`
- `system of record`

Also inspect:

- Area Canonical Maps
- All area document guides
- ADR index and ADR Front Matter
- Specification indexes
- API and schema references
- Operations and runbooks
- Configuration documentation
- Documentation templates

## Target Files or Areas
Unknown — the exhaustive file list is the output of this issue's own repository search scope (see above), not knowable in advance.

## Required Changes
### Classification rules

1. Do not treat a whole document as canonical for every claim it contains.
2. Assign each declaration to one decision target and claim type.
3. Do not register a source when ownership is ambiguous.
4. Register ambiguous ownership as Needs Confirmation or a governance gap.
5. Register multiple candidate normative sources as a Canonical Source Conflict.
6. Register design-versus-code differences as Known Issues rather than changing the design document automatically.
7. Register deployed-value differences as Configuration Drift.
8. Preserve current behavior and adopted design as separate claims.
9. Confirm that every referenced file exists in the source repository.
10. Do not use paths found only in the concatenated documentation file without verifying the original file.

### Migration requirements

1. Generate the inventory before editing authority mappings.
2. Review all Governance Primary documents by their owned decision target.
3. Separate ADR authority from runtime implementation evidence.
4. Separate Specification authority from Reference content.
5. Remove duplicate hand-maintained mappings after registry migration.
6. Update area guides to link to or render from the registry.
7. Run strict registry validation after migration.
8. Run existing documentation link and structure checks.
9. Keep body-content changes limited to canonical-source declarations and required cross-references.
10. Report unresolved mappings explicitly.

### Required deliverables

- Canonical-source migration inventory
- Updated Canonical Source Registry
- Updated area guides
- List of unresolved Canonical Source Conflicts
- List of missing canonical sources
- List of Needs Confirmation items created by the migration
- Validation output showing the migrated registry passes all implemented checks

## Constraints
Keep body-content changes limited to canonical-source declarations and required cross-references — do not perform unrelated rewrites of area guides or other documents touched during migration, per `AGENTS.md` Global Rule 5.

## Acceptance Criteria
- [ ] All active canonical-authority declarations are included in the inventory.
- [ ] Every migrated mapping has a decision target and claim type.
- [ ] No mapping is created solely from document recency.
- [ ] No whole-document authority is inferred when claims have different types.
- [ ] Existing Governance Primary documents are separated by owned target.
- [ ] All registered source paths exist.
- [ ] Ambiguous mappings are not silently guessed.
- [ ] Duplicate normative ownership is reported as a conflict.
- [ ] Area guides no longer maintain independent authority tables.
- [ ] The migrated registry passes strict validation.
- [ ] Existing documentation structure and link checks pass.
- [ ] Unrelated document content remains unchanged.

## Testing Expectations
Run the `M-01-05` registry validator against the migrated registry (must pass strict validation); run existing documentation structure and link checks (`uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_quality.py`).

## Documentation Impact
Yes — this issue updates area guides and the Canonical Source Registry to reflect the migrated inventory; it also produces the migration inventory and conflict/gap lists as deliverables (see Required deliverables).

## Out of Scope
- Do not fix application implementation deviations in this issue.
- Do not close Known Issues merely because a canonical source has been identified.
- Do not add historical or superseded documents to the active registry.

## Dependencies
Depends on `M-01-04` and `M-01-05`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-04`'s registry schema and `M-01-05`'s validator have landed before running this migration — the migrated registry must pass `M-01-05`'s strict validation as part of this issue's own completion. Generate the inventory before editing any authority mapping. When ownership is ambiguous, register it as Needs Confirmation or a governance gap rather than guessing — do not invent ownership to make the inventory look complete. Verify every referenced file exists in the actual source repository, not only in a concatenated documentation file. Do not perform body-content rewrites beyond canonical-source declarations and required cross-references.
