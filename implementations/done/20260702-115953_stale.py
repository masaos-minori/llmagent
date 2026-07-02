# Implementation: Remove stale Shared/DB documentation history and stale issue references

## Goal

Remove references to deleted source documents and stale issue IDs from active Shared/DB documents, and document current implementation directly.

## Scope

- docs/90_shared_01_overview.md: Remove stale references
- docs/90_shared_04_db_architecture_and_schema.md: Remove references to 07_ref-sqlite.md, 07_spec_db.md, DOCMISS-01, UNDOC-03
- docs/90_shared_05_db_api_and_operations.md: Fix stale reference (DESIGN-01)
- docs/90_shared_90_inconsistencies_and_known_issues.md: Confirm no stale issue IDs (only IMPORT-01, DESIGN-02 remain)
- Document workflow.sqlite and eventbus.sqlite as current specs
- Remove deletion history notes / migration notes

## Assumptions

1. 07_ref-sqlite.md, 07_spec_db.md don't exist in docs/ (deleted)
2. 90_shared_90 only has IMPORT-01, DESIGN-02 (no stale IDs — confirmed by grep)
3. DESIGN-01 is referenced at line 213 of 90_shared_05 with "resolved; extensibility rationale documented here" note — this reference should be removed

## Implementation

### Target files

- docs/90_shared_04_db_architecture_and_schema.md: Remove stale references
- docs/90_shared_05_db_api_and_operations.md: Fix DESIGN-01 reference
- docs/90_shared_01_overview.md: Remove stale references if any

### Procedure

#### Phase 1: Full-text search for target locations

Run `rg -n "07_ref-sqlite|07_spec_db|DOCMISS-01|UNDOC-03|TYPE-01|DESIGN-01|UNIMPL-01" docs/` to identify all locations.

#### Phase 2: Fix 90_shared_04

- Line 74: Remove or shorten comment about workflow_schema.py reference
- Lines 77-78: Delete Note block referencing 07_ref-sqlite.md / 07_spec_db.md
- Lines 291-292: Delete Note block about workflow.sqlite documentation
- Line 360: Remove UNDOC-03 reference (replace with direct trigger description)
- Add eventbus.sqlite to DB file table (per plans 52-53)

#### Phase 3: Fix 90_shared_05

- Line 213: Remove DESIGN-01 reference (delete "resolved; extensibility rationale documented here" note)

#### Phase 4: Final verification

- Run `rg -n "07_ref-sqlite|07_spec_db|DOCMISS-01|UNDOC-03|TYPE-01|DESIGN-01|UNIMPL-01" docs/` to confirm 0 matches

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No stale references | `rg -n "07_ref-sqlite\|07_spec_db\|DOCMISS-01\|UNDOC-03\|TYPE-01\|DESIGN-01\|UNIMPL-01" docs/` | 0 matches |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
