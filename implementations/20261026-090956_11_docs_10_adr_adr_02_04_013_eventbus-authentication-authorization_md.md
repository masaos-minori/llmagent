## Goal

Document in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` the
one-generation invariant, the runtime-only-vs-persistent semantics, the privileged-action
audit record, and the failure/empty-update behavior, and extend the verification matrix.
This procedure describes the ADR edit; it does not perform it (that is `code-implementation`'s
step).

## Scope

- Describe edits to `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
  only. Do not hand-edit the guarded/ADR body here.

## Assumptions

- The owner decisions UNK-01 (runtime-only default) and UNK-02 (empty/no-op handling) are
  recorded before this row is executed; the ADR must reflect the decided values.
- The ADR already documents INV-01/02/05/07 (plan evidence: adr_02_04_013:171-176).

## Design decisions

- Add an "Authorization generation" subsection (one-generation invariant, supports REQ-001).
- Add a "Persistence semantics" subsection documenting the runtime-only default and the
  `persistent:` response field (UNK-01; REQ-002).
- Add an "Audit record" subsection documenting `log_privileged_action` on effective change
  (REQ-003; INV-05).
- Add an "Empty / no-op update" subsection (REQ-004).
- Extend the verification matrix to cover these.

## Alternatives considered

- Placing this in a non-ADR ops doc: rejected — ADR-013 is the canonical governance record
  for the authentication/authorization contract (plan row).

## Implementation

### Target file

`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure

1. Add the one-generation invariant: config and token→principal map are published as one
   generation; no in-place `.clear()` window; a failed rebuild leaves the previous
   generation in force. Reference REQ-001.
2. Add the persistence semantics: the admin update is runtime-only by default (no config
   file write); the response returns `persistent: true/false`; restart loses the runtime
   change unless made in `config/eventbus.toml`. Record the UNK-01 decision. Reference
   REQ-002.
3. Add the audit-record contract: every effective change emits a redacted
   `log_privileged_action`; a no-op emits none; no token values (INV-05). Reference REQ-003,
   REQ-008.
4. Add the empty/no-op contract: `{}` or a no-op body is not reported as a successful
   change (record the UNK-02 decision). Reference REQ-004.
5. Extend the verification matrix with rows for the above.

### Method

Add subsections and matrix rows to the ADR; preserve existing ADR structure and ADR-004
preservation rules (do not reword existing decisions).

### Details

- Coordinate with seq 01 (admin handler) and seq 02 (auth publish) for the exact semantics
  documented; the ADR records the decided behavior, not a prescription.
- Do not edit `adr_02_04_006` (a different ADR; out of scope per eventbus006/008).

## Compatibility considerations

- The ADR is a governance record; additions are additive and must not alter existing
  decisions (see `tools/check_adr_preservation.py`).

## Security considerations

- Documents the fail-closed generation and audit contracts (INV-01/02/05/07).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run python tools/check_adr_preservation.py` — no existing ADR decision reworded.
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`,
  `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus` — clean.

## Completion criteria

- The ADR documents the one-generation invariant, persistence contract, audit record, and
  empty-update behavior; the verification matrix is extended.

## Out of Scope

- Editing `adr_02_04_006` or other ADRs.
- The UNK-01/UNK-02 decisions themselves — resolve before executing this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: docs row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers |
| 4 | Update documentation if in scope | Pending | — | — | This row IS the doc update |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
