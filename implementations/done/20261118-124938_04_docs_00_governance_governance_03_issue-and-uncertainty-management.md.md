## Goal
Correct the CSC-001 evidence (REQ-005), record the archived-file re-verification result (REQ-009), and after the decision add the pending ledger entries (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit
- The CSC-001 entry; after the decision, new ledger entries and a registry entry when the decision needs one.
- No archived file is read or edited.

## Assumptions
- Archived issue files under `issues/done/` are not read (UNK-03). The claims about them stay `Needs confirmation`; record that in this procedure's Notes and the final report.
- CSC-001 stays open: closing it needs an ADR-010 edit, which is outside the Plan (UNK-06).
- Ledger ids continue after the existing ones (the next three are AAL-019 for ADR-004, AAL-020 for ADR-005, AAL-021 for ADR-009's Degraded condition); AAL-022 is added only if the ADR-009 transaction boundary correction is treated as a decision change (UNK-05). Read the live ledger before numbering.

## Design decisions
- State present facts only: the identity modules do not exist and nothing references them; no history note.
- A pending ledger entry holds `Not recorded` for approver and date and never records an approval.

## Alternatives considered
Closing CSC-001 was rejected: its remaining action is an ADR-010 edit outside the Plan.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`
### Procedure
1. CSC-001: set `Required action` to say the corpus-identity modules are gone (no `corpus_identity.py` under `scripts/rag/` and no `scripts/` or `tests/` file references it) and that ADR-010's surviving present-tense wording is still to be moved to the withdrawn record or removed, a maintainer decision; set `Validation evidence` to the `rg` result that shows no reference; reword `Impact` so it no longer says the owning decision is open.
2. Record the archived-file re-verification result in the Notes: the three archived issue files were not read; the claims about them stay `Needs confirmation`; no archived file changed.
3. Gate: confirm that the maintainer's decision on the Source plan's option table (UNK-01: option A, B, or C) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Option C changes startup behavior and is a Plan amendment: stop. Write no policy decision and no approval text. Then add one pending entry per ADR change of procedures 05 to 07 in the same six-field format as the existing entries; add a Part 2 registry entry (next `NC-` id, all fifteen fields) only when the decision leaves an inline `Needs confirmation` marker in ADR-004.
### Method
Edit the entry in place; copy the format of the neighboring ledger entries; keep the part headings unchanged.
### Details
- `tools/check_issue_inventory_conformance.py` reads the ledger entries as Part 4 entries, so each ledger entry keeps exactly six fields and no Status field.
- The file stays under the docs size limit; keep entries short.

## Compatibility considerations
N/A: governance text; existing entries are untouched apart from CSC-001.

## Security considerations
N/A: documentation-only change; no approval text and no past-approval entry is written.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_issue_inventory_conformance.py`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_adr_structure.py` (after procedures 05 to 07)

## Completion criteria
- CSC-001 cites only existing paths and current facts, and its remaining action is stated (AC-5).
- The re-verification result is in the Notes and `git status` shows no archived file changed (AC-8).
- The pending ledger entries exist for every ADR change of procedures 05 to 07 (AC-7).

## Out of Scope
- Closing CSC-001.
- Reading or editing files under `issues/done/`.
- Editing ADR-010.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the CSC-001 entry (REQ-005) | Completed | 20261118-130636 | 20261118-130648 | CSC-001 Required action, Validation evidence, and Impact corrected to current facts; rg corpus_identity over scripts/ and tests/ lists no file; CSC-001 stays open (closing needs an ADR-010 edit outside the plan, UNK-06); changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md |
| 2 | Record the archived-file re-verification result (REQ-009) | Completed | 20261118-130648 | 20261118-130648 | Archived issue files (adrrev013, rmcompat001, rmcompat003) were not read and not edited; the claims about them stay Needs confirmation (UNK-03); git status shows no archived file changed |
| 3 | Confirm the maintainer decision (UNK-01) | Completed | 20261118-130648 | 20261118-130648 | Maintainer decision UNK-01 recorded in session 2026-11-18 via AskUserQuestion: option A (availability failure) |
| 4 | Add the pending ledger entries and, if needed, the registry entry (REQ-007) | Completed | 20261118-130648 | 20261118-130648 | Option A: pending ledger entries AAL-019 (ADR-004) and AAL-020 (ADR-005); ADR-009 needs no entry (Degraded set unchanged; boundary correction is a wording alignment per UNK-05). NC-002 registered for the item 8 justification the maintainer must write: inline marker goes on ADR-004 Decision Group 2 item 7 (line 73). The mandatoriness registry covers MCP servers only, so it is not changed |
| 5 | Run the checkers listed in Validation plan | Completed | 20261118-130821 | 20261118-130821 | After procedures 05 to 07: check_adr_structure (every pending bullet cites a ledger entry that exists), NC inventory, known-deviation sync, inventory conformance, docs checkers: pass |

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
- **Requirement ID**: `REQ-005`: CSC-001 evidence; `REQ-007`: pending ledger entries; `REQ-009`: archived-file re-verification
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
