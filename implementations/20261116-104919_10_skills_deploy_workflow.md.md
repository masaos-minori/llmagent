## Goal

Update `skills/deploy/workflow.md` to describe the one-rebuild-unit staleness in Phase 1b, and
make only the minimal, necessary change. The Phase 1 → Phase 1b flow is unchanged; what changes is
that the ten `mcp_<server>` names move as one unit, so when a change under any one server's
embedded paths marks them all stale, a single rebuild refreshes all ten. This row documents that
one clarification.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `skills/deploy/workflow.md` guides the deploy phases; Phase 1b (lines 61-89) covers rebuilding
  stale binaries.
- The ten MCP names are produced from one artifact and share one staleness unit
  (`tools/manage_binaries.py`, seq 02).

## Design decisions

- **One prose addition in Phase 1b.** The existing instructions ("rebuild only the binaries Phase 1
  reported as stale", pass names to `BUILD_ONLY`) stay correct; the addition explains the
  operator-facing consequence that all ten names rebuild in one invocation. No other section
  changes.

## Alternatives considered

- **Documenting the one-unit behavior in Phase 1's freshness description (lines 35-38).** Rejected —
  Phase 1 describes the per-binary report labels; the unit behavior is an operator action in Phase
  1b, so it belongs there.

## Implementation
### Target file
`skills/deploy/workflow.md`

### Procedure

1. In Phase 1b, after the paragraph ending at line 78 ("...the Event Bus and ingestion run from the
   deployed `scripts/` source and have no binary."), add one sentence stating the ten
   `mcp_<server>` names are one rebuild unit: a change under any one server's embedded paths marks
   all ten stale, so `BUILD_ONLY` carries all ten and `deploy/build_binaries.sh` rebuilds them in a
   single invocation, swapping all ten together.

### Method

- One prose addition after line 78 in Phase 1b. Preserve the surrounding steps and the
  `BUILD_ONLY` usage.

### Details

- The added sentence ties the `manage_binaries.py` staleness unit (which the Phase 1 report uses) to
  the Phase 1b rebuild action, so an operator who sees all ten names listed as `stale` knows one
  rebuild clears them.

## Compatibility considerations

- Pure documentation change; no script, config, or behavior changes.

## Security considerations

- None beyond accuracy. The staged-swap integrity gate still replaces the ten names all-or-nothing.

## Rollback considerations

`N/A: revert the commit`; the change is prose in a skill file.

## Validation plan

- Re-read Phase 1b (lines 61-89) to confirm the addition is accurate against
  `deploy/build_binaries.sh` (one invocation for the ten names) and `tools/manage_binaries.py` (one
  staleness unit).
- Confirm no other line was altered.

## Completion criteria

- Phase 1b states the ten MCP names are one rebuild unit rebuilt in a single invocation.
- All other lines are unchanged.

## Out of Scope

- Changing the deploy phase model or the freshness report labels.
- The build mechanics beyond the one-invocation fact, and the staleness implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | one prose addition in Phase 1b |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this row |

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
- **Requirement ID**: `REQ-008`
- **Source issue**: `issues/20261115-072739_buildperf001_mcp-multidist-binary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-193516_buildperf001_mcp-multidist-binary.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-104919
- **Related target files**: `skills/deploy/workflow.md`
