# Reduce implementation-derived detail in docs/06_eventbus_05_01_config-env-and-fields.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_01_config-env-and-fields.md`: keep the security-relevant meaning of `host`/`allow_public_bind`/`max_retry` and the fail-startup-on-removed-key policy; remove full environment-variable and field/default tables.

## Reason for Change
This chapter is the canonical source for configuration and startup security constraints (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: 設定とセキュリティ上の起動制約 = `06_eventbus_05_01_config-env-and-fields`). The fail-startup-on-deprecated-key policy is a deliberate safety mechanism and must remain explicit.

## Implementation Intent
Keep this chapter focused on which settings matter operationally/securely and why early config-error detection is intentional.

## Target Files or Areas
`docs/06_eventbus_05_01_config-env-and-fields.md`

## Required Changes
- Keep: the config file's role, the meaning of required and operationally-important settings, the security meaning of `host`/`allow_public_bind`, `max_retry`'s effect on DLQ operations, the policy of failing startup when deprecated config keys remain, the intent to detect config errors early.
- Remove or compress: a plain environment-variable table, an exhaustive field-type/default table, the `EventBusConfig.__post_init__()` explanation, internal names like `_REMOVED_CONFIG_KEYS`.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No exhaustive field/default table or internal-name reference remains; readers are pointed to `config/eventbus.toml` for exact values.
- The fail-startup-on-deprecated-key policy remains explicit.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the fail-startup-on-deprecated-key policy was not weakened. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches startup-security-relevant documentation — treat removal decisions conservatively.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `config.py`) or `config/eventbus.toml` itself — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_01_config-env-and-fields」. Do not touch any file under `scripts/eventbus/` or `config/eventbus.toml` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_01_config-env-and-fields」
- Generated at: 2026-08-05
