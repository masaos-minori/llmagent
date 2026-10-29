# Implementation Procedure: scripts/eventbus/publish_route.py (Published-at ownership procedure 2)

## Goal

Enable strict RFC 3339 validation of `published_at` at the publish route by attaching
a `jsonschema.FormatChecker` to the envelope validation call.

## Scope

- Pass a `FormatChecker` (new) instance to the `jsonschema.validate` call in
  `scripts/eventbus/publish_route.py`.
- Keep the existing passthrough of `published_at` to `insert_event` unchanged.

## Assumptions

- `jsonschema.validate` is called at exactly one site (`publish_route.py:42`) without a
  `format_checker` (new) argument today; the envelope schema declares `format: "date-time"`.
- `rfc3339-validator` will be installed (row 8); without it the registered
  `date-time` checker is inert.
- Only malformed strings can reach validation today: Pydantic `Event` accepts datetime
  objects and serializes them as RFC 3339 (`datetime.now(UTC).isoformat()`).

## Design decisions

- Enable the checker on the existing call site rather than adding a separate
  pre-validation step, keeping request handling in one gate (plan UNK-02 decision).
- The route continues to pass the validated string through unmodified (plan UNK-01
  decision).

## Alternatives considered

- `datetime.fromisoformat` pre-check without a new dependency (rejected: not full
  RFC 3339; plan dependency note records the rejection).

## Implementation
### Target file
`scripts/eventbus/publish_route.py`

### Procedure
1. Create a module-level `jsonschema.FormatChecker()` instance.
2. Pass it as the `format_checker` (new) argument to the existing `jsonschema.validate` call.
3. Confirm the existing `FormatChecker` (new) error path returns 422 with detail beginning
   `invalid event envelope` (it already does; no new handler needed).
4. Leave the `published_at=payload.published_at` passthrough to `insert_event` unchanged.

### Method
Inline edit at the validation call site; no new error handling code.

### Details
- A failed format check raises the same `FormatChecker` (new) exception class already caught
  in the route's envelope-validation error branch.

## Compatibility considerations

- Behavior change is intentional and plan-scoped: malformed `published_at` strings move
  from 200 (silent server rewrite) to 422.
- Overlap note: this file is also a target row of ebgen001 (procedure
  `implementations/20261028-235805_02_scripts_eventbus_publish_route.py.md`, already in
  `implementations/done/`); its generator passthrough fix is separate from this edit.

## Security considerations

- Rejecting unparseable timestamps at the API boundary prevents non-normalizable values
  reaching the store.

## Rollback considerations

- Drop the `format_checker` (new) argument to restore permissive behavior; combined with
  rollback of rows 3, 8, 9 to keep the default path intact.

## Validation plan

- `tests/eventbus/test_eventbus_publish_contract.py` malformed-format test flips to 422
  (row 4); `tests/eventbus/test_eventbus_publish.py` valid-path tests stay green.

## Completion criteria

- FormatChecker attached at the call site; malformed `published_at` returns 422 in
  tests; valid requests unchanged.

## Out of Scope

- Future-timestamp skew rules (plan UNK-02 decision).
- Redelivery-side normalization (plan UNK-03 decision: existing behavior maintained).

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261028-122454_ebpubat006_published-at-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-233320_ebpubat006_published-at-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-103639
- **Related target files**: scripts/eventbus/publish_route.py
