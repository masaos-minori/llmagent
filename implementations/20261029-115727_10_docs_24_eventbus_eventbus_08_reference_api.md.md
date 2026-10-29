## Goal

Update the audit signature rows in `docs/24_eventbus/eventbus_08_reference_api.md` to match the final code (`REQ-006`; AC-5): the `log_privileged_action` signature row gains the `actor` parameter and the `AuditRecord` row describes the new key and the `error_type=""` success convention.

## Scope

The `scripts/eventbus/audit.py` row block of the reference table (`eventbus_08_reference_api.md:64-66`) only. No other section of the doc, no other doc file, no code.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): the audit rows are at `eventbus_08_reference_api.md:64-66` -- `AuditRecord` (description "Structured payload for one EventBus audit record."), `log_auth_failure` and `log_privileged_action` signature rows; the wrapper rows (`dlq_requeue`, `admin_topics_authorization`, replay) already list `_principal` and stay accurate because seq 02 does not change wrapper signatures.
- Post-implementation signature to document: `def log_privileged_action(consumer_id, request_id, route, target, detail, actor) -> None` (matching the table's existing no-default style).
- Sequencing: land after seq 01-05 so the documented signatures match landed code; the archived ebpage003 procedure `implementations/20261029-094100_04_docs_24_eventbus_eventbus_11_replay_endpoint.md.md` edits a different doc file.

## Design decisions

- `AuditRecord` row description becomes: "Structured payload for one EventBus audit record. Privileged-action records carry a non-secret `actor` fingerprint; successful records carry `error_type=\"\"`." (current behavior only, per the Plan's docs policy).
- `log_auth_failure` row stays unchanged (out of scope of the code change).

## Alternatives considered

- Adding a new prose section about audit fields: rejected; the Plan's Documentation Impact limits the edit to the reference table rows, and `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` narrative mentions stay true without edits.

## Implementation
### Target file

`docs/24_eventbus/eventbus_08_reference_api.md`

### Procedure

1. Re-locate the audit rows by symbol name (line numbers shift if other procedures land first).
2. Update the `log_privileged_action` signature cell to include `actor`.
3. Update the `AuditRecord` description cell per the decision above.

### Method

Cell-level table edits; keep the table formatting (`|` layout) intact.

### Details

- No signature-row changes for `dlq_requeue` / `admin_topics_authorization` / replay wrappers: their parameter lists are unchanged by this plan (the `principal` argument is internal wiring, and the table documents wrapper signatures).

## Compatibility considerations

- Docs-only; keeps `check_docs_consistency.py` ground truth current.

## Security considerations

- Documents that only the non-secret fingerprint appears in records.

## Rollback considerations

- Restore the previous cell texts together with the seq 01 revert.

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain eventbus` (must be clean).

## Completion criteria

- The three audit rows match the landed code exactly; the docs consistency gate passes.

## Out of Scope

- Other table rows, other EventBus docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land after seq 01-05 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This row is the docs update |

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
- **Requirement ID**: REQ-006 (AC-5)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: docs/24_eventbus/eventbus_08_reference_api.md
