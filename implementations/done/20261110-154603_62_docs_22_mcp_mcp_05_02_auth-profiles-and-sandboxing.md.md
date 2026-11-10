## Goal
Remove `accept_all_for_tests` and profile references (REQ-008, AC-05/AC-07).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers were read on 2026-11-10 before the code phases; re-locate them with `rg` if the file changed. Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- The document is edited in Phase 6, after the code phases, so it describes the final behavior.

## Design decisions
- Describe behavior only; do not copy concrete config values (`skills/DESIGN.md` Docs content policy).
- English only (`skills/DESIGN.md` Output language).

## Alternatives considered
N/A: documentation-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`
### Procedure
1. Lines 36-40: delete the `## Security Profile (`security_profile`)` section (heading, the single-member paragraph, and the profile wording of the Enforcement Point); keep the Enforcement Point content as part of the Authentication section (empty `auth_token` rejected by `McpServerConfig`, by server startup, and as FATAL `mcp_auth` in Agent startup) without any profile wording.
2. Search the Authentication section for `accept_all_for_tests` or a test-only bypass sentence (rg found none at plan time; confirm and remove if present).
3. Check in-document anchors to the removed heading (`rg -n 'security-profile' docs`) and repoint or drop them.
### Method
- Locate each statement with `rg -n 'tool_definitions_strict|routing_drift_strict|security_profile|SecurityProfile|accept_all_for_tests|list_tools|allowed_tools|allowed_root|protected_branches|path_denylist|fail-open' docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` and read the surrounding lines before editing.
### Details
- Target behavior to state: Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- After the edit, `rg -n 'security_profile|SecurityProfile|accept_all_for_tests|list_tools_with_server_key' docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` returns nothing (AC-07, AC-05, AC-06).

## Compatibility considerations
N/A: documentation only; no code or config behavior changes in this row.

## Security considerations
N/A: documentation only; the text must not weaken the described fail-closed behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain mcp`.

## Completion criteria
- Every listed statement is changed, the checkers above pass, and no removed name remains in the file.

## Out of Scope
- Renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; any file other than the target; writing the ADR-004 rationale text (maintainer, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure | Done | 20261110-230601 | 20261110-230601 | Security Profile heading and single-member paragraph deleted; Enforcement Point merged into Authentication without profile wording; security-profile keyword removed |
| 2 | Run the documentation checkers per Validation plan | Done | 20261110-230601 | 20261110-230601 | structure/consistency --domain mcp pass; rg shows no removed names |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | accept_all_for_tests confirmed absent in the document (rg) | No further change |
| VF-2 | No in-document or cross-document anchors to #security-profile existed; only the Keywords entry | Keyword removed |

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
- **Related target files**: `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`
