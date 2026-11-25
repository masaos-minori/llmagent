## Goal

Point the ADR citation for the retry-class classification helper at the module that defines it after plan row 22
moved the helper out of `agent/tool_runner.py` (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The ADR's decision text is unchanged by this Plan: only the cited source path moves, so the invariant statement
  itself is not reworded.
- The first mention in INV-18 ("the class recorded by `scripts/agent/tool_runner.py`") stays: recording is still
  performed there; only the classification decision moved.

## Design decisions
- Update the citation rather than add an exception: the pre-commit ADR hook resolves the cited node against the
  named file, so a citation to a file that no longer defines the node is a finding, not a stylistic choice.

## Alternatives considered
- Keeping the helper in `tool_runner.py` — rejected: the module-size gate is the reason row 22 split it out, and
  the baseline is a ceiling that only shrinks.
- Adding an allowlist entry to the ADR hook — rejected: the citation is factually wrong after the move, so there is
  nothing to allow.

## Implementation
### Target file
`docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`

### Procedure
Replace `scripts/agent/tool_runner.py::_classify_retry_class` with
`scripts/agent/tool_call_identity.py::_classify_retry_class` in the "Explicit in code" citation of INV-18.

### Method
Edit the citation path; no other line of the ADR changes.

### Details
- The change is one path in one line (line 88). The second citation in the same line,
  `scripts/shared/mcp_dedup_config.py`, is unaffected.
- The ADR is not renumbered and no new ADR is created: the inline ADR-018 draft from row 22 stays a draft.

## Compatibility considerations
Runs with the code change of row 22 in the same change set; the ADR hook fails if the move lands without the
citation.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Gate | `uv run pre-commit run --all-files` | The ADR Invariant Matrix hook reports no finding |
| `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` | Gate | `uv run python tools/check_docs_consistency.py --domain overview` | No finding |

## Completion criteria
The cited node resolves against `scripts/agent/tool_call_identity.py` and the ADR hook reports nothing.

## Out of Scope
The ADR's decision text, the moved helper bodies (row 22), and the ADR index or graph regeneration.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Point the INV-18 citation at `scripts/agent/tool_call_identity.py` | Completed | — | 2026-11-25 |  |
| 2 | Run the ADR and documentation checkers (`rules/tool-gates.md`) | Completed | — | 2026-11-25 | check_adr_preservation reports the intended citation move (citation removed from tool_runner, added to tool_call_identity): INV-18 decision text unchanged, only the Explicit-in-code evidence path follows the helper moved by plan row 22; check_adr_invariant_matrix, check_adr_reference, check_adr_structure, check_docs_structure, check_docs_quality, check_docs_content_policy, check_docs_consistency --domain overview, check_adr_authority, generate_adr_authority --check all pass |

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
- **Requirement ID**: `REQ-007` (the generated reference and citation set stays in step with the moved symbol)
- **Source issue**: `issues/20261119-140511_mcpai004_logical-idempotency-key-replay.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261125-105505_mcpai004_logical-idempotency-key-replay.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-112546
- **Related target files**: `docs/10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md`