## Goal
- Reword ADR-013's token-storage Assumption from "plain string in config" to a `${ENV:...}`
  reference resolved at load time, and reference ADR-017 for the MCP token convention (Plan
  Phase 1; REQ-004; AC-004).

## Scope
**Release unit**: N/A: not part of a release unit
- **In-Scope**: the Assumption bullet at line 62 of
  `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`.
- **Out-of-Scope**: ADR-013's other Assumptions and its Invariants, ADR-017's text, all code.

## Assumptions
- Verified this cycle: the Assumption reads "stored as a plain string in config (following the
  existing `auth_token = \"${ENV:...}\"` convention...)" while `scripts/eventbus/config.py`
  (comment at line 260; resolution at lines 317-321) resolves `${ENV:VAR_NAME}` references
  via `shared.config_utils.resolve_env_ref` before validating any token value — the stored
  value is a reference, not a plain string.

## Design decisions
- Describe the load-time resolution mechanism (reference + resolver) rather than the literal
  config string, and defer the MCP token convention to ADR-017 as the `mcp.authentication`
  authority (`config/adr_authority.toml` line 68).

## Alternatives considered
- Keeping the "plain string" phrasing — rejected: it contradicts `scripts/eventbus/config.py`
  behavior and the Plan's AC-004.

## Implementation
### Target file
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` (Modify)
### Procedure
1. Reword the line 62 Assumption: token values are stored as `${ENV:...}` references resolved
   at configuration load time; reference ADR-017 (`adr_02_03_017_mcp-authentication.md`) for
   the MCP token convention.
### Method
- Docs-only edit; one Assumption bullet.
### Details
- Resolver facts to reflect: `_ENV_REF_RE` pattern and `resolve_env_ref()` at
  `scripts/shared/config_utils.py` lines 19-43; EventBus resolves before validation at
  `scripts/eventbus/config.py` lines 317-321.

## Compatibility considerations
- `tests/eventbus/test_eventbus_auth.py` (cited by the ADR-013 Verification matrix row) is
  unchanged; the ADR-013 -> ADR-017 mention adds a reference only, no new authority edge is
  required because `mcp.authentication` is already registered to ADR-017.

## Security considerations
- Accurate wording prevents documenting an env-var indirection as plain-string storage, which
  would weaken the token-handling expectations around `resolve_env_ref` failure behavior.

## Rollback considerations
- Revert the single docs commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`
- `uv run python tools/check_adr_reference.py` (ADR-017 reference must resolve)
- `uv run python tools/check_adr_invariant_matrix.py`
- N/A: no pytest or code targets (docs-only row; behavior already covered by
  `tests/eventbus/test_eventbus_auth.py`)

## Completion criteria
- AC-004: the Assumption describes load-time `${ENV:...}` resolution with an ADR-017 reference,
  and all ADR checkers pass with 0 findings.

## Out of Scope
- Any change to EventBus auth behavior or `scripts/eventbus/config.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-220310 | 20261118-220346 | Plan Phase 1 (no decision needed) Changed: docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row; no test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-220346 | 20261118-220746 | Docs checkers only; ruff/mypy/pytest N/A 3e member checkers Pass (structure/reference/invariant_matrix; check_docs_structure on the target Pass; no 'plain string' claim remains); row 3 awaits end-of-batch validation run 3e end-of-batch validation Pass: check_docs_quality (175 files, exit 0), check_docs_structure on 5 changed docs Pass, check_docs_content_policy Pass, check_docs_japanese N/A (no Japanese files), check_docs_consistency --domain mcp Pass, check_adr_structure/reference/authority/invariant_matrix Pass, check_workitem_traceability exit 0; pytest N/A (documentation-only, no scripts/config change); check_adr_preservation flags only the procedure-authorized edits (see Final Report) |
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
- **Requirement ID**: REQ-004 (AC-004)
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-210631_adrchk001_mcp-auth-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-212828
- **Related target files**: docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md