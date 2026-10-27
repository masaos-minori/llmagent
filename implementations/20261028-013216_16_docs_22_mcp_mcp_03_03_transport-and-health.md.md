# mcpcompat001-remove-the-re-export-claim-from-the-transport-and-health-doc

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Remove the sentence claiming `shared/mcp_config.py` re-exports the Health registry class from
`docs/22_mcp/mcp_03_03_transport-and-health.md`, leaving only current-boundary wording
(REQ-006; AC-6).

## Scope

- The single sentence at current L35, under the `## McpServerHealthRegistry (`shared/mcp_health.py`)`
  heading (L33):
  > The canonical module is `shared/mcp_health.py`; `shared/mcp_config.py` only re-exports the class.
- Nothing else in the file changes.

## Assumptions

- Verified 2026-10-28: L33-L35 are exactly as quoted in the plan's target row; the file contains
  no other `re-export` occurrence (grep verified: L35 is the only match).
- After procedure 01 lands, the sentence is factually false — so this doc edit belongs to the
  same change set and must not land before procedure 01.
- Cross-plan overlap (already recorded in `20261028-010601_03`): the pending mcpinv003 procedure
  on the same file edits the posture-gate bullet near L18, a disjoint region; whichever procedure
  lands second rebases by re-reading the file first. No text collision is expected.

## Design decisions

- Replace the two-clause sentence with one clause stating the current boundary only:
  `shared/mcp_health.py` is the canonical and only import path. The docs content policy forbids
  describing removed compatibility surfaces as present; no migration-window prose is kept.

## Alternatives considered

- Deleting the whole line: rejected — the section benefits from the explicit canonical-module
  statement (it is what a reader looking for the import path needs); only the re-export clause
  is stale.

## Implementation

### Target file

`docs/22_mcp/mcp_03_03_transport-and-health.md`

### Procedure

1. Replace L35 verbatim:
   ``` text
   The canonical module is `shared/mcp_health.py`; `shared/mcp_config.py` only re-exports the class.
   ```
   with:
   ``` text
   The canonical and only import path is `shared/mcp_health.py`.
   ```

### Method

Single-sentence replacement; surrounding heading (L33), blank line, and the `**State
Transitions:**` block (L37) untouched.

### Details

- No backticked callable references are introduced, so the `--check-doc-symbols` stage is
  unaffected (AC-7).

## Compatibility considerations

- Lands with procedures 01 and 17-19 in the same change set: after procedure 01 the re-export no
  longer exists, and the Phase 3 checker rule (`from shared.mcp_config` Health imports) does not
  read docs, so the doc edit has no code dependency ordering beyond procedure 01.
- Overlap with the pending `20261028-010601_03` procedure on the same file recorded above.

## Security considerations

- None; documentation-only.

## Rollback considerations

- Revert the sentence together with procedure 01's revert; the pre-change sentence described the
  pre-change code.

## Validation plan

- `uv run python tools/check_docs_consistency.py --domain mcp` — clean (AC-6).
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`
  — clean.
- `rg "re-export" docs/22_mcp/mcp_03_03_transport-and-health.md` returns nothing.

## Completion criteria

- The doc no longer claims a `shared/mcp_config.py` re-export and states only current boundaries
  (REQ-006, AC-6).

## Out of Scope

- Any other sentence in the file, including the posture-gate bullet touched by the mcpinv003
  procedure.
- The code-side re-export deletion — procedure 01.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Lands with procedure 01 in the same change set |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Doc checkers are the guards |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | check_docs_consistency --domain mcp |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | This document is the doc edit |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: docs/22_mcp/mcp_03_03_transport-and-health.md
