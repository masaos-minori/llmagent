## Goal

Update `skills/deploy/SKILL.md` to reflect the multi-main build and the one-rebuild-unit
staleness, and make only the minimal, necessary change. The deploy flow (clean-tree check,
freshness report, rebuild stale binaries, deploy, restart) is unchanged; what changes is that the
ten `mcp_<server>` names are produced from one artifact and behave as one freshness/swap unit. This
row documents those two additions.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- `skills/deploy/SKILL.md` is the deploy skill that guides pre-deploy, rebuild, deploy, and
  restart.
- §"Deploy scripts" (table, line 25) summarizes `deploy/build_binaries.sh`; §"Phase overview"
  (line 48) describes Phase 1b (rebuild stale binaries).
- The ten MCP names are installed under the existing `mcp_<server>` names; the agent keeps its own
  binary.

## Design decisions

- **Two targeted prose edits; nothing else.** The skill's behavior is unchanged, so the edits are
  confined to (1) the `build_binaries.sh` purpose so a reader understands why all ten rebuild
  together, and (2) the Phase 1b gate so a rebuild refreshes the whole ten-name unit. No new
  sections, no restructure.

## Alternatives considered

- **Adding a section on the multi-main build.** Rejected — the skill guides deploy, not the build;
  the build mechanism belongs in `deploy/build_binaries.sh`. Only the deploy-relevant consequence
  (ten names, one unit) belongs here.

## Implementation
### Target file
`skills/deploy/SKILL.md`

### Procedure

1. In the "Deploy scripts" table (line 25), update the `deploy/build_binaries.sh` purpose so it
   states the ten MCP `ENTRIES` entries are built in one Nuitka `--onefile` invocation producing a
   single artifact installed under the ten `mcp_<server>` names, and the agent is built
   separately. Keep "swap into `/opt/llm/bin/` after all pass" and "`--rollback` restores it".
2. In the "Phase overview" table (line 48), extend the Phase 1b goal so it states the ten
   `mcp_<server>` names are one rebuild unit: rebuilding once refreshes all ten, so a change under
   any one server's embedded paths marks all ten stale and a single rebuild clears them.

### Method

- Two prose edits in the two tables (lines 25 and 48). Preserve the table columns and the
  cross-references to `workflow.md`.

### Details

- Line 25 currently reads: "Build the Nuitka `--onefile` binaries (every `ENTRIES` entry, or
  `BUILD_ONLY`) into a staging directory, swap them into `/opt/llm/bin/` after all pass, and keep
  the previous set (`--rollback` restores it)". The edit narrows "every `ENTRIES` entry" to the
  ten MCP entries built together, and adds that the agent builds separately.
- Line 48 currently reads: "Rebuild the binaries the freshness report lists as stale or unknown".
  The edit adds that the ten MCP names move as one unit.

## Compatibility considerations

- Pure documentation change; no script, config, or behavior changes.

## Security considerations

- None beyond accuracy. Noting the one-unit rebuild does not weaken anything: the staged-swap
  integrity gate still replaces the ten names all-or-nothing.

## Rollback considerations

`N/A: revert the commit`; the change is prose in a skill file.

## Validation plan

- Re-read lines 25 and 48 to confirm they are accurate against
  `deploy/build_binaries.sh` (one artifact for the ten names) and `tools/manage_binaries.py` (one
  staleness unit).
- Confirm no other line was altered.

## Completion criteria

- Line 25 states the ten MCP names come from one artifact and the agent builds separately.
- Line 48 states the ten MCP names are one rebuild unit.
- All other lines are unchanged.

## Out of Scope

- Changing the deploy phase model or the Approval gate.
- The build mechanics beyond the one-artifact fact, and the staleness implementation.

## Verification Findings (2026-11-17, adversarial verification)

Verification Status: Verified — quoted lines confirmed.

- Line 25 quote confirmed verbatim: "Build the Nuitka `--onefile` binaries (every `ENTRIES`
  entry, or `BUILD_ONLY`) into a staging directory, swap them into `/opt/llm/bin/` after all
  pass, and keep the previous set (`--rollback` restores it)".
- Line 48 quote confirmed verbatim: "Rebuild the binaries the freshness report lists as stale
  or unknown".
- Docs content policy: state the unit ("all ten `mcp_<server>` names move as one unit" phrasing
  already exists in this skill's context); do not enumerate server names; run
  `tools/check_docs_content_policy.py` after the edit if it covers `skills/` (else the docs
  checker covers `docs/` only and a manual policy check applies).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-102950 | 20261117-103041 | two prose edits (lines 25, 48) Two table edits applied: build_binaries.sh row (single multi-main invocation, one artifact per mcp_<server> name, agent separate) and Phase 1b row (mcp_<server> names are one rebuild unit); no counts or name lists added |
| 2 | Add or update tests per Validation plan | Completed | 20261117-103041 | 20261117-103041 | N/A: documentation row N/A: documentation row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-103041 | 20261117-103041 | content_policy covers docs/ only; manual policy check clean; pre-commit skills file-reference check passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261117-103041 | 20261117-103041 | this row this row is the skills doc change itself |

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
- **Related target files**: `skills/deploy/SKILL.md`