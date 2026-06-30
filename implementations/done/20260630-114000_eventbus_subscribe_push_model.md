## Goal
- Confirm `/subscribe` uses EventBroker push (replay-plus-live-push), not polling — no "polling-based" descriptions found in docs.

## Scope
- Verify subscribe implementation, docs consistency, and test coverage for replay-to-push transition

## Findings

### Code verification
`scripts/eventbus/app.py:L291`: "register with broker BEFORE replay to capture events published during replay" — EventBroker push model ✓
`scripts/eventbus/app.py:L315-L321`: live delivery from `sub.queue.get()` after replay completes — no polling ✓

### Docs verification
`docs/06_eventbus_02_http_api_and_runtime.md:L84`: "no polling delay" — correctly describes push model ✓
`docs/06_eventbus_05_configuration_deploy_and_operations.md:L35`: "Subscribe polling was replaced with push-mode delivery via EventBroker" — acknowledges historical change ✓
No "polling-based" subscribe descriptions found in docs ✓

### Test coverage
`tests/test_eventbus_subscribe_transition.py`:
- `test_event_published_during_replay_delivered_via_live_push` — replay-to-push transition ✓
- `test_replay_ceil_deduplication` — dedup of events during replay ✓

## Conclusion
No changes needed — subscribe is clearly documented as push-based, not polling-based.
