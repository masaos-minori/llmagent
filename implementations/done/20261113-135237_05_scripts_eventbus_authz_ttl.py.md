## Goal

Remove `topic_authorization` from the TTL sweep's config rebuild and change counts, and write the sweep's audit record through `log_authorization_change` without the `gen:` detail suffix (REQ-002, REQ-004).

## Scope
**Release unit**: authorization-audit-record (with rows 03, 04, 14); the removal part belongs to the single-authorization-format unit (with rows 01, 02, 04, 06, 07, 14, 17)

## Assumptions
- The `EBAUTHGEN001 REQ-005` header comment (line 4) and any other label in this file stay for the rmcompat007 Plan; AC-6's grep does not cover this file (Plan Assumptions: this Plan must not delete labels outside its own row scope).

## Design decisions
- N/A: the call shape is fixed by the Plan Design (`log_authorization_change` with both generation kwargs).

## Alternatives considered
- Reporting expired topic pairs in the sweep `detail` with the old name: rejected; the format no longer exists (REQ-002).

## Implementation
### Target file
`scripts/eventbus/authz_ttl.py`
### Procedure
Delete the topic-pair rebuild and count, then replace the sweep's audit call.
### Method
Text deletion plus one call-site replacement.
### Details
- In `_removal_config` (37-68): delete the `topic_authorization` rebuild (51-63; the procedure's original 51-61 was re-verified 2026-11-13 — the second dict comprehension ends at 63) and the `topic_authorization=` constructor argument (67); keep the `consumer_authorization` rebuild (40-50); reword the function docstring (38-39) — it says "dropping expired pairs from both authorization mappings" and must describe the single mapping.
- In the sweep report (110-131): delete the `old_topic_pairs` collection block (115-119; original claim "117" is inside this block) and `counts["topic_authorization"]` (124-126).
- Drop the `gen:` detail part (130) and call `log_authorization_change` (row 03) with `previous_generation=gen.generation` and `new_generation=new_gen.generation` as required kwargs (REQ-004); keep the `persistent:false` part (129) and the remaining detail assembly (128).
- Update the import (17) accordingly: verified 2026-11-13 — the only audit call in this file is at 131, so the import is fully replaced with `log_authorization_change`.

### Companion test files
- `tests/eventbus/test_authz_generation_ttl.py`
  - Procedure (claims re-verified 2026-11-13; the original document had them swapped): the sweep-record assertions are patch-based — change `patch("eventbus.authz_ttl.log_privileged_action")` at 132, 165, and 203 to `log_authorization_change`, and the generation-kwarg assertions at 147-148 to the new function's kwargs; the `topic_authorization` fixture entries are at 310, 315, 320 (delete or convert to `consumer_authorization` entries); the startup-record patch at 269 targets `eventbus.app.log_privileged_action` and stays unchanged. There is currently no `gen:` detail assertion in this file (the original claim must not be implemented as a "replacement"); the no-`gen:` coverage lands in `test_admin_topics_authorization.py` and optionally as a new assertion here.
  - Validation: `uv run pytest tests/eventbus/test_authz_generation_ttl.py`

## Compatibility considerations
- `dataclasses.replace`/rebuild callers pass no `topic_authorization` once row 01 removes the field; the unit lands together.

## Security considerations
- Expiry sweeps keep a complete, unambiguous audit record with both generations (REQ-004).

## Rollback considerations
- Reverting the file restores the topic-pair sweep and the `gen:` suffix; audit records are append-only.

## Validation plan
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py`
- AC-2 acceptance search: `rg -n "topic_authorization" scripts/eventbus/authz_ttl.py` returns nothing (excluding the label comment left for rmcompat007 if it names the key; re-read line 4 before the search).
- AC-4: sweep record carries both generation fields and no `gen:` suffix.

## Completion criteria
- REQ-002 and REQ-004 states hold in this file; companion tests pass.

## Out of Scope
- The expiry-entry semantics described by the header comment (unchanged; only the topic format disappears).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | — |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | unit-2 targeted+full suites green; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/authz_ttl.py`, `tests/eventbus/test_authz_generation_ttl.py`
