# Enforce approval policy in configuration validation

## Priority
Medium

## Summary
Require `require_approval: true` in configuration validation for any workflow that can reach tools needing approval (shell execution, deletion, push, etc.), so a misconfiguration is detected at startup.

## Background
Source: local investigation notes (memo1.md, ISSUE-10), from AGENT-001. Documentation calls the approval policy mandatory; no code enforces it.

## Problem
- The default `default.json` sets `require_approval` to false (Explicit in code — `config/workflows/default.json`).
- Documentation says the approval policy is mandatory, but nothing in code enforces it (per investigation notes).

## Reason for Change
- A policy described as mandatory but not enforced is only nominal.
- Tool-level approval gates alone cannot confirm a whole stage's result after execution.

## Implementation Intent
- Detect, at startup, a workflow that allows approval-requiring operations without `require_approval: true`.

## Target Files or Areas
- `config/workflows/default.json`, `scripts/shared/production_config_validator.py`, `scripts/agent/workflow/workflow_loader.py`
- agent documentation, security_01

## Required Changes
- Add a ProductionConfigValidator rule: workflows allowing approval-requiring tools must set `require_approval=true`.
- Change `default.json` to `require_approval: true`.
- Update the approval-policy descriptions in the agent documents and security_01 to match the enforcement mechanism.

## Constraints
- Must not break non-production/test configurations that legitimately need no approval (to be decided).

## Acceptance Criteria
- Allowing an approval-requiring tool while `require_approval=false` is rejected at startup (test).

## Testing Expectations
- Validator unit tests; startup test with the default workflow; ruff, mypy, targeted pytest.

## Documentation Impact
Update approval-policy descriptions; remove Known Issue AGENT-001 from the ledger when done.

## Out of Scope
- Fail-closed workflow loading (separate issue); approval UI changes.

## Dependencies
- Complements the workflow-load fail-closed issue; together they complete the approval policy.

## Unresolved Questions
- Current contents of `default.json` and the validator rules (not read); which tools count as "approval-requiring".

## AI Implementation Instruction
Read the validator and workflow loader first. Keep the rule narrow and explicit; do not change approval behavior itself.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154046
- **Related target files**: `config/workflows/default.json`, `scripts/shared/production_config_validator.py`, `scripts/agent/workflow/workflow_loader.py`
