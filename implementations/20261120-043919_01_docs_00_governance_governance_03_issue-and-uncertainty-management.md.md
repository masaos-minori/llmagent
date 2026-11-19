## Goal

Register the two currently untracked pending items from the adrchk020 Plan as governance_03
Part 1 Known Issues — `MCP-003` (the never-performed ADR-004 Group 3 item 10 mandatoriness
assessment, including the `failure_category` re-evaluation proposal, REQ-003/REQ-004/REQ-005)
and `MCP-004` (the registry authority/placement reconciliation the stale registry header note
carried) — so the registry header can cite ledger IDs instead of an untracked "pending" note.

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 1 runs alone before the units)

## Assumptions

- Ledger IDs `MCP-003`/`MCP-004` are free: the active MCP group ends at `MCP-002`
  (`docs/00_governance/governance_03_issue-and-uncertainty-management.md:114`). Re-scan for
  `#### MCP-003`/`#### MCP-004` immediately before editing; on collision abort and report
  instead of renumbering (Plan Risk 1).
- AAL (Part 5) entries record approvals only; no approval exists yet, so neither item gets an
  AAL entry (Plan UNK-02). The `failure_category` re-evaluation stays a proposal in
  MCP-003's Recommended Action (Plan REQ-005).

## Design decisions

- Part 1 Known Issue placement, not AAL: matches `governance_03` Part 1 semantics (active
  discrepancies) vs Part 5 (approval records).
- MCP-003 Severity Medium (correctness of an ADR-mandated assessment gap); MCP-004 Severity
  Low (placement already fixed by ADR-004 item 13; only the owner-list approval awaits).

## Alternatives considered

- N/A: the Plan's Design decision 1 fixed the ledger placement; AAL and Part 2 (Needs
  Confirmation) do not fit unapproved open items.

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Insert two entries `#### MCP-003` and `#### MCP-004` into Part 1 `### Active Items` after
   the `MCP-002` entry, before the `#### SHARED-001` heading (line 134), keeping the
   ID-prefix group ordering (`MCP-*` ascending, then `SHARED-*`).
2. Fill all 17 Part 1 fields per the Entry Template (line 47) for each entry.

### Method
- Common fields: `Status`: open; `Area`: MCP; `Owner`: Repository owner; `First Found:`
  `adrchk020 mandatoriness registry posture re-verification` (an activity name, not a date).
- `Type`: design-gap for both (behavior/criterion gaps, not doc formatting).

### Details
- `MCP-003` (Severity Medium): Title names the unperformed ADR-004 Group 3 item 10 assessment.
  `Source`: `registry/component_mandatoriness.yaml` `rationale` lines (21, 33, 45, 57, 69, 81,
  93, 105, 117, 129 — "Not assessed as satisfying Decision Group 3 item 10"). `Target`:
  `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`. `Current Description`: ADR-004
  item 13 requires an approved classification; all 10 entries carry the status-quo default and
  `agent_08_04` (lines 46–52) restates the criteria with no approval record. `Observed
  Implementation`: every server is classified `required` with `startup_consequence:
  abort_startup`; no per-server item-10 assessment exists. `Impact`: the approved-classification
  precondition of ADR-004 item 13 is unmet for all 10 servers. `Recommended Action`: perform
  the per-server Group 3 item 10 assessment; additionally state whether `failure_category`
  should stay uniform `safety-integrity` or follow ADR-004 Group 2 item 7
  (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md:73`, MCP-server
  unavailability classes as an availability failure) — proposal only, no value changes here
  (Plan REQ-005). `Resolution Target`: maintainer assessment recorded in the registry via an
  approved change. `Related`: AAL-019, `registry/component_mandatoriness.yaml`.
- `MCP-004` (Severity Low): Title names the registry authority/placement reconciliation.
  `Source`: the former header note in `registry/component_mandatoriness.yaml` (line 6,
  "Authority/placement reconciliation pending adrauth001 (U-1)"). `Target`:
  `docs/00_governance/governance_01_documentation-policy.md`. `Current Description`: the
  registry home is fixed by ADR-004 item 13 and the registry is the canonical source for
  `mcp.component-mandatoriness` (`config/documentation_canonical_sources.toml:66-71`). `Observed
  Implementation`: the adrchk010 Plan's Resolution Matrix owner-list addition for this row
  (its REQ-017/UNK-02) is prepared but pending maintainer approval. `Impact`: the pending
  approval has no ledger entry. `Recommended Action`: maintainer approves or amends the
  governance_01 Resolution Matrix owner list for the `mcp.component-mandatoriness` row; no
  approval is written here (mirrors MCP-001/MCP-002 phrasing). `Resolution Target`: owner-list
  approval recorded in `governance_01_documentation-policy.md`. `Related`: MCP-003,
  `config/documentation_canonical_sources.toml`.

## Compatibility considerations

- Part 1 entries are free-form markdown bullets; no generated manifest or checker consumes
  individual entry text. `tools/check_needs_confirmation_inventory.py` covers Part 2 only and
  must stay exit-0.

## Security considerations

- N/A: documentation-only entry addition; no secret or posture value touched.

## Rollback considerations

- N/A: revert the commit (docs-only single-target change).

## Validation plan

- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py`
  (`routing.md` Tools — any `docs/*.md` edit).
- `uv run python tools/check_needs_confirmation_inventory.py` exit 0 (no Needs-Confirmation
  marker introduced).
- Re-read the edited Part 1 region and confirm group ordering (MCP-001..MCP-004 ascending,
  MCP group before SHARED group) and 17 fields per entry.

## Completion criteria

- Part 1 contains well-formed `MCP-003` and `MCP-004` entries with all 17 fields; MCP-003's
  Recommended Action carries the `failure_category` proposal citing ADR-004 Group 2 item 7;
  no registry value changed anywhere in the diff (Plan AC-03, AC-04); all three checkers exit 0.

## Out of Scope

- Any `classification`, `rationale`, or `failure_category` value change in the registry.
- Editing the governance_01 Resolution Matrix itself (the approval decision belongs to the
  owner), any Part 5 AAL entry (Plan UNK-02), and Part 2 Needs Confirmation items.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-scan for MCP-003/MCP-004 ID collisions, then insert both Part 1 entries after MCP-002 | Pending | — | — | |
| 2 | Run the docs checkers (`check_docs_quality.py`, `check_docs_structure.py`, `check_needs_confirmation_inventory.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (register the unperformed mandatoriness assessment), `REQ-004` (register the placement reconciliation), `REQ-005` (record the failure_category proposal)
- **Source issue**: issues/20261117-123020_adrchk020_mandatoriness-registry-posture.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-001311_adrchk020_mandatoriness-registry-posture.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-043919
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
