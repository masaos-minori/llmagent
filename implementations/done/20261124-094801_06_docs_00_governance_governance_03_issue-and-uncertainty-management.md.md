## Goal
Update the Approval Ledger (Part 5) so the old pending decisions are withdrawn or narrowed and three new pending items exist, and settle the SHARED-002 Known Issue, without writing any approver, date, or approval sentence (REQ-007).

## Scope
**Release unit**: adr-amendment

- Edits only `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: Part 5 entries and the SHARED-002 entry in Part 1.
- The plan's Phase 1 (add and update entries) and Phase 4 (withdraw entries) both land in this one document; apply them in that order inside one pass.

## Assumptions
- New entry IDs are AAL-039 (Repository Context and Episodic Memory, ADR-008), AAL-040 (removal of EventBus `events.jsonl`, ADR-006), AAL-041 (state-aware retention and replay expiration, ADR-006); the AAL-018 gap is not reused.
- The ledger Rules allow removal of an entry once its pending change is reverted; replacing a withdrawn decision with a new pending entry is not an approval.
- AAL-029 is narrowed, not removed (Plan Assumptions): its Decision and Scope keep only the no-loss statements under the ADR-008 schema-mismatch rule.

## Design decisions
- Entry order is kept ascending by ID; new entries are appended after AAL-038.
- `Approver` and `Date` are `Not recorded` in every new or updated entry.

## Alternatives considered
N/A: the ledger Rules define the only allowed ways to close or add an entry.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Update AAL-024 (line 555): Decision "Scope widened to six SQLite stores (title, Summary, Scope, Recovery Policy Matrix)"; Scope field unchanged apart from the wording "six SQLite stores".
2. Append AAL-039, AAL-040, AAL-041 after AAL-038, each with the six fields (ID, ADR, Decision, Approver, Date, Scope): AAL-039 ADR-008 "Repository Context (non-persistent) and Episodic Memory (the only persistent Agent memory, `session.sqlite` only); removal of memory JSONL, pin, manual writes, and `/memory`"; AAL-040 ADR-006 "Removal of EventBus `events.jsonl`; `eventbus.sqlite` is the sole source of truth"; AAL-041 ADR-006 "EventBus state-aware retention and replay expiration (`replay_position_expired`)".
3. Remove AAL-026 and AAL-027 (their pending bullets are removed from ADR-008 by document 02); narrow AAL-029 (Decision: no-loss statements hold under the ADR-008 schema-mismatch rule; Scope: Decision Detail 9, INV-07).
4. Part 1: remove SHARED-002 (the `memories_vec` classification disappears with the amended matrix, and Part 1 keeps no resolved entries) and add four Known Issue entries with all 17 fields, `Status: open`: EVENTBUS-001 (`events.jsonl` still written by `scripts/eventbus/publish_route.py`), EVENTBUS-002 (no retention, purge, capacity signals, replay floor, or HTTP 410; retention-participant registry undecided), SHARED-003 (agent memory code still implements the old Semantic/Episodic model and memory JSONL), SHARED-004 (lifecycle policies left undecided, for example the Session DB schema-mismatch policy for Episodic Memory). Place EVENTBUS entries after MCP-005 and SHARED entries in the SHARED group in ascending order (ordering convention stated under Part 1 Active Items). Each `Target` is the owning ADR, which must cite the ID in its Known Deviations (documents 01 and 02). Found in Step 3a of this cycle: the checker requires a Known Issue ID for every deviation bullet.

### Method
- Edit entries with the Edit tool in the existing `#### AAL-NNN` heading and bold-field format; confirm no ADR still cites AAL-026 or AAL-027 with `rg -n "AAL-026|AAL-027" docs/10_adr`.

### Details
- Part 5 Rules: never write approval text or an entry for a past approval; the Approval Record of each ADR is not touched here.
- The per-ADR review packages are delivered in the implementation report (UNK-05), not in this file.

## Compatibility considerations
N/A: documentation only; `tools/check_adr_structure.py` reads the `#### AAL-NNN` headings and the ADR bullets.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py` (each cited ID has an entry; each entry has a heading and six fields) and `uv run python tools/check_known_deviation_sync.py`.
- `uv run python tools/check_docs_structure.py` and `uv run python tools/check_metadata_field_policy.py`.

## Completion criteria
- AAL-039 to AAL-041 exist with `Not recorded` approver and date; AAL-024 reads six SQLite stores; AAL-026 and AAL-027 are removed; AAL-029 is narrowed; no ADR cites a missing entry.
- SHARED-002 is removed; EVENTBUS-001, EVENTBUS-002, SHARED-003, SHARED-004 exist with all 17 fields and are cited by the ADR Known Deviations; `uv run python tools/check_known_deviation_sync.py` passes.

## Out of Scope
- Other ledger entries (issue gov005); ADR Approval Records; recording approvals.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update AAL-024, add AAL-039 to AAL-041, withdraw AAL-026 and AAL-027, narrow AAL-029, remove SHARED-002, add four Known Issues per Implementation | Completed | 20261124-095631 | 20261124-095942 | Apply after documents 01 and 02 so no ADR cites a withdrawn entry Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md |
| 2 | Run the structure and metadata checks per Validation plan | Completed | 20261124-095942 | 20261124-100816 | Release unit adr-amendment Blocked: file outside procedure scope - tools/check_docs_structure.py (size ceilings) and registry/manifests/invariant_coverage.yaml (stale generated manifest) ADR checkers, generator, DB-separation, cited ADR tests (75) pass. Fallout approved by user: tools/check_docs_structure.py size ceilings, registry/manifests/invariant_coverage.yaml regenerated |

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
- **Requirement ID**: REQ-007 (Approval Ledger withdrawal, narrowing, and new pending entries)
- **Source issue**: issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-094324_adrdoc001_adr-eventbus-memory-amendment.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-094801
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`