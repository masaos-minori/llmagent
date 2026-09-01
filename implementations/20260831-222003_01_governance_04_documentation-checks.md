# Implementation Procedure: Correct GV Verification Matrix and Fix Mismatched Tool Filenames

## Goal

Correct `docs/00_governance_04_documentation-checks.md`'s Governance Verification Matrix to accurately reflect which GV rules are actually implemented by automated tools versus manual review, and fix all mismatched tool filenames referenced throughout the document.

## Scope

- Re-verify each GV rule marked Auto/Existing against actual tool implementations
- Correct Method/Tool/Status/Follow-up columns where they don't match reality
- Fix four mismatched tool filenames throughout the document
- Update Follow-up Work Needed list with newly reclassified Missing rules

## Assumptions

- The mapping between GV rule descriptions and registered check names/descriptions in `check_docs_quality.py` can be determined by reading the function bodies (not just the names)
- The four mismatched tool filenames are the only filename discrepancies in the document
- The existing Missing rows (GV-011 etc.) provide a sufficient template for correcting the Auto rows

## Design decisions

- Phase 1: Apply tool filename corrections first (simple text replacements, low risk)
- Phase 2: Re-verify each GV rule against actual tool implementations (requires reading source code)
- Phase 3: Update Follow-up Work Needed list based on Phase 2 findings
- Phase 4: Verify all changes for consistency

## Alternatives considered

- Could cross-reference all tools simultaneously during Phase 2, but sequential approach reduces cognitive load
- Could batch all GV rules into a single edit, but individual verification ensures accuracy

## Implementation

### Target file

`docs/00_governance_04_documentation-checks.md`

### Procedure

**Phase 1: Tool filename corrections**

1. Replace `check_doc_quality.py` → `check_docs_quality.py` everywhere in the document (Automated Checks headers, Usage examples, Governance Verification Matrix Tool/Review column)
2. Replace `check_no_compat.py` → `check_compat_shims.py` everywhere in the document
3. Replace `check_all_docstrings.py` → `check_docstrings.py` everywhere in the document
4. Replace `validate_docs_structure.py` → `check_docs_structure.py` everywhere in the document

**Phase 2: GV rule re-verification**

5. Read `tools/check_docs_quality.py` and map each registered core check to its actual behavior
6. Re-verify GV-001 against actual implementations; correct Method/Tool/Status/Follow-up as needed
7. Re-verify GV-002 against actual implementations; correct Method/Tool/Status/Follow-up as needed
8. Re-verify GV-003 against actual implementations; correct Method/Tool/Status/Follow-up as needed
9. Re-verify GV-005 against actual implementations; correct Method/Tool/Status/Follow-up as needed
10. Re-verify GV-006 against actual implementations; correct Method/Tool/Status/Follow-up as needed
11. Re-verify GV-007 against actual implementations; correct Method/Tool/Status/Follow-up as needed
12. Re-verify GV-008 against actual implementations; correct Method/Tool/Status/Follow-up as needed
13. Re-verify GV-009 against actual implementations; correct Method/Tool/Status/Follow-up as needed
14. Re-verify GV-013 against actual implementations; correct Method/Tool/Status/Follow-up as needed
15. Cross-reference other tools (`check_docs_consistency.py`, `check_needs_confirmation_inventory.py`, `check_compat_shims.py`, `check_suppression_justification.py`, `check_docstrings.py`, `check_tool_descriptions_sync.py`, `check_docs_structure.py`) for any checks that might be implemented outside `check_docs_quality.py`

**Phase 3: Follow-up Work Needed update**

16. Update Follow-up Work Needed list to include any rule newly reclassified as Missing

**Phase 4: Verification**

17. Verify all four tool filename corrections applied consistently across the entire document
18. Verify no GV rule remains marked Auto/Existing without a verifiable corresponding check

### Method

Document-only modification: search-and-replace for filename corrections, content edits for GV rule classifications.

### Details

- For Phase 1, use exact string replacement to ensure all occurrences are updated consistently
- For Phase 2, read each check function body in `tools/check_docs_quality.py` and trace what it actually checks
- When reclassifying a GV rule from Auto/Existing to Missing, change Method to `Manual`, Tool to `Human review`, Status to `Missing`, and add an entry to Follow-up Work Needed using the same format as existing entries (e.g., "Register Known Issue")
- If a corresponding check exists elsewhere under a different name, correct the Tool column accordingly rather than marking it Missing
- Document partial implementations explicitly in the Tool column (e.g., "Partial: check_docs_quality.py + check_docs_consistency.py")
- Record the evidence basis for each classification (e.g., "Confirmed by reading function body at line X")

## Compatibility considerations

- No behavioral changes; documentation-only correction
- Existing external references to the document remain valid
- The four filename corrections align the document with actual tool filenames, reducing confusion for users following Usage examples

## Security considerations

- None applicable; documentation-only change

## Rollback considerations

- All changes are reversible via git revert if issues arise
- No data loss risk since no content is deleted, only corrected

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_04_documentation-checks.md` | Manual verification of tool filename corrections | Search document for old filenames | No old filenames remain |
| `docs/00_governance_04_documentation-checks.md` | Manual verification of GV rule classifications | Compare each GV row against actual tool capabilities | Each Auto/Existing GV rule has a verifiable check |
| `docs/00_governance_04_documentation-checks.md` | Verify Follow-up Work Needed completeness | Review Follow-up Work Needed list | All newly Missing rules listed |

## Completion criteria

- All four tool filename corrections applied consistently across Automated Checks section headers, Usage examples, and the Governance Verification Matrix's Tool/Review column
- Every GV rule marked Existing/Auto in the matrix has a verifiable, named check function in the tool it cites
- Any GV rule reclassified from Existing to Missing appears in Follow-up Work Needed with a corresponding action item
- No GV rule remains marked Auto/Existing without a verifiable corresponding check

## Out of scope

- Implementing any new automated check to cover a rule found to be Missing
- Modifying any script under `tools/`
- Re-litigating which rules should exist at all
- Renumbering existing GV rule IDs

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Tool filename corrections | Done | — | — | All four filenames corrected |
| 2 | Phase 2: GV rule re-verification | Done | — | — | Verified against actual tool implementations |
| 3 | Phase 3: Follow-up Work Needed update | Done | — | — | Added newly Missing rules |
| 4 | Phase 4: Verification | Done | — | — | Consistency verified via grep |

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
- **Requirement ID**: REQ-001 through REQ-004
- **Source issue**: issues/20260831-162016_govdocs002_verification_matrix_accuracy_and_tool_names.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-222003_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260831-222003
- **Related target files**: docs/00_governance_04_documentation-checks.md
