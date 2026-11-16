## Goal

Update `docs/90_deployment/deployment_01_deployment.md` (§2.6, Compiled Artifacts) to reflect the
multi-main build and the one-rebuild-unit staleness, and make only the minimal, necessary change.
The deployed-host layout (eleven `mcp_<server>` names plus the agent in `/opt/llm/bin/`) is
unchanged; what changes is that the ten MCP names are produced from a single built artifact and
behave as one freshness/swap unit. This row documents those two additions.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The ten MCP names are installed under the existing `mcp_<server>` names in `/opt/llm/bin/`, so
  the deployed layout described in §2.6 stays accurate.
- The agent keeps its own binary and its pre-flight is unchanged.
- §2.6 is the section that describes the compiled artifacts, deploy placement, pre-flight, and
  freshness/rollback.

## Design decisions

- **Add two facts; change nothing else.** The doc already states eleven binaries are deployed and
  that deploy checks they are current. The two facts the Plan introduces that a reader of §2.6
  would otherwise miss are: (1) the ten MCP names share one built artifact, and (2) they form one
  freshness/swap unit. Both are deployment-relevant (the names are identical files; a swap or a
  stale verdict moves them together). Everything else in §2.6 stays verbatim.

## Alternatives considered

- **Rewriting §2.6 to describe the two-invocation build.** Rejected — the doc describes the
  deployed host, not the build host; the two-invocation detail is a build concern covered by
  `deploy/build_binaries.sh`. Only the deploy-relevant consequence (ten names, one artifact)
  belongs here.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure

1. In §2.6 (line 236), after describing that `deploy/build_binaries.sh` builds the agent plus one
   `mcp_<server>` per server, add one clause stating the ten MCP names are produced from a single
   built artifact (one Nuitka `--onefile` invocation) and installed under the ten existing
   `mcp_<server>` names, while the agent keeps its own build. Keep the "11 binaries" framing for
   the deployed host.
2. In the "Build, freshness, and rollback" paragraph (line 256), add one sentence stating the ten
   `mcp_<server>` names form one rebuild unit: a change under any one server's embedded paths marks
   all ten stale together, and their swap/rollback is all-or-nothing, so the set is replaced as a
   whole.
3. Leave the pre-flight, layout, and launch paragraphs (lines 240-254) unchanged — the agent
   binary and its pre-flight are unaffected.

### Method

- Two targeted prose additions in §2.6 (lines 236 and 256). No restructuring, no new sections, no
  changes to other sections.

### Details

- Line 236 currently reads: "`deploy/build_binaries.sh` builds the 11 binaries (the agent plus one
  `mcp_<server>` per MCP server) on the build host; ...". The added clause attaches to the first
  half (the build), before the semicolon clause about `deploy/deploy.sh`.
- Line 256 already describes swapping "the whole requested set"; the added sentence makes explicit
  that the ten MCP names are that whole set as a single unit.

## Compatibility considerations

- Pure documentation change; no script, config, or behavior changes.

## Security considerations

- None beyond accuracy: the added facts must not overstate the isolation. The ten names sharing one
  artifact does not weaken per-server configuration (each launcher still applies `restrict_to`
  before its server import).

## Rollback considerations

`N/A: revert the commit`; the change is prose in a reference doc.

## Validation plan

- Re-read §2.6 to confirm the two additions are accurate against
  `deploy/build_binaries.sh` (one artifact for the ten names) and `tools/manage_binaries.py` (one
  staleness unit for the ten names).
- Confirm no other section was altered.

## Completion criteria

- §2.6 states the ten MCP names come from one built artifact installed under the ten names.
- §2.6 states the ten MCP names form one freshness/swap rebuild unit.
- All other sections are unchanged.

## Out of Scope

- Changing the deployed layout description (eleven binaries, `/opt/llm/bin/`).
- The build mechanics (`deploy/build_binaries.sh`) or the staleness implementation
  (`tools/manage_binaries.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | two prose additions in §2.6 |
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
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`
