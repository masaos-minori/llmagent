## Goal
Remove the strict keys and state that an empty `allowed_tools` denies (REQ-008).

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
`docs/23_agent/agent_08_03_configuration-tools-memory.md`
### Procedure
1. Lines 29-30: delete the `tool_definitions_strict` and `routing_drift_strict` bullets; add one bullet saying a startup tool-definition mismatch or routing drift always aborts startup and the removed keys are rejected as unknown.
2. Line 35: `allowed_tools` empty means every tool is denied (not 'all allowed').
3. Line 87: replace the `Under tool_definitions_strict=True ...` sentence with the unconditional statement.
4. Line 88: replace the `allowed_tools=[]` allow-all sentence with deny-all at runtime plus the load-time validator error.
### Method
- Locate each statement with `rg -n 'tool_definitions_strict|routing_drift_strict|security_profile|SecurityProfile|accept_all_for_tests|list_tools|allowed_tools|allowed_root|protected_branches|path_denylist|fail-open' docs/23_agent/agent_08_03_configuration-tools-memory.md` and read the surrounding lines before editing.
### Details
- Target behavior to state: Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- After the edit, `rg -n 'security_profile|SecurityProfile|accept_all_for_tests|list_tools_with_server_key' docs/23_agent/agent_08_03_configuration-tools-memory.md` returns nothing (AC-07, AC-05, AC-06).

## Compatibility considerations
N/A: documentation only; no code or config behavior changes in this row.

## Security considerations
N/A: documentation only; the text must not weaken the described fail-closed behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_08_03_configuration-tools-memory.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
- Every listed statement is changed, the checkers above pass, and no removed name remains in the file.

## Out of Scope
- Renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; any file other than the target; writing the ADR-004 rationale text (maintainer, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure | Done | 20261110-231812 | 20261110-231812 | strict-key bullets replaced with one always-FATAL bullet naming the keys as rejected unknown keys; allowed_tools bullets (line 35 and Key Constraints) rewritten to deny-all incl. reload with load-time validator error |
| 2 | Run the documentation checkers per Validation plan | Done | 20261110-231812 | 20261110-231812 | structure/consistency --domain agent/quality/content-policy --strict pass; rg for removed names returns nothing |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | No mismatches: anchors 29-30/35/87-88 verified; unknown-key rejection confirmed via production_config_validator._check_unknown_production_keys (lines 275, 345-349, top-level keys not in sub-config dataclass fields) | Applied edits as specified |

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
- **Related target files**: `docs/23_agent/agent_08_03_configuration-tools-memory.md`
