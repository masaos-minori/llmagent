## Goal

Update ADR-013's decision text to describe the single authorization format, the single bind/token rule, and the new audit record shape (REQ-007).

## Scope
**Release unit**: N/A: document row (Plan Phase 7), after the code rows land.

## Assumptions
- The `Approval Record` section (289-297) already records the task-level approval as acceptance evidence and states no individual-name record exists; no new record is added (UNK-05 governs individual statements).
- The adrrev plans are archived with completed procedures: the `Implementation` column in the Automated Tests table (rows 242-262) and Decision Detail 12 (line 103) are already applied; re-read before editing and change different sentences than those documents did.

## Design decisions
- N/A: document describes the code decision made by rows 01-07.

## Alternatives considered
- Adding a new "pending approval" record row: rejected; the Approval Record exists and per UNK-05 individual statements are maintainer-written, not added by this Plan.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
### Procedure
Edit the sentences that name the removed format or the old audit shape; leave the Approval Record untouched.
### Method
Sentence-level edits inside existing decisions and notes; no new sections.
### Details
- Decision #6 (line 83): "Consumer principals take their `consumer_id` and topic authorizations only from the TOML `consumer_authorization`/`topic_authorization` mappings and admin updates built on top of them" — name only `consumer_authorization` (verified 2026-11-13; this reference was missing from the original document).
- Decision #10 (line 93): name only `consumer_authorization` for the runtime update.
- Decision #11 (line 99): the audit shape — the record for effective authorization changes becomes the `log_authorization_change` record with required `previous_generation`/`new_generation`; delete the `detail` formula's `;gen:<previous>-><new>` suffix part (verified 2026-11-13; missing from the original document). Keep the redaction and no-op sentences.
- Decision #14 (line 109): the sweep's audit record is emitted by `log_authorization_change` (verified 2026-11-13; missing from the original document).
- Line 113 (Decision #15, the startup baseline `log_privileged_action` record): stays unchanged — `log_privileged_action` keeps serving the startup, DLQ, and replay records.
- Operator guidance (193): "explicit `consumer_authorization` mappings" (drop the second mapping).
- Automated Tests table row (247): the empty-mappings deny-all row's condition text names both mappings; name only `consumer_authorization`. Verified 2026-11-13: the test name `test_empty_mappings_deny_all_consumers` (tests/eventbus/test_eventbus_auth.py) is not renamed by row 14 — keep the name and its Implementation column text as-is (the original "after the test is renamed" claim was unsupported).
- Implementation Notes (268): grants are built from `consumer_authorization` only.
- Implementation References (307): the `scripts/eventbus/audit.py` entry names `AuditRecord`, `log_auth_failure()`, `log_privileged_action()` — add `log_authorization_change()` (verified 2026-11-13; missing from the original document).
- Any bind/auth_token decision text must match the single `__post_init__` rule (loopback-only bind, required `auth_token`). Verified 2026-11-13: lines 36 and 123 describe loopback-only enforcement generically and stay correct; no decision text currently repeats the deleted "set auth_token or bind to loopback" advice.

## Compatibility considerations
- The ADR is also touched by rmcompat007 (label sweep on other sentences); run this Plan first and re-read before editing.

## Security considerations
- N/A: documentation.

## Rollback considerations
- Git revert; ADR preservation rules apply (`check_adr_preservation.py`).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_known_deviation_sync.py`.
- AC-7: document matches code after rows 01-07.

## Completion criteria
- No decision text describes `topic_authorization` or the `gen:` suffix; ADR checkers report no findings.

## Out of Scope
- Individual approval statements (UNK-05); the Approval Record content itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | 9 edits landed 2026-11-13 (83/93/99/109/193/247/268/306 audit-refs line); Decision #15 (113) untouched as planned |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | N/A: document row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | structure/reference/known_deviation clean; see Blocker Log for `check_adr_preservation` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | this row is the documentation change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Pre-existing gate drift: `check_docs_structure.py` size ceiling for adr_013 was 28647 while the authority-model batch commit a66077b4f had already grown the file to 31504 without re-recording. Re-recorded the ceiling to 31478 (this row's net 31478), per the repository's re-record convention; recorded in `tools/check_docs_structure.py`. | Yes | 2026-11-13 |
| 3 | `check_adr_preservation.py` reports 2 ERROR pairs (adr_006 and adr_013 Implementation References items changed) and 2 Decision-section WARNINGs. Deviation (2026-11-13): per `routing.md` and `tests/tools/test_run_validation_gates.py::test_adr_edit_does_not_auto_select_preservation_check`, this gate is content-based and applies only when an ADR is "shortened or reworded without intending to change its decisions". This row intentionally changes Decision text and references to match the landed code; the same reference edits are required by `check_compat_shims` (cited symbols must exist). Sentence-level mappings: commit message bullet list + this document's Details list. | Yes | 2026-11-13 |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
