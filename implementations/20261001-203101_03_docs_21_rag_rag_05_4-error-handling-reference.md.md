## Goal

Update the shared error-handling reference table entry for invalid `fetched_at` values
so it records the two `ValueError` subclasses instead of stating that message text is
the only distinction (REQ-003; AC-03).

## Scope

Edit line 108 of `docs/21_rag/rag_05_4-error-handling-reference.md`: replace the clause
*"message text is the only current distinction; no separate exception classes"* with a
statement naming `InvalidIncomingTimestampError` / `InvalidStoredTimestampError`, while
preserving the description that both still propagate uncaught to the URL-group
catch-all.

## Assumptions

- Line 108 currently reads: *"`ETagManager._is_stale_update()` raises `ValueError` —
  `Invalid incoming timestamp: {value}` or `Invalid stored timestamp: {value}` (message
  text is the only current distinction; no separate exception classes). Uncaught at the
  call site (`RagIngester.ingest_url_group()`), it propagates to the same catch-all as
  'Invalid `lang` value' above: skip URL group; `ERROR` (with traceback)."*
- The propagation behavior (uncaught → skip URL group → `ERROR` log) is unchanged by
  option (b); only the exception-type description updates.

## Design decisions

- Name both subclasses and keep the existing propagation sentence intact.
- Keep the cross-link to `rag_02_06_ingestion_pipeline-supporting-components.md`
  section 4.8.1.

## Alternatives considered

- Point readers at `etag_manager.py` instead of naming the subclasses inline: rejected
  — the reference table should be self-contained.
- Keep the prior "message text is the only current distinction" wording: rejected —
  it is now stale under option (b).

## Implementation

### Target file

`docs/21_rag/rag_05_4-error-handling-reference.md`

### Procedure

1. `rg -n "no separate exception classes|Invalid fetched_at` in the file to reconfirm
   line 108.
2. Read the surrounding table row to preserve Markdown table formatting.
3. Replace the "message text is the only current distinction" clause with the two
   subclass names; leave the propagation sentence unchanged.
4. Confirm the two RAG docs agree on the subclass names (row 2).

### Details

Update the row's exception description to read, equivalently:

> `ETagManager._is_stale_update()` raises `InvalidIncomingTimestampError` (invalid
> incoming `fetched_at`) or `InvalidStoredTimestampError` (invalid stored
> `fetched_at`) — both subclass `ValueError`; the message text
> (`Invalid incoming timestamp: {value}` vs `Invalid stored timestamp: {value}`)
> distinguishes the two at the call site. Uncaught at the call site
> (`RagIngester.ingest_url_group()`), it propagates to the same catch-all as "Invalid
> `lang` value" above: skip URL group; `ERROR` (with traceback). See
> [rag_02_06_ingestion_pipeline-supporting-components.md section 4.8.1]
> (rag_02_06_ingestion_pipeline-supporting-components.md#481-freshness-comparison-edge-cases-and-error-handling).

## Compatibility considerations

Doc-only. Names must match `rag_02_06_ingestion_pipeline-supporting-components.md`
(row 2) and the code in `etag_manager.py` (row 1).

## Security considerations

N/A: documentation change only.

## Rollback considerations

Restore the original "message text is the only current distinction" clause if option
(b) is later reversed.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/21_rag/rag_05_4-error-handling-reference.md` | Doc quality / structure / content policy | `uv run python tools/check_docs_quality.py` && `uv run python tools/check_docs_structure.py docs/21_rag/rag_05_4-error-handling-reference.md` && `uv run python tools/check_docs_content_policy.py` | No findings / no warnings on edited section |
| `docs/21_rag/rag_05_4-error-handling-reference.md` | Domain consistency | `uv run python tools/check_docs_consistency.py --domain rag` | No new discrepancies |

## Completion criteria

- Line 108 names both subclasses and no longer states that message text is the only
  distinction.
- Propagation-to-catch-all description and the cross-link are preserved.
- Consistent with the supporting-components doc (row 2).

## Out of scope

Other rows of the reference table unrelated to invalid `fetched_at` values.

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation change |
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
- **Requirement ID**: `REQ-003` — update the shared error-handling reference to name the two exception subclasses
- **Source issue**: issues/20260930-135010_etagexc01_etagmanager-_is_stale_update-exception-type-distinction-unresolved.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112407_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-203101
- **Related target files**: docs/21_rag/rag_05_4-error-handling-reference.md
