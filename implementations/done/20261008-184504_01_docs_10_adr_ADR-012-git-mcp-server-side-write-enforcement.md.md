## Goal
Correct ADR-012's Context, Decision items 2 and 3, INV-01/02, Verification, Security Consequences and Known Deviations (REQ-001 to REQ-007 of the Plan).

## Scope
- Only `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`; no other file is modified by this procedure.

## Assumptions
- UNK-02 resolved: the write allow-list (`GitService._validate_ref_allowlist`) rejects `+ : ^ ~ ? * [`, backslash, `..`, the `@` plus `{` sequence, whitespace and control characters, a `refs/` prefix and `HEAD`; an option-shaped value (leading `-`) is rejected by the Stage 5 ref-validity precondition (`repository_state._validate_ref`); `git_push` and `git_pull` also pass `--` before the branch (`format_output.py`).
- User decision (2026-10-08): a `Decision Change` line is added (UNK-01). MCP-001 and MCP-002 are not cited because they are not in the ledger.

## Design decisions
- The wording follows the validators actually in the repository, not memo2.md's earlier state in which only a leading `-` was rejected.
- Known Deviations uses the standard `Known Issue` form with MCP-004's ledger meaning.

## Alternatives considered
- Citing MCP-001 and MCP-002: rejected; they no longer exist in the ledger.

## Implementation
### Target file
docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md

### Procedure
1. Replace the "optional Bearer token" Context constraint.
2. Rewrite Decision Details #2 and #3 and INV-01 and INV-02.
3. Replace the "no force parameter" Verification item with the allow-list tests.
4. Rewrite the Security Consequences line and the Known Deviations entry.
5. Add the Decision Change line, run the checkers and the two cited test classes.

### Method
Exact-string replacements in one file.

### Details
Code claims keep their evidence labels; no line numbers or counts are added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None; the text describes existing validation and adds no behavior.

## Rollback considerations
- Revert the commit.

## Validation plan
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain mcp`) and `uv run pytest tests/mcp_servers/git/test_git_service_dispatch.py -k "WriteRefAllowlist or GitPushRefRejectionBeforeGit"`.

## Completion criteria
- The edits are in place, the cited tests exist and pass, and the checkers pass (REQ-001 to REQ-007).

## Out of scope
- Any file other than `docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md`, including `adr-index.md` and the governance ledger.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-184529 | 20261008-184529 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-184529 | 20261008-184529 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/done/20261008-094458_adr012fix_fix-adr-012-force-push-claim-and-known-deviations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-183905_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-184504
- **Related target files**: docs/10_adr/ADR-012-git-mcp-server-side-write-enforcement.md