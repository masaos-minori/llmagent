## Goal

State the verified approval-risk evaluation order, the `RiskLevel.NONE` short-circuit, the
protected-path/`allowed_root` interaction, and the tier-authoritative plan-mode rule as the canonical
description (REQ-002, REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Existing plan-mode rule text to align with: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md:105-112`.
- DT-01/DT-03/DT-06 Option A: the document describes the implemented posture, not a proposed one.

## Design decisions
- This document is the canonical source for the evaluation order; other approval documents link to it
  instead of restating the order (registered in Plan row 32).
- State the measured consequences explicitly: rules override tiers; tier-`NONE` rule-less tools never
  reach escalation; in-jail ruled path-bearing tools resolve to `HIGH`.

## Alternatives considered
N/A: documentation-only, wording fixed by REQ-002.

## Implementation
### Target file
`docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
### Procedure
1. Add an evaluation-order section: `approval_risk_rules` → `tool_safety_tiers` →
   `scripts/shared/tool_constants.py` default → `MEDIUM` fallback, then the `NONE` short-circuit before
   special-case and path escalation.
2. Align `:105-112` with the tier-authoritative plan-mode rule and `plan_blocked_tools` as its explicit
   extension.
3. Add the protected-path scope paragraph (inside the jail every ruled path-bearing tool escalates to
   `HIGH`; outside it the jail denies the call).
### Method
New sections plus edits to the existing plan-mode text; keep the document's existing heading structure.
### Details
- Cite `scripts/agent/tool_policy.py` function names so a reader can verify each claim against code.

## Compatibility considerations
Must stay consistent with the row 01 docstrings and the regenerated API reference (row 33).

## Security considerations
N/A: documentation of existing behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`.
- `uv run python tools/check_canonical_source_registry.py` after row 32 registers this document.

## Completion criteria
The document and `classify_risk()`'s docstring state the same order (AC-002), and this document is the
registered canonical source for the order claim (AC-010).

## Out of Scope
Configuration-guide wording (row 24), tier-mapping table (row 25), docstring edits (row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the evaluation-order, plan-mode, and protected-path text per Procedure | Completed | 20261119-075837 | 20261119-075837 | Added "Evaluation order" paragraph (rules -> tiers -> tool_constants default -> medium fallback; NONE short-circuit before special-case/path escalation, cites `classify_risk()`) and "Protected-path scope" paragraph (jail denies out-of-jail before escalation runs; cites `check_allowed_root()` / `check_approval()`). Procedure step 2 verified as no-op: plan-mode text at :105-112 already states the tier-authoritative rule + `plan_blocked_tools` extension |
| 3 | Run the documentation checkers (`routing.md` Tools) | Completed | 20261119-075837 | 20261119-075837 | check_docs_quality / check_docs_structure / check_docs_consistency --domain agent all pass; canonical-source registration happens in row 32 |

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
- **Requirement ID**: `REQ-002` (record the evaluation order), `REQ-010` (canonical source)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`
