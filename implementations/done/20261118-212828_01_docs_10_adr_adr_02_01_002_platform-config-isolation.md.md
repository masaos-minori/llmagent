## Goal
- Record the ADR-002 INV-04 amendment proposal in the governance_01 pending-amendment form
  (Plan Phase 2, gated): add the pending bullet under ADR-002's `### Approval Record` citing
  `AAL-030` (REQ-005; AC-001, AC-005).

## Scope
**Release unit**: N/A: not part of a release unit
- **In-Scope**: one pending-amendment bullet under `### Approval Record` (section exists at
  line 292) citing the `AAL-030` ledger entry added by the seq 05 procedure.
- **Out-of-Scope**: the INV-04 text itself (line 182), the INV-04 Verification-table row
  "Not verified (no automated test exists)" (line 233), and the Open-Items checkboxes
  (lines 339-340) — those are updated only when an approval is recorded, not this cycle;
  any maintainer approval text, Approver, or Date (forbidden by AC-005); the
  formal-exception alternative (stays available, UNK-01).

## Assumptions
- Gate: execute only after the user acknowledges the governance_03 scope amendment and the
  maintainer authorizes filing the proposal (Plan Phase 2 gate).
- Draft proposal wording (subject to maintainer decision, never merged without approval —
  UNK-01), from the Plan's `Affected areas`: "INV-04: The Agent's configuration files carry
  no MCP-server-owned settings. The only MCP-specific value the Agent is given is each
  enabled server's connection token, supplied through the environment-variable mechanism
  owned by ADR-017; an enabled server resolving to an empty token aborts startup per
  ADR-017."
- The `AAL-030` ledger entry must already exist in `governance_03` (seq 05 procedure runs
  first; `tools/check_adr_structure.py` requires every cited ID to have a ledger entry).

## Design decisions
- Use the governance_01 `ADR Pending Amendment Form` (line 298); the enforcing checker keeps
  the entry valid while unapproved.

## Alternatives considered
- Record a formal exception instead of an amendment (Issue's "(decision)" alternative) — kept
  available for the maintainer; not taken here (UNK-01).

## Implementation
### Target file
- `docs/10_adr/adr_02_01_002_platform-config-isolation.md` (Modify)
### Procedure
1. Confirm the Phase 2 gate is open (user acknowledgement + maintainer authorization).
2. Add the pending-amendment bullet under `### Approval Record` citing `AAL-030`, with the
   draft wording above and approval `Not recorded`.
### Method
- Docs-only edit; single added bullet; no changes to INV-04 text, Verification table, or
  Open Items.
### Details
- Evidence (verified this cycle): INV-04 text at line 182; Verification row at line 233;
  Open Items at lines 339-340; Approval Record section at line 292 ("No formal Approval
  Record ... has been created").

## Compatibility considerations
- ADR-002 is cited widely (`config/adr_authority.toml` edges, `docs/10_adr/adr_01_index.md`
  matrix); leaving INV-04 text untouched keeps every existing citation valid.
- Ordering dependency: the seq 05 procedure (`governance_03` `AAL-030` entry) must complete
  first.

## Security considerations
- No secret values are written; the wording describes env-var token supply only, matching
  `scripts/agent/startup_validation.py` lines 152-161 behavior.

## Rollback considerations
- Revert the single docs commit; remove the bullet. If the seq 05 entry was also added,
  revert both together to keep ledger/citation consistency.

## Validation plan
- `uv run python tools/check_adr_structure.py` (pending-bullet / ledger-citation rule)
- `uv run python tools/check_adr_reference.py`
- `uv run python tools/check_adr_authority.py`
- `uv run python tools/check_adr_invariant_matrix.py`
- N/A: no pytest or code targets (docs-only row; contradicting behavior is already covered
  by `tests/agent/test_startup.py::test_mcp_auth_fatal_when_any_server_missing_token`)

## Completion criteria
- AC-001 and AC-005: the proposal exists only in pending form, Approver/Date remain
  `Not recorded`, INV-04 text is unchanged, and all ADR checkers pass with 0 findings.

## Out of Scope
- Applying or approving the amendment; editing INV-04 or its verification rows; the
  formal-exception path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-220420 | 20261118-220448 | Gated: Plan Phase 2 (user acknowledgement of the governance_03 scope amendment + maintainer authorization); see Assumptions Gate released: user acknowledged the governance_03 scope amendment and authorized filing the proposal (session question 20261118-220333); dependency seq-05 ledger entry AAL-030 added first Changed: docs/10_adr/adr_02_01_002_platform-config-isolation.md |
| 2 | Add or update tests per Validation plan | N/A | — | — | Docs-only row; no test changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-220448 | 20261118-220746 | Docs checkers only; ruff/mypy/pytest N/A 3e member checkers Pass (structure pending-bullet/ledger-citation rule, reference, authority, invariant_matrix; INV-04 line 182 unchanged); row 3 awaits end-of-batch validation run 3e end-of-batch validation Pass: check_docs_quality (175 files, exit 0), check_docs_structure on 5 changed docs Pass, check_docs_content_policy Pass, check_docs_japanese N/A (no Japanese files), check_docs_consistency --domain mcp Pass, check_adr_structure/reference/authority/invariant_matrix Pass, check_workitem_traceability exit 0; pytest N/A (documentation-only, no scripts/config change); check_adr_preservation flags only the procedure-authorized edits (see Final Report) |
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
- **Requirement ID**: REQ-005 (AC-001, AC-005)
- **Source issue**: issues/20261117-123001_adrchk001_mcp-auth-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-210631_adrchk001_mcp-auth-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-212828
- **Related target files**: docs/10_adr/adr_02_01_002_platform-config-isolation.md