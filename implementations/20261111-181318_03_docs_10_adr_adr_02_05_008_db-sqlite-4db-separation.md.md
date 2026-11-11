## Goal

Harden `adr_02_05_008` (ADR-008) by removing the self-contradiction whose fix is unambiguous (Decision Detail #7/#8 wording, `REQ-003`) and by routing the genuinely ambiguous items to a maintainer decision without fabricating a resolution or an approval record (`memories_vec` correct classification `REQ-004`, Dry Run fix-vs-record `REQ-005`). The ADR index (`adr_01_index`) is verified to still track ADR-008 after the edits (`REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The Decision Details are explicitly numbered from line 114, so each clause under change can be edited in place without restructuring the list.
- The two confirmed self-contradictions are handled differently: the `db_07` 9.2/9.5 pair is resolved by `REQ-002` (this Plan's other procedure), while ADR-008's Decision #7/#8 wording is the one unambiguous wording fix; `memories_vec` classification, Dry Run fix-vs-record, Negative Consequences, Implementation References completeness, and INV numbering require maintainer input.
- Every byte outside the three clauses under change stays identical, so `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `check_known_deviation_sync.py` measure only intent (Plan Risks).
- ADR amendments require a maintainer approval record written by a maintainer; this Plan records the requirement and fabricates none.
- ADR-008 may also be edited by other concurrent frozen plans (the Plan notes adrrev008, and other plans target the same ADR). Confirm no conflicting in-flight edit lands first, and land this edit in the same commit as the other adrrev009 procedures on non-overlapping sections.

## Design decisions

- Keep the change documentation-only and localized to three clauses: Decision Detail #7 wording (`REQ-003`), the `memories_vec` dual-listing flag (`REQ-004`), and the Dry Run journal-mode deviation entry (`REQ-005`).
- For `REQ-003` preserve the factually accurate Decision Detail #8 verbatim and adjust only Decision Detail #7's wording so the two no longer read as contradictory.
- For `REQ-004` and `REQ-005` do not resolve the underlying business/policy question; document the contradiction and the deviation and assign resolution to a maintainer. Record neither a chosen classification nor an approval.
- Do not touch the `### Automated Tests` Implementation cells (non-empty cells and resolving citations are guarded by `check_adr_invariant_matrix.py`) or any invariant-matrix field.

## Alternatives considered

- N/A for `REQ-003`: a wording-only change carries no runtime, persistence, or public-interface impact.
- For `REQ-004` and `REQ-005` the alternatives are themselves maintainer decisions (for `memories_vec`: reclassify in the matrix versus leave and flag; for Dry Run: fix the code versus record the deviation). These are recorded as Unknowns in the Plan (UNK-02/UNK-03) and are not chosen here.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure

1. **`REQ-003` — remove the Decision #7/#8 textual tension.** Read the current Decision Details (heading at line 112). Preserve Decision Detail #8 (current line 121) verbatim. Reword Decision Detail #7 (current line 120) so it states that the logical IDs identify the same entity across databases and correlate related rows at query time as a *static logical reference*, explicitly not a live EventBus publish/consume path — the reading that contradicts #8. Keep every other byte of the file identical.
2. **`REQ-004` — flag the `memories_vec` dual-listing for a maintainer.** In `## Known Deviations` (heading at line 348), record that `session.sqlite` lists `memories_vec` under both "System of record" (line 92) and "Derived or rebuildable data" (line 93), that a store cannot be both, and that the correct classification is pending a maintainer decision. State only that a contradiction exists; do not assert which classification is correct.
3. **`REQ-005` — route the Dry Run journal-mode deviation to a maintainer.** Do not edit the `## Known Deviations` body yet. Instead record in this procedure's completion criteria that a maintainer must choose between (a) fixing Dry Run in code so no rollback-journal-to-WAL switch occurs, or (b) recording the deviation in `## Known Deviations` plus the governance ledger. Fabricate no approval.
4. **`REQ-006` — verify the ADR index still tracks ADR-008.** Read `docs/10_adr/adr_01_index.md` and confirm the ADR-008 row still carries the title "Separating SQLite into Four Databases", domain `05 db`, and INV-01 to INV-05. Update `adr_01_index` only if a field diverges (governance-gated amendment record); the edits in steps 1-3 change none of these fields, so no update is expected.

### Method

- **`REQ-003` (current line 120).** Replace the current text — *"Logical IDs such as Session ID, Workflow ID, and Event ID are used to relate data across DBs."* — with wording that keeps the accurate content (logical IDs correlate rows across databases) but removes the implication that conflicts with #8 (that events flow through the EventBus). Suggested wording: *"Logical IDs such as Session ID, Workflow ID, and Event ID identify the same entity across databases and are used to join related rows at query time. This is a static logical reference, not a live EventBus publish/consume path (see Decision Detail #8)."* Confirm the replacement removes the contradiction while preserving accuracy; if the accurate content itself turns out to be wrong (not just awkward), stop and route it to a maintainer rather than guessing. Preserve Decision Detail #8 (current line 121) byte-for-byte.
- **`REQ-004`.** Under `## Known Deviations` (current line 348, currently "Not applicable" at line 350), add a single prose bullet describing the structural contradiction and marking it pending a maintainer decision. Use prose only — no `### <ID>` Known Issue citation — so `check_known_deviation_sync.py` reports no dangling reference. Do not reclassify `memories_vec` in the Recovery Policy Matrix (lines 92/93); the correct classification is a maintainer business decision (UNK-02). If a maintainer later decides to track this formally, they create the Known Issue in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 (Target `adr_02_05_008...`) and the citation is added to this section; that handoff is the maintainer's.
- **`REQ-005`.** The `### Automated Tests` row at line 312 documents that Dry Run leaves the target DB unchanged for the covered results, with the parenthetical note that "a rollback-journal file is switched to WAL when opened and is not covered" — the journal-mode deviation. The `## Known Deviations` section (line 350) currently says "Not applicable", which is inconsistent with that documented edge. Do not resolve which side wins. If the maintainer chooses to record the deviation, model the entry on `adr_02_01_004`'s `## Known Deviations` (currently "Not applicable" at its lines 310-312) and add the matching Known Issue to the governance ledger first; if the maintainer chooses a code fix, add a regression to `tests/db/test_db_recovery.py`. Either way the decision and its approval record belong to a maintainer.
- **`REQ-006`.** No edit is expected; the step is a verification gate.

### Details

- Evidence for the claims above (verified against current source, HEAD `e700efa5f`):
  - **Decision Details** (heading `### Decision Details`, line 112). Decision Detail #7 (line 120) reads *"Logical IDs such as Session ID, Workflow ID, and Event ID are used to relate data across DBs."* Decision Detail #8 (line 121) reads *"Cross-DB consistency is guaranteed by idempotent processing and state reconciliation. No runtime component publishes to or consumes from the EventBus, so Events are not a consistency mechanism."* #7 lists "Event ID" among the cross-DB correlation keys, which reads as if events flow through the EventBus, while #8 denies that any runtime component publishes to or consumes from the EventBus — the textual tension the plan resolves by wording alone, without a factual correction.
  - **`memories_vec` dual-listing.** In the Recovery Policy Matrix, the "System of record" row (line 92) lists `session.sqlite` as `sessions, messages, memories, memories_vec`; the "Derived or rebuildable data" row (line 93) lists `session.sqlite` as `memories_vec (from memories)`. One store cannot be both system of record and derived/rebuildable.
  - **Dry Run deviation.** The `### Automated Tests` row at line 312 (INV-16) states Dry Run does not act on the target DB for the covered results, with the parenthetical that "a rollback-journal file is switched to WAL when opened and is not covered". The `## Known Deviations` heading is at line 348 and its body at line 350 currently reads "Not applicable".
  - **Index still tracks ADR-008.** `adr_01_index` line 52 records ADR-008, title "Separating SQLite into Four Databases", domain `05 db`; the invariant-matrix rows (lines 192-193) track ADR-008 INV-01 to INV-05. The wording edits in steps 1-3 change none of these indexed fields, so no index modification is required.
  - Reference model for a `## Known Deviations` entry: `adr_02_01_004` has the heading at line 310 and "Not applicable" at line 312.
- Do not fabricate: the `memories_vec` correct classification, the Dry Run fix-vs-record choice, and the maintainer approval record are all a maintainer's to make. Name the contradiction and the deviation; resolve nothing.
- Keep every other byte of the file identical (Plan Risks: scope each edit to the clause under change; re-run `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py` against `HEAD` before committing).

## Compatibility considerations

- N/A: documentation-only; no source, config, schema, migration, deployment, or public-interface change. Editing ADR-008 propagates through `check_adr_structure.py`, `check_adr_invariant_matrix.py`, and `check_known_deviation_sync.py`; those gates bound the blast radius.

## Security considerations

- N/A: no security-relevant behavior change. Documenting a known deviation improves operator awareness but changes no boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Action | Tool / Command | Expected Outcome |
|---|---|---|
| Structural + invariant + Known Deviation sync for ADR-008 | `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py` | No invariant/reference/Known Deviation changed outside intent; no dangling Known Issue ID; no resolved-item bullet |
| ADR index still tracks ADR-008 | `uv run python tools/check_adr_structure.py` (ADR-index gate) | ADR-008 entry (title, domain `05 db`, INV-01–05) unchanged |
| Cross-domain claim consistency (db domain) | `uv run python tools/check_docs_consistency.py --domain db` | Pass |
| Japanese-text policy | `uv run python tools/check_docs_japanese.py` | Pass (English only) |

## Completion criteria

- Decision Detail #7 (line 120) no longer implies a live EventBus publish/consume path; Decision Detail #8 (line 121) preserved verbatim; no new internal contradiction introduced.
- `## Known Deviations` flags the `memories_vec` dual-listing (lines 92/93) as a structural contradiction pending a maintainer decision, without asserting the correct classification.
- The Dry Run journal-mode deviation (Automated Tests line 312 vs `## Known Deviations` line 350) is recorded as a pending maintainer decision (code fix or deviation record); no approval record is fabricated.
- `adr_01_index` still tracks ADR-008 (title, domain, INV-01–05); no index edit made unless it diverges.
- `check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_docs_consistency.py --domain db`, and `check_docs_japanese.py` pass.

## Out of Scope

- Resolving the `memories_vec` classification (maintainer decision; UNK-02).
- Choosing to fix Dry Run in code versus record the deviation (maintainer decision; UNK-03).
- Editing Negative Consequences, Implementation References completeness, or INV numbering (maintainer decisions per the Plan).
- Modifying the `### Automated Tests` Implementation cells or any invariant-matrix field.
- Amending `adr_01_index` unless a tracked field diverges (governance-gated; REQ-006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (clarify ADR-008 Decision #7/#8 wording), `REQ-004` (flag `memories_vec` dual-listing for a maintainer decision), `REQ-005` (record the Dry Run journal-mode deviation per a maintainer decision), `REQ-006` (verify the ADR index still tracks ADR-008)
- **Source issue**: `issues/20261109-112922_adrrev009_adr008-recovery-align.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-233648_adrrev009_adr008-recovery-align.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-181318
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
