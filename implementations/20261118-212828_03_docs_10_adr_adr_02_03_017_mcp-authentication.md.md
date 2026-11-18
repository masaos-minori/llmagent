## Goal
- Fix the misattributed invariant citation in ADR-017's Negative Consequences: bypassing
  `require_auth_token()` violates `INV-02`, not `INV-03` (Plan Phase 1; REQ-002; AC-002).

## Scope
**Release unit**: N/A: not part of a release unit
- **In-Scope**: the Negative Consequences bullet at line 108 of
  `docs/10_adr/adr_02_03_017_mcp-authentication.md`.
- **Out-of-Scope**: the `INV-01..INV-05` definitions (lines 121-123), the Verification table
  (its INV citations are already correct), every other ADR.

## Assumptions
- Verified this cycle: line 108 reads "a new server that bypasses it violates INV-03";
  `INV-02` (line 122) is the `require_auth_token()` routing rule and `INV-03` (line 123) is
  the `attach_auth_middleware()` empty-token 401 rule — the bullet must cite `INV-02`.

## Design decisions
- Citation-only fix; the bullet's substance stays unchanged (minimal-diff docs edit).

## Alternatives considered
- Rewording the whole Negative Consequences section — rejected: the Plan's frozen row scopes
  this to the citation fix only.

## Implementation
### Target file
- `docs/10_adr/adr_02_03_017_mcp-authentication.md` (Modify)
### Procedure
1. Change the Negative Consequences bullet "a new server that bypasses it violates INV-03"
   to cite `INV-02`.
### Method
- Docs-only edit; a single citation token change.
### Details
- `require_auth_token()` lives at `scripts/mcp_servers/server.py` line 226; the routing rule
  it enforces is `INV-02`.

## Compatibility considerations
- Verification-table rows citing `INV-01`/`INV-02`/`INV-04` (lines 148-150) stay unchanged;
  `tools/check_adr_invariant_matrix.py` compares the index matrix with ADR invariants and is
  unaffected by this bullet.

## Security considerations
- The fix keeps the correct invariant attached to the shared token enforcement point, so the
  no-bypass rule (AC-002) remains traceable to `INV-02`.

## Rollback considerations
- Revert the single docs commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_invariant_matrix.py`
- `uv run python tools/check_adr_reference.py`
- `rg -n "violates INV-02" docs/10_adr/adr_02_03_017_mcp-authentication.md` shows the fixed
  bullet; no remaining Negative-Consequences citation of `INV-03`
- N/A: no pytest or code targets (docs-only row; the behavior is already covered by
  `tests/mcp_servers/test_require_auth_token.py::test_every_server_routes_through_shared_enforcement_point`)

## Completion criteria
- AC-002: the Negative Consequences bullet cites `INV-02` and all ADR checkers pass with 0
  findings.

## Out of Scope
- Any other edit to ADR-017; no decision is involved (Plan Phase 1).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 (no decision needed) |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row; no test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Docs checkers only; ruff/mypy/pytest N/A |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | The target file is the documentation itself (Step 1) |

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
- **Requirement ID**: REQ-002 (AC-002)
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-210631_adrchk001_mcp-auth-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-212828
- **Related target files**: docs/10_adr/adr_02_03_017_mcp-authentication.md
