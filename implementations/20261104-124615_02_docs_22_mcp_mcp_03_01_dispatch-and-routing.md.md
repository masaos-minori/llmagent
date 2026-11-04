## Goal
- Add one bullet to "Idempotency and retry" in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` that names the Agent's audit logical key and distinguishes it from the transport `X-Idempotency-Key`, so a reader cannot conflate the two (`REQ-002`: state how the audit key differs from the transport key).

## Scope
**Release unit**: N/A: not part of a release unit

- Documentation only: one added bullet in one section. The existing transport-key bullets stay byte-identical.

## Assumptions
- The audit key is the workflow, task, turn, and call id joined by colons, passed only to the audit event and never sent to a server; the transport key is a deterministic hash of the method, tool name, canonical arguments, and a session or token identity, sent as `X-Idempotency-Key` (checked in Step 3a against the runner and the transport).
- The documented way to follow one call across the Agent and a server is the join on the request id described in `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` ("Approval correlation"); the new bullet points to it instead of restating it (checked in Step 3a).
- The existing bullet "Key ownership" says the Agent generates one key per logical call; that wording stays as the Plan requires, and the new bullet is worded not to contradict it.
- Step 2 start conditions held: the Plan is not gated, has no blocking Unknown, and no cross-plan overlap names it.

## Design decisions
- Add a new bullet immediately after "Key ownership" rather than editing any existing bullet, so `AC-2` (existing transport description unchanged) is checkable with a diff that has only added lines.
- Describe the audit key by its parts and role, with no file, function, or symbol names, following the docs content policy (no implementation-location mapping).

## Alternatives considered
N/A: single added bullet; the Plan's DD-1 already chose to correct both sites.

## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

### Procedure
1. In the section "Idempotency and retry", locate the bullet that starts with `**Key ownership:**`.
2. Insert the new bullet on the line after it, before the `**Empty-key rule:**` bullet.

### Method
Add exactly this bullet (English, one paragraph):

```text
- **Audit key (separate):** the Agent's `tool_exec` audit event records its own workflow-scoped logical-call identity (workflow, task, turn, and call id joined by colons) in its `idempotency_key` field. This value is never sent to a server, is not the `X-Idempotency-Key`, and no de-duplication keys on it; to follow one call across the Agent and a server, join on the request id (see [mcp_02_03](mcp_02_03_audit-logging-and-errors.md)).
```

### Details
- Do not edit the section's intro paragraph or any other bullet.
- The relative link targets a sibling document of `docs/22_mcp/`; confirm it resolves with `tools/check_docs_structure.py`.

## Compatibility considerations
N/A: documentation only; no behavior, API, or reference-table change.

## Security considerations
N/A: the text names no secret, token, or concrete configuration value.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `git diff -U0 docs/22_mcp/mcp_03_01_dispatch-and-routing.md` shows added lines only inside the section (no removed line), which confirms the transport description is unchanged.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, and `uv run python tools/check_docs_consistency.py --domain mcp` report no findings.

## Completion criteria
- The section names the agent-audit logical key and states how it differs from the `X-Idempotency-Key` (`AC-2`).
- The existing transport-key bullets are unchanged and the docs checkers are clean.

## Out of Scope
- Changing any transport-key statement, the dedup cache description, or any other section.
- The audit-trace document (separate procedure) and the code comment (separate procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the audit-key bullet as described in Implementation > Procedure/Method | Pending | — | — | |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (dispatch doc names the audit key and distinguishes it from the transport key)
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-165600_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-124615
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
