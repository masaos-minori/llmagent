## Goal

Restate process-record removal during shutdown to match the coordinator's record-ownership rule (REQ-003; AC-2).

## Scope
**Release unit**: N/A: no release unit

## Assumptions

- Confirmed in Step 3a: `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md:21` states that shutdown removes the
  process entry before signalling; `scripts/agent/http_lifecycle_shutdown_coordinator.py:9` and `:109` state that
  nothing is removed before the termination attempt and a record is released only on a confirmed exit.
- `tests/agent/test_http_lifecycle_shutdown_coordinator.py::test_no_removal_before_termination` (`:115`) proves the
  code behavior, so the corrected statement is provable.
- The sibling document `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md:101` already states the rule
  correctly and is owned by the cliplc009 plan; this document must agree with it, not restate it differently.
- `tests/agent/test_http_lifecycle_shutdown_coordinator.py` is a validation reference, not a modification target: it
  is not a row of the Plan's target table.

## Design decisions

- The corrected sentence keeps the snapshot semantics (a snapshot exists only while the manager holds a process entry)
  and changes only the ordering claim: the entry is released after a confirmed exit, so after an unconfirmed
  termination the record is still held and re-terminated by the next `shutdown_all()`.

## Alternatives considered

- Rewriting the paragraph to describe only the reported failure — rejected: the surviving record is the registry
  entry itself under the coordinator's rule, so the failure-only wording would lose the re-termination behavior the
  sibling document already states.

## Implementation
### Target file
`docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`
### Procedure

- Replace the clause at `:21` that says shutdown removes the entry before signalling with the coordinator's rule:
  nothing is removed before the attempt, and the record is released only when its exit is confirmed.

### Method

- Sentence-level edit; no code path is touched.

### Details

- Keep the preceding sentence (the methods only poll or read cached states and do not terminate or restart processes)
  unchanged, and keep the facade paragraph that follows.

## Compatibility considerations

- No runtime behavior changes; the docs gates and the named test are the only checks affected.
- The file is referenced by `routing.md`, `.claude/commands/mcp-server-add.md`, the MCP guide files, and
  `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`; content-only edits do not break those links.

## Security considerations

- N/A: documentation-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Unit — `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py`: passes, including
  `test_no_removal_before_termination`.
- Docs gate — `uv run python tools/check_docs_consistency.py --domain mcp`.
- Sequence: format → lint → type → arch → security → test → coverage (`rules/toolchain.md`).

## Completion criteria

- The document states record ownership the way the coordinator implements it, the statement is provable by the named
  test, and the docs gate reports no finding.

## Out of Scope

- The sibling lifecycle document and its stderr-log path row (owned by the cliplc009 plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Restate the record-ownership rule per Procedure/Method/Details | Pending | — | — | Plan Phase 3 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Plan Phase 7 |

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
- **Requirement ID**: `REQ-003` (MCP lifecycle document states record ownership as implemented)
- **Source issue**: `issues/20261119-145312_cliplc014_cli-docs-consolidation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-223853_cliplc014_cli-docs-consolidation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-001124
- **Related target files**: `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md`
