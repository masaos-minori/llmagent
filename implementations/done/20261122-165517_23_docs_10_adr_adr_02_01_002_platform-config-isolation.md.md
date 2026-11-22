## Goal
Remove the removed prompt key from the ADR's Agent config-key example list (REQ-009, documentation claim correction).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 85 lists `system_prompt_tool` as an Agent config key with a built-in default; after row 01 deletes the key and row 04 removes the field, the ADR presents a key that no longer exists, so the example must drop it.
- The edit is confined to one example list entry: no Decision, Failure Policy, normative keyword, invariant, or Known Deviations statement changes, which is what `tools/check_adr_preservation.py` compares against `HEAD`. The ADR's ownership statement itself stays; the single-source decision is recorded because the repository has no decision-log document class (Plan Documentation Impact).
## Design decisions
- N/A: one list entry removed; no ADR decision change is being made.
## Alternatives considered
- Rewriting the row to describe the single source as a new ownership rule: rejected, that would change an ADR decision, which is outside this procedure's scope and needs a Plan revision.

## Implementation
### Target file
`docs/10_adr/adr_02_01_002_platform-config-isolation.md`
### Procedure
Delete `system_prompt_tool` from the example key list at line 85; leave the remaining example keys and the table row structure unchanged. Do not add replacement examples.

## Compatibility considerations
- `check_docs_consistency.py --domain agent` cross-checks config-key claims against `config/agent.toml`, so this row must be committed with row 01 or the checker reports a stale key.
## Security considerations
- N/A: no trust boundary is involved.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- `uv run python tools/check_docs_consistency.py --domain agent`; `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`; `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_adr_authority.py` (the ADR gates in `rules/tool-gates.md`).
## Completion criteria
- No ADR statement presents the removed key as an Agent config field, and the docs and ADR checks pass with no preserved-text finding (AC-6).
## Out of Scope
- History-style comment cleanup (`adrchk022`); any change to the ADR's decision text, Status, or approval statements.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure | Completed | 20261122-182914 | 20261122-182914 | commit with row 01 for the config-key check batch-run; example key removed; no replacement added |
| 3 | Run the validation sequence (`rules/tool-gates.md`) | Completed | — | 20261122-182914 | the docs and ADR checkers listed in Validation plan docs+ADR gates pass (pre-existing agent_14 warning unchanged). Finding: the edited table row is inside '## Decision' (subsection 'Per-Process Required Files and Keys'), contradicting the assumption that Decision text is unchanged; check_adr_preservation warns (exit 0) and requires a sentence-level mapping. Mapping: Decision > Per-Process Required Files and Keys > Agent row, Empty-Allowed Keys list: removed the entry 'system_prompt_tool' (key deleted by row 01, field removed by row 04); no other sentence changed |

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
- **Requirement ID**: `REQ-009` (correct the documentation statements presenting the removed key as a config field)
- **Source issue**: `issues/20261120-114213_agentcfg005_system-prompt-snapshot.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-162618_agentcfg005_system-prompt-snapshot.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-165517
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`