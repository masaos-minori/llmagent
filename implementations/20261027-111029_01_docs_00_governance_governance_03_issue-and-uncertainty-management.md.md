## Goal

Remove the five resolved Known Issue entries EVENTBUS-019 to EVENTBUS-023 from Part 1 of the ledger and leave an accurate empty-state body (`REQ-002`: remove resolved entries; `REQ-007`: keep the checkers clean).

## Scope

- Edit only Part 1 `### Active Items` of the target file.
- Remove an entry only if its Resolution Target was met in the Plan's Phase 1 verification (`REQ-001`). An entry whose target is not met stays, with `Observed Implementation` updated.
- Part 2 to Part 4 and every other section stay unchanged.

## Assumptions

- Plan Phase 1 (pytest run over `tests/eventbus tests/db tests/deploy`, per-entry evidence, owner acknowledgement per UNK-02 and UNK-03) is done before this edit. It modifies no file, so it has no procedure document.
- Source evidence checked in Step 3a: `dlq_repo.py` rollback paths, `auth.py` duplicate-token guard, `schema.py`/`create_schema.py`/`init_db.sh` fingerprint gate, `app.py` refuse-to-close on lock timeout, `ack_route.py` required `idempotency_key`. Test execution is still unconfirmed (UNK-01).
- Part 1 has no closing-summary line, so `check_closing_summary()` in `tools/check_issue_inventory_conformance.py` reports nothing.
- `check_known_deviation_sync.py` reports an ERROR for the ADR citations of removed IDs until rows 02 to 05 are applied. Run the checkers after row 05, not after this row.
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- Use the one-sentence empty-state form of Parts 2 to 4: `No active Known Issue items remain.`
- Remove the five `#### EVENTBUS-0xx` blocks whole; do not keep a closed-out entry.

## Alternatives considered

N/A: the Plan (Design section) already rejected keeping a placeholder entry, because a resolved item is removed, not kept closed.

## Implementation
### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Locate `### Active Items` in Part 1 (`rg -n "^### Active Items|^#### EVENTBUS-0" <target>`).
2. For each of EVENTBUS-019 to EVENTBUS-023 whose Resolution Target was met, delete the block from its `#### EVENTBUS-0xx` heading up to, not including, the next `#### ` heading or the `## Part 2` heading.
3. If no entry remains, keep the `### Active Items` heading and its ordering-convention paragraph, and write `No active Known Issue items remain.` as the body.
4. If an entry stays, update only its `Observed Implementation` and keep the other sixteen fields.

### Method

Edit the file with exact-string deletions. Do not reflow other text.

### Details

- Part 1 body shape after the edit: heading, ordering-convention paragraph, blank line, the empty-state sentence, blank line, `## Part 2: Needs Confirmation Inventory`.
- The ordering-convention paragraph names ID prefixes; leave it as is.

## Compatibility considerations

N/A: documentation only. `tools/check_known_deviation_sync.py`, `check_issue_inventory_conformance.py` and `check_needs_confirmation_inventory.py` read this file; they are run after row 05.

## Security considerations

N/A: no secret, credential, or code path is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_issue_inventory_conformance.py` (expect no finding with Part 1 empty).
- `uv run python tools/check_needs_confirmation_inventory.py`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/00_governance/governance_03_issue-and-uncertainty-management.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`.
- `uv run python tools/check_known_deviation_sync.py` after rows 02 to 05 are applied.

## Completion criteria

- Part 1 contains no EVENTBUS-019 to EVENTBUS-023 heading for an entry whose target was met.
- An emptied Part 1 body is exactly `No active Known Issue items remain.`
- `check_issue_inventory_conformance.py` reports no finding.

## Out of Scope

- ADR files and the ADR guide (rows 02 to 05).
- Registering any new Known Issue.
- Any change under `scripts/`, `deploy/`, `config/`, `tests/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm Plan Phase 1 evidence is recorded, then remove the resolved entries and write the empty-state sentence | Pending | — | — | |
| 2 | Run the documentation checkers for this file (`routing.md` Tools "When to run which tool") | Pending | — | — | Sync checker passes only after rows 02 to 05 |

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
- **Requirement ID**: `REQ-002` (remove resolved entries, empty-state body), `REQ-007` (checkers clean)
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111029
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
