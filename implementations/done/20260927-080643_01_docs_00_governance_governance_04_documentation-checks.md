# Implementation Procedure — Resolve GV-007 Status Inconsistency

## Goal

Resolve the status inconsistency between the Governance Verification Matrix and the Follow-up Work Needed section for GV-007 in `governance_04_documentation-checks.md`: the Matrix marks GV-007 as `Existing` but the Follow-up list still contains it as an uncompleted task.

## Scope

- Remove the GV-007 entry from the Follow-up Work Needed section
- Verify the Matrix Status remains `Existing`
- Address the numbering gap after removal

## Assumptions

- GV-007 is genuinely completed (Status="Existing", Follow-up="None" in the Matrix)
- `check_docs_structure.py` implements duplicate related link detection (confirmed at line 290)
- Items 1-3 were previously identified as GV-001, GV-002, GV-003 (completed, removed without renumbering)
- The section format should remain unchanged

## Design decisions

- Remove GV-007 from Follow-up Work Needed: the Matrix confirms completion
- Renumber remaining items sequentially from 1: simplest resolution consistent with REQ-003
- Add a note explaining the absence of items 1-3: prevents confusion about missing entries

## Alternatives considered

1. Leave GV-007 in both locations — rejected as it perpetuates the contradiction
2. Update the Matrix Status instead of removing from Follow-up — rejected per REQ-004 (do not alter Matrix Status column)
3. Add explanatory notes for deleted items — rejected as overly verbose; a single consolidated note suffices

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Read lines 290-298 of `governance_04_documentation-checks.md` to confirm GV-007 Matrix status
2. Confirm duplicate related link detection is implemented in `tools/check_docs_structure.py` (REQ-001 justification)
3. Remove the GV-007 entry from the Follow-up Work Needed section (line 319)
4. Verify the Matrix Status for GV-007 remains `Existing` (REQ-002)
5. Address the numbering gap after removal: add explanatory note for items 1-3 and renumber remaining items sequentially from 1
6. Do not alter the Matrix Status column (REQ-004)
7. Do not modify `check_docs_structure.py`'s existing functionality (REQ-005)

### Method

Edit-based modification of the Follow-up Work Needed section only.

### Details

**Before:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

4. **GV-007**: Implement Duplicate Related Link prohibition check
5. **GV-008**: Broaden to cover full issue inventory conformance scope (vocabulary, template, referential integrity)
...
14. **GV-020**: ...
```

**After:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

Note: Items 1-3 were previously listed for GV-001, GV-002, and GV-003. These items were completed (Status="Existing", Follow-up="None" in the Governance Verification Matrix) and removed without renumbering. Item 4 (GV-007) was removed because its follow-up work is complete (Status="Existing", Follow-up="None").

1. **GV-008**: Broaden to cover full issue inventory conformance scope (vocabulary, template, referential integrity)
2. **GV-009**: Implement Needs Confirmation owner and deadline validation
3. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
4. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
5. **GV-014**: Resolved — `check_adr_invariant_matrix.py` (Invariant Matrix cited test-path verification), `check_compat_shims.py`'s `ADR_PROHIBITED_PATTERNS` extension (per-ADR prohibited-pattern registry), and `check_adr_reference.py` (scoped ADR-reference requirement on matrix-named `scripts/*.py` files) ship the three staged checks this item originally requested. Remaining, optional scope: actually running each cited test in CI (this check only verifies the path exists), tracked as a future enhancement, not a gap in the current implementation.
6. **GV-015**: Resolved — `docs/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, and Governance Applicability Matrix sections separate the four relation types the previous single graph conflated; closing reference: `issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md`.
7. **GV-016**: Audit auto-check implementations against documentation claims
8. **GV-018**: Add glossary term classification validation
9. **GV-019**: Add metadata field usage policy enforcement
10. **GV-020**: Implement the `read_json_file`-style context-aware detection case (a name retained in source but no longer the current production path); promote `--check-removed-names` from opt-in to default-on once `plans/done/20260903-090104_plan.md` (toolroutedoc)'s corpus fix lands, per `check_compat_shims.py`'s own "report-only until compliant" convention.
    **Extended 2026-09-04** (`plans/done/20260903-093353_plan.md`, REQ-007): `_REMOVED_NAME_PATTERNS` now also flags `SecurityProfile.LOCAL`, `security_profile="local"`, `allow_public_bind`, and an unconditionally-permitted empty `auth_token`/`auth_token_env` as retired runtime-profile terms (all three removed by `localremoval`/`loopbackonly`/`mcpauth`, `plans/done/20260903-091417_plan.md`//). `_is_historical_context`'s marker set was extended with Japanese equivalents (解消/解決/廃止/撤廃/削除済み/確認済み) at the same time, since this repository's docs mix English and Japanese prose and the English-only marker set previously produced false positives on Japanese historical/resolved notes. An unrelated "local" meaning (filesystem, Git, RAG, database, process, localhost paths) is unaffected — the new patterns match only the specific retired identifiers above, not the word "local" itself. Running `--check-removed-names` against the current corpus after this extension found 14 pre-existing findings outside this Plan's own scope (`docs/governance_03`, `00_security_02`, `06_eventbus_01`, ADR-006, ADR-008, and others still describing `allow_public_bind` as current) — these are tracked as a follow-up documentation-drift cleanup, not fixed by this Plan.
```

## Compatibility considerations

N/A — documentation-only change, no code impact.

## Security considerations

N/A — documentation-only change, no security implications.

## Rollback considerations

Simple revert: restore original content including GV-007 entry. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Follow-up Work Needed section | Read lines 315-361 | GV-007 entry removed; numbering sequential 1-N with explanatory note |
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Matrix | Read line 298 | GV-007 Status remains `Existing` |

## Completion criteria

- The GV-007 entry does not exist in the Follow-up Work Needed section
- The Matrix's GV-007 Status remains `Existing`
- The Follow-up Work Needed numbering is consistent (sequential 1-N with explanatory note)

## Out of scope

- Modifying the Matrix Status column
- Changing any other rule's status
- Modifying `check_docs_structure.py`'s existing functionality
- Adding or removing items beyond GV-007

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm GV-007 is completed via Matrix and check_docs_structure.py | Completed | — | — | |
| 2 | Remove GV-007 entry and address numbering gap | Completed | — | — | |
| 3 | Manual verification | Completed | — | — | |

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
- **Source issue**: issues/20260926-183302_gov007_status_followup_mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-195525_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-080643
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
