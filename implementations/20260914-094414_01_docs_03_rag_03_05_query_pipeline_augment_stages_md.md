## Goal

Add a short note after `docs/03_rag_03_05_query_pipeline-augment-stages.md`'s "No-retry Policy" statement, clarifying that its stated rationale ("transient errors are rare," "content policy rejections will not succeed upon retry") is design reasoning recorded at the time the policy was introduced, not a claim backed by empirical measurement or a dedicated ADR — without fabricating the empirical analysis the Issue requests (REQ-001).

## Scope

- Add one short note after the existing "No-retry Policy" statement, stating its rationale's actual basis (design reasoning, cited to its introducing commit) and that no empirical data or ADR backs the specific claims

## Assumptions

- `git log --all -S "transient errors are rare"` found the complete commit history for this text — no earlier, unreachable commit exists that would predate `27fa06ae`
- No production telemetry or benchmark artifact exists elsewhere in the repository substantiating these claims — this Plan's search was scoped to `docs/adr/` and `git log`, not an exhaustive sweep of every log file or external system

## Design decisions

1. State the rationale's actual basis (design reasoning, cited to its introducing commit) rather than silently leave the existing text as if it were established fact — this directly serves a future reader deciding whether the policy merits revisiting
2. Do not create a new ADR — an ADR implies a formal design-review record with supporting analysis; fabricating one around unverified claims would be worse than the current state (a plain statement without a claimed formal-review pedigree)

## Alternatives considered

1. Creating a new ADR with fabricated empirical analysis, retry-vs-no-retry latency benchmarks, or content-policy-rejection-pattern analysis — rejected because the Issue's Recommended Action requests exactly this kind of content — per user direction, this Plan states the gap rather than inventing content to fill it
2. Changing the refiner's actual retry behavior — rejected because this is a documentation-only change
3. Conducting the empirical studies the Issue requests — rejected because a substantial, separate effort requiring production telemetry or controlled experiments, not a documentation-only fix

## Implementation

### Target file

`docs/03_rag_03_05_query_pipeline-augment-stages.md`

### Procedure

1. Re-confirm the commit history and absence of an ADR
2. Add the clarifying note after the "No-retry Policy" statement

### Method

Phase 1: Preparation — re-confirm evidence line numbers
- Re-run `git log --all -S "transient errors are rare"` and `grep -rl` across `docs/adr/` to reconfirm the citation and absence of an ADR (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

Phase 2: Core Logic — add the clarifying note
- Add the note after the "No-retry Policy" statement (line 156) (REQ-001; `docs/03_rag_03_05_query_pipeline-augment-stages.md`)

### Details

**Phase 1:** Verify via read/grep that:
- Section at `docs/03_rag_03_05_query_pipeline-augment-stages.md:156` states "**No-retry Policy**: Refiner failures are treated as non-critical quality degradations — allowing raw chunks as output. Retrying failed LLM calls offers low expected benefit while increasing latency (transient errors are rare, and content policy rejections will not succeed upon retry). If degraded output cannot be tolerated, completely disable the refiner by setting `use_refiner=false`."
- Origin traced to `27fa06ae` ("feat: add refiner fallback diagnostics and debug visibility") via `git log --all -S "transient errors are rare"`
- Commit message confirms: "docs: document no-retry policy rationale" — confirming this text was written as design reasoning accompanying the diagnostics feature, not derived from a prior empirical study or referenced ADR
- No ADR references the no-retry policy, "transient errors," or "content policy rejection" (confirmed via `grep -rl` across `docs/adr/` — no match; the grep results found only false positives about `retry_policy.max_attempts` for the eventbus/retry mechanism)
- No production telemetry, benchmark results, or retry-latency measurement exists anywhere in this repository that would substantiate "transient errors are rare" or quantify the latency cost of retrying

**Phase 2:** Append the following note after line 156:

```markdown
Note: This rationale was recorded as design reasoning at the time the policy was introduced (`27fa06ae`/`27fa06ae0`: "feat: add refiner fallback diagnostics and debug visibility"), not derived from measured retry-latency data or content-policy-rejection-pattern analysis. No ADR documents this policy. If this policy is revisited, the "transient errors are rare" and "retries increase latency" claims should be verified against actual production data first, since neither is currently substantiated.
```

## Compatibility considerations

This is a documentation-only additive change. No backward compatibility concerns. However, accurately documenting the rationale's actual basis helps readers understand whether the no-retry policy is based on empirical findings or design assumptions, which affects how confidently it can be relied upon.

## Security considerations

No security impact — documentation addition only. However, accurate documentation of the rationale's basis is important for understanding whether the no-retry policy's justification is empirically grounded or merely a design assumption.

## Rollback considerations

Simple revert: remove the added note. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/03_rag_03_05_query_pipeline-augment-stages.md | Manual — review added note for accuracy | Manual inspection + `git log -S` | Note accurately states the rationale's actual basis |

## Completion criteria

- [ ] The note states the no-retry policy's rationale was recorded as design reasoning at introduction time, citing the introducing commit(s) (REQ-001)
- [ ] The note states no ADR documents this policy (REQ-001)
- [ ] The note states the underlying claims ("transient errors are rare," retry latency cost) are unverified and should be checked against actual data before the policy is revisited (REQ-001)
- [ ] The existing "No-retry Policy" statement itself is unmodified

## Out of scope

- Creating a new ADR with fabricated empirical analysis, retry-vs-no-retry latency benchmarks, or content-policy-rejection-pattern analysis (the Issue's Recommended Action requests exactly this kind of content — per user direction, this Plan states the gap rather than inventing content to fill it)
- Changing the refiner's actual retry behavior
- Conducting the empirical studies the Issue requests (a substantial, separate effort requiring production telemetry or controlled experiments, not a documentation-only fix)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Re-confirm the commit history and absence of an ADR | Pending | — | — | |
| 2 | Phase 2: Add the clarifying note | Pending | — | — | |
| 3 | Verification: manual review | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183024_missing_refiner_no_retry_policy_rationale.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-211731_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-094414
- **Related target files**: docs/03_rag_03_05_query_pipeline-augment-stages.md
