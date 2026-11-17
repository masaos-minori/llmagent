## Goal

Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` to
state that the RAG consistency check is skipped on any runtime-stage FATAL (readiness or
tool discovery), not only on a readiness FATAL (`REQ-004`, `DOC-001`).

## Scope
**Release unit**: N/A: not part of a release unit

### Companion test files
- N/A: documentation-only change; no test file is modified.

## Assumptions
- The doc is high-level (intent and failure behavior); no implementation-location detail or
  line numbers are added, per `DOC-001`.
- The two occurrences that describe the readiness-only skip are the only places the doc
  scopes the skip to readiness.

## Design decisions
- Minimal text change: replace the "when readiness already reported a FATAL" clause with
  "on any runtime-stage FATAL (readiness or tool discovery)" in both occurrences.
- Keep the surrounding sentence structure and the rest of the paragraph/bullet intact so the
  high-level description stays coherent.

## Alternatives considered
- Adding implementation-location detail or line numbers: rejected — `DOC-001` explicitly
  forbids it; the doc must stay high-level.
- Editing only one occurrence: rejected — both occurrences scope the skip to readiness and
  would remain stale.

## Implementation
### Target file
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
Update exactly two occurrences. Verify there are exactly two with `rg` before editing.

1. Runtime-stage paragraph (`Operational Notes > Severity Mapping for Startup Verification`):
   change
   `it skips tool discovery and the RAG check when readiness already reported a FATAL.`
   to
   `it skips tool discovery and the RAG check on any runtime-stage FATAL (readiness or tool discovery).`

2. `mcp_auth` bullet (`Important Notes`): change
   `The runtime stage skips tool discovery and the RAG check when readiness already reported a FATAL; only the aggregated \`has_fatal\` of a stage decides whether startup aborts.`
   to
   `The runtime stage skips tool discovery and the RAG check on any runtime-stage FATAL (readiness or tool discovery); only the aggregated \`has_fatal\` of a stage decides whether startup aborts.`

Leave every other line untouched.

### Method
- Locate both occurrences with `rg -n "skips tool discovery and the RAG check"` and confirm
  exactly two matches (one in the runtime-stage paragraph, one in the `mcp_auth` bullet).
- Confirm neither occurrence already reads "any runtime-stage FATAL".
- Edit both occurrences with the replacements above; do not touch line numbers or add
  implementation-location detail.
- Re-run `rg` to confirm both now read "on any runtime-stage FATAL (readiness or tool
  discovery)" and that no readiness-only occurrence remains.

### Details
- The doc currently scopes the RAG-check skip to a readiness FATAL in two places: the
  runtime-stage paragraph (which lists `readiness`, `mcp_tool_discovery`,
  `rag_consistency` as the runtime-stage checks) and the `mcp_auth` bullet.
- After `scripts/agent/startup_validation.py` gains the `pipeline.has_fatal` short-circuit
  after MCP tool discovery (see the sibling procedure document), a tool-discovery FATAL also
  skips the RAG check, so both occurrences become stale unless updated.
- `DOC-001` requires the update stay high-level (intent and failure behavior only).

## Compatibility considerations
- Documentation-only change; no code behavior changes. The update makes the doc match the new
  behavior of `check_services` (RAG check skipped on any runtime-stage FATAL).

## Security considerations
- N/A: documentation-only change.

## Rollback considerations
- N/A: revert the commit; the two text replacements are isolated.

## Validation plan
- Consistency: run the docs consistency checker referenced by `REQ-004` (the plan's
  validation item for the doc row).
- Static: `stale_detector` and `check_workitem_structure` on this procedure document.

## Completion criteria
- Both occurrences now state the RAG check is skipped on any runtime-stage FATAL
  (readiness or tool discovery).
- No readiness-only occurrence remains.
- The doc stays high-level (no implementation-location detail or line numbers added).
- The docs consistency checker passes.

## Out of Scope
- Any change to `scripts/agent/startup_validation.py` or its tests (handled by the sibling
  procedure document).
- Changing what the RAG consistency check verifies or how it classifies severity.
- Editing any other document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261117-175055_startup001_rag-skip-tool-fatal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261117-201048_startup001_rag-skip-tool-fatal.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-202448
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
