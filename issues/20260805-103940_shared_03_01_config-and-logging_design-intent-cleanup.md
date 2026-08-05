# Reduce implementation-derived detail in docs/90_shared_03_01_runtime_and_execution-config-and-logging.md

## Priority
High

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`: keep the process-isolation config-loading policy and `restrict_to()` boundary enforcement; remove full method signatures and config-file listing tables.

## Reason for Change
This chapter is the canonical source for config separation and logging (per `memo-doc-shared-review.md` §「章間の正本ルール」: 設定分離とロギング = `90_shared_03_01_runtime_and_execution-config-and-logging`). Config-ownership separation is a deliberate cross-process boundary decision (per §「制約」 in the memo: each process reads only its own config file) and must not be lost.

## Implementation Intent
Keep this chapter focused on why `ConfigLoader` enforces process isolation, why there is no shared config file, and why production strengthens strict/security validation.

## Target Files or Areas
`docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`

## Required Changes
- Keep: `ConfigLoader`'s design intent, the process-isolation policy, the rule that each process reads only its own config file, `restrict_to()` as the boundary-enforcement mechanism, that agent's `load_all()` reads only `agent.toml`, the decision not to create a shared config file (duplicating needed values per process instead), the responsibility split between RAG-config validation and production-config validation, why production strengthens strict/security validation, Logger's operational role, the structured-log-plus-contextvars rationale for preventing concurrent-task log crosstalk, the stderr-fallback policy on log-write failure.
- Remove or compress: full `ConfigLoader` method signatures, a config-file listing table, a per-process `restrict_to()` call-site table, config-loading-flow pseudocode, the `ConfigValidationResult` dataclass definition, a full `Logger` method list, a full log-format field list.

## Acceptance Criteria
- The chapter follows the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full method signature, config-file table, or pseudocode flow remains.
- The process-isolation policy and `restrict_to()` boundary-enforcement rationale remain explicit and unweakened.

## Testing Expectations
Not required for behavior (documentation-only), but review must confirm the process-isolation/config-separation policy was not weakened. No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task, but touches a security-relevant config-separation boundary — treat removal decisions conservatively.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` (including `config_loader.py`, `logger.py`).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_03_01_runtime_and_execution-config-and-logging」. Do not edit code. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_03_01_runtime_and_execution-config-and-logging」
- Generated at: 2026-08-05
