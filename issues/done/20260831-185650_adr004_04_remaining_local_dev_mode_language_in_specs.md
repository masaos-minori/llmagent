# Remove remaining production/local-mode language from three Specification documents after ADR-004's Production-only revision

## Priority
Low

## Summary
`docs/adr/ADR-004-production-failure-handling-policy.md` defines Production as the only
supported operating mode and removed all Local/Dev-mode behavioral distinctions. Three
Specification documents — beyond the one already covered by a prior follow-up issue —
still describe a production-vs-local/dev behavioral difference, which now contradicts the
current ADR-004 model.

## Background
A prior follow-up issue (`issues/20260831-173019_adr004_03_related_docs_local_mode_language.md`)
already covers the same "production or local mode" phrase in
`docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`. During the
ADR-001/ADR-004/ADR-012 update work, the identical phrase was found in a second file
(`05_agent_10_01`), plus two more files describing an actual behavioral difference (not just
wording) between production and local/development.

## Problem
(Evidence: Explicit in code as documented, i.e. these are direct quotes from the current
Specification text — not yet cross-checked against current source for behavioral accuracy)

- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`:
  - "In production mode, unreachable health probes are treated as startup failure (FATAL). In
    local mode, they only issue a warning and continue." — describes an actual production/local
    behavioral split, not just wording.
  - "Failure in `mcp_tool_discovery` is treated as FATAL regardless of whether it is production
    or local mode." — the same phrase already targeted by `adr004_03` for a different file; this
    is a second, previously-unnoticed occurrence.
- `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`: "Missing Tiers... causes an error
  (fatal `RuntimeError`) in production, and a warning in local/development." and the parallel
  "Unknown Keys" bullet with the same production/local-development split.
- `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`: "The Production validator
  treats violations as errors only when `security_profile == "production"`; otherwise, they are
  downgraded to warnings with a `[local/development]` prefix."

## Reason for Change
ADR-004 (Accepted, Production-only model) states that safety/validation behavior must not be
relaxed based on execution mode, and that Production is the only supported mode. Specification
text describing an active production/local behavioral split — not just historical wording —
misrepresents the current approved architecture to anyone reading these documents, and may
reflect an actual implementation gap (the same class of gap already tracked in
`docs/adr/ADR-004-production-failure-handling-policy.md`'s Known Deviations for
`scripts/shared/mcp_config.py`).

## Implementation Intent
For each of the three locations: first confirm against current source
(`scripts/agent/startup.py`, `scripts/shared/production_config_validator.py`,
`agent/repl_health.py`, or wherever the actual check lives) whether the described
production/local behavioral difference still exists in code. If it does, this is a
code/ADR-004 conformance gap and should be raised as its own issue (do not silently document
around it). If the code has already been unified to Production-only behavior, correct the
Specification wording to remove the stale local/dev distinction, consistent with how
`adr004_03` handles its target file.

## Target Files or Areas
- `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`
- `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `docs/90_shared_03_01_runtime_and_execution-config-and-logging.md`
- `scripts/agent/startup.py`, `scripts/shared/production_config_validator.py` — read-only references to confirm current behavior before editing docs

## Required Changes
- Confirm current behavior in source for each of the three quoted claims.
- If code still branches on `security_profile`/local vs. production for these specific checks, open a separate implementation issue against ADR-004 conformance (do not fix code as part of this issue).
- If code no longer branches (Production-only already applies), reword the three quoted passages to remove the production/local split and the "regardless of whether it is production or local mode" phrasing, following the same approach as `adr004_03`.

## Constraints
- Do not change the substance of what is FATAL vs WARNING beyond removing the mode-based framing — only remove wording that implies multiple supported execution modes exist, unless source confirms an actual behavioral gap requiring its own fix.
- Do not perform a broader rewrite of any of the three documents beyond the identified passages.

## Acceptance Criteria
- Each of the three documents either (a) no longer contains "local mode", "local/development", or equivalent phrasing implying a still-supported non-Production execution mode, with wording corrected to match confirmed current behavior, or (b) has a newly-filed implementation issue tracking a confirmed remaining code-level production/local split, if one is found.
- `uv run python tools/check_docs_quality.py` on the affected files shows no new issues.

## Testing Expectations
Documentation-only change unless a code gap is confirmed, in which case follow that gap's own testing expectations (tracked in a separate issue).

## Documentation Impact
This issue is itself the documentation-accuracy fix (or the trigger for a follow-up implementation issue) for the three files listed above.

## Out of Scope
- `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md`, already covered by `issues/20260831-173019_adr004_03_related_docs_local_mode_language.md`.
- Any other document not listed above.
- Implementing a code fix if a genuine production/local behavioral gap is confirmed (raise as a separate issue instead).

## Dependencies
Follows the ADR-004 Production-only revision and the ADR-001/ADR-004/ADR-012 update work (2026-08-31). Related to `issues/20260831-173019_adr004_03_related_docs_local_mode_language.md` (same class of finding, different files).

## Unresolved Questions
Whether the two behavioral-difference claims (`05_agent_10_01`'s health-probe FATAL/WARNING split, and `production_config_validator.py`'s local/development downgrade-to-warning behavior) reflect real, still-present code branches, or stale documentation — needs source confirmation before deciding whether this is a doc fix or a code-conformance gap.

## AI Implementation Instruction
Read the actual current implementation for each of the three claims before editing any document. Do not assume the Specification text is wrong without checking source — if the code genuinely still differentiates production from local/development for these checks, file that as a separate ADR-004 conformance issue instead of silently rewording the Specification to hide it.
