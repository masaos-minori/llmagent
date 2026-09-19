## Goal
Add the 5 missing per-role authentication token fields and their startup-validation
note to `docs/06_eventbus_05_configuration-and-operations.md`'s Configuration
Fields list (`REQ-001`, `REQ-002`).

## Scope
In scope: adding 5 new bullet entries and 1 short note to the existing
"Configuration Fields" list in this one file. Out of scope: any other section of
this file, any change to `scripts/eventbus/config.py` or `ADR-013`.

## Assumptions
- The 5 fields and the startup-validation behavior are still accurate as of this
  cycle — re-verified: `scripts/eventbus/config.py:98-102` still defines
  `publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`,
  `admin_token` (all `str = ""`), and `_validate_token_combinations()`
  (`scripts/eventbus/config.py:47-60`) still raises `ValueError("At least one
  authentication token must be configured")` at line 60 when none of
  `auth_token`/the 5 per-role tokens is set. The target doc's Configuration
  Fields list (`docs/06_eventbus_05_configuration-and-operations.md:55-70`) still
  has exactly 16 entries and no per-role-token mention — no drift since the Plan
  was written.

## Design decisions
Append the 5 new entries directly after the existing `` `auth_token` `` entry
(line 66), preserving the existing bullet order (mirrors the dataclass field
order at `scripts/eventbus/config.py:98-102`), then add the validation note as a
new sentence in the paragraph immediately following the list (after line 72's
existing cross-field-validation sentence) rather than a new subsection — the
existing paragraph already documents `__post_init__()`/cross-field validation in
prose, so extending it keeps all "how this doc's fields interact" content in one
place.

## Alternatives considered
Adding the 5 fields as a new "Authentication Tokens" subsection was considered,
but rejected: the source issue's `AI Implementation Instruction` requires
matching the existing field-entry style exactly, and every other field
(including the closely related `auth_token`) lives in the flat Configuration
Fields list — introducing a subsection for only these 5 would break that
consistency for no documented benefit.

## Implementation
### Target file
docs/06_eventbus_05_configuration-and-operations.md

### Procedure
1. Insert 5 new bullet lines immediately after the `` - `auth_token` — ... ``
   line (currently line 66), one per field, in this order: `publisher_token`,
   `consumer_token`, `operator_token`, `monitoring_token`, `admin_token`.
2. Append one sentence to the paragraph following the list (currently line 72)
   documenting the startup-validation rule, cross-referencing `ADR-013` by its
   filename rather than restating its content.

### Method
Direct text edit (`Edit` tool) — no code generation or templating involved; this
is a pure documentation content addition.

### Details
- New bullet lines (style matches the existing `` - `field_name` — description
  (behavior note) `` pattern, e.g. the existing `` - `auth_token` — Required for
  all requests (startup fails if empty) `` entry):
  - `` - `publisher_token` — Grants publish-role access when set (per-role
    alternative to the shared `auth_token`) ``
  - `` - `consumer_token` — Grants consume-role access when set ``
  - `` - `operator_token` — Grants operator-role access when set ``
  - `` - `monitoring_token` — Grants monitoring-role (read-only health/metrics)
    access when set ``
  - `` - `admin_token` — Grants all-roles access when set (superuser-equivalent
    per-role token) ``
  - Do not state a default value beyond noting the empty-string default already
    used for `auth_token`'s style — these are secrets; describe purpose and
    validation behavior only (per `skills/DESIGN.md` No secrets in output, cited
    by the source issue's AI Implementation Instruction).
- Validation-note sentence to append after the existing cross-field-validation
  sentence (paragraph following the list): a short sentence stating that startup
  fails unless `auth_token` or at least one of the 5 per-role tokens above is
  configured, with an inline cross-reference to
  `docs/adr/ADR-013-eventbus-authentication-authorization.md` for the
  authorization-model rationale — do not restate the four-role model here.

## Compatibility considerations
Documentation-only addition; no runtime, schema, or public-interface change.
Existing readers of this section are unaffected — the change is purely additive
(5 new bullets + 1 sentence), no existing entry is reordered, renamed, or
removed.

## Security considerations
This is a security-relevant configuration surface (authentication tokens) — the
change must describe purpose and validation behavior only, never a token value
or example secret, per `skills/DESIGN.md` No secrets in output (see Details
above). No other security consideration applies (no code path is touched).

## Rollback considerations
Trivial to revert: `git checkout -- docs/06_eventbus_05_configuration-and-operations.md`
restores the pre-change content exactly, since this is a single-file, purely
additive text change with no downstream generated artifact depending on it.

## Validation plan
- Manual review: diff the edited file against
  `scripts/eventbus/config.py:98-102`'s field list and confirm all 5 fields (plus
  the already-present `auth_token`) now appear in the Configuration Fields list.
- Run `uv run python tools/check_docs_quality.py` — expect no new findings.
- Run `uv run python tools/check_docs_structure.py` — expect no new findings.

## Completion criteria
- `docs/06_eventbus_05_configuration-and-operations.md`'s Configuration Fields
  list contains 21 entries (the original 16 plus these 5).
- The startup-validation sentence is present and cross-references
  `docs/adr/ADR-013-eventbus-authentication-authorization.md`.
- `tools/check_docs_quality.py` and `tools/check_docs_structure.py` both report
  no new findings against this file.

## Out of scope
Any change to `scripts/eventbus/config.py`, `docs/adr/ADR-013-eventbus-authentication-authorization.md`,
or any other section of the target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the 5 field entries + validation note (Implementation > Procedure/Method/Details) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no automated test — manual review + structural checks only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Scoped to `tools/check_docs_quality.py` + `tools/check_docs_structure.py`, not the full Python toolchain (no code changed) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's own Target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001, REQ-002 (add 5 per-role token fields; document startup-validation behavior)
- **Source issue**: issues/done/20260918-130049_ebconf01_document-eventbus-per-role-auth-tokens.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104332_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-114039
- **Related target files**: docs/06_eventbus_05_configuration-and-operations.md
