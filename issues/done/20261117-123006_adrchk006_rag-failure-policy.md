# Decide the RAG consistency failure policy and align diagnostics

## Priority
High

## Summary
The RAG consistency check, ADR-004, ADR-005, ADR-009, and the archived RAG issue files disagree on what a derived-index failure is and how severe it is. Record one policy and align diagnostics with it.

## Background
Filed from the consolidated ADR review task list `memo-issue.md` (package `ADRCHK2-H06`; merged from ADRCHK-H07, M30, M34, L02, L05 (review findings H5, N8, N22, N42, N49, N50)). The review's claims carry the evidence label `Documentation only` unless this issue marks them otherwise; the implementer MUST re-verify each claim against current source before changing anything.

## Problem
Re-verified on 2026-11-18 against current source and docs (adversarial pass; labels follow `skills/DESIGN.md` Evidence labels). Archived files under `issues/done/` were not read, so claims about them stay `Needs confirmation`.
- Confirmed (`Explicit in code`): `scripts/agent/startup_validation.py` adds a warning and lets startup continue for a RAG consistency timeout, for any other exception, and for DEGRADED findings; only FATAL findings abort. ADR-004 Decision Group 2 forbids converting a safety/integrity failure into warning-only continuation, and its `## Exceptions` lists no RAG case.
- Corrected: the startup comment says the unverified state "is fail-closed downstream"; no module consumes the `rag_consistency` outcome except the startup reporter's counts, so the claim has no code support.
- Confirmed: ADR-005 `Fail-Open or Degraded Conditions` says the post-ingestion check only logs warnings, and its Degraded condition is `fts_gap > 0` or `orphan_vec_count > 0`.
- Corrected: ADR-009 lists `fts_gap > 0` as its Degraded condition, not None. It still words the skip of a file whose normalization fails and the Failure Policy correctly.
- Confirmed: ADR-009 `Transaction Boundary` says per chunk, while `TransactionManager.commit` in `scripts/rag/ingestion/transaction_commit.py` commits one `BEGIN IMMEDIATE` transaction per URL and ADR-005 says per document.
- Confirmed with a policy constraint: ADR-009 lists INV-01 to INV-08 as invariants, INV-10 and INV-11 appear only in `## Implementation Notes`, and a Manual Review line cites INV-11. INV-09 was folded into INV-04 (a pending amendment of the approval ledger). The Current-Specification-Only policy forbids a history note, so "explain INV-09" means stating the current numbering.
- Corrected: three findings, not two, carry `[CRITICAL]` with DEGRADED severity: FTS orphan, orphan vec rows, and chunks without vector rows; every FATAL finding is `[CRITICAL]` and every other DEGRADED finding is `[WARNING]`.
- Confirmed and widened: orphan vec rows, vector mismatch, and chunks without vector rows set `repair_action=rebuild_vec` while the message says to run `ingester.py --force`; documents without chunks also uses `rebuild_vec`; URL-level inconsistency sets `reconcile_url` while the message says to re-run ingestion. Since the repair persistence fix, `rebuild_vec` only removes orphan vector rows and `reconcile_url` only inserts missing FTS entries, so they fit the orphan-vector finding only.
- Confirmed: `scripts/rag/corpus_identity.py` does not exist and no `scripts/` or `tests/` file references `corpus_identity`; `governance_05` records the removal. CSC-001 itself concerns ADR-010's surviving present-tense wording, and its Validation evidence still cites `rmcompat003` as an open `issues/` path.
- Closed dependencies: the RAG repair persistence issue (code merged, `rebuild_vec` contract is orphan removal) and the ADR approval governance issue (ledger and pending-amendment form defined).

## Reason for Change
- The policy is contradicted: ADR-004 forbids continuing on a data-integrity failure with a warning only, yet startup continues with a warning on a timeout, an exception, or DEGRADED findings. ADR-005 only logs consistency mismatches. ADR-009 skips files that fail normalization and lists `fts_gap > 0` as its Degraded condition. No ADR-004 Exception covers this.
- The earlier issue files point in opposite directions: `rmcompat001` asks to document warn and continue, while `adrrev013` asks to choose between aborting and registering an exception. Both now live in `issues/done/`, so their stale text still misleads readers (`Explicit in code`: the files are under `issues/done/`).
- Stale text: `adrrev013` lists a closed issue as a dependency and rests on a refuted premise; `rmcompat001` targets a warning that is gone from the code; `rmcompat003` says removing corpus identity is not done, but `scripts/rag/corpus_identity.py` no longer exists (`Explicit in code`) and the RAG maintenance service no longer imports it. CSC-001 stays open because of this text.
- Findings contradict their own fields: orphan vector, vector mismatch, and chunks-without-vector findings set `repair_action=rebuild_vec` but tell users to run `ingester --force`; three `[CRITICAL]` messages have DEGRADED severity; "documents without chunks" uses `rebuild_vec`, which cannot fix that state; URL-level inconsistency uses `reconcile_url` but tells users to re-run ingestion.
- ADR wording is inconsistent: ADR-005 sets the transaction boundary per document and ADR-009 per chunk; ADR-009 skips INV-09 without saying why.

## Implementation Intent
- One recorded policy covers timeout, exception, DEGRADED, and FATAL results, and the code, ADR-004, ADR-005, ADR-009, and the RAG guide follow it.
- Every finding's prefix matches its severity, and its message names a repair that can fix it.
- The earlier issue files describe the current code, so CSC-001 can be closed on evidence.

## Target Files or Areas
- `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
- `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
- `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
- `scripts/db/rag_consistency.py`
- `scripts/agent/startup_validation.py`
- issues/done/20261109-113123_adrrev013_rag-consistency-policy.md (path now under done/)
- issues/done/20261110-170632_rmcompat001_rag-delegation-leftovers.md (path now under done/)
- issues/done/20261110-170753_rmcompat003_rag-corpus-identity-decision.md (path now under done/)
- `tests/db/`

## Required Changes
- (no decision needed) Re-verify each claim in the three archived issue files with `rg`, and record the result where the maintainer decides how to correct archived files.
- (no decision needed) Fix the finding messages, prefixes, and the repair action for documents without chunks (for example re-ingestion).
- (no decision needed) Align the transaction boundary wording with the ingester code, and explain the missing INV-09 in ADR-009.
- (decision) Classify derived-index mismatches as availability failures in ADR-004, or add an ADR-004 Exception with rationale and approval.
- Apply the decision to the startup timeout and exception branches, ADR-009's Degraded condition, and the RAG guide.

## Constraints
- Do not write the policy decision; prepare a short option table for the maintainer.
- Editing files under `issues/done/` conflicts with their archived status; the maintainer must confirm how to correct them (see Unresolved Questions).
- Do not write, paraphrase, or simulate a maintainer approval statement. A change to an ADR decision, invariant, Blocking value, or authority edge needs an approval record in the same change (governance_01, governance_05).
- Follow the Current-Specification-Only policy: no migrations, aliases, shims, tolerant fallbacks, or history-style comments such as removed on or formerly.
- Change only the Target Files; if another file must change, stop and report it as a scope amendment.
- Keep code comments, log text, and documentation in English.
- Before editing, re-run the searches named in Acceptance Criteria. Other plans edit the same files; if a defect is already gone, record the evidence and skip that task.
- Do not edit generated files (`registry/manifests/*.yaml`, guarded blocks) by hand; regenerate with `tools/generate_reference_table.py` or `tools/generate_adr_authority.py`.

## Acceptance Criteria
- ADR-004 explicitly covers the RAG consistency timeout, exception, and DEGRADED behavior.
- Each finding's prefix matches its severity, and its message names its `repair_action` (test).
- The three issue files no longer give opposite directions, and each acceptance search in them gives the expected result.

## Testing Expectations
Unit tests under `tests/db/` for prefix, severity, and repair action consistency; run the docs checkers and ADR checkers. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. ADR-004, ADR-005, ADR-009, the RAG consistency guide, and governance_03 (CSC-001 evidence).

## Out of Scope
- Persisting repairs in the maintenance service (see the RAG repair persistence issue).
- Choosing the policy on the maintainer's behalf.

## Dependencies
- `issues/20261117-123007_adrchk007_rag-repair-persistence.md` fixes `rebuild_vec` persistence, which the corrected repair actions rely on.
- `issues/20261117-123011_adrchk011_adr-approval-governance.md` defines how an ADR-004 Exception is registered and approved.
- `issues/20261117-123005_adrchk005_startup-fail-closed.md` uses FATAL until this decision is recorded.

## Unresolved Questions
- The memo names the three issue files under `issues/`, but they exist only under `issues/done/`. Whether to edit archived files or file corrections elsewhere is `不明`.
- To close CSC-001, ADR-010's surviving present-tense wording must be moved or removed; ADR-010 is not a Target File, so this is a scope amendment for the maintainer.
- The policy for derived-index mismatches, the check timeout, and the check exception is the maintainer's decision; the plan prepares the option table and stops at that gate.
- The claims about the three archived issue files are `Needs confirmation` until the maintainer decides whether an archived file may be read or edited.

## AI Implementation Instruction
- Do not write the policy decision. Prepare a short option table for the maintainer and stop.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123006
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`; `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`; `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `scripts/db/rag_consistency.py`; `scripts/agent/startup_validation.py`; `issues/done/20261109-113123_adrrev013_rag-consistency-policy.md (path now under done/)`; `issues/done/20261110-170632_rmcompat001_rag-delegation-leftovers.md (path now under done/)`; `issues/done/20261110-170753_rmcompat003_rag-corpus-identity-decision.md (path now under done/)`; `tests/db/`
