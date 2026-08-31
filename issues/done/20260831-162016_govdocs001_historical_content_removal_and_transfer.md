# Remove historical-only documentation content and confirm still-valid facts were transferred

## Priority
Medium

## Summary
Follow-on to the governance-policy change that established the Current-Specification-Only
Policy (`docs/00_governance_01_documentation-policy.md`). That change defined the policy
only; it explicitly did not perform physical removal of historical-only content. This issue
covers: (1) locating and removing any remaining Deprecated Items document or equivalent
historical-tracking artifact, and (2) confirming that any still-applicable fact from the
content already removed from `docs/00_governance_03_issue-and-uncertainty-management.md`
(18 archived Needs Confirmation entries, the Known Issues Migration Plan) was transferred to
its appropriate current canonical document before that content was deleted.

## Background
The Current-Specification-Only Policy states: "Before historical content of this kind is
removed from a document, any requirement, constraint, invariant, rationale, or verification
rule it contains that still applies to the current system must be transferred into the
appropriate current canonical document." The governance-policy change itself removed the
"Archived (Resolved) Items" table (NC-001 through NC-018) and the entire "Known Issues
Migration Plan" (Part 3) from `docs/00_governance_03_issue-and-uncertainty-management.md`,
per explicit instruction in that task, but the transfer-verification step described above was
out of scope for that task and was not performed.

## Problem
- The removed Archived (Resolved) Items table's entries record verified facts about current
  code, some of which may not be reflected anywhere else. For example: NC-004 recorded that
  `knn_search`'s distance metric is confirmed L2/Euclidean via an explicit
  `distance_metric=L2` DDL clause (source file cited: `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`); NC-016 recorded the confirmed signature and invocation pattern of
  an `on_usage` callback (source file cited: `90_shared_03_04_runtime_and_execution-caching-and-reference.md`). Whether these facts are already documented in
  their cited source files, independent of the now-deleted NC record, is unconfirmed.
  (Evidence: Needs confirmation — requires reading each cited source file.)
- The removed Known Issues Migration Plan described a still-unexecuted plan to migrate five
  area-specific Known Issues documents (`03_rag_90_inconsistencies_and_known_issues.md`,
  `04_mcp_90_inconsistencies_and_known_issues.md`,
  `05_agent_90_inconsistencies_and_known_issues.md`,
  `06_eventbus_90_inconsistencies_and_known_issues.md`,
  `90_shared_90_inconsistencies_and_known_issues.md`) to a common template. Deleting the plan
  does not resolve the underlying format inconsistency across those five documents — it only
  removes the record that the inconsistency was being tracked.
- Whether a "Deprecated Items" document or section still exists anywhere in the repository
  (independent of the removed canonical-source-matrix row that pointed to it) has not been
  confirmed.

## Reason for Change
Removing historical content without confirming still-valid facts were preserved risks losing
design knowledge (e.g., why a particular distance metric or callback signature was chosen)
that has no other record. The Current-Specification-Only Policy explicitly requires this
transfer step before removal is considered complete.

## Implementation Intent
1. Search the repository for any standalone "Deprecated Items" document or section; if found,
   evaluate its content against the Current-Specification-Only Policy and remove or fold in
   any still-valid requirement.
2. For each of the 18 formerly-archived NC entries (recoverable from git history of
   `docs/00_governance_03_issue-and-uncertainty-management.md` prior to the governance-policy
   change), read the cited source file and confirm the recorded fact is already present in
   that file's current content. If not present, add a concise statement of the current fact
   (not the full historical investigation narrative) to that file.
3. Decide whether to execute the five-area Known Issues format unification described in the
   removed Migration Plan, defer it, or explicitly drop it — and record that decision (e.g.,
   as a new issue if the work is still wanted, or note its rejection if not).

## Target Files or Areas
- Recoverable via `git log`/`git show` on `docs/00_governance_03_issue-and-uncertainty-management.md` for the removed content
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md` (NC-004)
- `90_shared_03_04_runtime_and_execution-caching-and-reference.md` (NC-016)
- The other 16 archived NC entries' cited source files (see the removed table for the full
  list; recoverable from git history)
- `03_rag_90_inconsistencies_and_known_issues.md`, `04_mcp_90_inconsistencies_and_known_issues.md`, `05_agent_90_inconsistencies_and_known_issues.md`, `06_eventbus_90_inconsistencies_and_known_issues.md`, `90_shared_90_inconsistencies_and_known_issues.md` — only if the format-unification decision is to proceed
- Unknown: whether a standalone Deprecated Items document exists

## Required Changes
- Confirm presence or absence of a standalone Deprecated Items artifact; remove or update it
  per the Current-Specification-Only Policy if found.
- For each of the 18 archived NC entries, verify (or add, if missing) the corresponding
  current-state fact in its cited source document.
- Record an explicit decision on the five-area Known Issues format-unification question
  (proceed as a new issue, defer, or drop).

## Constraints
- Do not restore the deleted Archived Items table or Migration Plan section — the removal
  itself is settled policy; this issue only verifies nothing load-bearing was lost.
- When adding a fact recovered from a removed NC entry to its target document, write it as a
  current statement of fact (no "NC-XXX confirmed..." framing, no investigation narrative) per
  `skills/DESIGN.md` Avoid implementation-reference duplication.
- Do not re-verify facts that are already clearly present in the target document — only add
  what is genuinely missing.

## Acceptance Criteria
- A definitive statement exists (in this issue's resolution or a follow-up record) on whether
  a standalone Deprecated Items artifact currently exists in the repository.
- Each of the 18 archived NC entries has been checked against its cited source file, with the
  outcome (already documented / added / not applicable) recorded.
- An explicit decision on the five-area Known Issues format unification is recorded, whether
  that decision is to proceed, defer, or drop it.

## Testing Expectations
Not required for the verification/transfer work itself (documentation-only). If any code-level fact turns out to be misdocumented during verification, register it as a Known Issue rather than silently correcting behavior.

## Documentation Impact
This issue is itself a documentation-impact task: it may touch any of the source files listed
under Target Files or Areas, adding a concise current-fact statement where one is confirmed
missing. Apply `skills/DESIGN.md` Avoid implementation-reference duplication when writing any
addition.

## Out of Scope
- Re-litigating the decision to remove the Archived Items table or Migration Plan (settled by
  the prior governance-policy change).
- Redesigning the Known Issues common template itself.
- Modifying `docs/00_governance_01_documentation-policy.md` through `_04_documentation-checks.md` (already updated by the prior task).
- Individual ADR file updates (tracked separately).

## Dependencies
Follows the governance-policy change that introduced the Current-Specification-Only Policy
(no issue file was generated for that task; see the corresponding session's final report for
context).

## Unresolved Questions
- Whether a standalone "Deprecated Items" document currently exists anywhere in the
  repository has not been confirmed — needs a repository-wide search before work begins.
- Whether the five-area Known Issues format unification is still wanted at all, given it was
  never started, needs an owner decision rather than an inferred answer.

## AI Implementation Instruction
- Recover the removed table/section content from git history before starting — do not
  reconstruct it from memory or guesswork.
- For each archived NC entry, read the actual current content of its cited source file before
  concluding the fact is or is not already present — do not assume based on the NC entry's
  age or resolution summary alone.
- Do not restore any of the removed historical sections themselves.
- If a source file is missing or renamed since the NC entry was archived, record that as a
  new Needs Confirmation entry rather than skipping the check silently.
- Stop and report if the standalone Deprecated Items artifact's existence cannot be confirmed
  with a repository-wide search.
