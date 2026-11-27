## Goal

State the public diagnostic display policy in the runtime-architecture documentation: PID/PGID
retained, logical identifiers in public snapshots, raw detail only through the verbose opt-in
(REQ-008 — documentation matches the display policy).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Line 173 describes `ManagedProcessRecord` and lists "stderr log" without distinguishing the internal
  path from the public snapshot value; that distinction is what this row adds.
- Step 3b correction: the procedure states that PID and PGID remain displayed in normal output. The
  display surface (`agent/commands/cmd_mcp.py`) prints only the pid; the pgid appears in the error-log
  line that carries the manual cleanup action. Per the confirmed decision the paragraph records the
  implementation as it is.
- The verbose opt-in is the existing `/debug verbose` log-level control (`scripts/agent/commands/cmd_debug.py`),
  a reference file, not a target: no new mechanism is documented.
- Docs-only row: no code change and no companion test row applies.

## Design decisions

- Document the boundary in one paragraph at the existing process-record paragraph, rather than adding
  a new section, so the display policy stays next to the object it describes.

## Alternatives considered

- N/A: the Plan's display policy (D5) is already decided; this row only records it.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`
### Procedure
- Extend the paragraph at line 173 to state that the record holds the internal log path while the
  public snapshot exposes a logical identifier.
- State that PID and PGID remain displayed in normal output and that raw detail is available only
  through the existing `/debug verbose` opt-in.

### Method
- Two sentences appended to the existing paragraph; no heading changes.

### Details
- Keep the existing link to `../22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` for the manual-cleanup
  path, which is why PID/PGID stay displayed.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: no new disclosure surface; the doc records the AC-1/AC-4 boundary.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Documentation gates per `rules/tool-gates.md`: `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`,
  and `uv run python tools/check_docs_consistency.py --domain agent`.
- Step 3b note: the consistency check reports one pre-existing warning in
  `agent_14_reference-api-subpackages-generated.md` (`/db` base command not registered); it is present
  at HEAD unchanged and is not caused by this row.

## Completion criteria

- The paragraph states the internal-path/public-identifier distinction, the retained PID/PGID, and the
  verbose opt-in, and the doc gates pass.

## Out of Scope

- The snapshot implementation (document 05) and the verbose mechanism itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-035000 | paragraph extended with the internal-path/public-identifier boundary and the display policy; Step 3b: only pid is displayed, pgid appears in the manual-cleanup error-log line, written per the confirmed decision |
| 2 | Run the documentation gates (`rules/tool-gates.md`) | Completed | 20261127-095216 | 20261127-095216 | docs gates pass; consistency check reports one pre-existing warning in agent_14 unrelated to this row; awaiting end-of-batch full suite docs gates pass; consistency check reports one pre-existing warning in agent_14 unrelated to this row; awaiting end-of-batch full suite; full suite: 15938 passed, 6 known baseline failures, 5 skipped; diff-cover 95%; eventbus health tests failed once under -n logical and pass serially, not baselined |

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
- **Requirement ID**: `REQ-008` (documentation states the public diagnostic display policy)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`