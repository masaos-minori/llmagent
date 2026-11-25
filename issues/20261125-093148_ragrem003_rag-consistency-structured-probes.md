# Make RAG consistency verification structured and complete

## Priority
High

## Summary
Make every consistency probe return a typed success, mismatch, or unverified result, check every stored vector, and let the startup path distinguish "unverified" from "consistent". Whether an unverified result must block startup is a policy decision that the current ADR answers the other way and is therefore left to the maintainer.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-03):
- Confirmed: `scripts/agent/startup_validation.py:277-297` turns a consistency timeout or exception into `add_warning` and continues. Those lines state the rule as ADR-004: ADR-004 Decision 7 (`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md:75`) classifies "a consistency check that fails and a consistency check that times out" as availability failures with startup continuing under a warning, while fatal consistency findings remain safety failures.
- Therefore the source note's premise that this "reverses the intended safety policy" is contradicted by the approved ADR text. The ledger entry `AAL-019` (the availability classification of RAG derived-index results, ADR-004 Group 2 item 7) is still pending approval, and `MCP-003` is a related open maintainer question (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`). Making an unverified check fatal would change ADR text and needs the maintainer's approval record; an implementer must not write one.
- Confirmed: `_safe_url_count_query` returns `{}` on any exception (`scripts/db/rag_consistency_queries.py:53-59`), and `_check_embedding_dimension` reads one row (`SELECT length(embedding) FROM chunks_vec LIMIT 1`, same file `:242-253`).
- Partly confirmed: `fk_unverified`, `embedding_unverified`, and `schema_unverified` already exist as findings with `DEGRADED` severity (`scripts/db/rag_consistency.py:401-440`), so a structured "unverified" notion exists for three probes but not for the URL-count probes or the overall report.
- Not verified: the claim that schema-fingerprint drift aborts report creation before a structured report exists.

## Problem
A failed chunk, vector, or FTS URL-count probe can produce an empty result that reads as "no mismatch", and a single-row dimension check cannot prove that all stored vectors share one dimension. The overall verification state has no distinct "unavailable" or "timed out" value for consumers other than startup.

## Reason for Change
Probe errors that disappear into empty results hide corruption; the structured report is also what post-ingestion checks, health, and recovery read.

## Implementation Intent
Introduce typed probe results and an overall state (`verified`, `inconsistent`, `unavailable`, `timed_out`) inside the report, check all vector rows with one SQL statement, and make `is_consistent()` false when any required probe is unverified. Keep the startup severity mapping (fatal versus warning) as a single, explicitly named policy point so the ADR decision can be applied by changing one place.

## Target Files or Areas
- `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/models.py`
- `scripts/shared/schema_fingerprint.py`
- `scripts/agent/startup_validation.py`, `scripts/agent/services/rag_maintenance_service.py`
- `tests/db/`, `tests/agent/`

## Required Changes
- Replace the `{}` fallback in `_safe_url_count_query` with a typed result; record each chunk, vector, and FTS probe as success, mismatch, or unverified.
- Convert schema-fingerprint drift into a structured finding; distinguish `schema_mismatch` from `schema_unverified`.
- Check embedding length for all rows and report the mismatch count plus a bounded sample of `chunk_id` values.
- Add the overall verification state and make an unverified report fail `is_consistent()`.
- Keep the failure category and safe diagnostic text in startup output; keep the cancellation stop event.
- Isolate the startup severity decision for unverified results in one place; do not change it in this issue unless the maintainer decision below says so.

## Constraints
- ADR-004 Decision 7 stays as written until the maintainer approves a change; do not edit ADR text or write an approval.
- No change to which confirmed findings are fatal.

## Acceptance Criteria
- A failed URL-count probe cannot produce a clean report; a malformed vector after a valid first row is detected.
- Schema drift yields a report with a structured finding.
- The report distinguishes verified, inconsistent, unavailable, and timed out.
- Startup behavior for a timeout or probe failure matches the maintainer's decision recorded below.

## Testing Expectations
Unit tests per probe outcome, a malformed-vector-after-first-row test, a schema-drift test, and startup tests for each state under the decided policy; changed-path gates and the ADR checkers if ADR files are touched.

## Documentation Impact
Update the RAG consistency and startup validation documents for the typed results; if the maintainer approves the fatal policy, record that approval in the ADR's Approval Record and close `AAL-019` through the maintainer's statement, not by an implementer.

## Out of Scope
- Embedding value validation (issues/20261125-093154_ragrem009_rag-embedding-validation.md).
- Changing ADR-004 text without an approval record.

## Dependencies
- Depends on issues/20261125-093146_ragrem001_rag-runtime-tool-contracts.md.
- Related: pending ledger entry `AAL-019` and the maintainer question `MCP-003` (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`); decide them together.

## Unresolved Questions
- `不明`: whether a consistency timeout, probe failure, or unverified report must abort startup. The approved ADR-004 text says it continues with a warning; the source note asks for the opposite. Only the maintainer can decide, and a change needs an ADR approval record.
- `不明`: whether schema-fingerprint drift currently raises before a report is built (not reproduced).

## AI Implementation Instruction
Implement the structured results first and keep the startup policy a single switch; do not make unverified results fatal, edit ADR-004, or write approval text unless the maintainer's decision and approval record exist.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093148
- **Related target files**: `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/agent/startup_validation.py`, `scripts/shared/schema_fingerprint.py`
