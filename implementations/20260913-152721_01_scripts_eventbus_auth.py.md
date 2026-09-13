## Goal
Fix the "no topic restriction" case (REQ-001) so `require_consumer_identity`
returns `"topics": None` — distinct from an explicit, non-empty allowlist — instead
of an empty `set()` that `subscribe_route.py` currently cannot distinguish from
"explicitly zero topics allowed."

## Scope
Only `require_consumer_identity`'s topic-allowlist block in
`scripts/eventbus/auth.py`. No change to its consumer_id-allowlist block (already
fixed, REQ-006 of the eb002 Plan), `_populate_token_maps`, or any other function in
this file.

## Assumptions
- `_TOKEN_TOPIC_MAP`'s only writer, `_populate_token_maps` (confirmed by reading
  the function), never assigns a token an empty set as anything other than
  "unset" — mirroring `_TOKEN_CONSUMER_MAP`'s parallel convention already fixed
  under REQ-006.
- `subscribe_route.py` is the only reader of `_identity["topics"]` across the
  codebase (confirmed by `rg` in the source Plan) — this document's change to that
  key's contract is fully covered by the companion
  `implementations/20260913-152721_02_scripts_eventbus_subscribe_route.py.md`
  document.

## Design decisions
Change the topic-allowlist block to resolve `_TOKEN_TOPIC_MAP.get(token, set())`
unconditionally (not gated on whether the `topics` parameter itself is non-empty),
then: if that resolved set is empty, return `None` for `"topics"` (unrestricted);
otherwise enforce the existing per-topic check against it (unchanged for the
non-empty case) and return the set.

## Alternatives considered
- **Keep returning `set()` for "unrestricted" and add a second boolean key (e.g.
  `"topics_unrestricted": True`) instead**: rejected — requires every current and
  future reader of the returned dict to check two keys instead of one; `None` is a
  simpler, single-field signal with no ambiguity.
- **Gate the "unrestricted" check on whether `topics` (the function's own
  parameter) was provided, rather than on `_TOKEN_TOPIC_MAP`'s resolved set**:
  rejected — this was the original (buggy) design; the caller's own `topics`
  parameter and whether *the token* has a configured restriction are independent
  facts, and conflating them is exactly the bug this Plan fixes.

## Implementation
### Target file
scripts/eventbus/auth.py

### Procedure
1. In `require_consumer_identity`'s topic-allowlist block (currently: `allowed_topics
   = set(); if topics: ...`), change it to resolve `allowed_topics_from_map =
   _TOKEN_TOPIC_MAP.get(token, set())` unconditionally, before checking `topics`.
2. If `allowed_topics_from_map` is empty, set the value that will be returned under
   `"topics"` to `None`.
3. Otherwise (non-empty `allowed_topics_from_map`), keep the existing per-topic
   enforcement: for each entry in the caller's own `topics` parameter (if any), raise
   403 if it is not in `allowed_topics_from_map`; the returned `"topics"` value is
   `allowed_topics_from_map` itself.
4. Update the function's docstring to state the `None`-means-unrestricted contract
   explicitly (per the source Plan's Risk mitigation), so a future reader of this
   function sees it documented at the source.

### Method
Restructure the existing `if topics: ...` block into an unconditional resolve step
followed by an empty-vs-non-empty branch — no new helper function; the logic is
small enough to stay inline, consistent with the rest of this function.

### Details
- Do not change the consumer_id-allowlist block above this one (already fixed under
  REQ-006 of the eb002 Plan) — this document's diff is confined to the
  topic-allowlist block only.
- Do not change `_populate_token_maps` — `_TOKEN_TOPIC_MAP`'s population logic
  already treats an empty set as "unset" (per this document's own Assumptions); only
  the *consumer* of that map (`require_consumer_identity`) needs to change how it
  reports that state onward.
- The function's own `topics` parameter (the caller-requested topic list, distinct
  from `_TOKEN_TOPIC_MAP`'s per-token allowlist) still gates whether any per-topic
  check runs at all when the map entry *is* non-empty — this document does not
  change that: if `topics` is empty/`None` and `allowed_topics_from_map` is
  non-empty, no topic can violate the allowlist (nothing was requested), so the
  loop simply does not execute, exactly as today.

## Compatibility considerations
A token with a genuinely non-empty `_TOKEN_TOPIC_MAP` entry sees no behavior
change — its enforcement and returned value are unchanged. A token with no entry
(or an empty one) previously returned `"topics": set()`; any caller code path
already confirmed (via the source Plan's `rg` sweep) not to exist could
theoretically depend on this being a `set` rather than `None` — none does, per that
sweep — so this is not expected to be a breaking change in practice.

## Security considerations
This is a **correctness fix in the permissive direction**: a token without a
configured topic restriction becomes usable for subscribing to any topic, which
matches `_populate_token_maps()`'s own documented intent ("empty means any topic")
rather than the current, stricter-than-intended behavior. A token with a real
restriction configured is unaffected — no security regression for that case.

## Rollback considerations
Single-function change in one file — revert this file's diff to roll back. No
schema, migration, or on-disk data impact. Independent of the companion
`subscribe_route.py` document's own revert — reverting only this file returns
`"topics"` to always being a `set` again, at which point `subscribe_route.py`'s
`is None` check (companion document) simply never triggers (safe, if
functionally reverting the fix).

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_subscribe.py -v` and confirm
  `test_subscribe_duplicate_consumer_id_returns_409` still reaches its own `409`
  assertion once the companion `subscribe_route.py` document's change also lands
  (this file's change alone does not make that test pass — see the companion
  document's own Validation plan for the full picture).
- Add a unit-level test calling `require_consumer_identity` directly with a token
  that has no `_TOKEN_TOPIC_MAP` entry, confirming the returned dict's `"topics"`
  key is `None`.
- Add a unit-level test calling `require_consumer_identity` directly with a token
  that has a non-empty `_TOKEN_TOPIC_MAP` entry, confirming the returned
  `"topics"` value is still the expected set (AC-3, no regression).
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no regression.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- `require_consumer_identity` returns `"topics": None` when the caller's token has
  no `_TOKEN_TOPIC_MAP` entry or an empty-set entry (AC-1).
- `require_consumer_identity` still enforces and returns the expected set for a
  token with a genuinely non-empty `_TOKEN_TOPIC_MAP` entry (AC-3, no regression).
- The function's docstring documents the `None`-means-unrestricted contract.

## Out of scope
- `subscribe_route.py`'s own interpretation of the returned value — covered by the
  companion document `implementations/20260913-152721_02_scripts_eventbus_subscribe_route.py.md`.
  `AC-2`/`AC-4` (full end-to-end behavior) cannot be confirmed by this document's
  change alone; they require that companion document's change too.
- `_TOKEN_CONSUMER_MAP`'s already-fixed counterpart (REQ-006, done).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-162615 | 20260913-162615 | require_consumer_identity now returns topics=None when the token has no non-empty _TOKEN_TOPIC_MAP entry; docstring updated to document the contract |
| 2 | Add or update tests per Validation plan | Completed | 20260913-162615 | 20260913-162615 | Added TestRequireConsumerIdentityTopicSemantics (2 unit tests): unrestricted token returns None; restricted token still enforces and returns the expected set |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-162615 | 20260913-162615 | ruff/mypy/bandit/lint-imports/diff-cover(100%)/pre-commit all passed; full tests/eventbus/ suite: only pre-existing/flaky failures remain (test_subscribe_duplicate_consumer_id_returns_409 now fails with TypeError instead of 403, expected until companion subscribe_route.py document lands) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-162615 | 20260913-162615 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/auth.py |

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
- **Source issue**: issues/done/20260913-143134_eb005_token-topic-map-empty-set-contradiction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-151824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-152721
- **Related target files**: scripts/eventbus/auth.py