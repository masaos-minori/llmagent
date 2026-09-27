# Implementation Procedure — Resolve GV-008/GV-009 Status/Follow-up Mismatch

## Goal

Resolve the status inconsistency between the Governance Verification Matrix and the Follow-up Work Needed section for GV-008 and GV-009 in `governance_04_documentation-checks.md`: the Matrix marks both as `Existing` but the Follow-up list still contains implementation tasks for each.

## Scope

- Evaluate the current coverage of `check_issue_inventory_conformance.py` against GV-008 requirements
- Evaluate the current coverage of `check_needs_confirmation_inventory.py` against GV-009 requirements
- Remove GV-008 entry from the Follow-up Work Needed section (fully implemented)
- Keep GV-009 entries unchanged (already consistent: Status="Existing", Follow-up="None")
- Address the numbering gap after GV-008 removal

## Assumptions

- GV-008 is fully implemented: `check_issue_inventory_conformance.py` covers all 5 areas (vocabulary, template field-count, orphaned bullets, closing summary, referential integrity)
- GV-009 is already consistent: Status="Existing", Follow-up="None" — no change needed
- Items 1-3 were previously identified as GV-001, GV-002, GV-003 (completed, removed without renumbering)
- Item 4 (GV-007) was previously identified as completed (Status="Existing", Follow-up="None")
- The section format should remain unchanged

## Design decisions

- Remove GV-008 from Follow-up Work Needed: the tool covers all 5 areas specified in GV-008
- Do not modify GV-009 entries: already consistent (Status="Existing", Follow-up="None")
- Renumber remaining items sequentially from 1: simplest resolution consistent with REQ-003
- Add a note explaining the absence of items 1-4: prevents confusion about missing entries

## Alternatives considered

1. Update the Matrix Status to `Partial` for GV-008 — rejected as the tool covers all 5 areas; "Partial" would understate the current state
2. Modify the Follow-up Work Needed descriptions instead of removing entries — rejected as overly verbose; removal is cleaner
3. Leave the mismatch unresolved — rejected as it perpetuates confusion for implementers

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Read lines 299-300 of `governance_04_documentation-checks.md` to confirm Matrix status for GV-008/GV-009
2. Confirm GV-008 coverage by reviewing `tools/check_issue_inventory_conformance.py` docstring (lines 1-18): covers vocabulary, template field-count, orphaned bullets, closing summary, referential integrity — all 5 areas
3. Confirm GV-009 coverage by reviewing `tools/check_needs_confirmation_inventory.py` docstring (lines 1-24): covers stale resolved markers, untracked inline markers, declared field count, missing NC fields (including Assigned To/Resolution Target)
4. Remove the GV-008 entry from the Follow-up Work Needed section (line 320)
5. Verify the Matrix Status for GV-008 remains `Existing` (REQ-002)
6. Verify the Matrix Status for GV-009 remains `Existing` and Follow-up remains `None` (no change needed)
7. Address the numbering gap after removal: add explanatory note for items 1-4 and renumber remaining items sequentially from 1
8. Do not alter the Matrix Status column (REQ-004)
9. Do not modify the tools' functionality (REQ-005)

### Method

Edit-based modification of the Follow-up Work Needed section only.

### Details

**Before:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

4. **GV-007**: Implement Duplicate Related Link prohibition check
5. **GV-008**: Broaden to cover full issue inventory conformance scope (vocabulary, template, referential integrity)
6. **GV-009**: Implement Needs Confirmation owner and deadline validation
7. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
...
14. **GV-020**: ...
```

**After:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

Note: Items 1-3 were previously listed for GV-001, GV-002, and GV-003. These items were completed (Status="Existing", Follow-up="None" in the Governance Verification Matrix) and removed without renumbering. Item 4 (GV-007) was removed because its follow-up work is complete (Status="Existing", Follow-up="None"). Item 5 (GV-008) was removed because `check_issue_inventory_conformance.py` covers all 5 areas: vocabulary conformance, template field-count, orphaned bullets, closing summary consistency, and referential integrity.

1. **GV-009**: Implement Needs Confirmation owner and deadline validation
2. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
3. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
4. **GV-014**: Resolved — `check_adr_invariant_matrix.py` (Invariant Matrix cited test-path verification), `check_compat_shims.py`'s `ADR_PROHIBITED_PATTERNS` extension (per-ADR prohibited-pattern registry), and `check_adr_reference.py` (scoped ADR-reference requirement on matrix-named `scripts/*.py` files) ship the three staged checks this item originally requested. Remaining, optional scope: actually running each cited test in CI (this check only verifies the path exists), tracked as a future enhancement, not a gap in the current implementation.
5. **GV-015**: Resolved — `docs/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, and Governance Applicability Matrix sections separate the four relation types the previous single graph conflated; closing reference: `issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md`.
6. **GV-016**: Audit auto-check implementations against documentation claims
7. **GV-018**: Add glossary term classification validation
8. **GV-019**: Add metadata field usage policy enforcement
9. **GV-020**: Implement the `read_json_file`-style context-aware detection case (a name retained in source but no longer the current production path); promote `--check-removed-names` from opt-in to default-on once `plans/done/20260903-090104_plan.md` (toolroutedoc)'s corpus fix lands, per `check_compat_shims.py`'s own "report-only until compliant" convention.
    **Extended 2026-09-04** (`plans/done/20260903-093353_plan.md`, REQ-007): `_REMOVED_NAME_PATTERNS` now also flags `SecurityProfile.LOCAL`, `security_profile="local"`, `allow_public_bind`, and an unconditionally-permitted empty `auth_token`/`auth_token_env` as retired runtime-profile terms (all three removed by `localremoval`/`loopbackonly`/`mcpauth`, `plans/done/20260903-091417_plan.md`//). `_is_historical_context`'s marker set was extended with Japanese equivalents (解消/解決/廃止/撤廃/削除済み/確認済み) at the same time, since this repository's docs mix English and Japanese prose and the English-only marker set previously produced false positives on Japanese historical/resolved notes. An unrelated "local" meaning (filesystem, Git, RAG, database, process, localhost paths) is unaffected — the new patterns match only the specific retired identifiers above, not the word "local" itself. Running `--check-removed-names` against the current corpus after this extension found 14 pre-existing findings outside this Plan's own scope (`docs/governance_03`, `00_security_02`, `06_eventbus_01`, ADR-006, ADR-008, and others still describing `allow_public_bind` as current) — these are tracked as a follow-up documentation-drift cleanup, not fixed by this Plan.
```

## Compatibility considerations

N/A — documentation-only change, no code impact.

## Security considerations

N/A — documentation-only change, no security implications.

## Rollback considerations

Simple revert: restore original content including GV-008 entry. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Follow-up Work Needed section | Read lines 315-361 | GV-008 entry removed; numbering sequential 1-N with explanatory note |
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Matrix | Read line 299 | GV-008 Status remains `Existing` |
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Matrix | Read line 300 | GV-009 Status remains `Existing`, Follow-up remains `None` |

## Completion criteria

- The GV-008 entry does not exist in the Follow-up Work Needed section
- The Matrix's GV-008 Status remains `Existing`
- The Matrix's GV-009 Status remains `Existing` and Follow-up remains `None`
- The Follow-up Work Needed numbering is consistent (sequential 1-N with explanatory note)

## Out of scope

- Modifying the Matrix Status column
- Changing any other rule's status
- Modifying `check_issue_inventory_conformance.py`'s existing functionality
- Modifying `check_needs_confirmation_inventory.py`'s existing functionality
- Adding or removing items beyond GV-008

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Evaluate GV-008 coverage via check_issue_inventory_conformance.py | Completed | — | — | |
| 2 | Evaluate GV-009 coverage via check_needs_confirmation_inventory.py | Completed | — | — | |
| 3 | Remove GV-008 entry and address numbering gap | Completed | — | — | |
| 4 | Manual verification | Completed | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260926-183302_gov008_009_status_followup_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-195651_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-081216
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
