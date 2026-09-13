# EventBus `_TOKEN_TOPIC_MAP` empty-set semantics contradict their own comment, rejecting legitimate subscribers

## Priority
Medium

## Summary
`scripts/eventbus/auth.py`'s `_populate_token_maps()` comments an empty
`_TOKEN_TOPIC_MAP` entry as meaning "any topic is allowed" for that token, but
`require_consumer_identity`'s actual topic-allowlist check — combined with how
`scripts/eventbus/subscribe_route.py` interprets its return value — does the
opposite: a token with no topic restriction configured ends up allowed for
*zero* topics, rejecting every subscribe request with a 403.

## Background
This is the same class of bug already found and fixed for `_TOKEN_CONSUMER_MAP` in
`implementations/done/20260913-122501_05_scripts_eventbus_auth.py.md` (REQ-006,
filed under the eb002 Plan): `_populate_token_maps()`'s own comment says an empty
set means "unrestricted," but the consuming code treated it as "nothing allowed."
That fix corrected `require_consumer_identity`'s `consumer_id` check. This issue is
the topic-allowlist counterpart of the same bug, discovered immediately afterward
while validating that fix end to end — but it could not be fixed the same way,
because the wrong interpretation lives partly in a different file
(`subscribe_route.py`), not only in `auth.py`.

## Problem
Confirmed by direct reproduction via
`tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409`
(a test whose only intent is to check consumer_id-duplicate rejection, topics
aside): with a `consumer_token` that has no `_TOKEN_TOPIC_MAP` entry,
`require_consumer_identity` (`scripts/eventbus/auth.py`) returns `{"topics": set()}`
whenever FastAPI resolves its own `topics` parameter to a non-empty value at all,
or — more subtly — `subscribe_route.py` (`scripts/eventbus/subscribe_route.py`)
reads that returned `"topics"` value as `caller_topics` and rejects (403) every
element of the request's own `topic` query list that is not already in
`caller_topics`, with no distinction between "the map says this consumer_id/token
combination is allowed zero topics" and "no topic restriction was ever configured
for this token." Both produce the same empty set, but only the first should mean
"reject everything."

## Reason for Change
Confirmed by repository evidence: the test named above currently fails with `403
Forbidden: topic 't' not allowed` instead of reaching the `409 Conflict` its own
scenario (a duplicate consumer_id) is supposed to exercise — a caller holding a
validly-configured `consumer_token` cannot subscribe to *any* topic today, which
defeats the purpose of configuring per-role tokens at all for `/subscribe`.

## Implementation Intent
Give "no topic restriction configured for this token" and "explicitly zero topics
allowed" distinguishable representations, then make both `require_consumer_identity`
and `subscribe_route.py` honor that distinction consistently. The exact mechanism
(e.g. `None` vs `set()` in the returned `"topics"` value, or a separate boolean key)
is a design decision for implementation time, not prescribed here — but it must not
be resolved by a narrower fix inside only one of the two files, since the
contradiction spans both.

## Target Files or Areas
- `scripts/eventbus/auth.py` (`require_consumer_identity`, `_populate_token_maps`)
- `scripts/eventbus/subscribe_route.py` (its interpretation of `_identity["topics"]`)

## Required Changes
- Decide and document how "unrestricted" is represented in
  `require_consumer_identity`'s return value, distinct from "explicitly zero topics
  allowed."
- Update `require_consumer_identity` to produce that representation when a token has
  no `_TOKEN_TOPIC_MAP` entry (or an entry that is an empty set, per
  `_populate_token_maps()`'s own existing comment).
- Update `subscribe_route.py`'s topic-allowlist check to honor that same
  representation.

## Constraints
Do not weaken topic-allowlist enforcement for a token that genuinely has one
configured (a non-empty `_TOKEN_TOPIC_MAP` entry) — only the "no entry configured"
case should become permissive, matching `_TOKEN_CONSUMER_MAP`'s already-fixed
counterpart.

## Acceptance Criteria
- A token with no `_TOKEN_TOPIC_MAP` entry can subscribe to any topic (no 403 for
  topic restriction).
- A token with a non-empty `_TOKEN_TOPIC_MAP` entry is still rejected (403) for a
  topic not in that entry.
- `tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409`
  passes (reaches its own intended 409 assertion, not a 403 from the unrelated
  topic-allowlist path).

## Testing Expectations
- Unit or integration test confirming a token with no topic restriction can
  subscribe to an arbitrary topic.
- Regression test confirming a token with an explicit, non-empty topic allowlist is
  still rejected for a topic outside it.
- Run the full `tests/eventbus/` suite to confirm no new failures.

## Documentation Impact
N/A: internal authorization-semantics fix; no operational or API-contract
documentation depends on this internal representation choice.

## Out of Scope
- `_TOKEN_CONSUMER_MAP`'s already-fixed counterpart (REQ-006, done).
- Any other authorization logic in `auth.py`/`subscribe_route.py` not related to the
  topic-allowlist check.

## Dependencies
N/A: none — independent of eb001/eb002/eb003/eb004, all already implemented.

## Unresolved Questions
- Exact representation choice (`None` vs. a separate flag vs. something else) for
  "unrestricted" is left to implementation time — a design decision, not a
  discovered fact.

## AI Implementation Instruction
Read `scripts/eventbus/auth.py`'s `require_consumer_identity` and
`_populate_token_maps`, and `scripts/eventbus/subscribe_route.py`'s topic-allowlist
block, in full before changing anything — re-verify this issue's claims against
current source, since it may have changed since filing. Do not fix this by silently
weakening the check for tokens that do have a real topic restriction configured.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/done/20260913-122501_04_tests_eventbus_test_eventbus_subscribe.py.md, implementations/done/20260913-122501_05_scripts_eventbus_auth.py.md
- **Generated at**: 20260913-143134
- **Related target files**: scripts/eventbus/auth.py, scripts/eventbus/subscribe_route.py
