# Validate security-relevant configuration on hot reload

## Priority
High

## Summary
Security-relevant Agent configuration fields are hot-reloadable with no validator, so a reload can apply values that startup would reject. Attach validators or make the fields restart-only.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H04`; merged from ADRCHK-H04 (review finding N6)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
`allowed_root`, `tool_safety_tiers`, `allowed_tools`, `approval_risk_rules`, and the other approval fields are registered with `hot_reloadable=True` and `validator_fn=None` in `scripts/agent/services/config_field_registry.py`. Evidence: the registry has the `hot_reloadable` field (`Explicit in code`); the per-field values are from the review.

## Reason for Change
- Reloads skip the startup checks: startup rejects an empty `allowed_root` and an incomplete `tool_safety_tiers`, but a reload applies new values without these checks.
- The validators exist but are not wired: `scripts/agent/services/config_validators.py` defines `validate_tool_safety_tiers` and `validate_approval_risk_rules`, and neither is attached to its registry entry.
- `tool_safety_tiers` decides whether approval is needed and whether plan mode allows a tool, so a bad reload can let write tools run without approval.
- ADR-002 and ADR-007 say configuration changes need a restart, which does not match the registry.

## Implementation Intent
- Each security-relevant field is validated on reload with the same rule as at startup, or it is not hot-reloadable.
- A rejected reload keeps the previous value in force.
- The ADRs state which fields can be reloaded.

## Target Files or Areas
- `scripts/agent/services/config_field_registry.py`
- `scripts/agent/services/config_validators.py`
- registry/manifests/config_ownership.yaml (regenerated)
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md`
- `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
- `tests/agent/services/`

## Required Changes
- Read the reload path and confirm the argument passed to `validator_fn` (the field value or the section dataclass).
- Attach `validate_tool_safety_tiers` and `validate_approval_risk_rules`.
- Add validators for `allowed_root` (a non-empty absolute path) and `allowed_tools` (a non-empty list of strings), or set `hot_reloadable=False`.
- Regenerate `config_ownership.yaml` and update ADR-002 and ADR-007.

## Constraints
- If a validator expects a different argument than the reload path passes, report it before changing any signature.
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- A reload with an invalid tier value or an empty `allowed_root` is rejected, and the previous value stays in force (test).
- The manifest shows a validator or `hot_reloadable: false` for each security-relevant field.

## Testing Expectations
Unit tests under `tests/agent/services/` for each rejected reload (write them first); run `uv run python tools/generate_reference_table.py --check` and the full validation sequence. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-002 and ADR-007 state which fields reload and which need a restart.

## Out of Scope
- Approval order or tier decisions (see the approval policy issue).
- Hand edits to the manifest.

## Dependencies
- `issues/20261117-123003_adrchk003_agent-approval-policy.md` defines the tier semantics this issue validates (soft dependency).

## Unresolved Questions
- The reload implementation was not reviewed. Needs `scripts/agent/config_dataclasses.py` and the reload service under `scripts/agent/services/` (file name unknown).

## AI Implementation Instruction
- Report an argument-shape mismatch before changing any signature.
- Regenerate the manifest; do not edit it by hand.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123004
- **Related target files**: `scripts/agent/services/config_field_registry.py`; `scripts/agent/services/config_validators.py`; `registry/manifests/config_ownership.yaml (regenerated)`; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; `tests/agent/services/`
