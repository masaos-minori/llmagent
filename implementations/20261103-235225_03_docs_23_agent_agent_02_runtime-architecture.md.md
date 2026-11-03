## Goal
Correct the one `docs/` statement that says `EventBusSubscriber` reconnects "with a fresh `consumer_id`" so it states the configured stable `consumer_id` and `since_seq` resume (`REQ-006`: documentation statement correction), in the same change that implements the code rows — not before.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The paragraph "EventBus Client Modules" in `docs/23_agent/agent_02_runtime-architecture.md` contains the phrase "reconnecting with a fresh `consumer_id`" (verified against the current file).
- This update is applied only after sibling procedure `implementations/20261103-235225_01_scripts_agent_eventbus_subscriber.py.md` has landed (REQ-006: docs must not claim resume before the code behaves that way).
- `docs/24_eventbus/*` already describe the server side correctly and do not change (the server is unchanged).

## Design decisions
- Edit only the stale sentence inside the existing paragraph; no new section and no wording about behavior the code does not yet have.
- Keep the claim aligned with the server-side resume precedence already documented in `docs/24_eventbus/` (client sends `since_seq`; server replays).

## Alternatives considered
- N/A: single-sentence correction; the Plan fixes the wording and timing.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`
### Procedure
Replace the parenthetical "reconnecting with a fresh `consumer_id`" in the "EventBus Client Modules" paragraph with wording that names the configured stable `consumer_id` and the `since_seq` resume-from-last-processed-`seq` behavior.
### Method
Single-sentence replacement inside the existing paragraph; route the edit through `skills/python-documentation/SKILL.md` per `routing.md`.
### Details
What a reader cannot infer from the Plan text: only the parenthetical changes; the surrounding sentences (which modules exist, that no runtime component imports them) stay as they are. Keep the statement consistent with `rules/coding.md` "Current behavior" classification — after the code lands this is plain current behavior, no special "Current behavior" framing.

## Compatibility considerations
N/A: one paragraph of prose; no generated block inside this file changes (the generated tables live in `agent_13_reference-api-generated.md` and the manifests, untouched per the sibling procedure's docstring constraint).

## Security considerations
N/A: documentation prose only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_02_runtime-architecture.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`
All pass (the docs checkers from `routing.md` Tools "When to run which tool").

## Completion criteria
- The paragraph names the configured stable `consumer_id` and the `since_seq` resume, and no statement in the file claims a fresh per-attempt `consumer_id` (AC-7).
- The docs checkers above exit 0.

## Out of Scope
- Any change to `docs/24_eventbus/*`, the generated reference docs, or the manifests; any change to the subscriber code itself (sibling procedure `implementations/20261103-235225_01_scripts_agent_eventbus_subscriber.py.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the "EventBus Client Modules" sentence per Implementation > Procedure/Method/Details, after the sibling code procedure has landed | Pending | — | — | Apply after `20261103-235225_01` completes (REQ-006) |
| 2 | Run the docs checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (correct the stale "fresh `consumer_id`" docs statement)
- **Source issue**: `issues/20261003-180343_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-152158_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-235225
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
