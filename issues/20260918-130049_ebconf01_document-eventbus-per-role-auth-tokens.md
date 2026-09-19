# Document missing per-role auth token fields in EventBus Configuration Fields

## Priority
High

## Summary
`docs/06_eventbus_05_configuration-and-operations.md`'s "Configuration Fields" list
omits 5 fields that exist in `scripts/eventbus/config.py`'s `EventBusConfig` dataclass
(`publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`,
`admin_token`) and the associated startup-validation rule that at least one per-role
token must be configured.

## Background
`EventBusConfig` (`scripts/eventbus/config.py`) defines these fields, and
`ADR-013-eventbus-authentication-authorization.md` documents the four-role
authorization model they implement (publisher/consumer/operator/monitoring, plus an
all-roles `admin_token`), but `docs/06_eventbus_05_configuration-and-operations.md`'s
"Configuration Fields" section — the operational reference an operator would use to
configure `config/eventbus.toml` — does not mention any of them.

## Problem
An operator configuring EventBus purely from
`docs/06_eventbus_05_configuration-and-operations.md`'s Configuration Fields list would
not know these 5 fields exist, or that at least one of them must be set (per
`scripts/eventbus/config.py`'s validation) for role-based authorization to function as
`ADR-013` intends.

## Reason for Change
This is a live documentation/code mismatch on a security-relevant configuration
surface (authentication/authorization tokens) — the kind of gap most likely to cause an
operational misconfiguration (e.g. deploying EventBus with only the legacy shared
`auth_token` and never realizing per-role tokens are available/expected).

## Implementation Intent
Add the 5 missing fields to the Configuration Fields list, in the same style as the
existing 16 entries, and add a short note on the startup-time "at least one per-role
token configured" requirement. Keep the addition purely descriptive (field name +
one-line purpose + validation behavior) — do not restate `ADR-013`'s full
authorization-model rationale here; cross-reference it instead.

## Target Files or Areas
`docs/06_eventbus_05_configuration-and-operations.md`

## Required Changes
- Add `publisher_token`, `consumer_token`, `operator_token`, `monitoring_token`,
  `admin_token` to the "Configuration Fields" list (near the existing `auth_token`
  entry), each with a one-line description of the role it grants.
- Add a short note that startup fails unless at least one of `auth_token` or a
  per-role token is configured, cross-referencing `ADR-013` rather than restating its
  content.

## Constraints
Do not change `scripts/eventbus/config.py` or any runtime behavior — this issue is
documentation-only.

## Acceptance Criteria
- `docs/06_eventbus_05_configuration-and-operations.md`'s Configuration Fields list
  includes every field currently defined in `EventBusConfig`.
- The per-role-token startup-validation behavior is documented with a cross-reference
  to `ADR-013`.

## Testing Expectations
No unit/integration tests apply (documentation-only). Run `uv run python
tools/check_docs_consistency.py --domain eventbus` after the edit to confirm no new
drift is introduced.

## Documentation Impact
This issue's entire deliverable is the documentation fix itself (see Required
Changes).

## Out of Scope
Any other section of `docs/06_eventbus_05_configuration-and-operations.md`; any change
to `scripts/eventbus/config.py` or `ADR-013`.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none — both the current doc content and the current code fields were directly
read and compared.

## AI Implementation Instruction
Match the existing field-entry style exactly (`` - `field_name` — one-line description
(default/behavior note if applicable) ``). Do not document a default value for any of
these token fields beyond noting the empty-string default already used for
`auth_token` — these are secrets, so describe purpose and validation behavior only,
never a token value (see `skills/DESIGN.md` No secrets in output).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-130049
- **Related target files**: docs/06_eventbus_05_configuration-and-operations.md
