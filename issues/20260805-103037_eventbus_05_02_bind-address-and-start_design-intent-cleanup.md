# Reduce implementation-derived detail in docs/06_eventbus_05_02_bind-address-and-start.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-eventbus-review.md` to `docs/06_eventbus_05_02_bind-address-and-start.md`: keep the no-public-bind-without-external-auth-boundary policy intact; remove address-classification tables and duplicated startup-command/TOML examples.

## Reason for Change
This chapter is the canonical source for the bind-address and no-public-exposure policy (per `memo-doc-eventbus-review.md` §「章間の正本ルール」: bind address と公開禁止方針 = `06_eventbus_05_02_bind-address-and-start`). This is the single most important security constraint in the whole doc set (Event Bus has no auth) and must not be diluted.

## Implementation Intent
Keep this chapter focused on why public binding is dangerous given no auth, why `allow_public_bind=true` is discouraged by default, and why startup failure is used to prevent unsafe exposure.

## Target Files or Areas
`docs/06_eventbus_05_02_bind-address-and-start.md`

## Required Changes
- Keep: that the Event Bus API has no authentication so a public bind is dangerous, that it should run within a loopback or trusted network, that `allow_public_bind=true` is discouraged in principle, that an external auth boundary is required if exposed, the design decision to use startup failure to prevent unsafe exposure.
- Remove or compress: a detailed exhaustive address-classification table, duplicated startup-command examples, a complete TOML example, a diff memo comparing actual deployment vs. documented example.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-eventbus-review.md` §「修正後の章構成テンプレート」.
- No exhaustive address-classification table or duplicated command/TOML example remains.
- The no-public-bind-without-external-auth-boundary policy and the startup-failure-as-protection decision remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must explicitly confirm the public-bind warning and startup-failure protection were not silently dropped or softened. No dedicated eventbus docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but is the highest-security-sensitivity chapter in this doc set — treat removal decisions conservatively per `memo-doc-eventbus-review.md` §「編集時の判断ルール」.

## Out of Scope
- Other `docs/06_eventbus_*.md` chapters.
- Any code under `scripts/eventbus/` (including `app.py`, `config.py`) — per AGENTS.md Global Rule 8, eventbus implementation changes are prohibited; this issue is documentation-only.

## AI Implementation Instruction
Follow `memo-doc-eventbus-review.md` §「06_eventbus_05_02_bind-address-and-start」. Do not touch any file under `scripts/eventbus/` — AGENTS.md Global Rule 8 forbids eventbus implementation changes (investigation only). This is the most safety-critical chapter in the doc set; when in doubt, keep security-relevant wording rather than trim it. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-eventbus-review.md` §「06_eventbus_05_02_bind-address-and-start」
- Generated at: 2026-08-05
