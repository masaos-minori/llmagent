## Goal

Regenerate the agent API manifest so it records the new public symbols of the job registry (REQ-010: generated artifacts reflect the implementation; AC-10).

## Scope
**Release unit**: R7-docs-generated (Phase 7)

- In scope: `registry/manifests/agent_api.yaml` as a committed generated artifact.

## Assumptions

- The manifest is written by `tools/generate_reference_table.py --manifests`; it is never hand-edited.
- The symbols appear only after the code rows land, so this row runs at the end of the plan.
- Step 2 overlap: this manifest is also a target row of `plans/20261124-095950_cliplc004_bounded-shutdown-machine.md`. Both plans regenerate it, so the changes are compatible; the regeneration must run after that plan's code rows have landed as well.

## Design decisions

- Generation only; no manifest entry is added by hand.

## Alternatives considered

- Hand-editing the manifest — rejected: the drift check compares the manifest against the source, so a hand edit reports as drift at the next run.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests`.
2. Confirm the manifest lists the new public symbols from `scripts/agent/services/maintenance_jobs.py` (row 1) and the changed service surface (row 22).

### Method

- No manual editing.

### Details

- The generator writes the manifests first and then re-renders the guarded documents, so this row produces rows 36 and 37 in the same run.

### Companion test files

- None. This is a generated artifact; its validation is the generator's drift check.

## Compatibility considerations

- The observed staleness after the earlier work is the reason this row is a target; the drift check is the gate that catches it.

## Security considerations

- N/A: generated artifact.

## Rollback considerations

- N/A: revert the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `registry/manifests/agent_api.yaml` | Generator | `uv run python tools/generate_reference_table.py --check` | No drift between manifest and source |

## Completion criteria

- The manifest matches the source symbols, and the drift check reports nothing.

## Out of Scope

- The Memory manifest (row 39), the rendered documents (rows 36, 37).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the manifest | Pending | — | — | Phase 7 |
| 2 | Run the generator drift check (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-010 (generated artifacts reflect the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `registry/manifests/agent_api.yaml`
