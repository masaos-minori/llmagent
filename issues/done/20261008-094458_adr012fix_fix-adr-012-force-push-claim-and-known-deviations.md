# Fix ADR-012 force-push rationale and reconcile with code and ledger

## Priority
Medium

## Summary
Reconcile ADR-012 with the current code and ledger: withdraw the unsupported "forced update unreachable" rationale, align the authentication wording with ADR-007, and correct Verification and Known Deviations. Code has moved ahead of memo2.md, so the scope must be re-derived first.

## Background
Source: local investigation notes (memo2.md, ADR-012 section; review findings H02, H06, G05). memo2.md assumes ref validation checks only a leading "-". Adversarial verification found that `git_service.py` now has an allow-list (`_validate_ref_allowlist`) that rejects "+", ":", "^", "~", "..", "@{", whitespace, and "refs/" prefixes, with tests (`TestWriteRefAllowlist`), and that the git_push/git_pull schemas now require `branch`. The ledger (MCP-002, MCP-004) and the ADR text still describe the old behavior.

## Problem
- Verification asserts a forced update is unreachable only because there is no force parameter; that reasoning ignores refspec syntax in arguments. The code now rejects refspec forms, so Verification should cite the allow-list tests instead.
- Context says "optional Bearer token", contradicting ADR-007 where it is mandatory.
- Security Consequences claim option injection is prevented by a leading "-" check, which does not describe the real validation.
- Known Deviations lists only AGENT-003; whether MCP-001, MCP-002, MCP-004 still apply depends on the ledger reconciliation.
- Verified: Decision items are already numbered 1 to 10, so finding G04 does not apply.

## Reason for Change
A wrong security rationale in an Accepted ADR is dangerous; reviewers rely on it. If Decision item 2, 3, or 4 wording changes, governance_01 requires a new approval record.

## Implementation Intent
- Re-verify code state first, then apply the memo2.md text only where it is still accurate.

## Target Files or Areas
- `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`
- `scripts/mcp_servers/git/git_service.py`, `scripts/mcp_servers/git/git_tools.py`, `scripts/mcp_servers/git/git_server.py` (read-only evidence)

## Required Changes
- Decide per Known Issue (MCP-001, MCP-002, MCP-004) whether it is still open.
- Replace the Context constraint (ADR-007 Bearer authentication).
- Replace the Verification item that relies on the missing force parameter with one backed by the allow-list tests.
- Correct Security Consequences, Invariants, Known Deviations, and Related ADRs accordingly.
- Record approval per governance_01 if a Decision item changes.

## Constraints
- governance_01 ADR Change Protocol applies to Decision changes.
- Known Deviations must cite only Known Issues that are open and accurately described in governance_03 Part 1.
- No source-code line numbers or concrete config values.

## Acceptance Criteria
- No sentence asserts that a forced update is unreachable merely because no force parameter exists.
- Verification and Known Deviations agree with code and ledger.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`, including Known Deviation sync. No code change.

## Documentation Impact
Documentation only: ADR-012 (Context, Security Consequences, Invariants, Verification, Known Deviations, Related ADRs, and approval record if needed).

## Out of Scope
- Fixing MCP-001 in code.
- Closing MCP-002/MCP-004 in the ledger (see the kiupd01 issue).

## Dependencies
- Related: the gitref01 and gitaudit01 issues, already in `issues/done/` (their code changes appear applied).
- Related: the kiupd01 issue (ledger state of MCP-002/MCP-004).

## Unresolved Questions
- Whether MCP-001 (audit records) is still reproducible: `git_server.py` now wraps `_audit_log` in `_audit_log_safe`; not verified here.
- Whether MCP-002 and MCP-004 are resolved in code (evidence above) and should be removed from the ledger rather than cited.
- The ADR states no formal Approval Record exists (task-level approval decision only); the form of a "new approval record" must be confirmed from governance_01 before editing.

## AI Implementation Instruction
Re-verify code state first (allow-list, tool schemas, audit path) and cite only Known Issues that still exist. Edit only the listed sections. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094458
- **Related target files**: `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`
