## Goal

Record the five-layer coverage for file-write-mcp, file-delete-mcp, and shell-mcp in
`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`, including the reasons a layer is not
applicable, and correct the Audit lines that currently state these servers write no shared record
(REQ-009, AC-009).

## Scope

- Add one layer-coverage section per server, in the shape already used by
  `docs/22_mcp/mcp_04_05_git.md`.
- Update the three `**Audit:**` lines so Layer2 reflects the shared record.
- Add the post-write, post-move, and post-delete verification facts to the implementation notes.

## Assumptions

- The layer names and section shape come from the Plan's Design section and the existing git-mcp
  document; no new vocabulary is introduced.
- The facts recorded are the ones the code now holds after Plan rows 1-5, not the pre-change state.

## Design decisions

- Keep the existing single-line `**Audit:**` Layer1/Layer2/Layer3 format for the catalog line, and put
  the prose detail in the new section, so the catalog table stays scannable.
- State not-applicable reasons explicitly rather than leaving a layer blank, which is what AC-009
  requires.

## Alternatives considered

- Record coverage only in `docs/91_security/security_02_high-risk-tool-common-policy.md`: rejected — the
  Plan's documentation shape makes the policy document point at tool documents instead of describing a
  gap.

## Implementation

### Target file

`docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`

### Procedure

1. Add a `### Guard and postcondition coverage` subsection to each of the three server sections.
2. Within each subsection, add `Common guard`, `Command-specific guard status`, `Postcondition
   verification`, and `Audit` sub-headings, matching the git-mcp document's names.
3. Update the three `**Audit:**` lines.
4. Extend the file-write and file-delete implementation notes with the new guard and verification facts.

### Method

Write one short paragraph per layer, each ending with the `(Explicit in code — <paths>)` marker the
document already uses.

### Details

- The Audit lines to update are at `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:39`,
  `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:69`, and
  `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md:111`.
- file-write-mcp: Layer2 becomes `mcp_tool_exec`; record that `max_write_bytes` is now enforced on both
  `write_file` and `edit_file`, that `edit_file` writes through the same tmp-file plus `os.replace` path
  as `write_file`, and that a write or move whose resulting state does not match is reported as a
  failure rather than as success.
- file-delete-mcp: Layer2 becomes `mcp_tool_exec` while Layer3 stays `delete_audit.log`; record that
  allowed-root protection applies on both the recursive and the non-recursive path, and that a delete
  whose target still exists is reported as a failure and is not written to the dedicated log.
- shell-mcp: Layer2 and Layer3 are already correct; record the not-applicable reasons — dangerous-option
  rejection cannot be complete for a free-form command surface, and an arbitrary allowed command has no
  expected resulting state, so exit-code classification, timeout, and truncation reporting are the result
  checks.
- Cite `scripts/mcp_servers/file/write_service.py`, `scripts/mcp_servers/file/delete_service.py`,
  `scripts/mcp_servers/file/write_server.py`, and `scripts/mcp_servers/file/delete_server.py` as the
  code evidence.

## Compatibility considerations

- The document's tool tables, health-response shapes, and configuration tables are unchanged.
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and
  `docs/91_security/security_02_high-risk-tool-common-policy.md` reference this coverage; their updates
  are Plan rows 18 and 19.

## Security considerations

- The document records enforcement facts only; no secret, token, or full command text is added.

## Rollback considerations

N/A: revert the commit. A rollback reopens the documentation gap AC-009 closes.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_workitem_structure.py --file implementations/20261017-162434_12_docs_22_mcp_mcp_04_02_file-write-file-delete-shell.md.md`

## Completion criteria

- Each of the three server sections states all five layers, with an explicit reason for every
  not-applicable layer (AC-009).
- No `**Audit:**` line in this file still claims file-write-mcp or file-delete-mcp writes no shared
  record (AC-009).
- The docs checkers report no findings for this file.

## Out of scope

- Changing tool schemas, configuration keys, or health-response shapes.
- Recording coverage for servers documented in other files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three layer-coverage subsections | Completed | — | 2026-10-17 | REQ-009 |
| 2 | Update the three Audit lines and the implementation notes | Completed | — | 2026-10-17 | AC-009 |
| 3 | Run the docs checkers | Completed | — | 2026-10-17 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-009
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md`