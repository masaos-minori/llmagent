## Goal
- Reduce ADR-007's duplicated MCP-token wording to a single authority reference to ADR-017,
  remove the non-existent "secret files" path, and state the disabled-server exclusion in
  the Fail-Fast token condition (Plan Phase 1; REQ-003; AC-003).

## Scope
**Release unit**: N/A: not part of a release unit
- **In-Scope**: Decision item 10 (line 78), the Fail-Fast token bullet, and the
  Implementation References token bullet (line 356) in
  `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`.
- **Out-of-Scope**: item 9 (already references ADR-017 correctly), ADR-017's own text (owned
  by the seq 03 procedure), all code.

## Assumptions
- ADR-017 is the authority for the authentication rules (shared-variable resolution,
  empty-token startup abort, fail-closed middleware); verified this cycle at
  `docs/10_adr/adr_02_03_017_mcp-authentication.md` lines 121-123.
- No secret-file loading path exists in code: `rg -ri "secret file|read_secret" scripts/`
  found no secret-file path (checked in Plan Step 2).

## Design decisions
- Reference-not-restatement: keep ADR-007's config-ownership point (ADR-002) but defer every
  authentication rule to ADR-017, matching the existing ADR-007 -> ADR-017 Specializes edge
  (`config/adr_authority.toml`).

## Alternatives considered
- Restating the full token rules in ADR-007 — rejected: creates a second policy source and
  conflicts with the ADR-017 authority registration (`config/adr_authority.toml`
  `mcp.authentication` -> ADR-017).

## Implementation
### Target file
- `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` (Modify)
### Procedure
1. Reduce Decision item 10 to its ADR-002 config-ownership point plus a reference to ADR-017
   for the token rules (it currently restates token supply at line 78).
2. In the Fail-Fast token bullet ("empty authentication token (Agent startup validation)"),
   add the enabled-scope / disabled-exclusion wording: the fatal finding applies to enabled
   servers only.
3. In the Implementation References token bullet (line 356), remove "or secret files".
### Method
- Docs-only edits; three targeted bullets; no behavior change.
### Details
- Disabled-server exclusion matches `scripts/agent/startup_validation.py` lines 152-161:
  `if not srv.is_disabled and not srv.auth_token` produces the fatal `mcp_auth` finding;
  `tests/agent/test_startup_validation.py::TestMcpAuthDisabledServers` covers both sides.

## Compatibility considerations
- `tests/mcp_servers/test_require_auth_token.py::TestRequireAuthToken::test_empty_token_raises`
  (cited by ADR-017 Verification) is unchanged.
- The "or secret files" removal matches current docs and code: no ADR or script describes a
  secret-file path (`rg -in "secret file" docs/10_adr/` re-check after the edit must show no
  remaining claim).

## Security considerations
- Removing the "secret files" wording eliminates a documented mechanism that does not exist
  in code, closing a false-config surface.

## Rollback considerations
- Revert the single docs commit; no downstream files depend on the removed wording.

## Validation plan
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_reference.py`
- `uv run python tools/check_adr_authority.py`
- `uv run python tools/check_adr_invariant_matrix.py`
- `rg -i "secret file" docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`
  returns no match
- N/A: no pytest or code targets (docs-only row)

## Completion criteria
- AC-003: ADR-007 defers token rules to ADR-017, contains no "secret files" wording, the
  Fail-Fast condition names the enabled-server scope, and all ADR checkers pass with 0
  findings.

## Out of Scope
- Changing any authentication behavior in `scripts/`; editing ADR-017 (seq 03 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-220145 | 20261118-220218 | Plan Phase 1 (no decision needed) Changed: docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row; no test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-220218 | 20261118-220746 | Docs checkers only; ruff/mypy/pytest N/A 3e member checkers Pass (structure/reference/authority/invariant_matrix; rg 'secret file' no match); row 3 awaits end-of-batch validation run 3e end-of-batch validation Pass: check_docs_quality (175 files, exit 0), check_docs_structure on 5 changed docs Pass, check_docs_content_policy Pass, check_docs_japanese N/A (no Japanese files), check_docs_consistency --domain mcp Pass, check_adr_structure/reference/authority/invariant_matrix Pass, check_workitem_traceability exit 0; pytest N/A (documentation-only, no scripts/config change); check_adr_preservation flags only the procedure-authorized edits (see Final Report) |
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
- **Requirement ID**: REQ-003 (AC-003)
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-210631_adrchk001_mcp-auth-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-212828
- **Related target files**: docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md