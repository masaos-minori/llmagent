## Goal
Make `subscribe_route.py`'s topic-allowlist check honor `require_consumer_identity`'s
new `None`-means-unrestricted contract (REQ-002, REQ-003), instead of iterating an
empty set and rejecting every requested topic.

## Scope
Only `subscribe()`'s topic-allowlist block in `scripts/eventbus/subscribe_route.py`.
No change to `require_consumer_identity` itself (covered by the companion `auth.py`
document), consumer_id handling, offset/replay logic, or any other part of this
file.

## Assumptions
- The companion document
  `implementations/20260913-152721_01_scripts_eventbus_auth.py.md` (or its
  already-implemented result) makes `require_consumer_identity` return `"topics":
  None` when the caller's token has no configured topic restriction, and the
  existing non-empty `set[str]` otherwise — this document's change is written
  against that resolved contract.
- `_identity` is already resolved as a real `dict` by FastAPI's dependency
  injection when this function runs via `scripts/eventbus/app.py`'s route wrapper
  (confirmed by the existing `isinstance(_identity, dict)` guard already handling
  the "not yet resolved" case) — this document does not change that guard, only
  what happens inside it.

## Design decisions
Change the topic-allowlist block from unconditionally treating
`_identity.get("topics", set())` as an iterable allowlist, to first checking
whether the resolved value `is None` (unrestricted — skip the per-topic check
entirely) before iterating it as a `set[str]` (unchanged enforcement for the
non-`None` case).

## Alternatives considered
- **Default to `set()` via `.get("topics", set())` and treat an empty set as
  unrestricted directly in this file, without changing `auth.py`'s return
  contract**: rejected — this was considered as an alternative, narrower fix
  confined to this file alone, but it cannot distinguish "the map has no entry for
  this token" (should be unrestricted) from "the map has a non-empty entry that
  happens not to include this specific requested topic yet is otherwise a real
  restriction" using the *default* value alone — the ambiguity is at the source
  (`auth.py`'s return value already having discarded that distinction into a bare
  `set()`), not fixable by a different default here. The source Plan's own Design
  section reached the same conclusion: the fix must span both files.

## Implementation
### Target file
scripts/eventbus/subscribe_route.py

### Procedure
1. Change `caller_topics = _identity.get("topics", set())` followed by an
   unconditional `for t in topic: if t not in caller_topics: raise 403` to: resolve
   `caller_topics = _identity.get("topics")` (no default — `None` is a real,
   meaningful value now, not "absent"), then only enter the per-topic loop when
   `caller_topics is not None`.

### Method
Single conditional-guard change around the existing loop — no change to the loop
body itself (still `for t in topic: if t not in caller_topics: raise
HTTPException(status_code=403, ...)` when it does run).

### Details
- Do not change the outer `if isinstance(_identity, dict):` guard — it still
  correctly no-ops when `_identity` was never resolved to a dict at all (a
  separate, unrelated case from "resolved to a dict with `topics: None`").
- Do not change any other part of `subscribe()` — `consumer_id`/offset/`Last-Event-ID`
  handling below the topic-allowlist block is unaffected.
- The stale comment above this block (currently claiming `_identity` "is never
  actually resolved by FastAPI's dependency injection here... Skip topic-allowlist
  enforcement rather than reject every request when identity resolution didn't
  actually run") describes an already-resolved, unrelated historical gap (tracked
  by `issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md`,
  already fixed by `plans/done/20260912-111042_plan.md`) — leave it as-is; correcting
  stale comments unrelated to this specific fix is out of scope for this document.

## Compatibility considerations
A request whose token has a genuinely non-empty topic allowlist configured sees no
behavior change. A request whose token has no configured restriction (or an empty
one) — previously rejected for every topic — is now accepted, matching the intended
"unrestricted" behavior; no existing caller can depend on that prior rejection as
correct behavior, since it contradicted `_populate_token_maps()`'s own documented
intent from the start.

## Security considerations
Matches the corresponding note in the companion `auth.py` document: this is a
correctness fix in the permissive direction for tokens with no configured topic
restriction, with no change to enforcement for tokens that do have one configured.

## Rollback considerations
Single conditional-guard change in one file — revert this file's diff to roll
back. Independent of the companion `auth.py` document's own revert: if that
document reverts first (this file's own change staying in place),
`_identity.get("topics")` would again always be a `set` (never `None`), so this
file's `is not None` check would simply always be true — equivalent to today's
behavior, safe either way.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_subscribe.py -v` and confirm
  `test_subscribe_duplicate_consumer_id_returns_409` passes (reaches its own
  intended `409 Conflict` assertion) — this is the end-to-end confirmation that
  both this document's and the companion `auth.py` document's changes work
  together (AC-4).
- Add an integration test (HTTP-level, via `TestClient`) confirming a token with no
  `_TOKEN_TOPIC_MAP` entry can subscribe to an arbitrary topic without a 403 (AC-1,
  AC-2).
- Add an integration test confirming a token with a genuinely non-empty
  `_TOKEN_TOPIC_MAP` entry is still rejected (403) for a topic outside that entry
  (AC-3, no regression).
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no regression.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- A request for any topic succeeds (no topic-restriction 403) when
  `_identity["topics"] is None` (AC-2).
- A request for a topic outside a genuinely non-empty `_TOKEN_TOPIC_MAP` entry is
  still rejected (403) (AC-3).
- `tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409`
  passes end-to-end (AC-4).

## Out of scope
- `require_consumer_identity`'s own return-value contract change — covered by the
  companion document `implementations/20260913-152721_01_scripts_eventbus_auth.py.md`.
- Correcting the stale comment describing an already-resolved, unrelated
  authorization-wiring gap (see Details).
- Any other part of `subscribe()` (offsets, `Last-Event-ID`, broker subscription).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-163146 | 20260913-163146 | subscribe() now treats _identity.get('topics') is None as unrestricted instead of iterating an empty set |
| 2 | Add or update tests per Validation plan | Completed | 20260913-163146 | 20260913-163146 | test_subscribe_duplicate_consumer_id_returns_409 now reaches its 409 assertion (AC-4); added test_subscribe_with_restricted_topic_rejects_disallowed_topic (AC-3, no regression) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-163146 | 20260913-163146 | ruff/mypy/bandit/lint-imports/diff-cover(100%)/pre-commit all passed; full tests/eventbus/ suite: only pre-existing dlq-requeue/startup failures remain, 0 new regressions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-163146 | 20260913-163146 | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/subscribe_route.py |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/done/20260913-143134_eb005_token-topic-map-empty-set-contradiction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-151824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-152721
- **Related target files**: scripts/eventbus/subscribe_route.py