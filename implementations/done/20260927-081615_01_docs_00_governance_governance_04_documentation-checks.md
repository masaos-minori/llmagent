# Implementation Procedure — Resolve GV-011/GV-012/GV-016/GV-018/GV-019 Status/Follow-up Mismatch

## Goal

Resolve the status inconsistency between the Governance Verification Matrix and the Follow-up Work Needed section for GV-011, GV-012, GV-016, GV-018, and GV-019 in `governance_04_documentation-checks.md`: the Matrix marks all five as `Missing` but the Follow-up list contains specific implementation tasks for each.

## Scope

- Evaluate whether each rule's implementation task should be registered as a Known Issue or if the Matrix Status should be updated
- Update the Matrix Status from `Missing` to `Partial` for all five rules (partial automation exists via manual review)
- Modify the Follow-up Work Needed descriptions to match the current state
- Address the numbering gap after modification

## Assumptions

- These rules are not Known Issues (which track documentation-code mismatches) but rather missing tooling capabilities
- Manual review provides partial coverage for all five rules (Manual method column already exists)
- Items 1-3 were previously identified as GV-001, GV-002, GV-003 (completed, removed without renumbering)
- Item 4 (GV-007) was previously identified as completed (Status="Existing", Follow-up="None")
- Item 5 (GV-008) was previously identified as completed (Status="Existing", Follow-up="None")
- The section format should remain unchanged

## Design decisions

- Update Matrix Status from `Missing` to `Partial` for all five rules: manual review provides partial coverage, and "Missing" implies no automation exists at all
- Modify Follow-up Work Needed descriptions to reflect the current state: the tasks are not new implementation goals but refinements of existing manual processes into automation
- Do not register Known Issues: Known Issues track documentation-code mismatches; these are missing tooling capabilities
- Renumber remaining items sequentially from 1: simplest resolution consistent with REQ-003
- Add a note explaining the absence of items 1-5: prevents confusion about missing entries

## Alternatives considered

1. Register Known Issues for all five rules — rejected as Known Issues track documentation-code mismatches, not missing tooling capabilities
2. Remove entries from the Follow-up Work Needed section entirely — rejected as the tasks are genuinely incomplete and should remain visible
3. Leave the mismatch unresolved — rejected as it perpetuates confusion for implementers

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Read lines 301-302, 306-308 of `governance_04_documentation-checks.md` to confirm current Matrix status for GV-011/GV-012/GV-016/GV-018/GV-019
2. Confirm each rule's Method is "Manual" and Gate is "Warning" or "Blocking" — partial coverage exists via manual review
3. Update the Matrix Status from `Missing` to `Partial` for all five rules (lines 301-302, 306-308)
4. Modify the Follow-up Work Needed descriptions to reflect the current state:
   - GV-011/GV-012: Change from "Implement cross-document canonical source conflict detection" to "Automate cross-document canonical source conflict detection (currently manual)"
   - GV-016: Change from "Audit auto-check implementations against documentation claims" to "Automate auto-check implementation audit (currently manual)"
   - GV-018: Change from "Add glossary term classification validation" to "Automate glossary term classification validation (currently manual)"
   - GV-019: Change from "Add metadata field usage policy enforcement" to "Automate metadata field usage policy enforcement (currently manual)"
5. Address the numbering gap after modification: add explanatory note for items 1-5 and renumber remaining items sequentially from 1
6. Do not alter the tools' functionality (REQ-004)
7. Keep changes isolated to `governance_04_documentation-checks.md` (REQ-005)

### Method

Edit-based modification of both the Matrix table and the Follow-up Work Needed section.

### Details

**Before:**

Matrix rows:
```
| GV-011 | Duplicate canonical document specification | Pol | Manual | Human review | PR | Warning | Missing | Register Known Issue |
| GV-012 | Multiple Primary Canonical Sources within the same area | Pol | Manual | Human review | PR | Warning | Missing | Register Known Issue |
| GV-016 | No unimplemented auto-checks documented as implemented | Chk | Manual | Human review | Periodic | Warning | Missing | Register Known Issue |
| GV-018 | Glossary limited to project-specific terms | Meta | Manual | Human review | Periodic | Warning | Missing | Register Known Issue |
| GV-019 | No unnecessary Metadata or Status fields added | Meta | Manual | Human review | Periodic | Warning | Missing | Register Known Issue |
```

Follow-up Work Needed:
```
4. **GV-007**: Implement Duplicate Related Link prohibition check
5. **GV-008**: Broaden to cover full issue inventory conformance scope (vocabulary, template, referential integrity)
6. **GV-009**: Implement Needs Confirmation owner and deadline validation
7. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
8. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
...
11. **GV-016**: Audit auto-check implementations against documentation claims
12. **GV-018**: Add glossary term classification validation
13. **GV-019**: Add metadata field usage policy enforcement
14. **GV-020**: ...
```

**After:**

Matrix rows:
```
| GV-011 | Duplicate canonical document specification | Pol | Manual | Human review | PR | Warning | Partial | Automate cross-document canonical source conflict detection (currently manual) |
| GV-012 | Multiple Primary Canonical Sources within the same area | Pol | Manual | Human review | PR | Warning | Partial | Automate cross-document canonical source conflict detection (currently manual) |
| GV-016 | No unimplemented auto-checks documented as implemented | Chk | Manual | Human review | Periodic | Warning | Partial | Automate auto-check implementation audit (currently manual) |
| GV-018 | Glossary limited to project-specific terms | Meta | Manual | Human review | Periodic | Warning | Partial | Automate glossary term classification validation (currently manual) |
| GV-019 | No unnecessary Metadata or Status fields added | Meta | Manual | Human review | Periodic | Warning | Partial | Automate metadata field usage policy enforcement (currently manual) |
```

Follow-up Work Needed:
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

Note: Items 1-3 were previously listed for GV-001, GV-002, and GV-003. These items were completed (Status="Existing", Follow-up="None" in the Governance Verification Matrix) and removed without renumbering. Item 4 (GV-007) was removed because its follow-up work is complete (Status="Existing", Follow-up="None"). Item 5 (GV-008) was removed because `check_issue_inventory_conformance.py` covers all 5 areas: vocabulary conformance, template field-count, orphaned bullets, closing summary consistency, and referential integrity. Items 6-10 (GV-011, GV-012, GV-016, GV-018, GV-019) were updated: Matrix Status changed from `Missing` to `Partial` (manual review provides partial coverage), and Follow-up descriptions modified to clarify that automation is needed while manual process exists.

1. **GV-011, GV-012**: Automate cross-document canonical source conflict detection (currently manual)
2. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
3. **GV-014**: Resolved — `check_adr_invariant_matrix.py` (Invariant Matrix cited test-path verification), `check_compat_shims.py`'s `ADR_PROHIBITED_PATTERNS` extension (per-ADR prohibited-pattern registry), and `check_adr_reference.py` (scoped ADR-reference requirement on matrix-named `scripts/*.py` files) ship the three staged checks this item originally requested. Remaining, optional scope: actually running each cited test in CI (this check only verifies the path exists), tracked as a future enhancement, not a gap in the current implementation.
4. **GV-015**: Resolved — `docs/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, and Governance Applicability Matrix sections separate the four relation types the previous single graph conflated; closing reference: `issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md`.
5. **GV-016**: Automate auto-check implementation audit (currently manual)
6. **GV-018**: Automate glossary term classification validation (currently manual)
7. **GV-019**: Automate metadata field usage policy enforcement (currently manual)
8. **GV-020**: Implement the `read_json_file`-style context-aware detection case (a name retained in source but no longer the current production path); promote `--check-removed-names` from opt-in to default-on once `plans/done/20260903-090104_plan.md` (toolroutedoc)'s corpus fix lands, per `check_compat_shims.py`'s own "report-only until compliant" convention.
    **Extended 2026-09-04** (`plans/done/20260903-093353_plan.md`, REQ-007): `_REMOVED_NAME_PATTERNS` now also flags `SecurityProfile.LOCAL`, `security_profile="local"`, `allow_public_bind`, and an unconditionally-permitted empty `auth_token`/`auth_token_env` as retired runtime-profile terms (all three removed by `localremoval`/`loopbackonly`/`mcpauth`, `plans/done/20260903-091417_plan.md`//). `_is_historical_context`'s marker set was extended with Japanese equivalents (解消/解決/廃止/撤廃/削除済み/確認済み) at the same time, since this repository's docs mix English and Japanese prose and the English-only marker set previously produced false positives on Japanese historical/resolved notes. An unrelated "local" meaning (filesystem, Git, RAG, database, process, localhost paths) is unaffected — the new patterns match only the specific retired identifiers above, not the word "local" itself. Running `--check-removed-names` against the current corpus after this extension found 14 pre-existing findings outside this Plan's own scope (`docs/governance_03`, `00_security_02`, `06_eventbus_01`, ADR-006, ADR-008, and others still describing `allow_public_bind` as current) — these are tracked as a follow-up documentation-drift cleanup, not fixed by this Plan.
```

## Compatibility considerations

N/A — documentation-only change, no code impact.

## Security considerations

N/A — documentation-only change, no security implications.

## Rollback considerations

Simple revert: restore original Matrix Status values ("Missing") and Follow-up Work Needed descriptions. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Matrix | Read lines 301-302, 306-308 | All five rules have Status="Partial" |
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Follow-up Work Needed | Read lines 315-361 | Descriptions reflect current state; numbering sequential 1-N with explanatory note |

## Completion criteria

- The Matrix Status for GV-011, GV-012, GV-016, GV-018, and GV-019 is `Partial` (not `Missing`)
- The Follow-up Work Needed descriptions for these five rules reflect the current state (automation needed, manual process exists)
- The Follow-up Work Needed numbering is consistent (sequential 1-N with explanatory note)
- No Known Issues registered in governance_03 (these are missing tooling capabilities, not documentation-code mismatches)

## Out of scope

- Modifying the tools' functionality
- Changing any other rule's status
- Registering Known Issues in governance_03_issue-and-uncertainty-management.md
- Adding or removing items beyond GV-011/GV-012/GV-016/GV-018/GV-019

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Evaluate whether each rule should be registered as Known Issue | Completed | — | — | |
| 2 | Update Matrix Status from Missing to Partial for all five rules | Completed | — | — | |
| 3 | Modify Follow-up Work Needed descriptions | Completed | — | — | |
| 4 | Address numbering gap | Completed | — | — | |
| 5 | Manual verification | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260926-183302_gov011_012_016_018_019_status_followup_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-195828_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-081615
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
