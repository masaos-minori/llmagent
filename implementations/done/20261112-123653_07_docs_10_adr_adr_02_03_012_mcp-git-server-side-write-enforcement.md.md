## Goal
Complete ADR-012: add ADR-007 to the front matter, invariants for Decision Details #5 to #10, the definitions of the documented safe exception and Stages 1 to 3, and test file paths in the Verification table (`REQ-002`, `REQ-004`, `REQ-008` / `AC-2`, `AC-4`).

## Scope
**Release unit**: authority-model

## Assumptions
- Front matter `related` lists no ADR; the body's Related ADRs already lists ADR-007 (so only the front matter changes, a Step 3a correction to the Plan row); invariants are INV-01 to INV-04 only (checked).
- Code facts (checked in `scripts/mcp_servers/git/repository_state.py` and `write_protection_pipeline.py`): `verify_preconditions(dry_run, allow_detached_head)` skips both guards when `dry_run` is true; otherwise rejects Detached HEAD unless `allow_detached_head` is true, and the dirty-worktree guard is unconditional; the pipeline runs Stage 3 (authorization), 4, 5, 5b, 6, 7, and its docstring says Stages 1-3 are handled before construction and 8-9 after.
- New invariants restate existing Decision text and cited tests; any without an automated test is Non-Blocking (Plan Assumptions).
- Security Reviewer approvals stay pending; no reviewer name or date is written (UNK-05).
- Test file paths resolved by search: `tests/mcp_servers/git/test_git_security_compliance.py`, `test_git_service_dispatch.py`, `test_repository_state.py`.

## Design decisions
- Number invariants INV-05 to INV-10 to match Decision Details #5 to #10, so no existing number changes.
- Add an `Implementation` column to the Automated Tests table, the same shape other ADRs use.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`

### Procedure
1. Add `adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` to the front matter `related`.
2. Add INV-05 to INV-10 under Invariants, one per Decision Detail #5 to #10.
3. In Decision Detail #5, define the documented safe exception (`dry_run`) and the Detached HEAD policy; in #9, define Stages 1 to 3.
4. Add the `Implementation` column with test file paths and map each existing row to its invariant.
5. Append `Current Decision Approval (pending)` lines.

### Method
- Safe exception: a `dry_run` request skips the dirty-worktree and Detached HEAD preconditions but is still subject to the protected-branch check (`test_dry_run_checkout_protected_branch_still_denied`); without `dry_run`, Detached HEAD is rejected unless the call sets `allow_detached_head`, and a Dirty Worktree is always rejected.
- Stages 1 to 3: repository path validation, write guard, and authorization (protected branch and ref validity); define them from the code docstring and verify the Stage 3 placement before writing.
- Table: rows citing `Decision Details #N` become `INV-0N` rows (keep the `Decision Details` wording in the Verifies cell if no invariant fits); every cited test gets its file path.
- Tests without an automated citation are marked Non-Blocking.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); no approval or reviewer name is written (UNK-05).
- Do not add reviewer names to the Approval section; report the Security Reviewer approval as pending in the final report.
- Run `check_adr_preservation.py` and explain each reported change.

## Compatibility considerations
N/A: documentation-only; invariants restate existing decisions, so no behavior or decision changes.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`, `check_adr_preservation.py` (only intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.
- `uv run python tools/check_known_deviation_sync.py` — pass.

## Completion criteria
- Front matter lists ADR-007; INV-05 to INV-10 exist; the safe exception and Stages 1 to 3 are defined; every cited test has a file path that exists.
- Pending approval lines exist; no reviewer is named.

## Out of Scope
- New behavior or new tests; Security Reviewer approval; changing Decision Detail wording beyond the two definitions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112-181217 | 20261112-181217 | ADR-012 verification table gained an Implementation column (INV-01..INV-10 mapped, cited tests resolved to existing file paths); Approval Record gained two pending-approval lines; adr_01_index.md INV-01/INV-03 citations updated for invariant-matrix agreement |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112-181217 | 20261112-181217 | check_adr_structure/invariant_matrix/reference/authority and check_docs_quality/content_policy --strict/japanese and check_known_deviation_sync pass; check_docs_structure size gate is non-blocking; check_adr_preservation reports only intended changes |

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
- **Requirement ID**: `REQ-002` / `REQ-004` / `REQ-008` — ADR-007 front matter; invariants for Decision Details #5-#10; exception and stage definitions; test paths
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md`
