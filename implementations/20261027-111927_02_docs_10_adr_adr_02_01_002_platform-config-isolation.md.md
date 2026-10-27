## Goal

Record ADR-002 INV-03 and INV-04 as not verified and make the Verification-related Completion Checklist items state the true status (`REQ-002`: not-verified records and checklist correction; `REQ-004`: no Invariant, Decision, Gate or Approval text changed).

## Scope

- Edit the Implementation cells of the INV-03 and INV-04 rows of `### Automated Tests`, and two items of `### Completion Checklist`.
- Keep the `## Completion Checklist`-family heading required by `tools/check_adr_structure.py`, and leave every other row and item unchanged.

## Assumptions

- Order: this row follows `plans/20261027-104411_govrev003_partial-verification-gate-rules.md`, whose vocabulary is implemented first (UNK-04). If it is not in `docs/10_adr/adr_01_index.md`, stop and report `Blocked`.
- Step 3a evidence: the INV-03 row ("An MCP server can start standalone without agent.toml") and the INV-04 row ("The Agent can start without being given MCP-specific Secrets") have Implementation `-`. `rg` over `tests/` finds no test for either, and `tests/mcp_servers/test_config_isolation_fail_closed.py` covers only a falsy own-config-file case.
- The checklist items "Each Invariant has a corresponding Verification" and "Automatable verification does not rely only on Manual Review" are currently marked `[x]`, which the table contradicts.
- UNK-02 (non-blocking): the Blocking column of both rows stays `Yes`; whether a Blocking invariant may stay Blocking while `Not verified` is decided with the repository owner under the govrev003 vocabulary. Report it as `Needs confirmation`.
- UNK-03: unchecking is the recommendation; the status note replaces the checkmark.
- Size gate: the file is 20369 B against the 24576 B default limit with no per-file exception (headroom 4207 B), so the edit fits.
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- Replace `-` with `Not verified (no automated test exists)` in both rows; invent no citation.
- Uncheck the two checklist items (`[x]` to `[ ]`) and append a short status note to each naming INV-03 and INV-04.

## Alternatives considered

- Keeping the items checked with a status note: acceptable fallback per UNK-03, rejected as default because a checked item would still overstate completeness.

## Implementation
### Target file

`docs/10_adr/adr_02_01_002_platform-config-isolation.md`

### Procedure

1. Re-check (read-only): `rg` once more over `tests/` for a test of standalone MCP server startup without `agent.toml` or Agent startup without MCP-specific Secrets. If one exists, cite its node ID instead of `Not verified` and report it.
2. In the `### Automated Tests` table, replace the `-` Implementation cell of the INV-03 and INV-04 rows with `Not verified (no automated test exists)`.
3. In `### Completion Checklist`, change `[x]` to `[ ]` for "Each Invariant has a corresponding Verification" and "Automatable verification does not rely only on Manual Review", and append ` (INV-03 and INV-04 are not verified)` to each.

### Method

Exact-string edits on the four lines.

### Details

- Keep the `[x]` state of every other checklist item.
- Do not add a Known Issue or Needs Confirmation entry; that is the repository owner's decision (Plan Documentation Impact).

## Compatibility considerations

N/A: documentation only. `check_adr_preservation.py` may report the table and checklist changes; review each as intended.

## Security considerations

N/A: no secret or credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_adr_structure.py` (the checklist heading is intact) and `uv run python tools/check_adr_preservation.py` (review every report).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py docs/10_adr/adr_02_01_002_platform-config-isolation.md`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.

## Completion criteria

- ADR-002 INV-03 and INV-04 are recorded as not verified.
- The two Verification checklist items match the table.
- No Invariant, Decision, Gate or Approval text changed; the checkers report no finding other than reviewed, intended preservation reports.

## Out of Scope

- Writing the missing tests.
- The ADR-001 table and the index (rows 01 and 03).
- Registering Known Issue or Needs Confirmation entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-check for tests of INV-03 and INV-04 (read-only) | Pending | — | — | |
| 2 | Mark INV-03 and INV-04 as not verified and correct the two checklist items | Pending | — | — | |
| 3 | Run the checkers named in the Validation plan | Pending | — | — | Review `check_adr_preservation.py` reports |

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
- **Requirement ID**: `REQ-002` (record INV-03 and INV-04 as not verified, correct the checklist), `REQ-004` (no other ADR text changed)
- **Source issue**: issues/20261027-101918_govrev004_adr-verification-evidence-sync.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104705_govrev004_adr-verification-evidence-sync.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111927
- **Related target files**: docs/10_adr/adr_02_01_002_platform-config-isolation.md
