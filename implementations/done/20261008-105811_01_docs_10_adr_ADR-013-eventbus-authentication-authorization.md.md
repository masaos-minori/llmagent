## Goal
Make ADR-013 describe EventBus authentication as it is wired, keep the intended policy visible, and record the two gaps as Known Deviations (REQ-001 to REQ-005 and REQ-008 of the Plan).

## Scope
- Edit only: Summary (one phrase), Assumptions, Problem and Current State, Decision 1, Rationale 4, Positive Consequences, Invariants (add INV-07), Failure Policy, Verification, Known Deviations, Implementation References (one line), and the Approval Record.
- Keep Status `Accepted` and existing numbering; do not edit other ADRs or documents.

## Assumptions
- EVENTBUS-015 and EVENTBUS-016 exist in the ledger before this edit (procedure 02 runs first; re-check).
- The user chose a task-level approval line for the Approval Record.
- /health is intended to require the Monitoring role and /publish the Publisher role.

## Design decisions
- Describe current behavior and record deviations; do not rewrite the ADR to bless unauthenticated routes.
- Attribute INV-01 evidence only to tests that actually exercise the production wiring.

## Alternatives considered
- Documenting /health and /publish as intentionally open: rejected; contradicts the health reference and INV-01.

## Implementation
### Target file
docs/10_adr/ADR-013-eventbus-authentication-authorization.md

### Procedure
1. Confirm EVENTBUS-015 and EVENTBUS-016 exist; read each section being edited.
2. Apply the replacements in Details by unique-text edits.
3. Add INV-07 after INV-06 and the Verification items.
4. Run the validation commands.

### Method
Targeted unique-string replacements; no restructuring.

### Details
- Summary: replace "adding Bearer-token authentication middleware" with "adding Bearer-token authentication resolved by per-route dependencies".
- Assumptions: replace "(simplest interpretation consistent with the Issue's Required Changes and Acceptance Criteria)" with "(all replay is treated as an operator action)".
- Problem: the sentence "EventBus routes in `scripts/eventbus/` authenticate and authorize callers via Bearer-token middleware and role-based authorization." becomes: EventBus routes are intended to authenticate callers by Bearer token and authorize them by role; roles are resolved by per-route dependencies and the HTTP middleware only assigns a request ID; /health and /publish are registered without a role dependency (EVENTBUS-016).
- Current State: say `attach_auth_middleware(app)` only assigns a request ID; routes other than /health and /publish require role-based authentication via `Depends(require_role(...))`; keep the consumer-identity sentence.
- Decision 1: replace "Bearer token, mirroring `scripts/mcp_servers/server.py::attach_auth_middleware()` pattern — a FastAPI `@app.middleware("http")` function checking `request.headers.get("Authorization", "")` against a configured token." with "Bearer token, resolved per route by FastAPI dependencies (`resolve_principal`, `require_role(...)`, `require_consumer_identity`): a missing or unknown token is rejected with 401 and a token whose roles do not include the route's role with 403. The HTTP middleware attached by `attach_auth_middleware()` only assigns `X-Request-Id`."; after "even when that token is otherwise valid." append "`auth_token` and `admin_token` are operator credentials and MUST NOT be distributed to publishers or consumers; role separation holds only for callers that hold a per-role token."
- Rationale 4: say the Bearer-token scheme follows the convention of the MCP server helper while EventBus resolves roles through dependencies; the audit record structure still mirrors the MCP audit record.
- Positive Consequences: replace the per-role token bullet with: per-role tokens restrict a caller that holds only that token, and because `auth_token` is mandatory and grants every role, role separation depends on keeping it operator-only (INV-07).
- Failure Policy: replace the "health endpoint remains accessible" bullet with "None. /health is intended to require the Monitoring role (not enforced by the application today; EVENTBUS-016)."
- Invariants: add "INV-07: A token that grants every role (`auth_token`, `admin_token`) is never distributed to a publisher or consumer process."
- Verification: append to the unauthenticated-request test item that these tests build their own fixture app with the role dependencies and do not cover the production wiring of /health and /publish (EVENTBUS-016); add a Manual Review item "**Test**: none — **Verifies**: INV-07 — **Type**: Manual Review (deployment configuration review) — **Blocking**: Yes".
- Known Deviations: keep EVENTBUS-008; add "- **Known Issue**: EVENTBUS-015 — tracked in governance_03 Part 1 (`auth_token` and `admin_token` grant every role; INV-07 depends on operator discipline only)" and "- **Known Issue**: EVENTBUS-016 — tracked in governance_03 Part 1 (/health and /publish are registered without a role dependency; violates INV-01)".
- Implementation References: change "`scripts/eventbus/app.py` — middleware registration" to "request-ID middleware registration and route dependencies".
- Approval Record: add a "Decision Change (2026-10-08)" line recording that the authentication description correction, INV-07, and the EVENTBUS-015/016 deviations were approved as a task-level approval decision (repository administrator instruction), with no individual reviewer names.

## Compatibility considerations
- The Known Deviation sync checker requires both Known Issue IDs to exist in the ledger.

## Security considerations
- The ADR now discloses missing authentication on two routes; no secrets or exploit steps are included.

## Rollback considerations
- Documentation only; revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`; search the ADR for "middleware" and "health" to confirm no stale claim remains.

## Completion criteria
- Decision 1, Problem, Current State, Rationale 4, Consequences, Failure Policy, Verification, Known Deviations, Assumptions, and the approval record match the Plan's acceptance criteria AC-1 to AC-5; checkers pass.

## Out of scope
- Code, the ledger, tools, other EventBus documents, and adr-index.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct Summary, Context, Decision 1, Rationale 4, References | Completed | 20261008-110226 | 20261008-110226 |  |
| 2 | Correct Consequences; add INV-07 and Verification | Completed | 20261008-110226 | 20261008-110226 |  |
| 3 | Correct Failure Policy and Verification attribution | Completed | 20261008-110226 | 20261008-110226 |  |
| 4 | Update Known Deviations and Assumptions | Completed | 20261008-110226 | 20261008-110226 |  |
| 5 | Update the approval record | Completed | 20261008-110226 | 20261008-110226 |  |
| 6 | Run the checkers | Completed | 20261008-110226 | 20261008-110226 |  |

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
- **Requirement ID**: REQ-001 (auth description), REQ-002 (consequences, INV-07), REQ-003 (health, verification), REQ-004 (deviations), REQ-005 (assumptions), REQ-008 (approval)
- **Source issue**: issues/20261008-094500_adr013fix_fix-adr-013-role-token-model-and-auth-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-103440_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-105811
- **Related target files**: docs/10_adr/ADR-013-eventbus-authentication-authorization.md