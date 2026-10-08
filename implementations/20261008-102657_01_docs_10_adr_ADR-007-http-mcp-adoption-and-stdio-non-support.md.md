## Goal
Make ADR-007 state only what is true: no TLS or separate-host benefits, an explicit mdq-mcp authentication exception, MCP-005 recorded as a Known Deviation, an accurate retry policy and middleware note (REQ-001 to REQ-008 of the Plan).

## Scope
- Edit only ADR-007's Decision Details 9 and 10, Rationale 2 and 3, the Alternative A disadvantages, Consequences, Invariants INV-09 and INV-10, a new Exceptions section, Retry Policy, Implementation Notes, Known Deviations, one Completion Checklist item, and the Approval Record.
- Keep Status `Accepted`, existing numbering, and every other section unchanged.

## Assumptions
- MCP-005 exists in the ledger (re-check immediately before editing; if absent, stop and report, per Plan UNK-04).
- Approval Record form: the user chose to add a task-level approval line (no individual names).
- The mdq exception describes intended behavior.

## Design decisions
- The Exceptions section goes directly after Invariants, as the ADR section order requires, and points to the mdq enforcement document instead of restating its details.
- Known Deviations uses the existing `**Known Issue**: <ID> — tracked in governance_03 Part 1 (...)` format.
- Rationale 3 is retitled "Deployment Independence" because separate-host placement is not supported.

## Alternatives considered
- Leave INV-09 universal and rely on the Known Deviation alone: rejected; the mdq exception is intended behavior, not a deviation.
- Remove the TLS mention from Decision 9: rejected; the "not implemented" note there is accurate and should stay.

## Implementation
### Target file
docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md

### Procedure
1. Confirm `#### MCP-005` exists in the ledger; read each section to be edited.
2. Apply the replacements listed in Details, section by section, each via a unique-text edit.
3. Add the Exceptions section after the Invariants list and before Failure Policy.
4. Run the validation commands; search the ADR for `TLS` and `separate host`.

### Method
Targeted unique-string replacements; no restructuring.

### Details
- Decision 9: after "every MCP server configuration must carry a non-empty authentication token" add the sentence "Every MCP server verifies the Bearer token on every endpoint, except as listed in Exceptions." Keep the existing TLS-not-implemented sentence and evidence note.
- Decision 10: "Fault isolation, operational monitoring, and independent deployment take priority over the cost of HTTP Serialization and Socket communication." (drop "placement on separate hosts").
- Rationale 2 body: "With HTTP, each server can authenticate every caller with a Bearer token and reject requests that do not carry it. A stdio channel offers no comparable per-request authentication point."
- Rationale 3: heading "### 3. Third Reason for Adoption — Deployment Independence"; body: "With HTTP, a server can be restarted, upgraded, or replaced without restarting the Agent, and its health can be probed by tools other than the Agent."
- Alternative A Disadvantages: replace the two lines "Authentication and TLS are difficult" and "No placement on separate hosts" with the single line "No per-request authentication point".
- Positive Consequences: replace "Security controls through authentication and TLS become possible" and "Placement on separate hosts becomes possible" with "Per-request authentication with a Bearer token becomes possible".
- Negative Consequences: replace "Authentication must be implemented" and "TLS configuration is required" with "Authentication tokens must be provisioned for every server" and "Placement on a separate host is not possible without designing TLS/mTLS (see Review Triggers)".
- INV-09: "MCP servers bind only to a loopback address. Every enabled server entry carries a non-empty authentication token, and every MCP server rejects requests without a matching Bearer token, except as listed in Exceptions."
- INV-10: "Fault isolation, operational monitoring, and independent deployment take priority over the cost of HTTP Serialization and Socket communication."
- New section "## Exceptions": mdq-mcp attaches the authentication middleware with an empty token and does not verify Bearer tokens at the HTTP layer; its security boundary is the fail-closed `allowed_dirs` path authorization (see the mdq enforcement document); the Agent-side `auth_token` for mdq must still be non-empty; changing this exception requires a decision recorded in this ADR.
- Retry Policy: "Retry target: HTTP 429/502/503/504 and transport-level request errors other than timeouts (for example, connection errors)"; keep "Retry count: bounded"; "Backoff: increasing delay between attempts for retryable HTTP statuses"; "Errors not retried: timeouts and other HTTP status codes".
- Implementation Notes first bullet: `run_http()` enforces loopback-only binding; each server module attaches the Bearer-token middleware through `attach_auth_middleware()`; mdq-mcp attaches it with an empty token (see Exceptions); rag-pipeline-mcp does not attach it (MCP-005). Second bullet: add that transport request errors other than timeouts are also retried.
- Known Deviations: replace "No confirmed deviations." with "- **Known Issue**: MCP-005 — tracked in governance_03 Part 1 (rag-pipeline-mcp does not attach the Bearer authentication middleware; violates INV-09)"; keep the following "Do not unconditionally align" sentence.
- Completion Checklist: keep the Known Issue item checked and append "(MCP-005)".
- Approval Record: add a line recording that on 2026-10-08 the removal of TLS and separate-host claims, the mdq authentication exception, and the MCP-005 deviation were approved as a task-level approval decision (repository administrator instruction), with no individual reviewer names.

## Compatibility considerations
- `check_known_deviation_sync.py` requires every cited Known Issue to exist in the ledger; MCP-005 does.
- adr-index rows for ADR-007 are updated by a separate issue and are not edited here.

## Security considerations
- The ADR now discloses missing authentication on one server; it contains no token values or exploit detail.

## Rollback considerations
- Documentation only; revert the implementation commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`
- `uv run python tools/check_known_deviation_sync.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `grep -n -i 'TLS\|separate host' docs/10_adr/ADR-007-*.md`: only Decision 9's "not implemented" note, the Negative Consequence note, and the Review Trigger remain.

## Completion criteria
- No TLS or separate-host benefit claim remains (REQ-001); Exceptions and MCP-005 recorded (REQ-002, REQ-003); Retry Policy and Implementation Notes accurate (REQ-004, REQ-005); checklist and approval record updated (REQ-006, REQ-007); checkers pass (REQ-008).

## Out of scope
- Code changes, the ledger, adr-index, other ADRs, the Verification test list, and the dead write-retry guard noted in the Plan (UNK-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct TLS, separate-host, and consequence claims | Completed | 20261008-103005 | 20261008-103005 |  |
| 2 | Update Decision 9, INV-09, and add Exceptions | Completed | 20261008-103005 | 20261008-103005 |  |
| 3 | Update Known Deviations and checklist item | Completed | 20261008-103005 | 20261008-103005 |  |
| 4 | Update Retry Policy and Implementation Notes | Completed | 20261008-103005 | 20261008-103005 |  |
| 5 | Update the approval record | Completed | 20261008-103005 | 20261008-103005 |  |
| 6 | Run checkers | Completed | 20261008-103005 | 20261008-103005 |  |

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
- **Requirement ID**: REQ-001 (TLS claims), REQ-002 (mdq exception), REQ-003 (MCP-005), REQ-004 (retry), REQ-005 (middleware note), REQ-006 (checklist), REQ-007 (approval), REQ-008 (checkers)
- **Source issue**: issues/20261008-094451_adr007fix_fix-adr-007-tls-claims,-mdq-exception,-and-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-102447_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-102657
- **Related target files**: docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md