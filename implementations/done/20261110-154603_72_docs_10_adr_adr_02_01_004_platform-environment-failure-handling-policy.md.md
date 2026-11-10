## Goal
Register the `path_denylist` empty-list exception with a PENDING rationale and drop the strict-key wording (REQ-008, REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers were read on 2026-11-10 before the code phases; re-locate them with `rg` if the file changed. Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- The document is edited in Phase 6, after the code phases, so it describes the final behavior.
- This file is shared with the (archived) adrrev003 Plan, which edited Decision Group 10 (fallback); this row edits Group 1 and the INV-01/INV-02 alignment text only.
- Edit order: Phase 6 runs after the code phases, so `config/github_mcp_server.toml` already carries its marker when this exception is registered.

## Design decisions
- The exception is the approved intent (owner decision 2026-11-10); `check_adr_preservation.py` may report an expected finding for the Group 1 addition, which is recorded in the final report.

## Alternatives considered
N/A: documentation-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
1. Lines 235-238 (Alignment with INV-01 and INV-02): line 238 says `ProductionConfigValidator` rejects strict keys that are not true; reword to state that the strict checks have no toggle (the keys no longer exist).
2. Decision Group 1 (heading at line 61, content lines 62-65): add the exception record for an empty `path_denylist` in the github server: it stays permitted although Group 1 forbids an empty safety list from relaxing a boundary. The rationale text is the maintainer's (UNK-01); write only a clearly marked PENDING placeholder, never an invented rationale.
3. Add one inline `Needs confirmation` marker at the pending rationale, following the marker format of existing markers (`rg -n 'Needs confirmation' docs`), then register it as a new entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` and run `check_needs_confirmation_inventory.py`; the implementer does not write the rationale; remove the marker only when the maintainer's text is supplied.
4. Do not change Group 1 decisions otherwise; no Known Deviations edit unless the repository check `check_known_deviation_sync.py` requires one (run it).
### Method
- Locate each statement with `rg -n 'tool_definitions_strict|routing_drift_strict|security_profile|SecurityProfile|accept_all_for_tests|list_tools|allowed_tools|allowed_root|protected_branches|path_denylist|fail-open' docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` and read the surrounding lines before editing.
### Details
- Target behavior to state: Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- After the edit, `rg -n 'security_profile|SecurityProfile|accept_all_for_tests|list_tools_with_server_key' docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` returns nothing (AC-07, AC-05, AC-06).

## Compatibility considerations
N/A: documentation only; no code or config behavior changes in this row.

## Security considerations
N/A: documentation only; the text must not weaken the described fail-closed behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_known_deviation_sync.py`.

## Completion criteria
- Every listed statement is changed, the checkers above pass, and no removed name remains in the file.

## Out of Scope
- Renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; any file other than the target; writing the ADR-004 rationale text (maintainer, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure | Done | 20261110-232433 | 20261110-232433 | Group 1 exception record added with PENDING placeholder and inline (Needs confirmation) marker; INV-02 alignment text reworded to unconditional checks/removed keys; intro sentence 'strict-default' -> 'unconditional' |
| 2 | Run the documentation checkers per Validation plan | Done | 20261110-232433 | 20261110-232433 | structure/quality/content-policy --strict/adr authority/nc inventory/known deviation pass; adr preservation exit 0 with 2 expected WARNINGs (Decision and Invariants section text changed) |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | check_adr_preservation WARNINGs require a sentence-level mapping: intro 'strict-default behavior enforces' -> 'unconditional startup checks enforce'; INV-02 alignment bullet reworded (strict-keys-not-true -> always-fatal + removed keys rejected as unknown); Group 1 exception record added; Verification-table '(strict keys)' parenthetical deleted | Mapping recorded here; no INV-NN invariant line, H2 sequence, front matter, Known Deviations, or Approval text changed |
| VF-2 | Verification table line cited 'Config Isolation (strict keys)' which the procedure did not list; stale after key removal | Parenthetical removed; registered as this finding |
| VF-3 | Procedure Assumption said config/github_mcp_server.toml carries a marker when this row runs; the file has no Needs confirmation marker, only the plain path_denylist=[] line | Marker placed in the ADR-004 Group 1 record only; inventory entry NC-001 registered and check_needs_confirmation_inventory.py reports no issues |
| VF-4 | check_known_deviation_sync.py passes unchanged; the new exception cites no Known Issue ID | No Known Deviations edit required |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
