## Goal

Correct the stale claim in `docs/23_agent/agent_02_runtime-architecture.md` that
`EventBusSubscriber` reconnects "with a fresh `consumer_id`" (REQ-006, AC-7). The
subscriber now reconnects with its configured stable `consumer_id` and resumes via
`since_seq`; the paragraph must state that instead.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- This doc edit runs after the code change in
  `implementations/20261103-151102_01_scripts_agent_eventbus_subscriber.py.md` lands,
  so the stated behavior is real (REQ-006: "not before").
- The only stale claim in this document is the parenthetical on the "EventBus Client
  Modules" heading line; no other sentence in the file mentions the subscriber's
  reconnect identity or resume input (verified by search for `consumer_id`,
  `since_seq`, and "fresh").
- The generated reference docs and manifests do not need regeneration: the first
  docstring line of each class is kept, so their summaries are unchanged.

## Design decisions
1. **Scope the edit to one parenthetical.** Replace only the phrase inside the
   parentheses after "`EventBusSubscriber` consumes the `/subscribe` SSE stream";
   leave every other word of the sentence intact so the diff touches a single clause.

## Alternatives considered
- Rewriting the whole "EventBus Client Modules" sentence (rejected: larger diff and
  risk to the unrelated "no runtime importer" claim; minimal diff suffices).

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
1. Open `docs/23_agent/agent_02_runtime-architecture.md`; locate the "EventBus Client
   Modules" paragraph (the `#####` heading on line 155 and its body on line 157).
2. Edit the parenthetical after "`EventBusSubscriber` consumes the `/subscribe` SSE
   stream": replace `(reconnecting with a fresh `consumer_id`)` with
   `(reconnecting with its configured stable `consumer_id` and resuming via
   `since_seq`)`.
3. Run the docs checkers named in the Validation plan (`routing.md` Tools "When to run
   which tool" for a `docs/*.md` edit touching the `agent` domain).
4. Confirm `tools/generate_reference_table.py --check` reports no drift (first
   docstring lines kept).

### Method
- Use a single `Edit` on the exact parenthetical string; preserve the surrounding
  sentence and the trailing "No runtime component..." sentence verbatim.
- Keep the wording at design-intent level (no config values, no line numbers) per
  `skills/DESIGN.md`.

### Details
- Old text (line 157): `(reconnecting with a fresh `consumer_id`)`
- New text: `(reconnecting with its configured stable `consumer_id` and resuming via
  `since_seq`)`
- No other occurrence of `consumer_id`, `since_seq`, or "fresh" exists in this file,
  so this is the only edit.

## Compatibility considerations
N/A: this is a documentation wording correction; no code, API, or behavior changes.

## Security considerations
N/A: no security-relevant content changes.

## Rollback considerations
N/A: revert the commit.

## Validation plan
Run every `docs/*.md` checker for an edited `agent`-domain document, each confirmed to
have examined this file:
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/generate_reference_table.py --check` (no drift)

## Completion criteria
The "EventBus Client Modules" paragraph states that `EventBusSubscriber` reconnects
with its configured stable `consumer_id` and resumes via `since_seq`; the stale
"fresh `consumer_id`" phrase is gone; the `agent`-domain docs consistency check and the
other docs checkers pass; the generated reference table shows no drift.

## Out of Scope
- Any change to `scripts/agent/eventbus_subscriber.py` docstrings (covered by the code
  procedure for this Plan).
- Changes to `docs/24_eventbus/*` (server side is already correct).
- Regenerating `registry/manifests/*.yaml` or the generated reference docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261103-163500 | 20261103-164000 | Replaced 'fresh consumer_id' parenthetical with stable consumer_id + since_seq resume wording (single-clause edit) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261103-164000 | 20261103-164500 | Docs checkers only (no tests) check_docs_quality/structure/content_policy/consistency(agent)/japanese pass; generate_reference_table --check no drift |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261103-164500 | 20261103-164500 | Doc wording corrected; no regeneration needed |

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
- **Requirement ID**: `REQ-006` (correct the subscriber's "fresh `consumer_id`" reconnect claim to the stable `consumer_id` + `since_seq` resume)
- **Source issue**: `issues/20261003-180343_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261101-152158_ebreconnect001_event-bus-reconnect-drops-missed-events.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-151102
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`