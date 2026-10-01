## Goal

Resolve the open Needs Confirmation marker for `_is_stale_update()`'s two invalid
timestamp cases into a definitive statement documenting the two `ValueError`
subclasses introduced by option (b) (REQ-003; AC-03).

## Scope

Remove the inline Needs Confirmation marker at line 52 of
`docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` and replace it with
a statement that an invalid incoming `fetched_at` raises
`InvalidIncomingTimestampError` and an invalid stored `fetched_at` raises
`InvalidStoredTimestampError` (both `ValueError` subclasses).

## Assumptions

- The marker currently reads: *"Both cases raise the same `ValueError` type — the
  message text is the only current distinguishing mechanism; no separate exception
  classes exist for the two cases (Needs confirmation: whether distinct exception types
  are intended in the future)."*
- Option (b) has been selected by the owner (UNK-01 resolved), so the two subclasses
  now exist (row 1) and the question is answerable definitively.
- The surrounding bullet structure ("Invalid stored timestamp", "Equal timestamps",
  "Missing / empty stored `fetched_at`") is preserved.

## Design decisions

- State the two subclass names and that both inherit `ValueError`; note that the
  message text still distinguishes them at the call site.
- Do not reintroduce a pending question — the decision is recorded, not reopened.

## Alternatives considered

- Leave the marker open: rejected — the owner decision is already recorded (UNK-01
  resolved); leaving it open would defeat the item's purpose.
- Pointer to the code source only: rejected — the supporting-components doc should
  state the contract directly rather than require a cross-read.

## Implementation

### Target file

`docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`

### Procedure

1. `rg -n "Needs confirmation"` in the file to reconfirm the marker location (~line 52).
2. Read the surrounding paragraph to preserve list formatting.
3. Replace the marker paragraph with a definitive two-subclass statement.
4. Confirm no other Needs Confirmation marker referencing these two cases remains.

### Details

Replace the block beginning *"Both cases raise the same `ValueError` type..."* through
"(Needs confirmation: ...)" with something equivalent to:

> An invalid incoming `fetched_at` raises `InvalidIncomingTimestampError`; an invalid
> stored `fetched_at` raises `InvalidStoredTimestampError`. Both subclass
> `ValueError`; the message text (`Invalid incoming timestamp: …` vs `Invalid stored
> timestamp: …`) still distinguishes the two at the call site.

## Compatibility considerations

Doc-only. Cross-check against `rag_05_4-error-handling-reference.md` (row 3) so both
docs use identical subclass names and propagation description.

## Security considerations

N/A: documentation change only.

## Rollback considerations

Restore the original Needs Confirmation paragraph if option (b) is later reversed.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Doc quality / structure / content policy | `uv run python tools/check_docs_quality.py` && `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` && `uv run python tools/check_docs_content_policy.py` | No findings / no warnings on edited section |
| `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Domain consistency | `uv run python tools/check_docs_consistency.py --domain rag` | No new discrepancies |

## Completion criteria

- No remaining Needs Confirmation marker references these two cases.
- Both subclass names are present and correct.
- Consistent with the shared error-handling reference table (row 3).

## Out of scope

Other sections of this doc unrelated to the freshness edge-case error handling.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261001-220406 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261001-220406 | N/A: documentation change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261001-220406 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: `REQ-003` — replace the open Needs Confirmation marker with a definitive statement of the two exception subclasses
- **Source issue**: issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-203101
- **Related target files**: docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md