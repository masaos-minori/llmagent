## Goal

Remove production-vs-local violation handling distinction on line 45 of `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`, replacing it with language consistent with ADR-004 Decision #1 (single common failure-handling policy across all environments).

## Scope

- Edit line 45 of `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` only.
- No test changes required (documentation-only change).

## Assumptions

- ADR-004's Production-only model is the authoritative design decision.
- The current code behavior (errors when `security_profile == "production"`, warnings otherwise) contradicts ADR-004 and should be corrected in documentation regardless of whether the code still implements this distinction.

## Design decisions

- Replace only the clause describing the production-vs-local distinction within line 45, preserving the rest of the paragraph intact.
- Cite ADR-004 Decision #1 explicitly in the replacement text.

## Alternatives considered

- Leave the line unchanged and add a note about the contradiction — rejected because the plan requires removal of the distinction, not annotation of it.
- Change only "only when security_profile == 'production'" to "regardless of environment" while keeping "otherwise, they are downgraded to warnings" — rejected because it would leave a partial distinction.

## Implementation

### Target file

`docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`

### Procedure

Edit the production-vs-local distinction clause within line 45.

### Method

In-place text substitution — replace the clause describing environment-based violation handling.

### Details

**Current line 45 (relevant clause):**
```
The Production validator treats violations as errors only when security_profile == "production"; otherwise, they are downgraded to warnings with a [local/development] prefix.
```

**Replacement clause:**
```
The Production validator treats violations as errors regardless of environment.
```

**Full updated sentence:**
```
Both validators return a ConfigValidationResult(errors, warnings) (with an ok property). The RAG validator checks cross-file consistency in the rag section (e.g., mismatch between embedding_dim/vec_dim, use_rrf=False, cache thresholds). The Production validator treats violations as errors regardless of environment. Validation items include: checking if _REQUIRED_STRICT_KEYS is False, bidirectional differences between tool_safety_tiers and the registry, whether allowed_tools == [], and an approval-risk floor check for git write tools (git_checkout/git_pull/git_push) that flags any of the three whose effective risk resolves below HIGH — via an invalid approval_risk_rules override, an explicit non-HIGH override, or an implicit tool_safety_tiers fallback — even when approval_risk_rules is absent from config entirely. If known_tools is omitted, it attempts dynamic retrieval from the registry.
```

This removes the production-vs-local distinction and aligns with ADR-004 Decision #1: "システムは、稼働するすべての環境に対して単一の共通障害処理方針を用いる。環境ごとに異なる障害処理方針を定義しない。"

## Compatibility considerations

- This is a documentation-only change. No runtime behavior is affected.
- The replacement shortens the sentence significantly by removing the conditional clause.

## Security considerations

- None. This is a documentation correction, not a security-sensitive change.

## Rollback considerations

- Restore the original clause if the replacement introduces ambiguity.
- No downstream dependencies on this specific wording exist in code.

## Validation plan

1. Read the edited file and confirm line 45 contains the replacement clause.
2. Run `uv run python tools/check_docs_quality.py docs/90_shared_03_01_runtime_and_execution-config-and-logging.md` to verify no new quality issues.
3. Grep for remaining "production" or "local/development" references on line 45 — there should be none.

## Completion criteria

- Line 45 reads: "The Production validator treats violations as errors regardless of environment."
- No remaining production-vs-local distinction language on line 45.
- `check_docs_quality.py` reports no new issues for this file.

## Out of scope

- Other production-vs-local distinctions in this document (if any).
- Changes to ADR-004 itself.
- Code changes to remove the production-mode branching.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-09-02 | 2026-09-02 | Replaced "only when security_profile == 'production'; otherwise, they are downgraded to warnings with a [local/development] prefix" with "regardless of environment" |
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
- **Related target files**: docs/90_shared_03_01_runtime_and_execution-config-and-logging.md
