## Goal

Reflect the DT-02 (fail-closed argument validation) and DT-01/DT-03 (tier/rule and plan-block posture)
decisions in ADR-003's text about approval state versus execution eligibility (REQ-004, REQ-009).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- Existing statements to extend: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md:36,48,55`
  (approval state and execution eligibility are distinct; Safety Tier/Write attributes must agree across
  Routing).
- ADR-003 INV-03 is evidenced by `tests/agent/test_tool_policy_comprehensive.py::TestClassifyOperationType`
  (matrix row `docs/10_adr/adr_01_index.md:184`), which row 12 extends.

## Design decisions
- Record the approved posture as a clarification of the existing invariants, not as a new invariant:
  rules are authoritative for approval risk, tiers decide execution eligibility (plan-mode blocking and
  the tier-vs-write classification), and schemas without `properties` fail closed.
- No invariant is renumbered or shortened (`check_adr_preservation.py` gate).

## Alternatives considered
Adding a new ADR-003 invariant for the tier/rule relationship — rejected; the distinction already exists
at `:36,48,55` and a second invariant would duplicate it.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
### Procedure
1. At `:36` and `:48`, state that an `approval_risk_rules` entry decides approval risk while the tier
   entry decides execution eligibility, so a tool may legitimately carry both.
2. At `:55`, add that argument validation fails closed when a schema defines no `properties`
   (`allow_extra_fields` is the only per-tool escape hatch).
### Method
Three localized edits to existing statements' surrounding prose.
### Details
- Keep the "distinct concepts" framing intact; the edits name which config key feeds which concept.

## Compatibility considerations
Row 31's matrix regeneration and row 35's manifest follow this document; row 30's wording must match the
row 08 config comments and the row 02 validator behavior.

## Security considerations
Fail-closed wording must not be softened into a recommendation.

## Rollback considerations
Revert the whole unit commit (see row 27).

## Validation plan
- `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_structure.py`,
  `uv run python tools/check_adr_invariant_matrix.py`,
  `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q`.

## Completion criteria
ADR-003's text matches the approved posture and its cited test still passes (AC-004, AC-009).

## Out of Scope
`config/agent.toml` (row 08), the validator (row 09), the matrix (row 31).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the DT-01/DT-02/DT-03 wording per Procedure | Completed | 20261119-081136 | 20261119-081136 | Three localized prose edits: Summary `:36` and Problem bullet `:48` now name the config-key split (`approval_risk_rules` -> approval state, `tool_safety_tiers` -> execution eligibility; both keys legitimate); Constraints `:55` adds the fail-closed schema rule (`tool_arg_validator.py` rejects non-empty args without `properties`; `RuntimeTool.allow_extra_fields` the only escape hatch — verified in `shared/runtime_tool.py:71` and `tool_preparation.py:132`). Invariant statements untouched |
| 3 | Run the ADR checkers (`routing.md` Tools) | Completed | 20261119-081136 | 20261119-081136 | check_adr_preservation / check_adr_structure / check_adr_invariant_matrix pass; 151 test_tool_policy_comprehensive tests pass |

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
- **Requirement ID**: `REQ-004` (DT-01/DT-02/DT-03 decisions), `REQ-009` (ADR record)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
