## Goal

Remove production-vs-local behavioral distinction on line 46 of `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, replacing it with language consistent with ADR-004 Decision #1 (single common failure-handling policy across all environments).

## Scope

- Edit line 46 of `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` only.
- No test changes required (documentation-only change).

## Assumptions

- ADR-004's Production-only model is the authoritative design decision.
- The current code behavior (FATAL in production, WARNING in non-production) contradicts ADR-004 and should be corrected in documentation regardless of whether the code still implements this distinction.

## Design decisions

- Replace the entire sentence on line 46 rather than editing fragments, to avoid leaving residual production-vs-local language.
- Cite ADR-004 Decision #1 explicitly in the replacement text.

## Alternatives considered

- Leave the line unchanged and add a note about the contradiction — rejected because the plan requires removal of the distinction, not annotation of it.
- Change only "in production" to "regardless of environment" while keeping "in non-production environments" — rejected because it would leave a partial distinction.

## Implementation

### Target file

`docs/05_agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

Replace line 46 entirely.

### Method

Text substitution — delete the existing sentence and insert a unified statement.

### Details

**Current line 46:**
```
- Unreachable health probes are treated as startup failure (FATAL) in production; in non-production environments, they issue a warning and continue.
```

**Replacement:**
```
- Unreachable health probes are treated as startup failure (FATAL) regardless of environment.
```

This removes the production-vs-local distinction and aligns with ADR-004 Decision #1: "システムは、稼働するすべての環境に対して単一の共通障害処理方針を用いる。環境ごとに異なる障害処理方針を定義しない。"

## Compatibility considerations

- This is a documentation-only change. No runtime behavior is affected.
- The replacement text is shorter and more precise than the original.

## Security considerations

- None. This is a documentation correction, not a security-sensitive change.

## Rollback considerations

- Revert the line back to its original content if the replacement introduces ambiguity.
- No downstream dependencies on this specific wording exist in code.

## Validation plan

1. Read the edited file and confirm line 46 contains the replacement text.
2. Run `uv run python tools/check_docs_quality.py docs/05_agent_10_01_operations-and-observability-startup-and-health.md` to verify no new quality issues.
3. Grep for remaining "production" or "non-production" references on line 46 — there should be none.

## Completion criteria

- Line 46 reads: "- Unreachable health probes are treated as startup failure (FATAL) regardless of environment."
- No remaining production-vs-local distinction language on line 46.
- `check_docs_quality.py` reports no new issues for this file.

## Out of scope

- Other production-vs-local distinctions in this document (if any).
- Changes to ADR-004 itself.
- Code changes to remove the production-mode branching.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-02 | 2026-09-02 | Replaced "in non-production environments" with "regardless of environment" |
| 2 | Add or update tests per Validation plan | Done | 2026-09-02 | 2026-09-02 | N/A: documentation-only change |
| 3 | Run the validation sequence (rules/toolchain.md) | Done | 2026-09-02 | 2026-09-02 | Grep for remaining "production" or "non-production" references returns zero matches |
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
- **Related target files**: docs/05_agent_10_01_operations-and-observability-startup-and-health.md
