## Goal

Present the Configuration Ownership Map / API Consumer Map trade-off to the owner and record their decision in the Change Impact Rule section (REQ-001).

## Scope

In scope: presenting the trade-off and recording the resulting decision and rationale in the Change Impact Rule's configuration/API-change bullet. Out of scope: building a Configuration Ownership Map or API Consumer Map.

## Assumptions

N/A: none.

## Design decisions

Record the decision as an inline note extending the existing bullet, rather than a new top-level section — keeps it co-located with the rule it clarifies.

## Alternatives considered

Filing the decision only in NC-025's entry: rejected — NC-025 is being removed (row 2 of this Plan); the decision must live in the rule it affects.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

1. Re-confirm the Change Impact Rule's configuration/API-change bullet (confirmed present, unchanged, at lines 340-343 as of this cycle) immediately before editing.
2. Present the owner with the trade-off: keep using the existing general-purpose Decision Target Canonical Source Matrix (low maintenance cost, coarser granularity) vs. build a dedicated Configuration Ownership Map / API Consumer Map (per-key ownership traceability, a new artifact to maintain).
3. Record whichever decision results, with rationale, as an addition to the existing bullet — replacing its parenthetical "no separate ... map exists (tracked as a Needs Confirmation entry...)" clause, since that NC entry is being removed.

### Method

Present-and-record decision task.

### Details

- Confirmed current bullet (re-verified this cycle, lines 340-343): "Configuration or API changes → continue to use the existing Canonical Source Precedence matrix (Decision Target Canonical Source Matrix); no separate Configuration Ownership Map or API Consumer Map exists (tracked as a Needs Confirmation entry in `docs/governance_03_issue-and-uncertainty-management.md`)".
- If the owner decides to keep the existing matrix: replace the parenthetical with the rationale (e.g. "a dedicated map was considered and rejected as unnecessary given current configuration/API change volume, per {date} review").
- If the owner decides a dedicated map is needed: state that decision and note that building it is separate, unstarted follow-up work (do not build it in this cycle).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

`git revert` the commit, or manually restore the prior parenthetical.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Automated | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py` | Pass, no new findings |

## Completion criteria

- The Change Impact Rule states the owner's decision and rationale (AC-1).

## Out of scope

- Building a Configuration Ownership Map or API Consumer Map.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-155959 | 20260927-155959 | Owner decision obtained (via AskUserQuestion, since this document has no other reachable owner channel): a dedicated Configuration Ownership Map / API Consumer Map is needed, but building it is separate, unstarted follow-up work — recorded in the bullet, not built this cycle |
| 2 | Add or update tests per Validation plan | Completed | 20260927-155959 | 20260927-155959 | N/A: documentation-only, automated checks per Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-155959 | 20260927-155959 | N/A: documentation-only; docs checkers run instead |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-155959 | 20260927-155959 | N/A: this document's own target file IS the documentation being updated |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260927-115841_nc025_decide-whether-a-configuration-ownership-map-or-api-consumer-map-is-needed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121503_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-124544
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
