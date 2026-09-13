# Issue: Missing Documentation for RAG Pipeline Refiner No-retry Policy Rationale

## Summary
`docs/03_rag_03_05_query_pipeline-augment-stages.md` states a no-retry policy for refiner failures but doesn't document the full rationale behind this decision.

## Evidence
- File: `docs/03_rag_03_05_query_pipeline-augment-stages.md`, section 5.6
- Text: "**No-retry Policy**: Refiner failures are treated as non-critical quality degradations — allowing raw chunks as output. Retrying failed LLM calls offers low expected benefit while increasing latency (transient errors are rare, and content policy rejections will not succeed upon retry)."
- The rationale is partially documented but lacks empirical evidence or design review history
- No ADR or design document references the no-retry policy

## Impact
- Developers modifying the refiner logic may not understand why retries aren't implemented
- Future changes could inadvertently add retry logic without understanding the trade-offs
- Operators cannot make informed decisions about retry configuration

## Recommended Action
Create an ADR documenting the no-retry policy rationale:
1. Empirical basis for "transient errors are rare" claim
2. Analysis of content policy rejection patterns
3. Latency impact analysis of adding retries
4. Alternative approaches considered and rejected
5. Conditions under which the policy should be revisited
