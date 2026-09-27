# Implementation Procedure — Resolve Numbering Gap in Follow-up Work Needed

## Goal

Resolve the numbering gap in the Follow-up Work Needed section of `governance_04_documentation-checks.md`: items start at 4 instead of 1, indicating items 1-3 were deleted without renumbering.

## Scope

- Investigate and resolve the numbering gap in the Follow-up Work Needed section
- Renumber remaining items sequentially starting from 1
- Add a note explaining why items 1-3 are absent

## Assumptions

- Items 1-3 corresponded to GV-001, GV-002, GV-003 which have "Existing"/"None" status in the Governance Verification Matrix, indicating their follow-up work was completed
- The section format should remain unchanged
- No content changes to existing entries beyond renumbering

## Design decisions

- Renumber rather than add explanatory notes: the simplest resolution consistent with the plan's intent
- Items 1-3 were completed (Status="Existing", Follow-up="None"), so a brief note suffices

## Alternatives considered

1. Add explanatory notes for each deleted item — rejected as overly verbose; a single consolidated note is sufficient
2. Restore items 1-3 — rejected as unnecessary since their follow-up work is already complete
3. Leave the gap with a single note — rejected per REQ-004 which requires sequential numbering if renumbering is appropriate

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Read lines 315-361 of `governance_04_documentation-checks.md` to confirm current state
2. Verify items 1-3 correspondence by checking the Governance Verification Matrix:
   - GV-001 (Required Front Matter): Status="Existing", Follow-up="None" — completed
   - GV-002 (Valid Document Status): Status="Existing", Follow-up="None" — completed
   - GV-003 (Unique ADR ID): Status="Existing", Follow-up="None" — completed
   - GV-004 does not exist in the matrix
3. Add a single consolidated note after the introductory sentence (line 317) explaining that items 1-3 were completed and removed
4. Renumber the remaining items sequentially from 1 to 11 (previously 4-14)
5. Do not alter the content of any existing entry beyond renumbering

### Method

Edit-based modification of the Follow-up Work Needed section only.

### Details

**Before:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

4. **GV-007**: Implement Duplicate Related Link prohibition check
...
14. **GV-020**: ...
```

**After:**
```
### Follow-up Work Needed

Rules marked "Missing" or "Partial" above need new inspection tools or processes:

Note: Items 1-3 were previously listed for GV-001, GV-002, and GV-003. These items were completed (Status="Existing", Follow-up="None" in the Governance Verification Matrix) and removed without renumbering.

1. **GV-007**: Implement Duplicate Related Link prohibition check
2. **GV-008**: Broaden to cover full issue inventory conformance scope (vocabulary, template, referential integrity)
3. **GV-009**: Implement Needs Confirmation owner and deadline validation
4. **GV-011, GV-012**: Implement cross-document canonical source conflict detection
5. **GV-013**: Extend `stale_patterns` custom rule config to cover canonical document references
6. **GV-014**: Resolved — `check_adr_invariant_matrix.py` (Invariant Matrix cited test-path verification), `check_compat_shims.py`'s `ADR_PROHIBITED_PATTERNS` extension (per-ADR prohibited-pattern registry), and `check_adr_reference.py` (scoped ADR-reference requirement on matrix-named `scripts/*.py` files) ship the three staged checks this item originally requested. Remaining, optional scope: actually running each cited test in CI (this check only verifies the path exists), tracked as a future enhancement, not a gap in the current implementation.
7. **GV-015**: Resolved — `docs/governance_01_documentation-policy.md`'s Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, and Governance Applicability Matrix sections separate the four relation types the previous single graph conflated; closing reference: `issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md`.
8. **GV-016**: Audit auto-check implementations against documentation claims
9. **GV-018**: Add glossary term classification validation
10. **GV-019**: Add metadata field usage policy enforcement
11. **GV-020**: Implement the `read_json_file`-style context-aware detection case (a name retained in source but no longer the current production path); promote `--check-removed-names` from opt-in to default-on once `plans/done/20260903-090104_plan.md` (toolroutedoc)'s corpus fix lands, per `check_compat_shims.py`'s own "report-only until compliant" convention.
    **Extended 2026-09-04** (`plans/done/20260903-093353_plan.md`, REQ-007): `_REMOVED_NAME_PATTERNS` now also flags `SecurityProfile.LOCAL`, `security_profile="local"`, `allow_public_bind`, and an unconditionally-permitted empty `auth_token`/`auth_token_env` as retired runtime-profile terms (all three removed by `localremoval`/`loopbackonly`/`mcpauth`, `plans/done/20260903-091417_plan.md`//). `_is_historical_context`'s marker set was extended with Japanese equivalents (解消/解決/廃止/撤廃/削除済み/確認済み) at the same time, since this repository's docs mix English and Japanese prose and the English-only marker set previously produced false positives on Japanese historical/resolved notes. An unrelated "local" meaning (filesystem, Git, RAG, database, process, localhost paths) is unaffected — the new patterns match only the specific retired identifiers above, not the word "local" itself. Running `--check-removed-names` against the current corpus after this extension found 14 pre-existing findings outside this Plan's own scope (`docs/governance_03`, `00_security_02`, `06_eventbus_01`, ADR-006, ADR-008, and others still describing `allow_public_bind` as current) — these are tracked as a follow-up documentation-drift cleanup, not fixed by this Plan.
```

## Compatibility considerations

N/A — documentation-only change, no code impact.

## Security considerations

N/A — documentation-only change, no security implications.

## Rollback considerations

Simple revert: restore original numbering. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_04_documentation-checks.md | Manual verification against Follow-up Work Needed section | Read lines 315-361 | Numbering gap resolved (sequential 1-N with explanatory note) |

## Completion criteria

- The Follow-up Work Needed section has sequential numbering starting from 1
- A note explaining the absence of items 1-3 is present
- No content changes to existing entries beyond renumbering

## Out of scope

- Changing the content of existing entries
- Modifying any section other than Follow-up Work Needed
- Adding or removing items from the list
- Modifying the Governance Verification Matrix table

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate the cause of the numbering gap | Completed | — | — | |
| 2 | Add explanatory note and renumber items | Completed | — | — | |
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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20260926-183302_followup_work_needed_numbering_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-195358_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-075210
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
