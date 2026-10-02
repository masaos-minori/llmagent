# Resolve dangling Known Issue references exposed by ADR translation

## Priority
Low

## Summary
Translating ADRs to English (`langadr001`) replaced full-width parentheses that had been hiding some Known Issue IDs from `tools/check_known_deviation_sync.py`. The newly visible IDs have no matching entry in any canonical Known Issues document, so the checker now reports them as dangling references. For each listed reference, either remove or update the stale reference in the ADR, or restore the missing canonical entry if the issue is still open.

## Background
- `check_known_deviation_sync.py` matches an ID only when it is followed by whitespace, an em dash, or end of line (`_ID_LOOKAHEAD_RE`). In the Japanese text, IDs were followed by full-width punctuation (for example `CI-003（`), so they were never checked. `Explicit in code`
- The translation follows the user-approved decision to translate faithfully rather than to format IDs in a way that avoids detection (code-implementation cycle for `implementations/done/20261001-115707_03_docs_10_adr_ADR-003-runtime-tool-registry-routing-authority.md.md`).

## Problem
Dangling references newly reported after translation:
- `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`, `### Known Issues`: `CI-003` (verification of the whole Reload execution flow), `CI-015` (tests for duplicate Tool ownership detection). Neither has a `### CI-003` / `### CI-015` entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`. The CI-014 batching note there records that CI-015 was removed after test coverage was added. `Explicit in code`
- `docs/10_adr/ADR-008-sqlite-4db-separation.md`, `### Known Issues`: `SHARED-003` (workflow/eventbus recovery runbook, marked resolved in the ADR text), `CI-002` (suspected legacy wording). Neither has an entry in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; `git log -S` shows they were removed by resolved-item cleanups (for example commit `56376da79`). `Explicit in code`

## Reason for Change
- Stale references point readers to Known Issues that no longer exist, and keep `check_known_deviation_sync.py` noisy.

## Implementation Intent
- For each reference, check the Known Issue history (git log of `governance_03`, closing plans) and decide whether it was resolved (remove or mark as resolved in the ADR) or is still open (restore a canonical entry).
- Do not change ADR decisions.

## Target Files or Areas
- `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`
- `docs/10_adr/ADR-008-sqlite-4db-separation.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (only if an entry must be restored)

## Required Changes
- Resolve each listed dangling reference with recorded evidence.

## Constraints
- Do not reformat IDs to evade `_ID_LOOKAHEAD_RE`.
- `docs/` text stays English.

## Acceptance Criteria
- `uv run python tools/check_known_deviation_sync.py` reports no dangling-reference warning for the listed IDs.

## Testing Expectations
Documentation-only. Run `check_known_deviation_sync.py` and `uv run pytest tests/tools/test_check_known_deviation_sync.py`.

## Documentation Impact
Yes. ADR Known Issues references, and governance_03 only if an entry is restored.

## Out of Scope
- Pre-existing dangling warnings that were already reported before translation (EVENTBUS-001/003/004/009/010, INV-07, DESIGN-1, DESIGN-2, EVENTBUS-008).
- The `check_known_deviation_sync.py` lookahead behavior itself.

## Dependencies
- Follows `langadr001` implementation.

## Unresolved Questions
- Whether CI-003 (Reload flow verification) was resolved or is still open; no canonical entry was found.

## AI Implementation Instruction
- Use git history as evidence; stop and ask if an ID's status cannot be determined.

## Traceability
- **Workflow phase**: code-implementation
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261001-105822_plan.md
- **Source implementation procedure**: implementations/done/20261001-115707_03_docs_10_adr_ADR-003-runtime-tool-registry-routing-authority.md.md
- **Generated at**: 20261001-125540
- **Related target files**: docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md, docs/10_adr/ADR-008-sqlite-4db-separation.md
