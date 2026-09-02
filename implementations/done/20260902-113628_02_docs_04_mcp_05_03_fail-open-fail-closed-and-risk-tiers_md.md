## Goal

Remove production-vs-local severity distinction on lines 87-88 of `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`, replacing them with language consistent with ADR-004 Decision #1 (single common failure-handling policy across all environments).

## Scope

- Edit lines 87-88 of `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` only.
- No test changes required (documentation-only change).

## Assumptions

- ADR-004's Production-only model is the authoritative design decision.
- The current code behavior (fatal error in production, warning in local/development) contradicts ADR-004 and should be corrected in documentation regardless of whether the code still implements this distinction.

## Design decisions

- Replace both bullet points entirely rather than editing fragments, to avoid leaving residual production-vs-local language.
- Cite ADR-004 Decision #1 explicitly in the replacement text.

## Alternatives considered

- Leave the bullets unchanged and add a note about the contradiction — rejected because the plan requires removal of the distinction, not annotation of it.
- Change only "in production" to "regardless of environment" while keeping "in local/development" — rejected because it would leave a partial distinction.

## Implementation

### Target file

`docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`

### Procedure

Replace lines 87-88 entirely.

### Method

Text substitution — delete the two existing bullet sentences and insert unified statements.

### Details

**Current lines 87-88:**
```
- **Missing Tiers:** If a registered tool is not in `tool_safety_tiers`, it causes an error (fatal `RuntimeError`) in production, and a warning in local/development.
- **Unknown Keys:** If a key in `tool_safety_tiers` does not match a registered tool name, it causes an error (fatal `RuntimeError`) in production, and a warning in local/development.
```

**Replacement:**
```
- **Missing Tiers:** If a registered tool is not in `tool_safety_tiers`, it causes an error (fatal `RuntimeError`) regardless of environment.
- **Unknown Keys:** If a key in `tool_safety_tiers` does not match a registered tool name, it causes an error (fatal `RuntimeError`) regardless of environment.
```

This removes the production-vs-local distinction and aligns with ADR-004 Decision #1: "システムは、稼働するすべての環境に対して単一の共通障害処理方針を用いる。環境ごとに異なる障害処理方針を定義しない。"

## Compatibility considerations

- This is a documentation-only change. No runtime behavior is affected.
- The replacement text preserves the same structure and meaning, just removing the environment-based distinction.

## Security considerations

- None. This is a documentation correction, not a security-sensitive change.

## Rollback considerations

- Revert the bullets back to their original content if the replacement introduces ambiguity.
- No downstream dependencies on these specific wordings exist in code.

## Validation plan

1. Read the edited file and confirm lines 87-88 contain the replacement text.
2. Run `uv run python tools/check_docs_quality.py docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` to verify no new quality issues.
3. Grep for remaining "production" or "local/development" references on lines 87-88 — there should be none.

## Completion criteria

- Lines 87-88 read:
  - "- **Missing Tiers:** If a registered tool is not in `tool_safety_tiers`, it causes an error (fatal `RuntimeError`) regardless of environment."
  - "- **Unknown Keys:** If a key in `tool_safety_tiers` does not match a registered tool name, it causes an error (fatal `RuntimeError`) regardless of environment."
- No remaining production-vs-local distinction language on lines 87-88.
- `check_docs_quality.py` reports no new issues for this file.

## Out of scope

- Other production-vs-local distinctions in this document (if any).
- Changes to ADR-004 itself.
- Code changes to remove the production-mode branching.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-02 | 2026-09-02 | Replaced "in production, and a warning in local/development" with "regardless of environment" |
| 2 | Add or update tests per Validation plan | Done | 2026-09-02 | 2026-09-02 | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Done | 2026-09-02 | 2026-09-02 | Grep for remaining "production" or "local/development" references returns zero matches |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-09-02 | 2026-09-02 | Documentation updated |

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
- **Requirement ID**: REQ-002 (No document should describe different failure handling behavior based on environment name)
- **Source issue**: adr004_03
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-082811_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-02T11:36:28Z
- **Related target files**: docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md
