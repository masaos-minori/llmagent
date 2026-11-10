## Goal
State routing drift as always fatal in the ADR-003 startup validation description (REQ-008) without changing any decision.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers were read on 2026-11-10 before the code phases; re-locate them with `rg` if the file changed. Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- The document is edited in Phase 6, after the code phases, so it describes the final behavior.

## Design decisions
- Edit wording only; no invariant, reference, test citation, or Approval text changes (check_adr_preservation.py must not report an ERROR).

## Alternatives considered
N/A: documentation-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
### Procedure
1. Line 256 (invariant table row INV-04): change 'No (warning only; in strict mode startup is aborted, ...)' to state that drift aborts startup and the Routing decision itself is unaffected; keep the INV-04 text, test citations, and Decision Detail reference intact.
2. Line 286: change '(FATAL under `tool_definitions_strict`, otherwise WARNING)' to 'FATAL'.
3. The plan notes the memo's ADR-003 branch was not found separately in code; only these two description lines change.
### Method
- Locate each statement with `rg -n 'tool_definitions_strict|routing_drift_strict|security_profile|SecurityProfile|accept_all_for_tests|list_tools|allowed_tools|allowed_root|protected_branches|path_denylist|fail-open' docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` and read the surrounding lines before editing.
### Details
- Target behavior to state: Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- After the edit, `rg -n 'security_profile|SecurityProfile|accept_all_for_tests|list_tools_with_server_key' docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` returns nothing (AC-07, AC-05, AC-06).

## Compatibility considerations
N/A: documentation only; no code or config behavior changes in this row.

## Security considerations
N/A: documentation only; the text must not weaken the described fail-closed behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_adr_preservation.py`, `uv run python tools/check_adr_authority.py`.

## Completion criteria
- Every listed statement is changed, the checkers above pass, and no removed name remains in the file.

## Out of Scope
- Renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; any file other than the target; writing the ADR-004 rationale text (maintainer, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure | Done | 20261110-232003 | 20261110-232003 | INV-04 table row: warning-only/strict-mode wording replaced with 'startup is aborted on drift' (Routing decision wording kept); line 286 strict-conditioned FATAL clause reduced to (FATAL); no invariant/test-citation/Approval text touched |
| 2 | Run the documentation checkers per Validation plan | Done | 20261110-232003 | 20261110-232003 | structure/quality/content-policy --strict/adr preservation/adr authority pass; rg for removed names returns nothing |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | No mismatches: anchors 256/286 verified against current file; ADR-003 has no strict-key code branch per the plan note | Applied wording-only edits as specified |

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
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`
