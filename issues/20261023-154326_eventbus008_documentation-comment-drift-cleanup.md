# Remove obsolete implementation history and repair EventBus documentation and comment drift

## Priority
Low

## Summary
Remove resolved implementation history from EventBus comments, tests and generated references, fix inaccurate security wording, duplicate definitions, malformed endpoint paths and typographical errors, and regenerate machine-owned references with their generator.

## Background
Re-verified against HEAD:
- `scripts/eventbus/config.py` defines `_DEFAULT_CONFIG_PATH` and `_DEFAULT_SCHEMA_PATH` twice (lines 13-14 and 23-24).
- The same file states `The API has no authentication — this is a security risk.` in `_validate_deployment_mode` and `EventBusConfig.__post_init__`, while the implemented model is Bearer token plus role-based access (ADR-013); the real concern is a non-loopback bind.
- Stale narrative comments remain, for example `scripts/eventbus/ack_route.py:16` (`write_offset removed — replaced by ...`), `ack_route.py:183` (`REQ-004: events.acked_at removed ...`), and `scripts/eventbus/delivery_repo.py:111` (`events-level failure counters are legacy and no longer written`). `grep -rn "REQ-0" scripts/eventbus/*.py` returns 41 matches of requirement-tag comments.
- The remaining memo items (resolved orphan-row comment in the ACK route, malformed endpoint paths in generated references, spelling and grammar across test text) were not enumerated; `scripts/eventbus/delivery_repo.py:180` mentions orphan rows in a comment that may be the one meant.
This cleanup should follow the implementation issues (`eventbus001` to `eventbus007`) because they replace several of these comments. Do not mix it with behavior changes.

## Problem
Source comments, tests and generated references keep resolved implementation history, inaccurate wording, duplicate definitions, stale ACK explanations and malformed endpoint paths, which obscure the current contract and make AI-assisted maintenance less reliable.

## Reason for Change
Active documentation should describe current invariants and failure behavior, and stale comments can lead a future change to restore removed behavior.

## Implementation Intent
A focused editorial cleanup after H-01 to M-02: keep active design rationale and operational warnings, remove historical narratives, fix spelling and grammar, and regenerate generated references instead of hand-editing them.

## Target Files or Areas
`scripts/eventbus/config.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py` and other `scripts/eventbus/*.py` comments, EventBus tests, `docs/24_eventbus/`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/23_agent/` or other generated reference files that contain EventBus endpoint tables (generator: `tools/generate_reference_table.py`).

## Required Changes
- Remove pre-fix, completed-issue, removed-test, legacy-offset and resolved-path narratives and the duplicate default-path constant definitions.
- Replace the inaccurate `API has no authentication` wording with the current loopback-defense rationale; remove the resolved orphan-row comment in the ACK route.
- Shorten repository comments to active transaction, concurrency and failure invariants.
- Correct spelling, grammar, capitalization and terminology in the affected English text.
- Fix malformed endpoint paths and regenerate reference tables through the generator.

## Constraints
No behavior change; comments and documentation follow `skills/DESIGN.md` Docs content policy.

## Acceptance Criteria
- No active comment presents removed behavior as current.
- Security wording matches the implemented authentication and authorization model.
- Endpoint paths render correctly and generated reference blocks are regenerated, not edited by hand.
- Current rationale and operational warnings remain intact.

## Testing Expectations
Documentation link check, generated-reference drift check (`tools/generate_reference_table.py --check`), removed-name check, docs structure and quality checkers, ruff format and the existing EventBus tests unchanged.

## Documentation Impact
This issue is the documentation update.

## Out of Scope
Behavior changes of any kind; contract decisions owned by H-01 to M-02.

## Dependencies
Depends on H-01 to M-02 (replacement contracts must exist first). No open issue under `issues/` overlaps.

## Unresolved Questions
- Which of the 41 `REQ-0xx` tag comments are active traceability markers (kept) and which are resolved history (removed)? Decide with a list produced at planning time.
- The malformed endpoint paths are not identified; locate them through `tools/generate_reference_table.py --check` and the docs link checkers before planning.

## AI Implementation Instruction
- Read the listed implementation, tests, and design documents before editing; keep changes minimal and do not rewrite unrelated files.
- Preserve the existing public contract unless this issue explicitly names a contract change; an unresolved owner decision is reported, not guessed.
- Do not resolve an implementation defect by changing documentation alone.
- Keep transaction, locking, authorization, durability and fail-closed boundaries explicit.
- Add or update automated tests for every acceptance criterion; do not implement out-of-scope items.

## Traceability
- **Workflow phase**: `issue-creator` (converted from `memo-issue.md`, task `L-01`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-154326
- **Related target files**: `scripts/eventbus/config.py`, `scripts/eventbus/ack_route.py`, `docs/` EventBus documents
